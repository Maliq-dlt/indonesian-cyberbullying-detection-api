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
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS classification_memory (
                        text TEXT PRIMARY KEY,
                        is_toxic INTEGER,
                        is_bully INTEGER,
                        reason TEXT,
                        decision_source TEXT,
                        confidence REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_validated INTEGER DEFAULT 0
                    )
                """)
            print("PostgreSQL terkoneksi & tabel diverifikasi.")
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

async def save_classification_memory(res: HybridResponse):
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
                    (text, is_toxic, is_bully, reason, decision_source, confidence, is_validated) 
                    VALUES ($1, $2, $3, $4, $5, $6, 0)
                    ON CONFLICT (text) DO UPDATE SET
                        is_toxic = EXCLUDED.is_toxic,
                        is_bully = EXCLUDED.is_bully,
                        reason = EXCLUDED.reason,
                        decision_source = EXCLUDED.decision_source,
                        confidence = EXCLUDED.confidence
                """, 
                res.text, 
                1 if res.is_toxic else 0, 
                1 if res.is_bully else 0, 
                res.reason, 
                res.decision_source, 
                float(max(res.probability_toxic, res.probability_bully)))
        except Exception as e:
            print(f"Warning: PostgreSQL error pada save_classification_memory: {e}")

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
