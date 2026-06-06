# Stage 1: Build virtual environment and wheels
FROM python:3.11-slim AS builder

WORKDIR /app

# Install compilation tools (some python modules require compilation during pip install)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY cyberbullying_api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r /app/requirements.txt

# Stage 2: Final runtime environment
FROM python:3.11-slim AS runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
    PLAYWRIGHT_BROWSERS_PATH=/app/ms-playwright \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Install runtime packages for Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    && playwright install --with-deps chromium \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy dataset kamus yang diperlukan untuk preprocessing
COPY ["dataset", "/app/dataset/"]

# Copy seluruh isi folder API beserta file model yang telah dilatih
COPY cyberbullying_api /app/cyberbullying_api

# Set working directory ke folder API
WORKDIR /app/cyberbullying_api

# Pastikan direktori browser profile ada dan writable
RUN mkdir -p /app/cyberbullying_api/tiktok_browser_profile

# Tambahkan user non-privileged untuk faktor keamanan
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

# Ekspos port API (8000) dan UI (7860)
EXPOSE 8000 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
