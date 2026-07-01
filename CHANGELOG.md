# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.0] - 2026-07-01

### Added
- **Structured JSON Logging**: Production-ready structured logging with JSON format for observability (ELK/Loki compatible).
- **Correlation ID Middleware**: `X-Request-ID` header on every request for distributed tracing.
- **API Versioning (`/api/v1/`)**: New versioned route prefix with backward-compatible legacy routes.
- **Security Headers Middleware**: `X-Content-Type-Options`, `X-Frame-Options`, `HSTS`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control` on all responses.
- **Request Size Limit Middleware**: 10MB body limit to prevent DoS via large payloads (HTTP 413).
- **JWT Secret Hardening**: Secure `secrets.token_hex(32)` generation in dev, mandatory explicit secret in production.
- **Zustand State Management**: Centralized frontend state store replacing prop drilling pattern in App.tsx.
- **Home.tsx Sub-Components**: Extracted `ChatSimulator`, `FeaturesShowcase`, `DashboardHistoryChart` from 1336-line God component.
- **Pagination**: Offset/limit/order parameters on HITL `/data/categorized` and training `/train/history` endpoints with `_pagination` metadata.
- **Prometheus Metrics**: `REQUESTS_TOTAL` counter and `REQUESTS_LATENCY` histogram with `/metrics` endpoint.
- **CI Pipeline**: GitHub Actions workflows for CI, CodeQL analysis, and Docker publishing.
- **Admin Module Decomposition**: Split monolithic `admin.py` into `auth.py`, `settings.py`, `training.py`, `hitl.py`, `scraper.py`.
- **Frontend Test Suite**: 45 Vitest tests covering Detector components, XAIHighlightText, API normalization, and utilities.
- **Backend Test Suite**: 101 pytest tests covering confidence, monitoring, normalizer, trie, predictor, and all route modules.

### Changed
- **Async Endpoints**: Converted 4 sync predict endpoints (`lexicon`, `ml`, `transformers`, `ensemble`) to async using `asyncio.to_thread`.
- **Model Reload**: `api_reload_models` now uses `asyncio.to_thread(init_models)` to avoid blocking the event loop.
- **JWT Fallback**: Removed insecure hardcoded JWT secret; dev mode generates random per-process secrets.
- **Credential Sanitization**: Removed real `GEMINI_API_KEY` and `HF_TOKEN` from `.env`.
- **`print()` Elimination**: All `print()` calls in `predict.py` replaced with structured `logger` calls.

### Security
- Sanitized real API credentials from `.env` file.
- Added `JWT_SECRET` to `.env.example` with fallback documentation.
- Security headers prevent clickjacking, MIME sniffing, and information leakage.

---

## [1.2.0] - 2026-06-06

### Added
- **GitHub Enterprise Structure**: Added `.github/workflows/ci.yml` pipeline, Pull Request templates, issue templates, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and `CHANGELOG.md`.
- **Active Learning Dashboard**: Complete visual frontend module for labeling and retraining.
- **Persistent Profile Mounting**: Added persistent TikTok Chrome session data directory mounting in `docker-compose.yml`.

### Changed
- **TikTok Scraper (Network Interception)**: Rewrote TikTok scraper to capture response bodies via Playwright network interception, replacing DOM parsing.
- **TikTok Login Flow**: Updated `login_tiktok.py` to use a persistent context, bypass Google secure browser login checks, and automatically store cookie sessions.
- **Ruff Linting**: Reorganized backend files and added Ruff configs for modern Python formatting.

### Fixed
- **Google Sign-In Rejected**: Resolved Playwright automation blocks by utilizing the local installed Google Chrome executable and masking browser automation flags (`navigator.webdriver`).
- **Memory Encryption Gaps**: Hardened the Fernet key derivation logic to derive the encryption key directly from the configured API key securely.

---

## [1.1.0] - 2026-05-15

### Added
- **Hybrid Decision Architecture**: Orchestrated the 3-Tier classification mechanism (Lexicon / ML / ONNX / LLM).
- **SQLite Fallback Cache**: Implemented semantic cache in SQL to optimize repeated classification calls.
- **Docker Compose**: Pre-configured services including PostgreSQL, Redis, and pgvector.
