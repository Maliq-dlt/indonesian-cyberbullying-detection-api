import pytest
import os

@pytest.fixture
def anyio_backend():
    return "asyncio"

def test_read_root(client):
    """Menguji status ketersediaan API server."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"

def test_health_endpoint(client):
    """Menguji endpoint health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "alive" in data["message"]

def test_models_status_endpoint(client):
    """Menguji endpoint status model."""
    response = client.get("/models/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "models_loaded" in data
    assert "thresholds" in data

def test_api_scrape_tiktok(client):
    """Menguji endpoint scraping komentar TikTok."""
    payload = {
        "url": "https://www.tiktok.com/@xyz/video/987654321",
        "max_comments": 2
    }
    from unittest.mock import patch
    with patch("scraper.tiktok.scrape_tiktok_comments") as mock_scrape:
        mock_scrape.return_value = (["Komentar uji 1", "Komentar uji 2"], True)
        response = client.post("/api/scrape/tiktok", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) == 2
        assert data["data"][0] == "Komentar uji 1"

def test_api_scrape_x(client):
    """Menguji endpoint scraping replies tweet X/Twitter."""
    payload = {
        "url": "https://x.com/jack/status/20",
        "max_tweets": 2
    }
    from unittest.mock import patch
    with patch("scraper.twitter.scrape_x_tweets") as mock_scrape:
        mock_scrape.return_value = (["Tweet uji 1", "Tweet uji 2"], True)
        response = client.post("/api/scrape/x", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) == 2
        assert data["data"][0] == "Tweet uji 1"

@pytest.mark.anyio
async def test_api_categorized_and_reallocate(client):
    """Menguji endpoint penarikan data kuadran dan relokasi (Active Learning)."""
    from classifier.database import save_classification_memory
    from models import HybridResponse
    
    test_text = "Kalimat pengujian relokasi active learning"
    res = HybridResponse(
        text=test_text,
        is_toxic=False,
        is_bully=False,
        probability_toxic=0.1,
        probability_bully=0.1,
        category="Aman",
        decision_source="Test",
        reason="Testing reallocation"
    )
    await save_classification_memory(res)
    
    response = client.get("/api/data/categorized?limit=50")
    assert response.status_code == 200
    data = response.json()
    assert "toxic_bully" in data
    assert "non_toxic_non_bully" in data
    
    found_init = False
    for item in data["non_toxic_non_bully"]:
        if item["text"] == test_text:
            found_init = True
            break
    assert found_init is True
    
    payload = {
        "text": test_text,
        "new_is_toxic": True,
        "new_is_bully": True
    }
    realloc_resp = client.post("/api/data/reallocate", json=payload)
    assert realloc_resp.status_code == 200
    assert realloc_resp.json()["success"] is True
    
    response = client.get("/api/data/categorized?limit=50")
    assert response.status_code == 200
    data = response.json()
    
    found_moved = False
    for item in data["toxic_bully"]:
        if item["text"] == test_text:
            found_moved = True
            assert item["is_validated"] == 1
            break
    assert found_moved is True

def test_api_train_and_logs(client):
    """Menguji endpoint start training dan streaming logs dengan mock subprocess."""
    import routes.state as state
    from unittest.mock import patch
    import subprocess
    import sys
    
    with patch("subprocess.Popen") as mock_popen:
        mock_process = subprocess.Popen([sys.executable, "-c", "print('=== Memulai Pelatihan Ulang ===')"])
        mock_popen.return_value = mock_process
        
        try:
            response = client.post("/api/train/start")
            assert response.status_code == 200
            assert response.json()["success"] is True
            
            with client.stream("GET", "/api/train/logs") as stream_resp:
                assert stream_resp.status_code == 200
                first_line = next(stream_resp.iter_lines())
                assert first_line is not None
                assert "data:" in first_line
        finally:
            if state.TRAINING_PROCESS is not None:
                try:
                    state.TRAINING_PROCESS.terminate()
                    state.TRAINING_PROCESS.wait(timeout=2.0)
                except Exception:
                    pass
                state.TRAINING_PROCESS = None
            if state.LOG_FILE_HANDLE is not None:
                try:
                    state.LOG_FILE_HANDLE.close()
                except Exception:
                    pass
                state.LOG_FILE_HANDLE = None

@pytest.mark.anyio
async def test_key_rotation_utility():
    """Menguji utilitas rotasi kunci rotate_key.py terhadap SQLite."""
    from classifier.database import save_classification_memory
    from rotate_key import rotate_sqlite_database, get_fernet_cipher
    from models import HybridResponse
    import sqlite3
    import hashlib
    
    old_key = os.getenv("API_KEY", "") or "default_secure_fallback_key_for_cyberbullying_api_classification_memory"
    new_key = "new_super_secure_key_for_test_rotation"
    
    test_text = "Kalimat pengujian rotasi kunci aman"
    res = HybridResponse(
        text=test_text,
        is_toxic=False,
        is_bully=False,
        probability_toxic=0.0,
        probability_bully=0.0,
        category="Aman",
        decision_source="TestRotation",
        reason="Testing Key Rotation Utility"
    )
    await save_classification_memory(res)
    
    from classifier.db_config import get_sqlite_db_path
    db_path = get_sqlite_db_path()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT encrypted_text FROM classification_memory WHERE text_hash = ?", (hashlib.sha256(test_text.encode("utf-8")).hexdigest(),))
    old_ciphertext = cursor.fetchone()[0]
    conn.close()
    
    rotate_sqlite_database(old_key, new_key, db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT encrypted_text FROM classification_memory WHERE text_hash = ?", (hashlib.sha256(test_text.encode("utf-8")).hexdigest(),))
    new_ciphertext = cursor.fetchone()[0]
    conn.close()
    
    assert old_ciphertext != new_ciphertext
    
    new_cipher = get_fernet_cipher(new_key)
    decrypted = new_cipher.decrypt(new_ciphertext.encode("utf-8")).decode("utf-8")
    assert decrypted == test_text
    
    rotate_sqlite_database(new_key, old_key, db_path)

def test_api_update_cookies(client):
    """Menguji endpoint pembaruan cookie sesi scraper."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cookie_path = os.path.join(base_dir, "cookies_tiktok.json")
    backup_path = os.path.join(base_dir, "cookies_tiktok.json.bak")
    
    import shutil
    has_backup = False
    if os.path.exists(cookie_path):
        shutil.copyfile(cookie_path, backup_path)
        has_backup = True
        
    try:
        payload = {
            "platform": "tiktok",
            "cookies": [
                {
                    "name": "sessionid",
                    "value": "mocksessionvalue12345",
                    "domain": ".tiktok.com",
                    "path": "/"
                }
            ]
        }
        response = client.post("/api/settings/cookies", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "berhasil diperbarui" in data["message"]
    finally:
        if has_backup:
            if os.path.exists(backup_path):
                shutil.move(backup_path, cookie_path)
        else:
            if os.path.exists(cookie_path):
                os.remove(cookie_path)

@pytest.mark.anyio
async def test_api_get_categorized_data_with_filters(client):
    """Menguji penyaringan kueri pada GET /api/data/categorized."""
    from classifier.database import save_classification_memory
    from models import HybridResponse
    
    res1 = HybridResponse(
        text="Kalimat uji spesifik untuk pencarian aktif satu",
        is_toxic=True,
        is_bully=True,
        probability_toxic=0.95,
        probability_bully=0.90,
        category="Toxic & Bully",
        decision_source="FilterTestOne",
        reason="Seed data one"
    )
    res2 = HybridResponse(
        text="Komentar biasa saja aman dan nyaman",
        is_toxic=False,
        is_bully=False,
        probability_toxic=0.05,
        probability_bully=0.02,
        category="Aman",
        decision_source="FilterTestTwo",
        reason="Seed data two"
    )
    await save_classification_memory(res1)
    await save_classification_memory(res2)

    response = client.get("/api/data/categorized?search=spesifik")
    assert response.status_code == 200
    data = response.json()
    assert len(data["toxic_bully"]) >= 1
    assert "aktif satu" in data["toxic_bully"][0]["text"]
    
    response = client.get("/api/data/categorized?confidence_min=0.9&confidence_max=1.0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["toxic_bully"]) >= 1
    
    response = client.get("/api/data/categorized?decision_source=FilterTestTwo")
    assert response.status_code == 200
    data = response.json()
    assert len(data["non_toxic_non_bully"]) >= 1
    assert "aman dan nyaman" in data["non_toxic_non_bully"][0]["text"]

@pytest.mark.anyio
async def test_api_reallocate_data_bulk(client):
    """Menguji endpoint relokasi massal (bulk reallocation)."""
    payload = {
        "items": [
            {
                "text": "Kalimat uji spesifik untuk pencarian aktif satu",
                "new_is_toxic": False,
                "new_is_bully": False
            },
            {
                "text": "Komentar biasa saja aman dan nyaman",
                "new_is_toxic": True,
                "new_is_bully": True
            }
        ]
    }
    response = client.post("/api/data/reallocate/bulk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data berhasil direlokasi" in data["message"]
    
    response = client.get("/api/data/categorized?search=spesifik")
    assert response.status_code == 200
    data = response.json()
    assert len(data["non_toxic_non_bully"]) >= 1
    assert any(item["text"] == "Kalimat uji spesifik untuk pencarian aktif satu" for item in data["non_toxic_non_bully"])
