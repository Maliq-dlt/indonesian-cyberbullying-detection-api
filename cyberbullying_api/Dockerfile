# 1. Menggunakan base image python slim yang ringan
FROM python:3.10-slim

# 2. Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1

# 3. Buat folder aplikasi utama
WORKDIR /app

# 4. Salin requirements.txt terlebih dahulu (agar Docker cache bisa dimanfaatkan)
COPY cyberbullying_api/requirements.txt /app/cyberbullying_api/requirements.txt

# 5. Instal dependensi Python
# Optimasi: Menginstal PyTorch versi CPU-only untuk memperkecil ukuran image Docker secara drastis
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r /app/cyberbullying_api/requirements.txt

# 6. Salin dataset kamus yang diperlukan untuk preprocessing
COPY "dataset 1" /app/dataset\ 1
COPY "dataset 2" /app/dataset\ 2
COPY "cyberbullying-indonesia" /app/cyberbullying-indonesia

# 7. Salin seluruh isi folder API beserta file model yang telah dilatih
COPY cyberbullying_api /app/cyberbullying_api

# 8. Set working directory ke folder API untuk menjalankan Uvicorn
WORKDIR /app/cyberbullying_api

# 9. Ekspos port 8000
EXPOSE 8000

# 10. Jalankan aplikasi web server Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
