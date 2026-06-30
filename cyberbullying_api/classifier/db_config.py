import os
import re
import json
import asyncio
import base64
import hashlib
from typing import List, Dict, Any
import time

try:
    import asyncpg
    import redis.asyncio as redis
except ImportError:
    asyncpg = None
    redis = None
    print("Warning: asyncpg atau redis tidak terinstal. Modul Database mungkin tidak beroperasi.")

from cryptography.fernet import Fernet

# === Konfigurasi Kriptografi ===
api_key = os.getenv("API_KEY", "")
env = os.getenv("ENV", "production").lower()

if not api_key:
    if env != "development":
        raise ValueError(
            "CRITICAL: Variabel lingkungan API_KEY tidak diatur di lingkungan non-development! "
            "Server menolak startup demi perlindungan data (Kunci enkripsi tidak boleh menggunakan nilai bawaan)."
        )
    # Gunakan kunci acak unik per-instalasi (disimpan ke file lokal) agar tidak hardcoded di source code
    _dev_key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", ".dev_encryption_key")
    os.makedirs(os.path.dirname(_dev_key_path), exist_ok=True)
    if os.path.exists(_dev_key_path):
        with open(_dev_key_path, "r") as _f:
            key_source = _f.read().strip().encode("utf-8")
    else:
        import secrets
        _random_key = secrets.token_hex(32)
        with open(_dev_key_path, "w") as _f:
            _f.write(_random_key)
        key_source = _random_key.encode("utf-8")
        print(f"WARNING: Kunci enkripsi development baru digenerate dan disimpan di {_dev_key_path}")
else:
    key_source = api_key.encode("utf-8")

derived_key = base64.urlsafe_b64encode(hashlib.sha256(key_source).digest())
CIPHER_SUITE = Fernet(derived_key)

def encrypt_text(text: str) -> str:
    if not text:
        return ""
    try:
        return CIPHER_SUITE.encrypt(text.encode("utf-8")).decode("utf-8")
    except Exception as e:
        print(f"Warning: Gagal mengenkripsi teks: {e}")
        return text

def decrypt_text(enc_text: str) -> str:
    if not enc_text:
        return ""
    try:
        return CIPHER_SUITE.decrypt(enc_text.encode("utf-8")).decode("utf-8")
    except Exception:
        # Fallback jika data belum terenkripsi (dukungan kompatibilitas backward)
        return enc_text

# === Konfigurasi Infrastruktur Baru (PostgreSQL & Redis) ===
PG_URL = os.getenv("PG_URL", "postgresql://cyber_user:cyber_password@127.0.0.1:5432/cyberbullying_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

class EventLoopSafeLock:
    def __init__(self):
        self._locks = {}

    def _get_lock(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.Lock()
        if loop not in self._locks:
            self._locks[loop] = asyncio.Lock()
        return self._locks[loop]

    async def acquire(self):
        return await self._get_lock().acquire()

    def release(self):
        self._get_lock().release()

    def locked(self):
        return self._get_lock().locked()

    async def __aenter__(self):
        await self._get_lock().acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._get_lock().release()

PG_POOL = None
REDIS_CLIENT = None
SQLITE_WRITE_LOCK = EventLoopSafeLock()

PG_FAILED_UNTIL = 0.0

async def get_pg_pool():
    global PG_POOL, PG_FAILED_UNTIL
    current_time = time.time()
    if PG_POOL is None and current_time < PG_FAILED_UNTIL:
        return None
        
    if PG_POOL is None and asyncpg is not None:
        try:
            PG_POOL = await asyncpg.create_pool(PG_URL, min_size=1, max_size=10, timeout=2.0)
            async with PG_POOL.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # Cek jika tabel classification_memory menggunakan skema lama (kolom 'text' ada)
                has_old_text = False
                try:
                    table_info = await conn.fetchrow("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name='classification_memory' AND column_name='text'
                    """)
                    if table_info:
                        has_old_text = True
                except Exception:
                    pass
                
                if has_old_text:
                    print("Melakukan migrasi PostgreSQL ke skema baru yang terenkripsi...")
                    await conn.execute("ALTER TABLE classification_memory RENAME TO classification_memory_old;")
                    await conn.execute("""
                        CREATE TABLE classification_memory (
                            text_hash VARCHAR(64) PRIMARY KEY,
                            encrypted_text TEXT,
                            is_toxic INTEGER,
                            is_bully INTEGER,
                            reason TEXT,
                            decision_source TEXT,
                            confidence REAL,
                            probability_toxic REAL,
                            probability_bully REAL,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            is_validated INTEGER DEFAULT 0,
                            embedding VECTOR(384)
                        )
                    """)
                    old_rows = await conn.fetch("SELECT * FROM classification_memory_old;")
                    for row in old_rows:
                        text = row["text"]
                        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
                        enc_text = encrypt_text(text)
                        await conn.execute("""
                            INSERT INTO classification_memory 
                            (text_hash, encrypted_text, is_toxic, is_bully, reason, decision_source, confidence, probability_toxic, probability_bully, timestamp, is_validated, embedding)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                        """, 
                        text_hash, enc_text, row["is_toxic"], row["is_bully"], row["reason"], row["decision_source"], 
                        row["confidence"], row["probability_toxic"], row["probability_bully"], row["timestamp"], row["is_validated"], row["embedding"])
                    await conn.execute("DROP TABLE classification_memory_old;")
                    print("Migrasi PostgreSQL selesai.")
                else:
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS classification_memory (
                            text_hash VARCHAR(64) PRIMARY KEY,
                            encrypted_text TEXT,
                            is_toxic INTEGER,
                            is_bully INTEGER,
                            reason TEXT,
                            decision_source TEXT,
                            confidence REAL,
                            probability_toxic REAL,
                            probability_bully REAL,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            is_validated INTEGER DEFAULT 0,
                            embedding VECTOR(384)
                        )
                    """)
                try:
                    await conn.execute("ALTER TABLE classification_memory ADD COLUMN IF NOT EXISTS probability_toxic REAL;")
                    await conn.execute("ALTER TABLE classification_memory ADD COLUMN IF NOT EXISTS probability_bully REAL;")
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS retraining_history (
                            id SERIAL PRIMARY KEY,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            f1_toxic REAL,
                            f1_bully REAL,
                            threshold_toxic REAL,
                            threshold_bully REAL,
                            active_version TEXT
                        );
                    """)
                except Exception:
                    pass
                try:
                    await conn.execute("CREATE INDEX IF NOT EXISTS classification_memory_embedding_idx ON classification_memory USING hnsw (embedding vector_cosine_ops);")
                    print("Indeks HNSW pgvector berhasil dikonfigurasi.")
                except Exception as idx_err:
                    print(f"Warning: Gagal membuat indeks HNSW pgvector (melewati): {idx_err}")
            print("PostgreSQL terkoneksi & tabel diverifikasi (dengan pgvector).")
        except Exception as e:
            print(f"Warning: Gagal inisialisasi PostgreSQL: {e}")
            PG_FAILED_UNTIL = current_time + 60.0
    return PG_POOL

REDIS_FAILED_UNTIL = 0.0

async def get_redis():
    global REDIS_CLIENT, REDIS_FAILED_UNTIL
    current_time = time.time()
    if REDIS_CLIENT is None and current_time < REDIS_FAILED_UNTIL:
        return None

    if REDIS_CLIENT is None and redis is not None:
        try:
            REDIS_CLIENT = redis.from_url(
                REDIS_URL, 
                decode_responses=True, 
                socket_timeout=1.5, 
                socket_connect_timeout=1.5
            )
            await REDIS_CLIENT.ping()
            print("Redis terkoneksi.")
        except Exception as e:
            print(f"Warning: Gagal inisialisasi Redis: {e}")
            REDIS_FAILED_UNTIL = current_time + 60.0
            REDIS_CLIENT = None
    return REDIS_CLIENT

def init_sqlite_db(db_path: str):
    import sqlite3
    conn = sqlite3.connect(db_path, timeout=30.0)
    cursor = conn.cursor()
    
    # Periksa apakah tabel classification_memory sudah ada dan menggunakan skema lama (kolom 'text' ada)
    cursor.execute("PRAGMA table_info(classification_memory)")
    columns = cursor.fetchall()
    
    has_old_text = False
    if columns:
        col_names = [col[1] for col in columns]
        if "text" in col_names:
            has_old_text = True
            
    if has_old_text:
        print("Melakukan migrasi SQLite ke skema baru yang terenkripsi...")
        cursor.execute("ALTER TABLE classification_memory RENAME TO classification_memory_old")
        cursor.execute("""
            CREATE TABLE classification_memory (
                text_hash TEXT PRIMARY KEY,
                encrypted_text TEXT,
                is_toxic INTEGER,
                is_bully INTEGER,
                reason TEXT,
                decision_source TEXT,
                confidence REAL,
                probability_toxic REAL,
                probability_bully REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_validated INTEGER DEFAULT 0,
                embedding TEXT
            )
        """)
        cursor.execute("SELECT text, is_toxic, is_bully, reason, decision_source, confidence, probability_toxic, probability_bully, timestamp, is_validated FROM classification_memory_old")
        old_rows = cursor.fetchall()
        for row in old_rows:
            text = row[0]
            text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            enc_text = encrypt_text(text)
            cursor.execute("""
                INSERT INTO classification_memory 
                (text_hash, encrypted_text, is_toxic, is_bully, reason, decision_source, confidence, probability_toxic, probability_bully, timestamp, is_validated, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
            """, (
                text_hash, enc_text, row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9]
            ))
        cursor.execute("DROP TABLE classification_memory_old")
        conn.commit()
        print("Migrasi SQLite selesai.")
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classification_memory (
                text_hash TEXT PRIMARY KEY,
                encrypted_text TEXT,
                is_toxic INTEGER,
                is_bully INTEGER,
                reason TEXT,
                decision_source TEXT,
                confidence REAL,
                probability_toxic REAL,
                probability_bully REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_validated INTEGER DEFAULT 0,
                embedding TEXT
            )
        """)
        try:
            cursor.execute("ALTER TABLE classification_memory ADD COLUMN probability_toxic REAL;")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE classification_memory ADD COLUMN probability_bully REAL;")
        except Exception:
            pass
        try:
            cursor.execute("ALTER TABLE classification_memory ADD COLUMN embedding TEXT;")
        except Exception:
            pass
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS retraining_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                f1_toxic REAL,
                f1_bully REAL,
                threshold_toxic REAL,
                threshold_bully REAL,
                active_version TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_class_mem_timestamp ON classification_memory(timestamp);")
        conn.commit()
    conn.close()

def init_cache_db():
    masked_pg = re.sub(r'(://[^:]*:)([^@/]+)(@)', r'\1***\3', PG_URL)
    masked_redis = re.sub(r'(://[^:]*:)([^@/]+)(@)', r'\1***\3', REDIS_URL)
    print(f"Sistem Infrastruktur siap menggunakan PostgreSQL ({masked_pg}) dan Redis ({masked_redis}) secara lazy.")
    
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "cache", "cloud_llm_cache.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        init_sqlite_db(db_path)
    except Exception as e:
        print(f"Warning: Gagal inisialisasi SQLite database: {e}")
