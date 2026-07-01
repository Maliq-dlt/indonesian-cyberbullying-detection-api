# Contributing to BullyGuard ID

Thank you for your interest in contributing to BullyGuard ID! As a project designed for enterprise-scale collaboration (20+ active developers), we maintain high standards of code quality, security, and developer workflow.

Please read this guide to understand our branching model, commit conventions, code style, and how to set up your environment.

---

## 🏛️ Git Branching Strategy

We follow a modified **GitFlow** branching model:

* **`main`**: Production-ready code. Only merged from `develop` via Pull Requests. Direct pushes are disabled.
* **`develop`**: Integration branch for new features. All feature branches must branch off and merge back into `develop`.
* **`feature/*`**: Used for developing new features (e.g., `feature/custom-lexicon-weights`).
* **`bugfix/*`**: Used for fixing bugs from `develop` (e.g., `bugfix/tiktok-session-timeout`).
* **`hotfix/*`**: Used to fix critical production issues directly on `main`, which are then back-merged into `develop`.

---

## 💬 Commit Message Conventions

We enforce **Conventional Commits** to auto-generate changelogs and maintain a readable git history. Commit messages must follow this structure:

```text
<type>(<scope>): <description>

[optional body]
```

### Types:
* **`feat`**: A new feature (e.g., `feat(scraper): add fallback proxies for X scraper`)
* **`fix`**: A bug fix (e.g., `fix(auth): prevent rate limiter bypass`)
* **`docs`**: Documentation changes only (e.g., `docs(api): document websocket endpoints`)
* **`style`**: Changes that do not affect the meaning of the code (white-space, formatting, etc.)
* **`refactor`**: A code change that neither fixes a bug nor adds a feature (e.g., `refactor(model): clean up ONNX loader`)
* **`test`**: Adding missing tests or correcting existing tests
* **`chore`**: Changes to the build process or auxiliary tools and libraries (e.g., updating dependencies)

---

## 🛠️ Development Setup

### Backend (FastAPI)
1. **Virtual Environment**: Create a virtual environment using Python 3.11+
   ```bash
   cd cyberbullying_api
   python -m venv .venv
   source .venv/bin/activate # or .venv\Scripts\activate on Windows
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment Variables**: Create a local `.env` file from `.env.example`. **Never commit your `.env` file.**
   ```env
   ENV=development
   API_KEY=your_secure_development_key
   JWT_SECRET=your_jwt_secret  # Falls back to API_KEY if not set
   PG_URL=postgresql://cyber_user:cyber_password@localhost:5432/cyberbullying_db
   REDIS_URL=redis://localhost:6379/0
   ```

### Frontend (React + Vite)
1. **Node Version**: Use Node.js v20.x
2. **Install packages**:
   ```bash
   cd frontend
   npm install
   ```
3. **Run Dev Server**:
   ```bash
   npm run dev
   ```

---

## 🛡️ Security Guidelines

* **No Hardcoded Secrets**: Never commit private keys, API tokens, passwords, cookies, or user sessions. Use environment variables.
* **Secrets Scanning**: Pre-commit hooks will reject pushes containing patterns matching Hugging Face tokens (`hf_*`), credentials, or JSON cookie dumps.
* **Database Encryption**: All classification memory columns containing sensitive user metadata (e.g., usernames) are encrypted in PostgreSQL using Fernet symmetric encryption derived from `API_KEY`.

---

## 🧪 Testing Requirements

We maintain a high test coverage threshold (>80%). The project currently has **101 backend tests** and **45 frontend tests**.
* **Run Backend Tests**:
  ```bash
  # From project root (requires PYTHONPATH)
  $env:ENV="development"; $env:PYTHONPATH=".;cyberbullying_api"; pytest tests/ -q
  $env:ENV="development"; $env:PYTHONPATH=".;cyberbullying_api"; pytest cyberbullying_api/tests/ -q
  ```
* **Run Frontend Tests**:
  ```bash
  cd frontend
  npx vitest run
  ```
* Ensure you write unit tests for every new router endpoint, service utility, or data model you add.
* Mock external API calls (e.g., Hugging Face hub, Cloud LLM (Gemini API), TikTok HTTP endpoints) using pytest fixtures.

---

## 📝 Code Style & Linting

### Python (Backend)
We use `ruff` for linting and formatting.
- Format check: `ruff format --check`
- Lint check: `ruff check`

### TypeScript (Frontend)
We use `eslint` and `prettier`.
- Run linting: `npm run lint`
