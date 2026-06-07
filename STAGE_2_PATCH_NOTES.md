# Stage 2 Patch Notes — Backend Security & Production Configuration

## Files changed / added

```text
cyberbullying_api/routes/deps.py
cyberbullying_api/main.py
docker-compose.yml
docker-compose.prod.yml
.env.example
docs/SECURITY_HARDENING.md
```

## Main improvements

### 1. API key hardening

`verify_api_key()` now:

- reads `API_KEY` dynamically from environment;
- requires `X-API-Key` for protected endpoints when `API_KEY` is set;
- blocks missing `API_KEY` outside development/test/local;
- uses constant-time hash comparison;
- keeps local development flexible through `ALLOW_MISSING_API_KEY_IN_DEV=true`.

### 2. Rate limit hardening

`rate_limit_ollama_and_batch()` now:

- uses configurable limit/window;
- hashes the rate-limit key before storing it in Redis;
- supports proxy-aware IP detection only when explicitly enabled;
- fails open in development by default;
- fails closed in production when `RATE_LIMIT_FAIL_OPEN=false`.

### 3. Webhook protection

`is_safe_webhook_url()` now:

- rejects private/local/reserved IPs;
- rejects non-HTTPS webhook URLs outside development;
- supports optional `WEBHOOK_ALLOWED_HOSTS` allowlist.

### 4. Startup validation

`main.py` now validates critical production config at startup:

- production/staging requires `API_KEY`;
- production/staging requires explicit `ALLOWED_ORIGINS`;
- warns about risky rate-limit settings.

### 5. CORS is narrower

The API now limits CORS methods and headers instead of using full wildcard behavior.

### 6. Docker Compose cleanup

The updated compose file uses `.env` values for:

- PostgreSQL credentials;
- Redis password;
- API key;
- CORS origins;
- rate-limit settings;
- ports.

`docker-compose.prod.yml` disables hot reload and forces stricter production settings.

## How to apply

Copy these files into your repository root, replacing the existing files when prompted.

Then run:

```bash
git checkout -b security/stage-2-hardening
cp -r bullyguard_stage2_security/* .
git add cyberbullying_api/routes/deps.py cyberbullying_api/main.py docker-compose.yml docker-compose.prod.yml .env.example docs/SECURITY_HARDENING.md STAGE_2_PATCH_NOTES.md
git commit -m "security: harden API key, rate limiting, CORS, and compose config"
```

## Local test

```bash
cp .env.example .env
docker compose up -d --build
curl http://localhost:8000/health
```

Test protected endpoint:

```bash
curl -H "X-API-Key: change_this_to_a_long_random_secret" http://localhost:8000/models/status
```

## Production test

Update `.env` first:

```env
ENV=production
API_KEY=<long-random-secret>
ALLOW_MISSING_API_KEY_IN_DEV=false
ALLOWED_ORIGINS=https://your-frontend-domain.com
RATE_LIMIT_FAIL_OPEN=false
POSTGRES_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
```

Then run:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Important warning

This patch improves baseline security, but it is not a full production security audit. For real deployment, add reverse proxy TLS, request body limits, logging, dependency scanning, and secret scanning.
