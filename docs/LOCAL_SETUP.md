# Local Setup Guide — BullyGuard ID

Dokumen ini berisi panduan setup lokal yang lebih rapi daripada README utama.

---

## 1. Clone Repository

```bash
git clone https://github.com/Maliq-dlt/indonesian-cyberbullying-detection-api.git
cd indonesian-cyberbullying-detection-api
```

---

## 2. Environment

Salin file environment contoh:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Minimal konfigurasi:

```env
ENV=development
API_KEY=change_me_to_a_long_random_secret
PG_URL=postgresql://cyber_user:cyber_password@localhost:5432/cyberbullying_db
REDIS_URL=redis://:cyber_redis_pass@localhost:6379/0
```

---

## 3. Jalankan PostgreSQL dan Redis

```bash
docker compose up -d db redis
```

Cek container:

```bash
docker compose ps
```

---

## 4. Setup Backend

```bash
cd cyberbullying_api
python -m venv .venv
```

Aktivasi virtualenv:

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows CMD:

```cmd
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependency:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Jalankan server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Buka:

```text
http://localhost:8000/docs
```

---

## 5. Setup Frontend

Dari root project:

```bash
cd frontend
npm install
npm run dev
```

Buka:

```text
http://localhost:5173
```

---

## 6. Testing

Backend:

```bash
pytest cyberbullying_api/tests
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

---

## 7. Masalah Umum

### Backend tidak bisa connect ke PostgreSQL

Cek apakah container database aktif:

```bash
docker compose ps
```

Cek log:

```bash
docker compose logs db
```

### Redis error

Cek password Redis di `.env` dan `docker-compose.yml`.

### Endpoint menolak request

Pastikan header API key dikirim:

```text
X-API-Key: change_me_to_a_long_random_secret
```

### Frontend tidak bisa akses API

Cek `ALLOWED_ORIGINS` dan pastikan origin frontend terdaftar.
