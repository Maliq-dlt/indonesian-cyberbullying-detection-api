"""Shared FastAPI dependencies for authentication, rate limiting, and webhook safety.

Stage 2 security cleanup goals:
- Do not accidentally expose protected endpoints without API_KEY in non-development environments.
- Compare API keys using constant-time comparison.
- Make rate limiting configurable and fail closed in production by default.
- Keep local development usable without forcing Redis/API key setup.
- Keep webhook SSRF protection explicit and readable.
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import os
import socket
from typing import Optional
from urllib.parse import urlparse

from fastapi import Header, HTTPException, Request, status, Depends, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
import jwt
from datetime import datetime, timezone, timedelta
import classifier


NON_PRODUCTION_ENVS = {"local", "dev", "development", "test", "testing"}


def get_env() -> str:
    return os.getenv("ENV", "production").strip().lower()


def is_development_env() -> bool:
    return get_env() in NON_PRODUCTION_ENVS


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def verify_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")) -> None:
    """Validate the X-API-Key header for protected endpoints.

    Local development may allow an empty API_KEY only when
    ALLOW_MISSING_API_KEY_IN_DEV=true. Production/staging must always have
    API_KEY configured and every protected request must provide it.
    """

    expected_key = os.getenv("API_KEY", "").strip()

    if not expected_key:
        if is_development_env() and _bool_env("ALLOW_MISSING_API_KEY_IN_DEV", True):
            return

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: API_KEY must be set for protected endpoints.",
        )

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required. Send it using the X-API-Key header.",
        )

    expected_bytes = expected_key.encode("utf-8")
    provided_bytes = x_api_key.encode("utf-8")

    if not hmac.compare_digest(provided_bytes, expected_bytes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )


def _get_client_ip(request: Request) -> str:
    """Return client IP.

    X-Forwarded-For is trusted only when TRUST_PROXY_HEADERS=true. Without this
    guard, clients can spoof their IP and bypass per-IP rate limiting.
    """

    if _bool_env("TRUST_PROXY_HEADERS", False):
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",", 1)[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()

    return request.client.host if request.client else "unknown"


async def rate_limit_cloud_llm_and_batch(request: Request) -> None:
    """Rate limit expensive endpoints.

    Defaults:
    - 15 requests per 60 seconds per client IP and path.
    - In development, Redis failure fails open so local work is not blocked.
    - In production/staging, Redis failure fails closed unless RATE_LIMIT_FAIL_OPEN=true.
    """

    limit = _int_env("RATE_LIMIT_REQUESTS_PER_MINUTE", 15)
    window_seconds = _int_env("RATE_LIMIT_WINDOW_SECONDS", 60)
    fail_open = _bool_env("RATE_LIMIT_FAIL_OPEN", is_development_env())

    redis_client = await classifier.get_redis()
    if not redis_client:
        if fail_open:
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiter is unavailable. Try again later.",
        )

    try:
        client_ip = _get_client_ip(request)
        path_normalized = request.url.path.rstrip("/").lower() or "/"
        key_source = f"{client_ip}:{path_normalized}"
        key_hash = hashlib.sha256(key_source.encode("utf-8")).hexdigest()[:32]
        key = f"rate_limit:{key_hash}"

        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.ttl(key)
        current_count, current_ttl = await pipe.execute()

        if current_count == 1 or current_ttl < 0:
            await redis_client.expire(key, window_seconds)

        if int(current_count) > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Limit is {limit} requests per {window_seconds} seconds.",
            )

    except HTTPException:
        raise
    except Exception as exc:
        print(f"Warning: failed to evaluate Redis rate limit: {exc}")
        if fail_open:
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rate limiter failed. Try again later.",
        )


def is_safe_webhook_url(url: str) -> bool:
    """Validate webhook URL to reduce SSRF risk.

    Blocks local, loopback, multicast, link-local, unspecified, and private IPs.
    This is a defensive baseline. For real production integrations, prefer an
    explicit domain allowlist using WEBHOOK_ALLOWED_HOSTS.
    """

    try:
        parsed = urlparse(url)
        if parsed.scheme not in {"https", "http"}:
            return False

        # Safer default for production: HTTPS only unless explicitly allowed.
        if not is_development_env() and parsed.scheme != "https":
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        allowed_hosts_raw = os.getenv("WEBHOOK_ALLOWED_HOSTS", "").strip()
        if allowed_hosts_raw:
            allowed_hosts = {host.strip().lower() for host in allowed_hosts_raw.split(",") if host.strip()}
            if hostname.lower() not in allowed_hosts:
                return False

        addr_info = socket.getaddrinfo(hostname, None, family=socket.AF_INET)
        for addr in addr_info:
            ip = ipaddress.ip_address(addr[4][0])
            if (
                ip.is_loopback
                or ip.is_private
                or ip.is_multicast
                or ip.is_link_local
                or ip.is_unspecified
                or ip.is_reserved
            ):
                return False

        return True
    except Exception:
        return False

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/token",
    scopes={
        "predict": "Akses untuk analisis dan prediksi cyberbullying (Core API).",
        "admin": "Akses administratif untuk manajemen data HITL, scraper, dan retraining model."
    },
    auto_error=False
)

JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("API_KEY", "bullyguard_id_dev_insecure_key_source")).strip()
ALGORITHM = "HS256"

async def get_current_user(
    security_scopes: SecurityScopes,
    token: Optional[str] = Depends(oauth2_scheme),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
) -> dict:
    # 1. Dev mode bypass jika diizinkan dan token serta API Key kosong
    if is_development_env() and _bool_env("ALLOW_MISSING_API_KEY_IN_DEV", True) and not token and not x_api_key:
        return {"username": "dev_admin", "scopes": ["predict", "admin"]}

    # 2. Jika tidak ada token JWT tetapi ada X-API-Key, validasi X-API-Key untuk backward compatibility
    if not token and x_api_key:
        expected_key = os.getenv("API_KEY", "").strip()
        if expected_key:
            expected_bytes = expected_key.encode("utf-8")
            provided_bytes = x_api_key.encode("utf-8")
            if hmac.compare_digest(provided_bytes, expected_bytes):
                return {"username": "apikey_user", "scopes": ["predict", "admin"]}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key tidak valid.",
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token autentikasi atau API key tidak ditemukan. Silakan login ke /api/auth/token terlebih dahulu.",
            headers={"WWW-Authenticate": f"Bearer realm='cyberbullying_api' scope='{security_scopes.scope_str}'"},
        )

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_scopes = payload.get("scopes", [])
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token tidak valid: klaim sub tidak ditemukan.",
                headers={"WWW-Authenticate": "Bearer error='invalid_token'"},
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token autentikasi telah kedaluwarsa. Silakan lakukan autentikasi ulang.",
            headers={"WWW-Authenticate": "Bearer error='invalid_token', error_description='token expired'"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token autentikasi tidak valid atau rusak.",
            headers={"WWW-Authenticate": "Bearer error='invalid_token'"},
        )

    # Validasi scopes (RBAC)
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Hak akses tidak mencukupi. Diperlukan scope: {scope}",
                headers={"WWW-Authenticate": f"Bearer error='insufficient_scope', scope='{security_scopes.scope_str}'"},
            )

    return {"username": username, "scopes": token_scopes}
