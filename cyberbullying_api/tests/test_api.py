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
    """Menguji model Machine Learning mendeteksi kalimat positif sebagai aman."""
    payload = {"text": "Selamat pagi semuanya, selamat beraktivitas!"}
    response = client.post("/predict/ml", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_cyberbullying"] is False
    assert data["probability"] < 0.5

def test_predict_ml_toxic(client):
    """Menguji model Machine Learning mendeteksi kalimat kasar sebagai cyberbullying."""
    payload = {"text": "dasar tolol goblok kamu"}
    response = client.post("/predict/ml", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_cyberbullying"] is True
    assert data["probability"] > 0.5
