"""Authentication endpoints — login for JWT access token."""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
import logging
import os
import jwt
from datetime import datetime, timedelta, timezone

from routes.deps import JWT_SECRET, ALGORITHM

logger = logging.getLogger("bullyguard")

public_router = APIRouter(prefix="/api", tags=["auth"])


@public_router.post("/auth/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    expected_username = os.getenv("ADMIN_USERNAME", "admin").strip()
    expected_password = os.getenv("ADMIN_PASSWORD", "admin").strip()
    expected_api_key = os.getenv("API_KEY", "").strip()

    authenticated = False
    scopes = []

    if form_data.username == expected_username and form_data.password == expected_password:
        authenticated = True
        scopes = ["predict", "admin"]
    elif form_data.username == "apikey" and expected_api_key and form_data.password == expected_api_key:
        authenticated = True
        scopes = ["predict", "admin"]
    elif form_data.username == "guest" and form_data.password == "guest":
        authenticated = True
        scopes = ["predict"]

    if not authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username, password, atau API key tidak cocok.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_scopes = []
    for scope in form_data.scopes:
        if scope in scopes:
            token_scopes.append(scope)

    if not token_scopes:
        token_scopes = scopes

    expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    to_encode = {
        "sub": form_data.username,
        "scopes": token_scopes,
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

    return {
        "access_token": encoded_jwt,
        "token_type": "bearer",
        "expires_in": 3600,
        "scopes": token_scopes
    }
