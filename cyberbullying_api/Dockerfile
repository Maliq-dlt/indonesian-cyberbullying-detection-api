# Stage 1: Build virtual environment and wheels
FROM python:3.11-slim AS builder

WORKDIR /app

# Install compilation tools (some python modules require compilation during pip install)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv for extremely fast and resource-efficient package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create virtual environment
RUN /bin/uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install runtime requirements using uv and cache mounts to speed up consecutive builds.
# The full requirements.txt keeps training/export/dev dependencies for local use.
COPY cyberbullying_api/requirements.docker.txt /app/requirements.txt
RUN --mount=type=cache,target=/root/.cache/uv \
    /bin/uv pip install -r /app/requirements.txt


# Stage 2: Final runtime environment
FROM python:3.11-slim AS runner

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AUTO_EXPORT_ONNX=false \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
    PLAYWRIGHT_BROWSERS_PATH=/app/ms-playwright \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Playwright is optional because its browser/system dependencies make the image much larger.
ARG INSTALL_PLAYWRIGHT=false
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    && if [ "$INSTALL_PLAYWRIGHT" = "true" ]; then \
        pip install --no-cache-dir "playwright>=1.40.0" \
        && playwright install --with-deps chromium; \
    fi \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy dataset kamus yang diperlukan untuk preprocessing
COPY ["dataset", "/app/dataset/"]

# Copy API source. Large runtime artifacts are mounted by Compose and excluded by .dockerignore.
COPY cyberbullying_api /app/cyberbullying_api

# Set working directory ke folder API
WORKDIR /app/cyberbullying_api

# Pastikan direktori runtime ada dan writable
RUN mkdir -p \
    /app/cyberbullying_api/cache \
    /app/cyberbullying_api/models \
    /app/cyberbullying_api/tiktok_browser_profile

# Tambahkan user non-privileged untuk faktor keamanan
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

# Ekspos port API (8000) dan UI (7860)
EXPOSE 8000 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
