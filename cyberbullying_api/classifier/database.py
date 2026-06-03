import os
import re
import json
import asyncio
from typing import List, Dict, Any

try:
    import asyncpg
    import redis.asyncio as redis
except ImportError:
    asyncpg = None
    redis = None
    print("Warning: asyncpg atau redis tidak terinstal. Modul Database mungkin tidak beroperasi.")

from models import HybridResponse, determine_category

# === Konfigurasi Infrastruktur Baru (PostgreSQL & Redis) ===
PG_URL = os.getenv("PG_URL", "postgresql://cyber_user:cyber_password@127.0.0.1:5432/cyberbullying_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

PG_POOL = None
REDIS_CLIENT = None

async def get_pg_pool():
    global PG_POOL
    if PG_POOL is None and asyncpg is not None:
        try:
            PG_POOL = await asyncpg.create_pool(PG_URL, min_size=1, max_size=10)
            async with PG_POOL.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS classification_memory (
                        text TEXT PRIMARY KEY,
                        is_toxic INTEGER,
                        is_bully INTEGER,
                        reason TEXT,
                        decision_source TEXT,
                        confidence REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_validated INTEGER DEFAULT 0,
                        embedding VECTOR(384)
                    )
                """)
            print("PostgreSQL terkoneksi & tabel diverifikasi (dengan pgvector).")
        except Exception as e:
            print(f"Warning: Gagal inisialisasi PostgreSQL: {e}")
    return PG_POOL

async def get_redis():
    global REDIS_CLIENT
    if REDIS_CLIENT is None and redis is not None:
        try:
            REDIS_CLIENT = redis.from_url(REDIS_URL, decode_responses=True)
            await REDIS_CLIENT.ping()
            print("Redis terkoneksi.")
        except Exception as e:
            print(f"Warning: Gagal inisialisasi Redis: {e}")
            REDIS_CLIENT = None
    return REDIS_CLIENT

def init_cache_db():
    # Inisialisasi basis data kini dilakukan secara asinkron (lazy loading) via get_pg_pool() dan get_redis()
    print(f"Sistem Infrastruktur siap menggunakan PostgreSQL ({PG_URL}) dan Redis ({REDIS_URL}) secara lazy.")

async def get_cached_response(text: str) -> Dict[str, Any] | None:
    r = await get_redis()
    if r:
        try:
            res = await r.get(f"ollama:{text}")
            if res:
                return json.loads(res)
        except Exception as e:
            print(f"Warning: Redis error pada get_cached_response: {e}")
    return None

async def save_cached_response(text: str, response_dict: Dict[str, Any]):
    r = await get_redis()
    if r:
        try:
            await r.setex(f"ollama:{text}", 604800, json.dumps(response_dict)) # Cache 7 hari
        except Exception as e:
            print(f"Warning: Redis error pada save_cached_response: {e}")

async def save_classification_memory(res: HybridResponse, embedding_json: str = None):
    r = await get_redis()
    if r:
        try:
            mem_data = {
                "is_toxic": res.is_toxic,
                "is_bully": res.is_bully,
                "reason": res.reason,
                "decision_source": res.decision_source,
                "confidence": max(res.probability_toxic, res.probability_bully)
            }
            await r.set(f"mem:{res.text}", json.dumps(mem_data), ex=2592000) # Cache 30 hari
        except Exception:
            pass
            
    pool = await get_pg_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO classification_memory 
                    (text, is_toxic, is_bully, reason, decision_source, confidence, is_validated, embedding) 
                    VALUES ($1, $2, $3, $4, $5, $6, 0, $7::vector)
                    ON CONFLICT (text) DO UPDATE SET
                        is_toxic = EXCLUDED.is_toxic,
                        is_bully = EXCLUDED.is_bully,
                        reason = EXCLUDED.reason,
                        decision_source = EXCLUDED.decision_source,
                        confidence = EXCLUDED.confidence,
                        embedding = COALESCE(EXCLUDED.embedding, classification_memory.embedding)
                """, 
                res.text, 
                1 if res.is_toxic else 0, 
                1 if res.is_bully else 0, 
                res.reason, 
                res.decision_source, 
                float(max(res.probability_toxic, res.probability_bully)),
                embedding_json)
                return
        except Exception as e:
            print(f"Warning: PostgreSQL error pada save_classification_memory: {e}")

    # Fallback to SQLite
    try:
        import sqlite3
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "cache", "ollama_cache.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classification_memory (
                text TEXT PRIMARY KEY,
                is_toxic INTEGER,
                is_bully INTEGER,
                reason TEXT,
                decision_source TEXT,
                confidence REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_validated INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            INSERT INTO classification_memory 
            (text, is_toxic, is_bully, reason, decision_source, confidence, is_validated) 
            VALUES (?, ?, ?, ?, ?, ?, 0)
            ON CONFLICT(text) DO UPDATE SET
                is_toxic = excluded.is_toxic,
                is_bully = excluded.is_bully,
                reason = excluded.reason,
                decision_source = excluded.decision_source,
                confidence = excluded.confidence
        """, (
            res.text, 
            1 if res.is_toxic else 0, 
            1 if res.is_bully else 0, 
            res.reason, 
            res.decision_source, 
            float(max(res.probability_toxic, res.probability_bully))
        ))
        conn.commit()
        conn.close()
    except Exception as sq_err:
        print(f"Warning: SQLite error pada save_classification_memory fallback: {sq_err}")

async def get_classification_memory(text: str) -> HybridResponse | None:
    r = await get_redis()
    if r:
        try:
            cached = await r.get(f"mem:{text}")
            if cached:
                data = json.loads(cached)
                is_toxic = data["is_toxic"]
                is_bully = data["is_bully"]
                base_source = re.sub(r'\s*\((Redis Cache|PG Database)\)$', '', data["decision_source"])
                return HybridResponse(
                    text=text,
                    is_toxic=is_toxic,
                    is_bully=is_bully,
                    probability_toxic=data["confidence"] if is_toxic else 0.0,
                    probability_bully=data["confidence"] if is_bully else 0.0,
                    category=determine_category(is_toxic, is_bully),
                    decision_source=base_source + " (Redis Cache)",
                    reason=data["reason"]
                )
        except Exception as e:
            print(f"Warning: Redis error saat membaca memori: {e}")
            
    pool = await get_pg_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT is_toxic, is_bully, reason, decision_source, confidence 
                    FROM classification_memory 
                    WHERE text = $1
                """, text)
                if row:
                    is_toxic = bool(row["is_toxic"])
                    is_bully = bool(row["is_bully"])
                    if r:
                        mem_data = {
                            "is_toxic": is_toxic,
                            "is_bully": is_bully,
                            "reason": row["reason"],
                            "decision_source": row["decision_source"],
                            "confidence": row["confidence"]
                        }
                        await r.setex(f"mem:{text}", 2592000, json.dumps(mem_data))
                        
                    base_source = re.sub(r'\s*\((Redis Cache|PG Database)\)$', '', row["decision_source"])
                    return HybridResponse(
                        text=text,
                        is_toxic=is_toxic,
                        is_bully=is_bully,
                        probability_toxic=row["confidence"] if is_toxic else 0.0,
                        probability_bully=row["confidence"] if is_bully else 0.0,
                        category=determine_category(is_toxic, is_bully),
                        decision_source=base_source + " (PG Database)",
                        reason=row["reason"]
                    )
        except Exception as e:
            print(f"Warning: PostgreSQL error saat membaca memori: {e}")
    return None


async def get_unvalidated_memory(limit: int = 50) -> List[Dict[str, Any]]:
    results = []
    pool = await get_pg_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT text, is_toxic, is_bully, reason, decision_source, confidence, timestamp, is_validated
                    FROM classification_memory
                    WHERE is_validated = 0
                    ORDER BY timestamp DESC
                    LIMIT $1
                """, limit)
                for r in rows:
                    results.append(dict(r))
            return results
        except Exception as e:
            print(f"Warning: PostgreSQL error pada get_unvalidated_memory: {e}")

    # SQLite fallback
    try:
        import sqlite3
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "cache", "ollama_cache.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT text, is_toxic, is_bully, reason, decision_source, confidence, timestamp, is_validated
                FROM classification_memory
                WHERE is_validated = 0
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            for r in rows:
                results.append(dict(r))
            conn.close()
    except Exception as e:
        print(f"Warning: SQLite error pada get_unvalidated_memory: {e}")
    return results


async def update_validation_status(text: str, is_toxic: bool, is_bully: bool, is_validated: int = 1):
    # Update Redis cache memory if active
    r = await get_redis()
    if r:
        try:
            mem_data = {
                "is_toxic": is_toxic,
                "is_bully": is_bully,
                "reason": "Umpan balik koreksi manusia (Validated)",
                "decision_source": "Koreksi Manusia",
                "confidence": 1.0
            }
            await r.set(f"mem:{text}", json.dumps(mem_data), ex=2592000)
        except Exception:
            pass

    pool = await get_pg_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO classification_memory 
                    (text, is_toxic, is_bully, reason, decision_source, confidence, is_validated) 
                    VALUES ($1, $2, $3, $4, $5, 1.0, $6)
                    ON CONFLICT (text) DO UPDATE SET
                        is_toxic = EXCLUDED.is_toxic,
                        is_bully = EXCLUDED.is_bully,
                        reason = EXCLUDED.reason,
                        decision_source = EXCLUDED.decision_source,
                        confidence = EXCLUDED.confidence,
                        is_validated = EXCLUDED.is_validated
                """, 
                text, 
                1 if is_toxic else 0, 
                1 if is_bully else 0, 
                "Umpan balik koreksi manusia (Validated)", 
                "Koreksi Manusia",
                is_validated)
            print(f"[HITL] Berhasil memvalidasi data di PostgreSQL untuk: '{text}'")
            return True
        except Exception as e:
            print(f"Warning: PostgreSQL error pada update_validation_status: {e}")

    # SQLite fallback
    try:
        import sqlite3
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "cache", "ollama_cache.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classification_memory (
                text TEXT PRIMARY KEY,
                is_toxic INTEGER,
                is_bully INTEGER,
                reason TEXT,
                decision_source TEXT,
                confidence REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_validated INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            INSERT INTO classification_memory 
            (text, is_toxic, is_bully, reason, decision_source, confidence, is_validated) 
            VALUES (?, ?, ?, ?, ?, 1.0, ?)
            ON CONFLICT(text) DO UPDATE SET
                is_toxic = excluded.is_toxic,
                is_bully = excluded.is_bully,
                reason = excluded.reason,
                decision_source = excluded.decision_source,
                confidence = excluded.confidence,
                is_validated = excluded.is_validated
        """, (text, 1 if is_toxic else 0, 1 if is_bully else 0, "Umpan balik koreksi manusia (Validated)", "Koreksi Manusia", is_validated))
        conn.commit()
        conn.close()
        print(f"[HITL] Berhasil memvalidasi data di SQLite untuk: '{text}'")
        return True
    except Exception as e:
        print(f"Warning: SQLite error pada update_validation_status: {e}")
    return False

