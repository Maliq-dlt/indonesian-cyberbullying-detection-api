"""Training endpoints — model training, reload, logs streaming, history."""

import asyncio
import contextlib
import logging
import os
import sys

import classifier
import routes.state as state
from fastapi import APIRouter, HTTPException, Security
from fastapi.responses import StreamingResponse
from routes.deps import get_current_user

logger = logging.getLogger("bullyguard")


def run_async_in_new_loop(coro_func, *args):
    """Helper to run an async function in a new thread."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro_func(*args))
    finally:
        loop.close()


router = APIRouter(prefix="/api", tags=["admin"], dependencies=[Security(get_current_user, scopes=["admin"])])


@router.post("/train/start")
async def api_start_training(model_type: str = "both"):
    if model_type not in ["ml", "transformer", "both"]:
        raise HTTPException(status_code=400, detail="model_type harus berupa 'ml', 'transformer', atau 'both'")

    async with state.TRAINING_LOCK:
        r = await classifier.get_redis()

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
                logger.warning("Failed to check Celery worker status", extra={"error": str(e)})

        if celery_active and r:
            try:
                status = await r.get("training_status")
                if status == "running":
                    return {"success": False, "message": "Proses pelatihan ulang sedang berjalan di Celery worker."}
            except Exception as e:
                logger.warning("Failed to read training_status from Redis", extra={"error": str(e)})
                if state.TRAINING_PROCESS is not None and state.TRAINING_PROCESS.poll() is None:
                    return {"success": False, "message": "Proses pelatihan ulang sedang berjalan."}
        else:
            if state.TRAINING_PROCESS is not None and state.TRAINING_PROCESS.poll() is None:
                return {"success": False, "message": "Proses pelatihan ulang sedang berjalan."}

        if celery_active:
            try:
                from tasks import run_retrain_task

                if r:
                    try:
                        await r.set("training_status", "running")
                    except Exception as redis_err:
                        logger.warning("Failed to update training status in Redis", extra={"error": str(redis_err)})
                run_retrain_task.delay(model_type)
                return {
                    "success": True,
                    "message": f"Proses pelatihan ulang ({model_type.upper()}) berhasil dimulai di Celery worker di latar belakang.",
                }
            except Exception as e:
                logger.error("Error starting Celery retrain, falling back to local", extra={"error": str(e)})

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        scripts_to_run = []
        if model_type in ("ml", "both"):
            scripts_to_run.append(os.path.join(base_dir, "retrain.py"))
        if model_type in ("transformer", "both"):
            scripts_to_run.append(os.path.join(base_dir, "train_transformer.py"))

        log_path = os.path.join(base_dir, "cache", "training.log")

        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"=== Memulai Pelatihan Ulang ({model_type.upper()}) (Background Process) ===\n")
        except Exception as e:
            logger.warning("Failed to clear training log", extra={"error": str(e)})

        try:
            import subprocess

            if state.LOG_FILE_HANDLE is not None:
                with contextlib.suppress(Exception):
                    state.LOG_FILE_HANDLE.close()
            state.LOG_FILE_HANDLE = open(log_path, "a", encoding="utf-8", buffering=1)
            try:
                if r:
                    try:
                        await r.set("training_status", "running")
                    except Exception as redis_err:
                        logger.warning(
                            "Failed to update training status in Redis (start)", extra={"error": str(redis_err)}
                        )

                first_script = scripts_to_run[0]
                state.TRAINING_PROCESS = subprocess.Popen(
                    [sys.executable, "-u", first_script], stdout=state.LOG_FILE_HANDLE, stderr=subprocess.STDOUT
                )

                async def monitor_training(proc, log_handle, remaining_scripts):
                    try:
                        await asyncio.to_thread(proc.wait)
                        logger.info("Training process completed", extra={"pid": proc.pid, "exit_code": proc.returncode})

                        if proc.returncode == 0 and remaining_scripts:
                            next_script = remaining_scripts[0]
                            logger.info("Running next training script", extra={"script": next_script})
                            with contextlib.suppress(Exception):
                                log_handle.write(f"\n>>> Menjalankan {os.path.basename(next_script)}...\n")
                            next_proc = subprocess.Popen(
                                [sys.executable, "-u", next_script], stdout=log_handle, stderr=subprocess.STDOUT
                            )
                            await monitor_training(next_proc, log_handle, remaining_scripts[1:])
                            return

                        with contextlib.suppress(Exception):
                            log_handle.close()

                        try:
                            r_client = await classifier.get_redis()
                            if r_client:
                                if proc.returncode == 0:
                                    await r_client.set("training_status", "completed")
                                    await r_client.publish("model_reload", "reload")
                                else:
                                    await r_client.set("training_status", "failed")
                        except Exception as redis_err:
                            logger.warning(
                                "Failed to update training status in Redis (completed)", extra={"error": str(redis_err)}
                            )

                        if proc.returncode == 0:
                            logger.info("Reloading models after training...")
                            from classifier.predictor import init_models

                            init_models()
                            logger.info("Model hot-reloaded successfully")
                    except Exception as ex:
                        logger.error("Error monitoring training process", extra={"error": str(ex)})
                        try:
                            r_client = await classifier.get_redis()
                            if r_client:
                                await r_client.set("training_status", "failed")
                        except Exception as redis_err:
                            logger.warning(
                                "Failed to update training status in Redis (error)", extra={"error": str(redis_err)}
                            )

                asyncio.create_task(monitor_training(state.TRAINING_PROCESS, state.LOG_FILE_HANDLE, scripts_to_run[1:]))

            except Exception:
                state.LOG_FILE_HANDLE.close()
                state.LOG_FILE_HANDLE = None
                if r:
                    try:
                        await r.set("training_status", "failed")
                    except Exception as redis_err:
                        logger.warning(
                            "Failed to update training status in Redis (exception)", extra={"error": str(redis_err)}
                        )
                raise
            return {
                "success": True,
                "message": f"Proses pelatihan ulang ({model_type.upper()}) berhasil dimulai di latar belakang.",
            }
        except Exception as e:
            logger.error("Error starting retrain process", extra={"error": str(e)})
            raise HTTPException(status_code=500, detail="Gagal memulai proses pelatihan ulang model.")


@router.post("/train/reload")
async def api_reload_models():
    try:
        from classifier.predictor import init_models

        await asyncio.to_thread(init_models)
        return {"success": True, "message": "Model berhasil dimuat ulang secara manual."}
    except Exception as e:
        logger.error("Error reloading models", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Gagal memuat ulang model dari disk.")


@router.get("/train/logs")
async def api_stream_logs():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(base_dir, "cache", "training.log")

    if not os.path.exists(log_path):
        return StreamingResponse(
            (line for line in ["data: Berkas log belum tersedia. Memulai proses pelatihan untuk membuat log.\n"]),
            media_type="text/event-stream",
        )

    async def log_generator():
        with open(log_path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                yield f"data: {line}"
                await asyncio.sleep(0.01)

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
                            logger.warning(
                                "Failed to read training_status from Redis (logs)", extra={"error": str(redis_err)}
                            )
                            async with state.TRAINING_LOCK:
                                is_finished = state.TRAINING_PROCESS is None or (
                                    state.TRAINING_PROCESS is not None and state.TRAINING_PROCESS.poll() is not None
                                )
                    else:
                        async with state.TRAINING_LOCK:
                            is_finished = state.TRAINING_PROCESS is None or (
                                state.TRAINING_PROCESS is not None and state.TRAINING_PROCESS.poll() is not None
                            )

                    if is_finished:
                        line = f.readline()
                        while line:
                            yield f"data: {line}"
                            line = f.readline()
                        yield "data: [SELESAI] Proses pelatihan telah selesai.\n"
                        break
                    await asyncio.sleep(0.5)

    return StreamingResponse(log_generator(), media_type="text/event-stream")


@router.get("/train/history")
async def api_get_training_history(limit: int = 50, offset: int = 0, order: str = "asc"):
    from classifier.database import get_retraining_history

    data = await get_retraining_history(limit=limit, offset=offset, order=order)
    return {
        "data": data,
        "_pagination": {
            "limit": limit,
            "offset": offset,
            "total_fetched": len(data),
            "has_more": len(data) >= limit,
            "order": order,
        },
    }
