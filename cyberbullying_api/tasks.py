import os
import sys
import subprocess
from celery import Celery
import redis
from dotenv import load_dotenv
if os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists("../.env"):
    load_dotenv("../.env")
else:
    load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.update(
    worker_max_tasks_per_child=1,
    task_track_started=True,
    result_expires=3600,
)

@celery_app.task
def run_retrain_task(model_type: str = "both"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ml_script_path = os.path.join(base_dir, "retrain.py")
    transformer_script_path = os.path.join(base_dir, "train_transformer.py")
    log_path = os.path.join(base_dir, "cache", "training.log")
    
    # 1. Update status to running in Redis
    try:
        r = redis.from_url(REDIS_URL)
        r.set("training_status", "running")
    except Exception as e:
        print(f"Warning in Celery task (Redis status update): {e}")
        r = None
        
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"=== Memulai Pelatihan Ulang ({model_type.upper()}) via Celery Worker ===\n")
        
    try:
        scripts_to_run = []
        if model_type in ("ml", "both"):
            scripts_to_run.append(("Machine Learning (retrain.py)", ml_script_path))
        if model_type in ("transformer", "both"):
            scripts_to_run.append(("Transformer (train_transformer.py)", transformer_script_path))
            
        for name, script_path in scripts_to_run:
            with open(log_path, "a", encoding="utf-8", buffering=1) as log_file:
                log_file.write(f"\n>>> Menjalankan {name}...\n")
                # Jalankan script dengan mode unbuffered (-u)
                proc = subprocess.Popen(
                    [sys.executable, "-u", script_path],
                    stdout=log_file,
                    stderr=subprocess.STDOUT
                )
                try:
                    proc.wait(timeout=3600)  # Timeout 1 jam per script
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()  # Bersihkan status zombie
                    if r is not None:
                        r.set("training_status", "failed")
                    raise Exception(f"Pelatihan {name} dibatalkan karena melebihi batas waktu (timeout 1 jam)")
                
            if proc.returncode != 0:
                if r is not None:
                    r.set("training_status", "failed")
                raise Exception(f"Pelatihan {name} gagal dengan exit code {proc.returncode}")
                
        if r is not None:
            r.set("training_status", "completed")
            r.publish("model_reload", "reload")
        return f"Retraining {model_type} success"
    except Exception as e:
        if r is not None:
            r.set("training_status", "failed")
        raise e
