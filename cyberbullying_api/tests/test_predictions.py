import pytest


def test_predict_lexicon_safe(client):
    """Menguji bahwa kalimat positif diklasifikasikan sebagai AMAN oleh leksikon."""
    payload = {"text": "Semangat belajarnya ya, jangan menyerah!"}
    response = client.post("/predict/lexicon", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_cyberbullying"] is False
    assert data["risk_label"] == "aman/tidak terdeteksi"
    assert data["score"] == 0

def test_predict_lexicon_toxic(client):
    """Menguji kata kasar terdeteksi oleh leksikon."""
    payload = {"text": "kamu goblok banget sih"}
    response = client.post("/predict/lexicon", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_cyberbullying"] is True
    assert data["risk_label"] in ["sedang", "tinggi"]
    assert len(data["matches"]) > 0

def test_predict_ml_safe(client):
    """Menguji ML mendeteksi kalimat positif sebagai non-toxic & non-bully."""
    payload = {"text": "Semangat belajarnya ya, jangan menyerah!"}
    response = client.post("/predict/ml", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_toxic"] is False
    assert data["is_bully"] is False
    assert "Normal" in data["category"]

def test_predict_ml_sarcasm(client):
    """Menguji ML mendeteksi sarkasme sebagai non-toxic tapi bully."""
    payload = {"text": "ganteng banget mukalu kaya spakbor mio"}
    response = client.post("/predict/ml", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_toxic"] is False
    assert data["is_bully"] is True
    assert "Sarkasme" in data["category"]

def test_predict_ml_slang_praise(client):
    """Menguji ML mendeteksi slang pujian sebagai toxic tapi non-bully."""
    payload = {"text": "kamu hebat banget sih anjing"}
    response = client.post("/predict/ml", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_toxic"] is True
    assert data["is_bully"] is False
    assert "slang" in data["category"]

def test_predict_ml_direct_bully(client):
    """Menguji ML mendeteksi serangan langsung sebagai toxic & bully."""
    payload = {"text": "Kamu bodoh banget sih, dasar tolol!"}
    response = client.post("/predict/ml", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_toxic"] is True
    assert data["is_bully"] is True
    assert "bully" in data["category"]

def test_predict_ensemble_sarcasm(client):
    """Menguji Ensemble mendeteksi sarkasme halus ujian nol sebagai non-toxic & bully."""
    payload = {"text": "Wah pintar sekali kamu ya, sampai nilai ujianmu nol."}
    response = client.post("/predict/ensemble", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_toxic"] is False
    assert data["is_bully"] is True
    assert "Sarkasme" in data["category"]

def test_predict_hybrid_route_fast(client):
    """Menguji rute hybrid menyelesaikan kalimat mudah langsung di Tier 1."""
    payload = {"text": "Hari ini cuaca sangat cerah."}
    response = client.post("/predict/hybrid", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_toxic"] is False
    assert data["is_bully"] is False
    assert "Tier 1" in data["decision_source"]
    assert "Normal" in data["category"]

def test_predict_batch_processing(client):
    """Menguji endpoint prediksi batch untuk daftar komentar."""
    payload = {
        "texts": [
            "Semangat belajarnya ya, jangan menyerah!",
            "Kamu bodoh banget sih, dasar tolol!",
            "kamu hebat banget sih anjing"
        ]
    }
    response = client.post("/predict/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 3
    assert data["results"][0]["is_toxic"] is False
    assert data["results"][1]["is_toxic"] is True
    assert data["results"][2]["is_toxic"] is True

def test_predict_text_length_validation(client):
    """Menguji batas karakter input (max 500) dan min (1)."""
    response = client.post("/predict/lexicon", json={"text": ""})
    assert response.status_code == 422

    long_text = "anjing " * 100
    response = client.post("/predict/lexicon", json={"text": long_text})
    assert response.status_code == 422

def test_predict_batch_constraints(client):
    """Menguji batasan pada input batch."""
    response = client.post("/predict/batch", json={"texts": []})
    assert response.status_code == 422

    payload = {"texts": ["Semangat!"] * 51}
    response = client.post("/predict/batch", json=payload)
    assert response.status_code == 422

    long_text = "goblok " * 100
    payload = {"texts": ["Semangat!", long_text]}
    response = client.post("/predict/batch", json=payload)
    assert response.status_code == 422

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_sqlite_write_concurrency():
    """Menguji bahwa penyimpanan klasifikasi memori secara paralel ke SQLite tidak memicu Lock Error."""
    import asyncio

    from classifier.database import get_classification_memory, save_classification_memory
    from models import HybridResponse

    res_list = [
        HybridResponse(
            text=f"Teks tes konkurensi SQLite ke-{i}",
            is_toxic=False,
            is_bully=False,
            probability_toxic=0.1,
            probability_bully=0.1,
            category="Aman",
            decision_source="Test",
            reason="Testing SQLite concurrency"
        )
        for i in range(10)
    ]

    tasks = [save_classification_memory(res) for res in res_list]
    await asyncio.gather(*tasks)

    retrieved = await get_classification_memory("Teks tes konkurensi SQLite ke-5")
    assert retrieved is not None
    assert retrieved.text == "Teks tes konkurensi SQLite ke-5"

@pytest.mark.anyio
async def test_semantic_caching():
    """Menguji kecocokan semantik cache (Semantic Caching) menggunakan SQLite fallback."""
    import json

    from classifier.database import get_classification_memory, save_classification_memory
    from classifier.predictor import EMBEDDING_MODEL
    from models import HybridResponse

    if EMBEDDING_MODEL is None:
        pytest.skip("SentenceTransformer EMBEDDING_MODEL tidak dimuat.")

    text_1 = "Gue benci banget sama orang itu karena dia jahat"
    text_2 = "Gue benci banget sama orang itu karena dia jahat."

    emb_json = json.dumps(EMBEDDING_MODEL.encode([text_1])[0].tolist())

    res = HybridResponse(
        text=text_1,
        is_toxic=True,
        is_bully=True,
        probability_toxic=0.9,
        probability_bully=0.9,
        category="Bullying",
        decision_source="ManualTest",
        reason="Komentar mengandung ujaran kebencian."
    )
    await save_classification_memory(res, emb_json)

    cached_res = await get_classification_memory(text_2)

    assert cached_res is not None
    assert "Semantic Cache Match" in cached_res.decision_source
    assert cached_res.is_toxic is True
    assert cached_res.is_bully is True

def test_word_importances_in_predictions(client):
    """Menguji bahwa key 'word_importances' dikembalikan dan terisi pada kalimat yang terdeteksi toxic/bully."""
    payload = {"text": "kamu goblok banget sih"}
    response = client.post("/predict/hybrid", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "word_importances" in data
    assert isinstance(data["word_importances"], list)
    if len(data["word_importances"]) > 0:
        first_imp = data["word_importances"][0]
        assert "word" in first_imp
        assert "weight_toxic" in first_imp
        assert "weight_bully" in first_imp


def test_predict_hybrid_stream_lexicon_bypass(client):
    import json
    payload = {"text": "kamu goblok banget sih unikstreambypass"}
    response = client.post("/predict/hybrid/stream", json=payload)
    assert response.status_code == 200
    text_content = response.text
    assert "data: " in text_content
    done_event = None
    for line in text_content.strip().split("\n"):
        if line.startswith("data: "):
            evt = json.loads(line[6:])
            if evt.get("done"):
                done_event = evt
                break
    assert done_event is not None
    assert "Tier 1 (Lexicon Kamus)" in done_event["final_data"]["decision_source"]

