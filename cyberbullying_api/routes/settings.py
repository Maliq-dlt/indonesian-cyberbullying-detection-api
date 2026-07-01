"""Settings endpoints — cookies, webhook config, recalibration."""

import json
import logging
import os
from urllib.parse import urlparse

import httpx
from classifier.settings_store import get_settings, save_settings
from fastapi import APIRouter, HTTPException, Security
from models import UpdateCookiesRequest
from pydantic import BaseModel
from routes.deps import get_current_user, is_safe_webhook_url

logger = logging.getLogger("bullyguard")

router = APIRouter(prefix="/api", tags=["admin"], dependencies=[Security(get_current_user, scopes=["admin"])])


class SettingsUpdate(BaseModel):
    webhook_url: str
    webhook_enabled: bool


class TestWebhookRequest(BaseModel):
    webhook_url: str


@router.post("/settings/cookies")
async def api_update_cookies(req: UpdateCookiesRequest):
    platform = req.platform.strip().lower()
    if platform not in ["tiktok", "x"]:
        raise HTTPException(status_code=400, detail="Platform harus berupa 'tiktok' atau 'x'.")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if platform == "tiktok":
        filepath = os.path.join(base_dir, "cookies_tiktok.json")
    else:
        filepath = os.path.join(base_dir, "cookies_x.json")

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(req.cookies, f, indent=4)
        return {"success": True, "message": f"Cookie sesi {platform.upper()} berhasil diperbarui."}
    except Exception as e:
        logger.error("Error updating cookies", extra={"platform": platform, "error": str(e)})
        raise HTTPException(status_code=500, detail=f"Gagal memperbarui file cookie {platform}: {str(e)}")


@router.get("/settings")
async def api_get_settings():
    return await get_settings()


@router.post("/settings")
async def api_save_settings(req: SettingsUpdate):
    if req.webhook_enabled and not is_safe_webhook_url(req.webhook_url):
        raise HTTPException(status_code=400, detail="URL Webhook tidak valid atau diblokir (SSRF Protection).")
    return await save_settings({"webhook_url": req.webhook_url, "webhook_enabled": req.webhook_enabled})


@router.post("/settings/test-webhook")
async def api_test_webhook(req: TestWebhookRequest):
    parsed = urlparse(req.webhook_url)
    scheme = parsed.scheme
    hostname = parsed.hostname or ""
    port = parsed.port
    path = parsed.path or "/"
    query = parsed.query

    if scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Skema URL harus http atau https.")
    if not hostname:
        raise HTTPException(status_code=400, detail="Hostname tidak valid.")
    if not is_safe_webhook_url(req.webhook_url):
        raise HTTPException(status_code=400, detail="URL Webhook tidak valid atau diblokir (SSRF Protection).")

    # Build a fully sanitised URL from trusted-parsed components only (SSRF mitigation)
    netloc = f"{hostname}:{port}" if port else hostname
    safe_url = f"{scheme}://{netloc}{path}"
    if query:
        safe_url = f"{safe_url}?{query}"

    payload = {
        "event": "webhook_test",
        "timestamp": "2026-06-05T00:00:00Z",
        "message": "Ini adalah payload uji coba integrasi webhook BullyGuard ID.",
        "sample_data": {"text": "kamu sangat hebat sekali", "is_toxic": False, "is_bully": False, "category": "Aman"},
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.post(safe_url, json=payload)
            return {"success": True, "status_code": res.status_code, "response": res.text[:200]}
    except Exception:
        raise HTTPException(
            status_code=400, detail="Gagal menghubungi webhook. Periksa URL dan pastikan server webhook aktif."
        )


@router.post("/settings/recalibrate")
async def api_recalibrate_ensemble():
    try:
        import sqlite3

        import numpy as np
        from classifier.db_config import decrypt_text, get_pg_pool
        from classifier.predictor import predict_ml, predict_transformer_raw

        records = []
        pool = await get_pg_pool()
        if pool:
            try:
                async with pool.acquire() as conn:
                    rows = await conn.fetch("""
                        SELECT encrypted_text, is_toxic, is_bully
                        FROM classification_memory
                        WHERE is_validated = 1
                    """)
                    for r in rows:
                        records.append(
                            {
                                "text": decrypt_text(r["encrypted_text"]),
                                "is_toxic": int(r["is_toxic"]),
                                "is_bully": int(r["is_bully"]),
                            }
                        )
            except Exception as pg_err:
                logger.error("Error fetching validation data from PostgreSQL", extra={"error": str(pg_err)})

        if not records:
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                db_path = os.path.join(base_dir, "cache", "cloud_llm_cache.db")
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT encrypted_text, is_toxic, is_bully
                        FROM classification_memory
                        WHERE is_validated = 1
                    """)
                    rows = cursor.fetchall()
                    for r in rows:
                        records.append(
                            {
                                "text": decrypt_text(r["encrypted_text"]),
                                "is_toxic": int(r["is_toxic"]),
                                "is_bully": int(r["is_bully"]),
                            }
                        )
                    conn.close()
            except Exception as sq_err:
                logger.error("Error fetching validation data from SQLite", extra={"error": str(sq_err)})

        if len(records) < 5:
            default_w = {"ml_toxic": 0.5, "tr_toxic": 0.5, "ml_bully": 0.65, "tr_bully": 0.35}
            settings = await get_settings()
            settings["ensemble_weights"] = default_w
            await save_settings(settings)
            return {
                "success": True,
                "calibrated": False,
                "message": f"Jumlah data tervalidasi ({len(records)}) terlalu sedikit (minimal 5). Menggunakan bobot default.",
                "weights": default_w,
            }

        y_toxic, y_bully = [], []
        ml_toxic_probs, ml_bully_probs = [], []
        tr_toxic_probs, tr_bully_probs = [], []

        for rec in records:
            text = rec["text"]
            ml_res = predict_ml(text)
            tr_res = predict_transformer_raw(text)

            y_toxic.append(rec["is_toxic"])
            y_bully.append(rec["is_bully"])
            ml_toxic_probs.append(ml_res.probability_toxic)
            ml_bully_probs.append(ml_res.probability_bully)
            tr_toxic_probs.append(tr_res["toxic_prob"])
            tr_bully_probs.append(tr_res["bully_prob"])

        best_w_toxic, min_mse_toxic = 0.5, float("inf")
        best_w_bully, min_mse_bully = 0.65, float("inf")

        grid = np.linspace(0.15, 0.85, 71)

        for w in grid:
            se_toxic = [
                (w * ml_toxic_probs[i] + (1 - w) * tr_toxic_probs[i] - y_toxic[i]) ** 2 for i in range(len(records))
            ]
            mse_t = sum(se_toxic) / len(records)
            if mse_t < min_mse_toxic:
                min_mse_toxic = mse_t
                best_w_toxic = float(w)

            se_bully = [
                (w * ml_bully_probs[i] + (1 - w) * tr_bully_probs[i] - y_bully[i]) ** 2 for i in range(len(records))
            ]
            mse_b = sum(se_bully) / len(records)
            if mse_b < min_mse_bully:
                min_mse_bully = mse_b
                best_w_bully = float(w)

        w_ml_toxic = round(best_w_toxic, 2)
        w_tr_toxic = round(1.0 - w_ml_toxic, 2)
        w_ml_bully = round(best_w_bully, 2)
        w_tr_bully = round(1.0 - w_ml_bully, 2)

        new_w = {"ml_toxic": w_ml_toxic, "tr_toxic": w_tr_toxic, "ml_bully": w_ml_bully, "tr_bully": w_tr_bully}

        settings = await get_settings()
        settings["ensemble_weights"] = new_w
        await save_settings(settings)

        return {
            "success": True,
            "calibrated": True,
            "sample_size": len(records),
            "message": f"Optimal weights calibrated successfully using {len(records)} validated samples.",
            "weights": new_w,
        }
    except Exception as e:
        logger.error("Error during recalibration", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Gagal melakukan kalibrasi bobot ensemble: {str(e)}")
