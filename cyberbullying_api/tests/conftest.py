import pytest
from fastapi.testclient import TestClient
import sys
import os

# Menambahkan folder parent ke path agar main.py bisa diimpor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set ENV ke development agar pengujian API Key dilewati saat testing
os.environ["ENV"] = "development"
# Kosongkan PG_URL dan REDIS_URL agar testing menggunakan SQLite isolated fallback,
# menghindari masalah konkurensi/cross-loop sharing pool asyncpg & redis.
os.environ["PG_URL"] = ""
os.environ["REDIS_URL"] = ""

from main import app

@pytest.fixture(scope="session")
def client():
    """Fixture tunggal tingkat sesi (session-scoped) untuk membuat TestClient FastAPI.
    Menghindari inisialisasi ganda model deep learning (XLM-RoBERTa & SentenceTransformers)
    di setiap file uji, sehingga mempercepat waktu eksekusi pengujian secara drastis
    tanpa mengurangi cakupan pengujian sama sekali.
    """
    with TestClient(app) as c:
        yield c
