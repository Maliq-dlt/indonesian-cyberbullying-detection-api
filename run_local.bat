@echo off
title BullyGuard ID Local Runner
echo ==========================================================
echo           BullyGuard ID Local Runner (No Docker)
echo ==========================================================
echo.

:: 1. Cek file .env
if not exist .env (
    echo [INFO] Berkas .env tidak ditemukan. Menyalin dari .env.example...
    copy .env.example .env
)

:: 2. Jalankan Backend FastAPI di jendela baru
echo [INFO] Menjalankan Backend API...
start "BullyGuard Backend API" cmd /k "cd cyberbullying_api && ..\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

:: 3. Jalankan Frontend React di jendela baru
echo [INFO] Menjalankan Frontend Web Dashboard...
start "BullyGuard Frontend Dashboard" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================================
echo [SUKSES] Backend dan Frontend sedang berjalan!
echo - API Backend: http://localhost:8000
echo - API Docs (Swagger): http://localhost:8000/docs
echo - Web Dashboard: http://localhost:5173 atau http://localhost:3000
echo ==========================================================
echo Silakan tekan sembarang tombol untuk menyelesaikan peluncuran ini.
pause
