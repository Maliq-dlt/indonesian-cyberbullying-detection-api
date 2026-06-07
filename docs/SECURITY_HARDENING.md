# 🔒 Security Hardening Report — BullyGuard ID

Dokumen ini menjelaskan langkah-langkah peningkatan keamanan (*security hardening*) yang diterapkan pada sistem BullyGuard ID untuk melindungi API dan infrastruktur dari potensi serangan siber.

---

## 🔑 1. Autentikasi API Key bertipe Constant-Time

Endpoint yang sensitif kini dilindungi secara ketat menggunakan otentikasi header `X-API-Key`.
- **Perbandingan Waktu Tetap (Constant-Time)**: Menggunakan pustaka `secrets.compare_digest` untuk membandingkan kunci autentikasi. Hal ini mencegah serangan *timing attack* yang dapat menebak API key dengan mengukur variasi waktu respon server.
- **Kebijakan Environment**:
  - **Lokal (Dev)**: Mengizinkan bypass jika `ALLOW_MISSING_API_KEY_IN_DEV=true`.
  - **Production**: API akan **menolak berjalan** atau menolak seluruh request jika `API_KEY` tidak diset.

> [!IMPORTANT]
> **Rekomendasi Konfigurasi Production:**
> ```env
> ENV=production
> API_KEY=rahasia_api_key_yang_sangat_panjang_dan_acak_12345
> ALLOW_MISSING_API_KEY_IN_DEV=false
> ```

---

## 🛡️ 2. Proteksi Rate Limiting Berbasis Redis

Untuk mencegah serangan brute-force, scraping massal, atau kelebihan beban (*denial of service*), rate limiter dipasang pada endpoint prediksi:
- **Konfigurasi Default**:
  ```env
  RATE_LIMIT_REQUESTS_PER_MINUTE=15
  RATE_LIMIT_WINDOW_SECONDS=60
  ```
- **Kebijakan Fail-Open / Fail-Closed**:
  - Di development, `RATE_LIMIT_FAIL_OPEN=true` mengizinkan request tetap jalan meskipun Redis mati (untuk kemudahan setup tanpa docker).
  - Di production, `RATE_LIMIT_FAIL_OPEN=false` wajib diterapkan. Jika Redis tidak dapat dihubungi, API akan menolak request secara aman (*fail-closed*) demi mencegah bypass rate-limit.

---

## 🌐 3. Kebijakan CORS yang Ketat

- **Tanpa Wildcard di Production**: Penggunaan asal domain wildcard `*` dilarang keras di production.
- **Konfigurasi Origin**: Domain frontend resmi harus didefinisikan secara eksplisit di `.env`:
  ```env
  ALLOWED_ORIGINS=https://dashboard.bullyguard.id,https://api.bullyguard.id
  ```

---

## 🐳 4. Keamanan Docker Credentials (Environment Variables)

- Semua password bawaan (*hardcoded*) pada berkas `docker-compose.yml` telah dipindahkan menggunakan *interpolation syntax*:
  ```yaml
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-cyber_password}
  ```
- Kredensial default ini hanya berlaku untuk lokal. Di production, Docker akan otomatis mengambil variabel lingkungan yang disuplai oleh sistem hosting Anda yang aman.

---

## 🚫 5. Proteksi Server-Side Request Forgery (SSRF) pada Webhook

Sistem webhook yang digunakan untuk mengirim notifikasi hasil deteksi rentan terhadap serangan SSRF jika penyerang mengirim IP internal server.
- **Penyaringan IP (IP Filtering)**: Sistem secara otomatis memeriksa dan memblokir request webhook yang mengarah ke:
  - Loopback IP (`127.0.0.1`, `::1`)
  - Private IP (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
  - Link-Local / Multicast / Unspecified IPs
- **Allowlist Host**: Anda dapat membatasi domain webhook eksternal yang sah melalui `.env`:
  ```env
  WEBHOOK_ALLOWED_HOSTS=hooks.slack.com,discord.com
  ```

---

## 🛡️ 6. Keamanan Header Reverse Proxy

API Key rate limiter memerlukan IP asli klien untuk melacak limit.
- **Trust Proxy Headers**: Hanya aktifkan `TRUST_PROXY_HEADERS=true` jika backend berada di belakang reverse proxy terpercaya (seperti Nginx atau Cloudflare).
- Jika bernilai `false`, header `X-Forwarded-For` dan `X-Real-IP` akan diabaikan untuk mencegah pemalsuan IP (*IP spoofing*).

---

## 🗂️ 7. Pemetaan Keamanan Endpoint

| Endpoint API | Akses Publik | Keterangan / Proteksi |
| :--- | :---: | :--- |
| **`/`** | ✅ Ya | Landing page statis |
| **`/health`** | ✅ Ya | Status pengecekan kontainer (*healthcheck*) |
| **`/docs`** | ⚠️ Dev Only | Swagger UI (Wajib dimatikan di production) |
| **`/predict/*`** | ❌ Dilindungi | Endpoint klasifikasi hybrid |
| **`/models/*`** | ❌ Dilindungi | Pengaturan dan retrain model |

---

## 📝 8. Agenda Perbaikan Keamanan Selanjutnya
- [ ] Menerapkan autentikasi berbasis token session/JWT jika aplikasi berkembang mendukung multi-user.
- [ ] Menambahkan audit logging untuk mendokumentasikan setiap aksi admin (retraining model, audit data).
- [ ] Membatasi ukuran body payload request di tingkat reverse proxy (Nginx `client_max_body_size`) untuk mencegah serangan denial-of-service via upload teks raksasa.
- [ ] Menambahkan pemindaian celah keamanan dependensi (*dependency vulnerability scanning*) otomatis di CI/CD.

