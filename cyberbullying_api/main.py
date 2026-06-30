"""FastAPI entrypoint for BullyGuard ID.

Stage 2 security cleanup:
- Validate critical production environment variables during startup.
- Keep /health public but protect model details.
- Use safer CORS defaults and warnings for risky production configuration.
"""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
if os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists("../.env"):
    load_dotenv("../.env")
else:
    load_dotenv()

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

import classifier
import routes.state as state
from routes.admin import router as admin_router
from routes.deps import verify_api_key
from routes.predict import router as predict_router


NON_PRODUCTION_ENVS = {"local", "dev", "development", "test", "testing"}


def current_env() -> str:
    return os.getenv("ENV", "production").strip().lower()


def is_development_env() -> bool:
    return current_env() in NON_PRODUCTION_ENVS


def validate_runtime_config() -> None:
    """Fail early for unsafe production configuration."""

    env = current_env()
    api_key = os.getenv("API_KEY", "").strip()
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "").strip()

    if not is_development_env() and not api_key:
        raise RuntimeError("API_KEY must be configured when ENV is not development/test/local.")

    if not is_development_env() and (not allowed_origins or "*" in allowed_origins):
        raise RuntimeError("ALLOWED_ORIGINS must be explicit in production/staging. Do not use '*'.")

    if is_development_env() and not api_key:
        print("WARNING: API_KEY is not set. Protected endpoints may run without authentication in development mode.")

    if env == "production" and os.getenv("RATE_LIMIT_FAIL_OPEN", "").lower() in {"1", "true", "yes"}:
        print("WARNING: RATE_LIMIT_FAIL_OPEN is enabled in production. This weakens abuse protection.")


async def listen_model_reload() -> None:
    from classifier import get_redis

    await asyncio.sleep(2.0)

    while True:
        try:
            redis_client = await get_redis()
            if redis_client:
                pubsub = redis_client.pubsub()
                await pubsub.subscribe("model_reload")
                print("[Redis Pub/Sub] Subscribed to 'model_reload'.")

                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message and message.get("data") == "reload":
                        print("[Redis Pub/Sub] Received model_reload signal. Reloading model...")
                        try:
                            from classifier.predictor import init_models

                            await asyncio.to_thread(init_models)
                            print("[Redis Pub/Sub] Model reloaded successfully.")
                        except Exception as reload_err:
                            print(f"[Redis Pub/Sub] Failed to reload model: {reload_err}")
                    await asyncio.sleep(0.5)
            else:
                await asyncio.sleep(10.0)

        except asyncio.CancelledError:
            break
        except Exception as exc:
            print(f"[Redis Pub/Sub] Connection error: {exc}. Reconnecting in 10 seconds...")
            await asyncio.sleep(10.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_runtime_config()

    # Heavy model initialization is moved to a thread so the event loop is not blocked.
    await asyncio.to_thread(classifier.init_models)

    pubsub_task = asyncio.create_task(listen_model_reload())
    try:
        yield
    finally:
        pubsub_task.cancel()
        try:
            await pubsub_task
        except asyncio.CancelledError:
            pass

        try:
            if state.LOG_FILE_HANDLE is not None:
                try:
                    state.LOG_FILE_HANDLE.close()
                except Exception:
                    pass
                print("Training log file handle closed.")

            pool = getattr(classifier, "PG_POOL", None)
            if pool:
                await pool.close()
                print("PostgreSQL connection pool closed.")

            redis_client = getattr(classifier, "REDIS_CLIENT", None)
            if redis_client:
                await redis_client.close()
                print("Redis connection closed.")
        except Exception as exc:
            print(f"Warning: shutdown cleanup failed: {exc}")


app = FastAPI(
    title="🛡️ BullyGuard ID — Indonesian Cyberbullying Detection API",
    description=(
        "### BullyGuard ID API\n"
        "Sistem deteksi perundungan siber (cyberbullying) dan ujaran kebencian (hate speech) "
        "berbahasa Indonesia menggunakan arsitektur Hybrid Klasifikasi 3-Tier:\n\n"
        "* **Tier 1 (Lexicon & Machine Learning)**: Analisis berbasis leksikon abusive dan model Logistic Regression + TF-IDF.\n"
        "* **Tier 2 (Deep Learning)**: Model XLM-RoBERTa ONNX Quantized untuk pemahaman konteks semantik.\n"
        "* **Tier 3 (Cloud LLM)**: Fallback dinamis menggunakan Gemini API dan pencarian RAG (Retrieval-Augmented Generation).\n\n"
        "Dokumentasi API lengkap dengan penanganan Active Learning dan Social Media Scraper (TikTok + X/Twitter)."
    ),
    version="1.1.0",
    contact={
        "name": "BullyGuard ID Team",
        "url": "https://github.com/Maliq-dlt/indonesian-cyberbullying-detection-api",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
)

allowed_origins_raw = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
)
allowed_origins = [origin.strip() for origin in allowed_origins_raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False if "*" in allowed_origins else True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)

app.include_router(predict_router)
app.include_router(admin_router)


@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "BullyGuard ID API is running.",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "API is alive.",
        "environment": current_env(),
    }


@app.get("/models/status", dependencies=[Depends(verify_api_key)])
def models_status():
    from classifier.predictor import (
        ML_MODEL,
        PREPARED_LEXICON,
        THRESHOLDS,
        TRANSFORMER_MODEL,
        TRANSFORMER_SESSION,
    )

    return {
        "status": "online" if ML_MODEL is not None else "offline",
        "models_loaded": {
            "lexicon": len(PREPARED_LEXICON) > 0,
            "machine_learning": ML_MODEL is not None,
            "transformers_onnx": TRANSFORMER_SESSION is not None,
            "transformers_pytorch": TRANSFORMER_MODEL is not None,
        },
        "thresholds": THRESHOLDS,
    }
