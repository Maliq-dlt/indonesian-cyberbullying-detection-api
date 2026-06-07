# Security Hardening Notes — Stage 2

This document explains the security changes introduced in Stage 2.

## 1. API key behavior

Protected endpoints now require `X-API-Key` when `API_KEY` is configured.

In local development, missing `API_KEY` is still allowed only when:

```env
ENV=development
ALLOW_MISSING_API_KEY_IN_DEV=true
```

In production/staging, the API refuses to start or refuses protected requests if `API_KEY` is missing.

Recommended production value:

```env
ENV=production
API_KEY=<long-random-secret>
ALLOW_MISSING_API_KEY_IN_DEV=false
```

## 2. Rate limiting

Expensive endpoints such as hybrid prediction, batch prediction, and scraping use Redis-based rate limiting.

Default:

```env
RATE_LIMIT_REQUESTS_PER_MINUTE=15
RATE_LIMIT_WINDOW_SECONDS=60
```

Development may fail open if Redis is unavailable:

```env
RATE_LIMIT_FAIL_OPEN=true
```

Production should fail closed:

```env
RATE_LIMIT_FAIL_OPEN=false
```

This prevents the API from silently accepting unlimited requests when Redis is down.

## 3. CORS

Production must use explicit origins:

```env
ALLOWED_ORIGINS=https://your-frontend-domain.com
```

Do not use `*` in production.

## 4. Docker secrets

The updated `docker-compose.yml` uses environment variables instead of fixed credentials.

Old pattern:

```yaml
POSTGRES_PASSWORD: cyber_password
```

Improved pattern:

```yaml
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-cyber_password}
```

The fallback is acceptable for local development only. Production must override it through `.env` or your deployment platform secrets.

## 5. Webhook SSRF protection

Webhook URLs are checked to block:

- localhost / loopback IPs
- private network IPs
- multicast / link-local / unspecified IPs
- reserved IPs
- non-HTTPS URLs in non-development environments

Optional allowlist:

```env
WEBHOOK_ALLOWED_HOSTS=hooks.slack.com,discord.com
```

## 6. Reverse proxy IP trust

`X-Forwarded-For` and `X-Real-IP` are trusted only when:

```env
TRUST_PROXY_HEADERS=true
```

Keep it false unless the API is behind a trusted reverse proxy.

## 7. Public endpoints

Safe to keep public:

- `/`
- `/health`
- `/docs` during development only, depending on your deployment preference

Protected:

- `/predict/*`
- `/api/*`
- `/models/status`

## 8. Remaining security work

Stage 2 improves baseline security, but it is not a full security audit. Remaining work:

- Replace single API key with proper user/session auth if multiple users are expected.
- Add audit logging for admin actions.
- Add request body size limits at reverse proxy level.
- Add abuse monitoring.
- Add secret scanning in CI.
- Add dependency vulnerability scanning.
