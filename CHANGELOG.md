# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
