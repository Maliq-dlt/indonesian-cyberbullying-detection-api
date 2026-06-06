import os
import sys
import subprocess
from celery import Celery
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.update(
    worker_max_tasks_per_child=1,
    task_track_started=True,
    result_expires=3600,
)

@celery_app.task
def run_retrain_task():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(base_dir, "retrain.py")
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
        f.write("=== Memulai Pelatihan Ulang via Celery Worker ===\n")
        
    try:
        with open(log_path, "a", encoding="utf-8", buffering=1) as log_file:
            # Jalankan retrain.py dengan mode unbuffered (-u)
            proc = subprocess.Popen(
                [sys.executable, "-u", script_path],
                stdout=log_file,
                stderr=subprocess.STDOUT
            )
            proc.wait()
            
        if proc.returncode == 0:
            if r is not None:
                r.set("training_status", "completed")
                r.publish("model_reload", "reload")
            return "Retraining success"
        else:
            if r is not None:
                r.set("training_status", "failed")
            raise Exception(f"Retraining failed with exit code {proc.returncode}")
    except Exception as e:
        if r is not None:
            r.set("training_status", "failed")
        raise e
