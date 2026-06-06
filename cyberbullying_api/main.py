from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from contextlib import asynccontextmanager
import os
import classifier
import routes.state as state
from routes.predict import router as predict_router
from routes.admin import router as admin_router

async def listen_model_reload():
    from classifier import get_redis
    await asyncio.sleep(2.0)
    while True:
        try:
            r = await get_redis()
            if r:
                pubsub = r.pubsub()
                await pubsub.subscribe("model_reload")
                print("[Redis Pub/Sub] Berhasil subskripsi ke channel 'model_reload'.")
                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message and message["data"] == "reload":
                        print("[Redis Pub/Sub] Menerima sinyal model_reload. Memuat ulang model...")
                        try:
                            from classifier.predictor import init_models
                            await asyncio.to_thread(init_models)
                            print("[Redis Pub/Sub] Model berhasil dimuat ulang secara dinamis!")
                        except Exception as reload_err:
                            print(f"[Redis Pub/Sub] Gagal memuat ulang model: {reload_err}")
                    await asyncio.sleep(0.5)
            else:
                await asyncio.sleep(10.0)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[Redis Pub/Sub] Koneksi terputus atau error: {e}. Menghubungkan kembali dalam 10 detik...")
            await asyncio.sleep(10.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Jalankan inisialisasi model yang berat di thread pool agar tidak memblokir event loop
    await asyncio.to_thread(classifier.init_models)
    if not state.API_KEY_ENV:
        print("WARNING: Variabel lingkungan API_KEY tidak diatur! API berjalan tanpa autentikasi (Terbuka untuk Publik).")
    
    pubsub_task = asyncio.create_task(listen_model_reload())
    yield
    pubsub_task.cancel()
    try:
        await pubsub_task
    except asyncio.CancelledError:
        pass
    # Pembersihan (Cleanup) koneksi
    try:
        if state.LOG_FILE_HANDLE is not None:
            try:
                state.LOG_FILE_HANDLE.close()
            except Exception:
                pass
            print("File handle training log berhasil ditutup.")
            
        pool = getattr(classifier, "PG_POOL", None)
        if pool:
            await pool.close()
            print("Koneksi PostgreSQL berhasil ditutup.")
        redis_client = getattr(classifier, "REDIS_CLIENT", None)
        if redis_client:
            await redis_client.close()
            print("Koneksi Redis berhasil ditutup.")
    except Exception as e:
        print(f"Peringatan: Gagal melakukan cleanup pada shutdown: {e}")

app = FastAPI(
    title="Cyberbullying & Hate Speech Detection API",
    description="API untuk mendeteksi cyberbullying bahasa Indonesia menggunakan pendekatan Leksikon, Machine Learning, dan Deep Learning Transformers.",
    version="1.0.0",
    lifespan=lifespan
)

allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173")
allowed_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True if "*" not in allowed_origins else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(predict_router)
app.include_router(admin_router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Cyberbullying & Hate Speech Detection API is running."
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "API is alive and running."
    }

@app.get("/models/status")
def models_status():
    from classifier.predictor import ML_MODEL, PREPARED_LEXICON, TRANSFORMER_SESSION, TRANSFORMER_MODEL, THRESHOLDS
    return {
        "status": "online" if ML_MODEL is not None else "offline",
        "models_loaded": {
            "lexicon": len(PREPARED_LEXICON) > 0,
            "machine_learning": ML_MODEL is not None,
            "transformers_onnx": TRANSFORMER_SESSION is not None,
            "transformers_pytorch": TRANSFORMER_MODEL is not None
        },
        "thresholds": THRESHOLDS
    }
