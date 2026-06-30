#!/bin/bash
echo "=========================================================="
echo "          BullyGuard ID Local Runner (No Docker)"
echo "=========================================================="
echo ""

# 1. Cek file .env
if [ ! -f .env ]; then
    echo "[INFO] Berkas .env tidak ditemukan. Menyalin dari .env.example..."
    cp .env.example .env
fi

# Determine python virtual environment activation path
if [ -d ".venv" ]; then
    PYTHON_EXEC=".venv/bin/python"
else
    PYTHON_EXEC="python3"
fi

# 2. Jalankan Backend FastAPI & Frontend React secara paralel
echo "[INFO] Menjalankan Backend API & Frontend Dashboard..."

# Cleanup trap to kill background processes on exit
cleanup() {
    echo ""
    echo "[INFO] Menghentikan Backend dan Frontend..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}
trap cleanup SIGINT SIGTERM

# Start Backend
cd cyberbullying_api && ../$PYTHON_EXEC -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start Frontend
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo "=========================================================="
echo "[SUKSES] Backend dan Frontend sedang berjalan!"
echo "- API Backend: http://localhost:8000"
echo "- API Docs (Swagger): http://localhost:8000/docs"
echo "- Web Dashboard: http://localhost:5173 atau http://localhost:3000"
echo "=========================================================="
echo "Tekan CTRL+C untuk menghentikan kedua layanan."

# Wait for background processes to keep shell open
wait
