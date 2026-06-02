import pytest
from fastapi.testclient import TestClient
import sys
import os

# Menambahkan folder parent ke path agar main.py bisa diimpor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

@pytest.fixture(scope="module")
def client():
    """Fixture untuk membuat TestClient dengan trigger startup event FastAPI."""
    with TestClient(app) as c:
        yield c

def test_read_root(client):
    """Menguji status ketersediaan API server."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "models_loaded" in data

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
    assert "Aman" in data["category"]

def test_predict_ml_sarcasm(client):
    """Menguji ML mendeteksi sarkasme sebagai non-toxic tapi bully."""
    payload = {"text": "ganteng banget mukalu kaya spakbor mio"}
    response = client.post("/predict/ml", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_toxic"] is False
    assert data["is_bully"] is True
    assert "Sarcasm" in data["category"]

def test_predict_ml_slang_praise(client):
    """Menguji ML mendeteksi slang pujian sebagai toxic tapi non-bully."""
    payload = {"text": "kamu hebat banget sih anjing"}
    response = client.post("/predict/ml", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_toxic"] is True
    assert data["is_bully"] is False
    assert "Casual Slang" in data["category"]

def test_predict_ml_direct_bully(client):
    """Menguji ML mendeteksi serangan langsung sebagai toxic & bully."""
    payload = {"text": "Kamu bodoh banget sih, dasar tolol!"}
    response = client.post("/predict/ml", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_toxic"] is True
    assert data["is_bully"] is True
    assert "Serangan Langsung" in data["category"]

def test_predict_ensemble_sarcasm(client):
    """Menguji Ensemble mendeteksi sarkasme halus ujian nol sebagai non-toxic & bully."""
    payload = {"text": "Wah pintar sekali kamu ya, sampai nilai ujianmu nol."}
    response = client.post("/predict/ensemble", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_toxic"] is False
    assert data["is_bully"] is True
    assert "Sarcasm" in data["category"]
