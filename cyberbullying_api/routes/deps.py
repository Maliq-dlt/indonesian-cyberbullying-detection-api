from fastapi import Header, HTTPException, Request
import os
import hashlib
import hmac
import socket
import ipaddress
from urllib.parse import urlparse
import classifier
from routes.state import API_KEY_ENV

def verify_api_key(x_api_key: str = Header(None)):
    if not API_KEY_ENV:
        if os.getenv("ENV", "production").lower() != "development":
            raise HTTPException(status_code=500, detail="Konfigurasi Server Error: API_KEY harus diatur kecuali di lingkungan 'development'.")
        return
    
    # Proteksi Timing Attack menggunakan hashing SHA-256 dan perbandingan constant-time
    expected_hash = hashlib.sha256(API_KEY_ENV.encode("utf-8")).digest()
    provided_hash = hashlib.sha256(x_api_key.encode("utf-8")).digest() if x_api_key else b""
    
    if not hmac.compare_digest(provided_hash, expected_hash):
        raise HTTPException(status_code=401, detail="API Key tidak valid atau tidak disediakan.")

async def rate_limit_ollama_and_batch(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    r = await classifier.get_redis()
    if r:
        try:
            path_normalized = request.url.path.rstrip('/').lower()
            key = f"rate_limit:{client_ip}:{path_normalized}"
            
            # Gunakan pipeline untuk mendapatkan nilai setelah inkrementasi dan TTL secara atomik
            pipe = r.pipeline()
            pipe.incr(key)
            pipe.ttl(key)
            val, ttl = await pipe.execute()
            
            # Jika baru dibuat (nilai = 1) atau tidak memiliki TTL, atur kedaluwarsa ke 60 detik
            if val == 1 or ttl < 0:
                await r.expire(key, 60)
                
            if val > 15:
                raise HTTPException(status_code=429, detail="Terlalu banyak permintaan. Batas limit terlampaui (15 request/menit).")
        except HTTPException:
            raise
        except Exception as e:
            print(f"Warning: Gagal mengevaluasi rate limit di Redis: {e}")

def is_safe_webhook_url(url: str) -> bool:
    """Memvalidasi URL webhook untuk mencegah kerentanan SSRF (Server-Side Request Forgery).
    Memblokir IP lokal, loopback, multicast, link-local, dan subnet privat.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            return False
        
        hostname = parsed.hostname
        if not hostname:
            return False
            
        # Selesaikan hostname ke IP addresses
        addr_info = socket.getaddrinfo(hostname, None)
        for addr in addr_info:
            ip_str = addr[4][0]
            ip = ipaddress.ip_address(ip_str)
            if ip.is_loopback or ip.is_private or ip.is_multicast or ip.is_link_local or ip.is_unspecified:
                return False
        return True
    except Exception:
        return False
