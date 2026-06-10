from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
import asyncio
import os
import classifier
from models import (
    ScrapeTikTokRequest, ScrapeXRequest, ScrapeResponse, ReallocateRequest, ReallocateResponse,
    UpdateCookiesRequest, BulkReallocateRequest
)
from routes.deps import verify_api_key, rate_limit_cloud_llm_and_batch
import routes.state as state

router = APIRouter(prefix="/api", tags=["admin"])

@router.post("/scrape/tiktok", response_model=ScrapeResponse, dependencies=[Depends(verify_api_key), Depends(rate_limit_cloud_llm_and_batch)])
async def api_scrape_tiktok(req: ScrapeTikTokRequest):
    try:
        from scraper.tiktok import scrape_tiktok_comments
        max_comments = req.max_comments if req.max_comments is not None else 20
        comments, success = await scrape_tiktok_comments(req.url, max_comments)
        if not success:
            raise HTTPException(status_code=502, detail="Gagal mengikis data dari TikTok. Server tujuan tidak merespons atau memblokir scraping.")
        return ScrapeResponse(success=success, count=len(comments), data=comments)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error scraping TikTok: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengikis data komentar TikTok. Silakan coba lagi nanti.")


@router.post("/scrape/x", response_model=ScrapeResponse, dependencies=[Depends(verify_api_key), Depends(rate_limit_cloud_llm_and_batch)])
async def api_scrape_x(req: ScrapeXRequest):
    try:
        from scraper.twitter import scrape_x_tweets
        max_tweets = req.max_tweets if req.max_tweets is not None else 20
        tweets, success = await scrape_x_tweets(req.url, max_tweets)
        if not success:
            raise HTTPException(status_code=502, detail="Gagal mengikis data dari X. Server tujuan tidak merespons atau memblokir scraping.")
        return ScrapeResponse(success=success, count=len(tweets), data=tweets)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error scraping X: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengikis data replies X/Twitter. Silakan coba lagi nanti.")


@router.get("/data/categorized", dependencies=[Depends(verify_api_key)])
async def api_get_categorized_data(
    limit: int = 500,
    confidence_min: float | None = None,
    confidence_max: float | None = None,
    decision_source: str | None = None,
    search: str | None = None
):
    try:
        from classifier import get_categorized_memory
        data = await get_categorized_memory(
            limit=limit,
            confidence_min=confidence_min,
            confidence_max=confidence_max,
            decision_source=decision_source,
            search=search
        )
        return data
    except Exception as e:
        print(f"Error fetching memory data: {e}")
        raise HTTPException(status_code=500, detail="Gagal mengambil memori data klasifikasi dari basis data.")


@router.post("/data/reallocate", response_model=ReallocateResponse, dependencies=[Depends(verify_api_key)])
async def api_reallocate_data(req: ReallocateRequest):
    try:
        from classifier import update_validation_status
        success = await update_validation_status(req.text, req.new_is_toxic, req.new_is_bully, is_validated=1)
        if success:
            return ReallocateResponse(success=True, message="Data berhasil direlokasi dan divalidasi.")
        else:
            return ReallocateResponse(success=False, message="Gagal merekam relokasi data ke basis data.")
    except Exception as e:
        print(f"Error reallocating data: {e}")
        raise HTTPException(status_code=500, detail="Gagal memperbarui alokasi kategori data di database.")


@router.post("/data/reallocate/bulk", response_model=ReallocateResponse, dependencies=[Depends(verify_api_key)])
async def api_reallocate_data_bulk(req: BulkReallocateRequest):
    try:
        from classifier import update_validation_status
        success_count = 0
        for item in req.items:
            success = await update_validation_status(item.text, item.new_is_toxic, item.new_is_bully, is_validated=1)
            if success:
                success_count += 1
                
        if success_count == len(req.items):
            return ReallocateResponse(success=True, message=f"Semua ({success_count}) data berhasil direlokasi dan divalidasi.")
        elif success_count > 0:
            return ReallocateResponse(success=True, message=f"Sebagian ({success_count}/{len(req.items)}) data berhasil direlokasi dan divalidasi.")
        else:
            return ReallocateResponse(success=False, message="Gagal merekam relokasi data massal ke basis data.")
    except Exception as e:
        print(f"Error bulk reallocating data: {e}")
        raise HTTPException(status_code=500, detail="Gagal memperbarui alokasi kategori data massal di database.")


@router.post("/train/start", dependencies=[Depends(verify_api_key)])
async def api_start_training():
    async with state.TRAINING_LOCK:
        r = await classifier.get_redis()
        
        # 1. Cek apakah Celery worker aktif
        celery_active = False
        if r:
            try:
                from tasks import celery_app
                inspect = celery_app.control.inspect(timeout=0.5)
                if inspect:
                    workers = inspect.ping()
                    if workers:
                        celery_active = True
            except Exception as e:
                print(f"Warning: Gagal memeriksa status Celery worker: {e}")
            
        # 2. Cek status ketersediaan pelatihan
        if celery_active and r:
            try:
                status = await r.get("training_status")
                if status == "running":
                    return {"success": False, "message": "Proses pelatihan ulang sedang berjalan di Celery worker."}
            except Exception as e:
                print(f"Warning: Gagal membaca training_status dari Redis: {e}")
                if state.TRAINING_PROCESS is not None and state.TRAINING_PROCESS.poll() is None:
                    return {"success": False, "message": "Proses pelatihan ulang sedang berjalan."}
        else:
            if state.TRAINING_PROCESS is not None and state.TRAINING_PROCESS.poll() is None:
                return {"success": False, "message": "Proses pelatihan ulang sedang berjalan."}
                
        # 3. Memicu pelatihan Celery jika aktif
        if celery_active:
            try:
                from tasks import run_retrain_task
                if r:
                    try:
                        await r.set("training_status", "running")
                    except Exception as redis_err:
                        print(f"Warning: Gagal update status di Redis: {redis_err}")
                getattr(run_retrain_task, "delay")()
                return {"success": True, "message": "Proses pelatihan ulang berhasil dimulai di Celery worker di latar belakang."}
            except Exception as e:
                print(f"Error starting Celery retrain: {e}. Fallback ke mode lokal...")
                
        # 4. Fallback ke subprocess lokal
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_path = os.path.join(base_dir, "retrain.py")
        log_path = os.path.join(base_dir, "cache", "training.log")
        
        # Bersihkan file log lama
        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("=== Memulai Pelatihan Ulang (Background Process) ===\n")
        except Exception as e:
            print(f"Warning: Gagal membersihkan log: {e}")
            
        try:
            import sys
            import subprocess
            if state.LOG_FILE_HANDLE is not None:
                try:
                    state.LOG_FILE_HANDLE.close()
                except Exception:
                    pass
            state.LOG_FILE_HANDLE = open(log_path, "a", encoding="utf-8", buffering=1)
            try:
                if r:
                    try:
                        await r.set("training_status", "running")
                    except Exception as redis_err:
                        print(f"Warning: Gagal update status di Redis: {redis_err}")
                state.TRAINING_PROCESS = subprocess.Popen(
                    [sys.executable, "-u", script_path],
                    stdout=state.LOG_FILE_HANDLE,
                    stderr=subprocess.STDOUT
                )
                
                async def monitor_training(proc, log_handle):
                    try:
                        await asyncio.to_thread(proc.wait)
                        print(f"Proses retraining selesai dengan kode keluar: {proc.returncode}")
                        try:
                            log_handle.close()
                        except Exception:
                            pass
                        
                        try:
                            r_client = await classifier.get_redis()
                            if r_client:
                                if proc.returncode == 0:
                                    await r_client.set("training_status", "completed")
                                    await r_client.publish("model_reload", "reload")
                                else:
                                    await r_client.set("training_status", "failed")
                        except Exception as redis_err:
                            print(f"Warning: Gagal update status di Redis setelah selesai: {redis_err}")
                                
                        if proc.returncode == 0:
                            print("Memanggil init_models() untuk memuat ulang model...")
                            from classifier.predictor import init_models
                            init_models()
                            print("Model berhasil di-hot-reload secara otomatis!")
                    except Exception as ex:
                        print(f"Error memantau proses retraining: {ex}")
                        try:
                            r_client = await classifier.get_redis()
                            if r_client:
                                await r_client.set("training_status", "failed")
                        except Exception as redis_err:
                            print(f"Warning: Gagal update status di Redis setelah error: {redis_err}")
                
                asyncio.create_task(monitor_training(state.TRAINING_PROCESS, state.LOG_FILE_HANDLE))
                
            except Exception:
                state.LOG_FILE_HANDLE.close()
                state.LOG_FILE_HANDLE = None
                if r:
                    try:
                        await r.set("training_status", "failed")
                    except Exception as redis_err:
                        print(f"Warning: Gagal update status di Redis setelah error: {redis_err}")
                raise
            return {"success": True, "message": "Proses pelatihan ulang berhasil dimulai di latar belakang."}
        except Exception as e:
            print(f"Error starting retrain process: {e}")
            raise HTTPException(status_code=500, detail="Gagal memulai proses pelatihan ulang model.")


@router.post("/train/reload", dependencies=[Depends(verify_api_key)])
async def api_reload_models():
    try:
        from classifier.predictor import init_models
        init_models()
        return {"success": True, "message": "Model berhasil dimuat ulang secara manual."}
    except Exception as e:
        print(f"Error reloading models: {e}")
        raise HTTPException(status_code=500, detail="Gagal memuat ulang model dari disk.")


@router.get("/train/logs", dependencies=[Depends(verify_api_key)])
async def api_stream_logs():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(base_dir, "cache", "training.log")
    
    if not os.path.exists(log_path):
        return StreamingResponse(
            (line for line in ["data: Berkas log belum tersedia. Memulai proses pelatihan untuk membuat log.\n"]),
            media_type="text/event-stream"
        )
        
    async def log_generator():
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            # Baca konten yang sudah ada
            for line in f:
                yield f"data: {line}"
                await asyncio.sleep(0.01)
                
            # Terus membaca baris baru secara asinkron
            while True:
                line = f.readline()
                if line:
                    yield f"data: {line}"
                else:
                    r = await classifier.get_redis()
                    is_finished = False
                    if r:
                        try:
                            status = await r.get("training_status")
                            if status in ["completed", "failed"]:
                                is_finished = True
                        except Exception as redis_err:
                            print(f"Warning: Gagal membaca training_status dari Redis di logs: {redis_err}")
                            async with state.TRAINING_LOCK:
                                is_finished = state.TRAINING_PROCESS is None or (state.TRAINING_PROCESS is not None and state.TRAINING_PROCESS.poll() is not None)
                    else:
                        async with state.TRAINING_LOCK:
                            is_finished = state.TRAINING_PROCESS is None or (state.TRAINING_PROCESS is not None and state.TRAINING_PROCESS.poll() is not None)
                            
                    if is_finished:
                        # Cek sekali lagi apakah ada data tersisa
                        line = f.readline()
                        while line:
                            yield f"data: {line}"
                            line = f.readline()
                        yield "data: [SELESAI] Proses pelatihan telah selesai.\n"
                        break
                    await asyncio.sleep(0.5)
                    
    return StreamingResponse(log_generator(), media_type="text/event-stream")


@router.post("/settings/cookies", dependencies=[Depends(verify_api_key)])
async def api_update_cookies(req: UpdateCookiesRequest):
    import json
    
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
        print(f"Error updating cookies for {platform}: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal memperbarui file cookie {platform}: {str(e)}")


from pydantic import BaseModel
from classifier.settings_store import get_settings, save_settings
from classifier.database import get_retraining_history

class SettingsUpdate(BaseModel):
    webhook_url: str
    webhook_enabled: bool

@router.get("/settings", dependencies=[Depends(verify_api_key)])
async def api_get_settings():
    return await get_settings()

@router.post("/settings", dependencies=[Depends(verify_api_key)])
async def api_save_settings(req: SettingsUpdate):
    if req.webhook_enabled:
        from routes.deps import is_safe_webhook_url
        if not is_safe_webhook_url(req.webhook_url):
            raise HTTPException(status_code=400, detail="URL Webhook tidak valid atau diblokir (SSRF Protection).")
    return await save_settings({
        "webhook_url": req.webhook_url,
        "webhook_enabled": req.webhook_enabled
    })

@router.get("/train/history", dependencies=[Depends(verify_api_key)])
async def api_get_training_history():
    return await get_retraining_history()


class TestWebhookRequest(BaseModel):
    webhook_url: str

@router.post("/settings/test-webhook", dependencies=[Depends(verify_api_key)])
async def api_test_webhook(req: TestWebhookRequest):
    from routes.deps import is_safe_webhook_url
    if not is_safe_webhook_url(req.webhook_url):
        raise HTTPException(status_code=400, detail="URL Webhook tidak valid atau diblokir (SSRF Protection).")
    import httpx
    payload = {
        "event": "webhook_test",
        "timestamp": "2026-06-05T00:00:00Z",
        "message": "Ini adalah payload uji coba integrasi webhook BullyGuard ID.",
        "sample_data": {
            "text": "kamu sangat hebat sekali",
            "is_toxic": False,
            "is_bully": False,
            "category": "Aman"
        }
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.post(req.webhook_url, json=payload)
            return {
                "success": True, 
                "status_code": res.status_code, 
                "response": res.text[:200]
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail="Gagal menghubungi webhook. Periksa URL dan pastikan server webhook aktif.")

@router.post("/settings/recalibrate", dependencies=[Depends(verify_api_key)])
async def api_recalibrate_ensemble():
    try:
        from classifier.db_config import get_pg_pool, decrypt_text
        from classifier.settings_store import get_settings, save_settings
        from classifier.predictor import predict_ml, predict_transformer_raw
        import sqlite3
        import numpy as np
        
        # 1. Ambil data tervalidasi (is_validated = 1)
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
                        records.append({
                            "text": decrypt_text(r["encrypted_text"]),
                            "is_toxic": int(r["is_toxic"]),
                            "is_bully": int(r["is_bully"])
                        })
            except Exception as pg_err:
                print(f"Error fetching validation data from PostgreSQL: {pg_err}")
                
        if not records:
            # Fallback ke SQLite
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
                        records.append({
                            "text": decrypt_text(r["encrypted_text"]),
                            "is_toxic": int(r["is_toxic"]),
                            "is_bully": int(r["is_bully"])
                        })
                    conn.close()
            except Exception as sq_err:
                print(f"Error fetching validation data from SQLite: {sq_err}")

        # Jika kurang dari 5 sampel, gunakan bobot default
        if len(records) < 5:
            default_w = {
                "ml_toxic": 0.5,
                "tr_toxic": 0.5,
                "ml_bully": 0.65,
                "tr_bully": 0.35
            }
            settings = await get_settings()
            settings["ensemble_weights"] = default_w
            await save_settings(settings)
            return {
                "success": True,
                "calibrated": False,
                "message": f"Jumlah data tervalidasi ({len(records)}) terlalu sedikit (minimal 5). Menggunakan bobot default.",
                "weights": default_w
            }
            
        # 2. Hitung probabilitas dari ML dan Transformer
        y_toxic = []
        y_bully = []
        ml_toxic_probs = []
        ml_bully_probs = []
        tr_toxic_probs = []
        tr_bully_probs = []
        
        for rec in records:
            text = rec["text"]
            y_t = rec["is_toxic"]
            y_b = rec["is_bully"]
            
            # Predict ML
            ml_res = predict_ml(text)
            ml_t_p = ml_res.probability_toxic
            ml_b_p = ml_res.probability_bully
            
            # Predict Transformer
            tr_res = predict_transformer_raw(text)
            tr_t_p = tr_res["toxic_prob"]
            tr_b_p = tr_res["bully_prob"]
            
            y_toxic.append(y_t)
            y_bully.append(y_b)
            ml_toxic_probs.append(ml_t_p)
            ml_bully_probs.append(ml_b_p)
            tr_toxic_probs.append(tr_t_p)
            tr_bully_probs.append(tr_b_p)
            
        # 3. Grid search optimal weights to minimize Mean Squared Error (MSE)
        best_w_toxic = 0.5
        min_mse_toxic = float('inf')
        
        best_w_bully = 0.65
        min_mse_bully = float('inf')
        
        # Grid search dari 0.15 ke 0.85
        grid = np.linspace(0.15, 0.85, 71) # interval 0.01
        
        for w in grid:
            # Toxic MSE
            se_toxic = []
            for i in range(len(records)):
                p_comb = w * ml_toxic_probs[i] + (1 - w) * tr_toxic_probs[i]
                se_toxic.append((p_comb - y_toxic[i]) ** 2)
            mse_t = sum(se_toxic) / len(records)
            if mse_t < min_mse_toxic:
                min_mse_toxic = mse_t
                best_w_toxic = float(w)
                
            # Bully MSE
            se_bully = []
            for i in range(len(records)):
                p_comb = w * ml_bully_probs[i] + (1 - w) * tr_bully_probs[i]
                se_bully.append((p_comb - y_bully[i]) ** 2)
            mse_b = sum(se_bully) / len(records)
            if mse_b < min_mse_bully:
                min_mse_bully = mse_b
                best_w_bully = float(w)
                
        # Bulatkan hasil ke 2 desimal
        w_ml_toxic = round(best_w_toxic, 2)
        w_tr_toxic = round(1.0 - w_ml_toxic, 2)
        w_ml_bully = round(best_w_bully, 2)
        w_tr_bully = round(1.0 - w_ml_bully, 2)
        
        new_w = {
            "ml_toxic": w_ml_toxic,
            "tr_toxic": w_tr_toxic,
            "ml_bully": w_ml_bully,
            "tr_bully": w_tr_bully
        }
        
        # Simpan ke settings
        settings = await get_settings()
        settings["ensemble_weights"] = new_w
        await save_settings(settings)
        
        return {
            "success": True,
            "calibrated": True,
            "sample_size": len(records),
            "message": f"Optimal weights calibrated successfully using {len(records)} validated samples.",
            "weights": new_w
        }
    except Exception as e:
        print(f"Error during recalibration: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal melakukan kalibrasi bobot ensemble: {str(e)}")



