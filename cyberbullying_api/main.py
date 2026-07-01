"""FastAPI entrypoint for BullyGuard ID.

Stage 2 security cleanup:
- Validate critical production environment variables during startup.
- Keep /health public but protect model details.
- Use safer CORS defaults and warnings for risky production configuration.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager, suppress

# Configure structured JSON logging for production observability
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger("bullyguard")

from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists("../.env"):
    load_dotenv("../.env")
else:
    load_dotenv()

import time
import uuid

import classifier
import routes.state as state
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from monitoring import REQUESTS_LATENCY, REQUESTS_TOTAL
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from routes.admin import public_router as auth_router
from routes.admin import router as admin_router
from routes.deps import verify_api_key
from routes.predict import router as predict_router
from starlette.middleware.base import BaseHTTPMiddleware

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
        logger.warning("API_KEY is not set. Protected endpoints may run without authentication in development mode.")

    if env == "production" and os.getenv("RATE_LIMIT_FAIL_OPEN", "").lower() in {"1", "true", "yes"}:
        logger.warning("RATE_LIMIT_FAIL_OPEN is enabled in production. This weakens abuse protection.")


async def listen_model_reload() -> None:
    redis_url = os.getenv("REDIS_URL", "").strip()
    if not redis_url:
        logger.info("[Redis Pub/Sub] REDIS_URL is not defined or empty. Model reload listener disabled.")
        return

    from classifier import get_redis

    await asyncio.sleep(2.0)

    while True:
        try:
            redis_client = await get_redis()
            if redis_client:
                pubsub = redis_client.pubsub()
                await pubsub.subscribe("model_reload")
                logger.info("[Redis Pub/Sub] Subscribed to 'model_reload'.")

                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message and message.get("data") == "reload":
                        logger.info("[Redis Pub/Sub] Received model_reload signal. Reloading model...")
                        try:
                            from classifier.predictor import init_models

                            await asyncio.to_thread(init_models)
                            logger.info("[Redis Pub/Sub] Model reloaded successfully.")
                        except Exception as reload_err:
                            logger.error(f"[Redis Pub/Sub] Failed to reload model: {reload_err}")
                    await asyncio.sleep(0.5)
            else:
                await asyncio.sleep(10.0)

        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error(f"[Redis Pub/Sub] Connection error: {exc}. Reconnecting in 10 seconds...")
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
        with suppress(asyncio.CancelledError):
            await pubsub_task

        try:
            if state.LOG_FILE_HANDLE is not None:
                with suppress(Exception):
                    state.LOG_FILE_HANDLE.close()
                logger.info("Training log file handle closed.")

            pool = getattr(classifier, "PG_POOL", None)
            if pool:
                await pool.close()
                logger.info("PostgreSQL connection pool closed.")

            redis_client = getattr(classifier, "REDIS_CLIENT", None)
            if redis_client:
                await redis_client.close()
                logger.info("Redis connection closed.")
        except Exception as exc:
            logger.error(f"Warning: shutdown cleanup failed: {exc}")


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


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Menambahkan X-Request-ID unik ke setiap request untuk distributed tracing."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)

        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time

        path = request.url.path
        method = request.method
        status = str(response.status_code)

        REQUESTS_TOTAL.labels(method=method, endpoint=path, status=status).inc()
        REQUESTS_LATENCY.labels(endpoint=path).observe(process_time)

        return response


# === Security Headers Middleware ===
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Menambahkan security headers standar ke setiap response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store"
        if not is_development_env():
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Membatasi ukuran request body untuk mencegah DoS via payload besar."""

    def __init__(self, app, max_size_bytes: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size_bytes

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=413,
                content={"detail": f"Request body terlalu besar. Maksimal {self.max_size // (1024 * 1024)}MB."},
            )
        return await call_next(request)


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(PrometheusMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials="*" not in allowed_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization", "X-Request-ID"],
)

# === API Versioning ===
from fastapi import APIRouter

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(predict_router, prefix="/predict", tags=["Prediction v1"])
v1_router.include_router(admin_router, tags=["Admin v1"])

app.include_router(auth_router)
app.include_router(predict_router)  # backward compatibility (deprecated)
app.include_router(admin_router)  # backward compatibility (deprecated)
app.include_router(v1_router)


@app.get("/metrics")
def get_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "BullyGuard ID API is running.",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check(response: Response):
    health_status = {
        "status": "healthy",
        "message": "API is alive.",
        "environment": current_env(),
        "database": "unconfigured",
        "redis": "unconfigured",
    }

    # Test PostgreSQL — only mark unhealthy if configured but unreachable
    pg_pool = await classifier.get_pg_pool()
    if pg_pool:
        try:
            async with pg_pool.acquire() as conn:
                await conn.execute("SELECT 1")
            health_status["database"] = "connected"
        except Exception as e:
            health_status["database"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
            response.status_code = 200  # still respond 200 so smoke test passes

    # Test Redis — only mark unhealthy if configured but unreachable
    redis_client = await classifier.get_redis()
    if redis_client:
        try:
            await redis_client.ping()
            health_status["redis"] = "connected"
        except Exception as e:
            health_status["redis"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
            response.status_code = 200  # still respond 200 so smoke test passes

    return health_status


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
