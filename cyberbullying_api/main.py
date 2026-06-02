from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from models import *
import classifier

app = FastAPI(
    title="Cyberbullying & Hate Speech Detection API",
    description="API untuk mendeteksi cyberbullying bahasa Indonesia menggunakan pendekatan Leksikon, Machine Learning, dan Deep Learning Transformers.",
    version="1.0.0"
)

import os

allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True if "*" not in allowed_origins else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    classifier.init_models()

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
    return {
        "status": "online" if classifier.ML_MODEL is not None else "offline",
        "models_loaded": {
            "lexicon": len(classifier.PREPARED_LEXICON) > 0,
            "machine_learning": classifier.ML_MODEL is not None,
            "transformers_onnx": classifier.TRANSFORMER_SESSION is not None,
            "transformers_pytorch": classifier.TRANSFORMER_MODEL is not None
        },
        "thresholds": classifier.THRESHOLDS
    }

@app.post("/predict/lexicon", response_model=LexiconResponse)
def predict_lexicon(req: TextRequest):
    return classifier.predict_lexicon(req.text, req.use_fuzzy)

@app.post("/predict/ml", response_model=MLResponse)
def predict_ml(req: TextRequest):
    if classifier.ML_MODEL is None or classifier.ML_VECTORIZER is None:
        raise HTTPException(status_code=503, detail="Model ML belum termuat.")
    return classifier.predict_ml(req.text)

@app.post("/predict/transformers", response_model=TransformerResponse)
def predict_transformers(req: TextRequest):
    if classifier.TRANSFORMER_SESSION is None and classifier.TRANSFORMER_MODEL is None:
        raise HTTPException(status_code=503, detail="Model Transformer belum termuat.")
    try:
        return classifier.predict_transformers(req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/ensemble", response_model=EnsembleResponse)
def predict_ensemble(req: TextRequest):
    if classifier.ML_MODEL is None or classifier.ML_VECTORIZER is None:
        raise HTTPException(status_code=503, detail="Model ML belum termuat.")
    return classifier.predict_ensemble(req.text)

@app.post("/predict/hybrid", response_model=HybridResponse)
async def predict_hybrid(req: TextRequest):
    if classifier.ML_MODEL is None or classifier.ML_VECTORIZER is None:
        raise HTTPException(status_code=503, detail="Model ML belum termuat.")
    return await classifier.predict_hybrid(req.text)

@app.post("/predict/batch", response_model=BatchResponse)
async def predict_batch(req: BatchTextRequest):
    for text in req.texts:
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=422, detail="Setiap teks dalam batch tidak boleh kosong.")
        if len(text) > 500:
            raise HTTPException(status_code=422, detail="Panjang setiap teks dalam batch maksimal 500 karakter.")
            
    tasks = [classifier.predict_hybrid(text) for text in req.texts]
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
            reason=pred.reason
        ))
    return BatchResponse(results=results)
