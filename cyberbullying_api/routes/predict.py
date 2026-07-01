from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Security
from fastapi.responses import StreamingResponse
import asyncio
import json
import classifier
from models import (
    TextRequest, LexiconResponse, MLResponse, TransformerResponse, EnsembleResponse, HybridResponse,
    BatchTextRequest, BatchResponse, BatchItemResponse
)
from routes.deps import rate_limit_cloud_llm_and_batch, get_current_user
from monitoring import PREDICTIONS_TOTAL

router = APIRouter(prefix="/predict", tags=["prediction"], dependencies=[Security(get_current_user, scopes=["predict"])])

@router.post("/lexicon", response_model=LexiconResponse)
def predict_lexicon(req: TextRequest):
    return classifier.predict_lexicon(req.text, bool(req.use_fuzzy))

@router.post("/ml", response_model=MLResponse)
def predict_ml(req: TextRequest):
    if classifier.ML_MODEL is None or classifier.ML_VECTORIZER is None:
        raise HTTPException(status_code=503, detail="Model ML belum termuat.")
    return classifier.predict_ml(req.text)

@router.post("/transformers", response_model=TransformerResponse)
def predict_transformers(req: TextRequest):
    if classifier.TRANSFORMER_SESSION is None and classifier.TRANSFORMER_MODEL is None:
        raise HTTPException(status_code=503, detail="Model Transformer belum termuat.")
    try:
        return classifier.predict_transformers(req.text)
    except Exception as e:
        print(f"Error Transformer: {e}")
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal server saat menjalankan model Transformer.")

@router.post("/ensemble", response_model=EnsembleResponse)
def predict_ensemble(req: TextRequest):
    if classifier.ML_MODEL is None or classifier.ML_VECTORIZER is None:
        raise HTTPException(status_code=503, detail="Model ML belum termuat.")
    return classifier.predict_ensemble(req.text)

async def send_webhook_notification(webhook_url: str, payload: dict):
    from routes.deps import is_safe_webhook_url
    if not is_safe_webhook_url(webhook_url):
        print(f"Warning: Percobaan SSRF terdeteksi! Webhook ke {webhook_url} dibatalkan.")
        return
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.post(webhook_url, json=payload)
            print(f"Webhook sent: {res.status_code}")
    except Exception as e:
        print(f"Failed to send webhook to {webhook_url}: {e}")

@router.post("/hybrid", response_model=HybridResponse, dependencies=[Depends(rate_limit_cloud_llm_and_batch)])
async def predict_hybrid(req: TextRequest, background_tasks: BackgroundTasks):
    if classifier.ML_MODEL is None or classifier.ML_VECTORIZER is None:
        raise HTTPException(status_code=503, detail="Model ML belum termuat.")
    
    import time
    start_time = time.perf_counter()
    res = await classifier.predict_hybrid(req.text)
    execution_time_ms = (time.perf_counter() - start_time) * 1000.0
    res.execution_time = round(execution_time_ms, 2)
    
    try:
        from classifier.settings_store import get_settings
        settings = await get_settings()
        if settings.get("webhook_enabled") and settings.get("webhook_url"):
            if res.is_toxic or res.is_bully:
                payload = {
                    "event": "cyberbullying_detected",
                    "text": res.text,
                    "is_toxic": res.is_toxic,
                    "is_bully": res.is_bully,
                    "probability_toxic": res.probability_toxic,
                    "probability_bully": res.probability_bully,
                    "category": res.category,
                    "decision_source": res.decision_source,
                    "reason": res.reason
                }
                background_tasks.add_task(send_webhook_notification, settings["webhook_url"], payload)
    except Exception as e:
        print(f"Warning: Gagal mempersiapkan task webhook: {e}")
        
    try:
        PREDICTIONS_TOTAL.labels(decision_source=res.decision_source, category=res.category).inc()
    except Exception as exc:
        print(f"Warning: Gagal merekam metrik prediksi: {exc}")
        
    return res

@router.post("/batch", response_model=BatchResponse, dependencies=[Depends(rate_limit_cloud_llm_and_batch)])
async def predict_batch(req: BatchTextRequest):
    for text in req.texts:
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=422, detail="Setiap teks dalam batch tidak boleh kosong.")
        if len(text) > 500:
            raise HTTPException(status_code=422, detail="Panjang setiap teks dalam batch maksimal 500 karakter.")
            
    _batch_sem = asyncio.Semaphore(5)
    async def _limited_predict(t):
        async with _batch_sem:
            return await classifier.predict_hybrid(t)
    tasks = [_limited_predict(text) for text in req.texts]
    predictions = await asyncio.gather(*tasks)
    
    results = []
    for pred in predictions:
        results.append(BatchItemResponse(
            text=pred.text,
            is_toxic=pred.is_toxic,
            is_bully=pred.is_bully,
            probability_toxic=pred.probability_toxic,
            probability_bully=pred.probability_bully,
            category=pred.category,
            decision_source=pred.decision_source,
            reason=pred.reason,
            word_importances=pred.word_importances
        ))
    return BatchResponse(results=results)


@router.post("/hybrid/stream", dependencies=[Depends(rate_limit_cloud_llm_and_batch)])
async def predict_hybrid_stream_endpoint(req: TextRequest):
    if classifier.ML_MODEL is None or classifier.ML_VECTORIZER is None:
        raise HTTPException(status_code=503, detail="Model ML belum termuat.")

    async def event_generator():
        try:
            async for event in classifier.predict_hybrid_stream(req.text):
                # Format to JSON string and yield as SSE data
                data_dict = {
                    "chunk": event.get("chunk"),
                    "done": event.get("done"),
                }
                if event.get("final_data"):
                    final_data = event.get("final_data")
                    try:
                        PREDICTIONS_TOTAL.labels(decision_source=final_data.decision_source, category=final_data.category).inc()
                    except Exception as exc:
                        print(f"Warning: Gagal merekam metrik prediksi stream: {exc}")
                    data_dict["final_data"] = {
                        "text": final_data.text,
                        "is_toxic": final_data.is_toxic,
                        "is_bully": final_data.is_bully,
                        "probability_toxic": final_data.probability_toxic,
                        "probability_bully": final_data.probability_bully,
                        "category": final_data.category,
                        "decision_source": final_data.decision_source,
                        "reason": final_data.reason,
                        "word_importances": [
                            {"word": w.word, "weight_toxic": w.weight_toxic, "weight_bully": w.weight_bully}
                            if hasattr(w, "word") else w for w in final_data.word_importances
                        ]
                    }
                yield f"data: {json.dumps(data_dict)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

