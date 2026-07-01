import pytest
from fastapi.testclient import TestClient
import sys
import os

# Menambahkan folder parent ke path agar main.py bisa diimpor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set ENV ke test agar pengujian menggunakan isolated test database dan dilewati saat testing
os.environ["ENV"] = "test"
os.environ["ALLOW_MISSING_API_KEY_IN_DEV"] = "true"
# Kosongkan PG_URL dan REDIS_URL agar testing menggunakan SQLite isolated fallback,
# menghindari masalah konkurensi/cross-loop sharing pool asyncpg & redis.
os.environ["PG_URL"] = ""
os.environ["REDIS_URL"] = ""
os.environ["API_KEY"] = "test-key"

from main import app

@pytest.fixture(scope="session")
def client():
    """Fixture tunggal tingkat sesi (session-scoped) untuk membuat TestClient FastAPI.
    Menghindari inisialisasi ganda model deep learning (XLM-RoBERTa & SentenceTransformers)
    di setiap file uji, sehingga mempercepat waktu eksekusi pengujian secara drastis
    tanpa mengurangi cakupan pengujian sama sekali.
    """
    # Clean up test SQLite database if exists to ensure isolated test environment
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    test_db = os.path.join(base_dir, "cache", "test_cloud_llm_cache.db")
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except Exception:
            pass

    with TestClient(app, headers={"X-API-Key": "test-key"}) as c:
        yield c
