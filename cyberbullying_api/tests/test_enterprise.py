import pytest
import os

@pytest.mark.anyio
async def test_auth_token_success(client):
    # Test valid credentials
    payload = {
        "username": "admin",
        "password": "admin",
        "scope": "predict admin"
    }
    response = client.post("/api/auth/token", data=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "predict" in data["scopes"]
    assert "admin" in data["scopes"]

@pytest.mark.anyio
async def test_auth_token_apikey_exchange(client):
    # Set API_KEY temporarily
    orig_key = os.environ.get("API_KEY")
    os.environ["API_KEY"] = "super-secret-key"
    try:
        payload = {
            "username": "apikey",
            "password": "super-secret-key",
            "scope": "predict"
        }
        response = client.post("/api/auth/token", data=payload)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["scopes"] == ["predict"]
    finally:
        if orig_key is not None:
            os.environ["API_KEY"] = orig_key
        else:
            os.environ.pop("API_KEY", None)

@pytest.mark.anyio
async def test_auth_token_failure(client):
    payload = {
        "username": "wrong_user",
        "password": "wrong_password"
    }
    response = client.post("/api/auth/token", data=payload)
    assert response.status_code == 401

@pytest.mark.anyio
async def test_rbac_token_scopes(client):
    # Disable allow missing api key bypass temporarily to force token validation
    orig_bypass = os.environ.get("ALLOW_MISSING_API_KEY_IN_DEV")
    os.environ["ALLOW_MISSING_API_KEY_IN_DEV"] = "false"
    
    try:
        # 1. Get token with ONLY predict scope
        payload = {
            "username": "guest",
            "password": "guest",
            "scope": "predict"
        }
        resp = client.post("/api/auth/token", data=payload)
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        
        # 2. Test prediction route with predict token -> Success
        headers = {"Authorization": f"Bearer {token}"}
        resp_pred = client.post("/predict/lexicon", json={"text": "halo apa kabar"}, headers=headers)
        assert resp_pred.status_code == 200
        
        # 3. Test admin route with predict token -> Forbidden (403)
        resp_admin = client.get("/api/settings", headers=headers)
        assert resp_admin.status_code == 403
        
        # 4. Test admin route with invalid token -> Unauthorized (401)
        headers_invalid = {"Authorization": "Bearer invalidtoken123"}
        resp_invalid = client.get("/api/settings", headers=headers_invalid)
        assert resp_invalid.status_code == 401
    finally:
        if orig_bypass is not None:
            os.environ["ALLOW_MISSING_API_KEY_IN_DEV"] = orig_bypass
        else:
            os.environ.pop("ALLOW_MISSING_API_KEY_IN_DEV", None)

@pytest.mark.anyio
async def test_prometheus_metrics_endpoint(client):
    # Trigger a request first to ensure requests_total counter is populated
    client.get("/")
    
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "cyberbullying_requests_total" in response.text
    assert "# HELP cyberbullying_requests_total" in response.text

def test_kms_mock_integration():
    # Set mock provider
    os.environ["KMS_PROVIDER"] = "mock"
    try:
        from classifier.kms import get_encryption_key
        key = get_encryption_key()
        assert key == b"mock-vault-secret-key-value-12345"
    finally:
        os.environ.pop("KMS_PROVIDER", None)

def test_onnx_gpu_provider_config():
    try:
        import onnxruntime as ort
    except ImportError:
        ort = None
        
    if ort is not None:
        available = ort.get_available_providers()
        assert "CPUExecutionProvider" in available
