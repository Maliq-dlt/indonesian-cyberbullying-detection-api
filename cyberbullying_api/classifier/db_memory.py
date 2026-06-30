import os
import sqlite3
import re
import json
import hashlib
import asyncio
from typing import List, Dict, Any, Optional
from models import HybridResponse, determine_category
from classifier.db_config import (
    get_pg_pool, get_redis, encrypt_text, decrypt_text, SQLITE_WRITE_LOCK
)

async def save_classification_memory(res: HybridResponse, embedding_json: str | None = None):
    # Validasi bahwa embedding adalah daftar angka finite yang valid
    if embedding_json:
        try:
            emb_list = json.loads(embedding_json)
            if isinstance(emb_list, list):
                import math
                if any(not math.isfinite(x) for x in emb_list):
                    embedding_json = None
            else:
                embedding_json = None
        except Exception:
            embedding_json = None
            
    text_hash = hashlib.sha256(res.text.encode("utf-8")).hexdigest()
    enc_text = encrypt_text(res.text)

    r = await get_redis()
    if r:
        try:
            mem_data = {
                "is_toxic": res.is_toxic,
                "is_bully": res.is_bully,
                "reason": res.reason,
                "decision_source": res.decision_source,
                "confidence": max(res.probability_toxic, res.probability_bully),
                "probability_toxic": res.probability_toxic,
                "probability_bully": res.probability_bully
            }
            await r.set(f"mem:{text_hash}", json.dumps(mem_data), ex=2592000) # Cache 30 hari
        except Exception:
            pass
            
    pool = await get_pg_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO classification_memory 
                    (text_hash, encrypted_text, is_toxic, is_bully, reason, decision_source, confidence, probability_toxic, probability_bully, is_validated, embedding) 
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 0, $10::vector)
                    ON CONFLICT (text_hash) DO UPDATE SET
                        encrypted_text = EXCLUDED.encrypted_text,
                        is_toxic = EXCLUDED.is_toxic,
                        is_bully = EXCLUDED.is_bully,
                        reason = EXCLUDED.reason,
                        decision_source = EXCLUDED.decision_source,
                        confidence = EXCLUDED.confidence,
                        probability_toxic = EXCLUDED.probability_toxic,
                        probability_bully = EXCLUDED.probability_bully,
                        embedding = COALESCE(EXCLUDED.embedding, classification_memory.embedding)
                """, 
                text_hash,
                enc_text,
                1 if res.is_toxic else 0, 
                1 if res.is_bully else 0, 
                res.reason, 
                res.decision_source, 
                float(max(res.probability_toxic, res.probability_bully)),
                float(res.probability_toxic),
                float(res.probability_bully),
                embedding_json)
                return
        except Exception as e:
            print(f"Warning: PostgreSQL error pada save_classification_memory: {e}")

    # Fallback to SQLite
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "cache", "cloud_llm_cache.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        def write_sqlite():
            conn = sqlite3.connect(db_path, timeout=30.0)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO classification_memory 
                (text_hash, encrypted_text, is_toxic, is_bully, reason, decision_source, confidence, probability_toxic, probability_bully, is_validated, embedding) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                ON CONFLICT(text_hash) DO UPDATE SET
                    encrypted_text = excluded.encrypted_text,
                    is_toxic = excluded.is_toxic,
                    is_bully = excluded.is_bully,
                    reason = excluded.reason,
                    decision_source = excluded.decision_source,
                    confidence = excluded.confidence,
                    probability_toxic = excluded.probability_toxic,
                    probability_bully = excluded.probability_bully,
                    embedding = COALESCE(excluded.embedding, classification_memory.embedding)
            """, (
                text_hash, 
                enc_text,
                1 if res.is_toxic else 0, 
                1 if res.is_bully else 0, 
                res.reason, 
                res.decision_source, 
                float(max(res.probability_toxic, res.probability_bully)),
                float(res.probability_toxic),
                float(res.probability_bully),
                embedding_json
            ))
            conn.commit()
            conn.close()

        async with SQLITE_WRITE_LOCK:
            await asyncio.to_thread(write_sqlite)
    except Exception as sq_err:
        print(f"Warning: SQLite error pada save_classification_memory fallback: {sq_err}")

async def get_classification_memory(text: str) -> HybridResponse | None:
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    r = await get_redis()
    if r:
        try:
            cached = await r.get(f"mem:{text_hash}")
            if cached:
                data = json.loads(cached)
                is_toxic = data["is_toxic"]
                is_bully = data["is_bully"]
                base_source = re.sub(r'\s*\((Redis Cache|PG Database)\)$', '', data["decision_source"])
                return HybridResponse(
                    text=text,
                    is_toxic=is_toxic,
                    is_bully=is_bully,
                    probability_toxic=data.get("probability_toxic", data["confidence"] if is_toxic else 0.0),
                    probability_bully=data.get("probability_bully", data["confidence"] if is_bully else 0.0),
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
                    SELECT is_toxic, is_bully, reason, decision_source, confidence, probability_toxic, probability_bully 
                    FROM classification_memory 
                    WHERE text_hash = $1
                """, text_hash)
                if row:
                    is_toxic = bool(row["is_toxic"])
                    is_bully = bool(row["is_bully"])
                    prob_toxic = row["probability_toxic"] if row["probability_toxic"] is not None else (row["confidence"] if is_toxic else 0.0)
                    prob_bully = row["probability_bully"] if row["probability_bully"] is not None else (row["confidence"] if is_bully else 0.0)
                    
                    if r:
                        mem_data = {
                            "is_toxic": is_toxic,
                            "is_bully": is_bully,
                            "reason": row["reason"],
                            "decision_source": row["decision_source"],
                            "confidence": row["confidence"],
                            "probability_toxic": prob_toxic,
                            "probability_bully": prob_bully
                        }
                        await r.set(f"mem:{text_hash}", json.dumps(mem_data), ex=2592000)
                        
                    base_source = re.sub(r'\s*\((Redis Cache|PG Database)\)$', '', row["decision_source"])
                    return HybridResponse(
                        text=text,
                        is_toxic=is_toxic,
                        is_bully=is_bully,
                        probability_toxic=prob_toxic,
                        probability_bully=prob_bully,
                        category=determine_category(is_toxic, is_bully),
                        decision_source=base_source + " (PG Database)",
                        reason=row["reason"]
                    )
        except Exception as e:
            print(f"Warning: PostgreSQL error saat membaca memori: {e}")
            
    # SQLite fallback read
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "cache", "cloud_llm_cache.db")
        if os.path.exists(db_path):
            def read_sqlite():
                conn = sqlite3.connect(db_path, timeout=10.0)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT is_toxic, is_bully, reason, decision_source, confidence, probability_toxic, probability_bully 
                    FROM classification_memory 
                    WHERE text_hash = ?
                """, (text_hash,))
                row = cursor.fetchone()
                conn.close()
                return dict(row) if row else None

            row = await asyncio.to_thread(read_sqlite)
            if row:
                is_toxic = bool(row["is_toxic"])
                is_bully = bool(row["is_bully"])
                prob_toxic = row["probability_toxic"] if row["probability_toxic"] is not None else (row["confidence"] if is_toxic else 0.0)
                prob_bully = row["probability_bully"] if row["probability_bully"] is not None else (row["confidence"] if is_bully else 0.0)
                base_source = re.sub(r'\s*\((Redis Cache|PG Database|SQLite Database)\)$', '', row["decision_source"])
                
                if r:
                    try:
                        mem_data = {
                            "is_toxic": is_toxic,
                            "is_bully": is_bully,
                            "reason": row["reason"],
                            "decision_source": row["decision_source"],
                            "confidence": row["confidence"],
                            "probability_toxic": prob_toxic,
                            "probability_bully": prob_bully
                        }
                        await r.set(f"mem:{text_hash}", json.dumps(mem_data), ex=2592000)
                    except Exception:
                        pass
                
                return HybridResponse(
                    text=text,
                    is_toxic=is_toxic,
                    is_bully=is_bully,
                    probability_toxic=prob_toxic,
                    probability_bully=prob_bully,
                    category=determine_category(is_toxic, is_bully),
                    decision_source=base_source + " (SQLite Database)",
                    reason=row["reason"]
                )
    except Exception as sq_err:
        print(f"Warning: SQLite error pada get_classification_memory fallback: {sq_err}")
        
    # 5. Semantic Cache Lookup (jika tidak ada pencocokan eksak)
    try:
        from classifier.predictor import EMBEDDING_MODEL
        if EMBEDDING_MODEL is not None:
            query_embedding = EMBEDDING_MODEL.encode([text])[0].tolist()
            
            # Coba pencarian semantik di PostgreSQL (menggunakan pgvector)
            pool = await get_pg_pool()
            if pool:
                try:
                    async with pool.acquire() as conn:
                        row = await conn.fetchrow("""
                            SELECT encrypted_text, is_toxic, is_bully, reason, decision_source, confidence, probability_toxic, probability_bully,
                                   (embedding <=> $1::vector) as distance
                            FROM classification_memory
                            WHERE embedding IS NOT NULL
                            ORDER BY embedding <=> $1::vector LIMIT 1
                        """, str(query_embedding))
                        
                        if row and row["distance"] is not None and row["distance"] <= 0.02:
                            is_toxic = bool(row["is_toxic"])
                            is_bully = bool(row["is_bully"])
                            prob_toxic = row["probability_toxic"] if row["probability_toxic"] is not None else (row["confidence"] if is_toxic else 0.0)
                            prob_bully = row["probability_bully"] if row["probability_bully"] is not None else (row["confidence"] if is_bully else 0.0)
                            
                            decrypted_text = decrypt_text(row["encrypted_text"])
                            similarity_pct = round((1.0 - row["distance"]) * 100, 1)
                            
                            # Simpan kecocokan eksak di Redis agar pemanggilan identik berikutnya lebih cepat
                            if r:
                                try:
                                    mem_data = {
                                        "is_toxic": is_toxic,
                                        "is_bully": is_bully,
                                        "reason": row["reason"],
                                        "decision_source": f"Semantic Cache Match ({similarity_pct}%)",
                                        "confidence": row["confidence"],
                                        "probability_toxic": prob_toxic,
                                        "probability_bully": prob_bully
                                    }
                                    await r.set(f"mem:{text_hash}", json.dumps(mem_data), ex=2592000)
                                except Exception:
                                    pass
                                    
                            return HybridResponse(
                                text=text,
                                is_toxic=is_toxic,
                                is_bully=is_bully,
                                probability_toxic=prob_toxic,
                                probability_bully=prob_bully,
                                category=determine_category(is_toxic, is_bully),
                                decision_source=f"Semantic Cache Match ({similarity_pct}%)",
                                reason=f"[Cocok Semantik dengan '{decrypted_text}'] {row['reason']}"
                            )
                except Exception as pg_sem_err:
                    print(f"Warning: Gagal PostgreSQL semantic cache lookup: {pg_sem_err}")

            # Fallback pencarian semantik di SQLite menggunakan Python numpy
            try:
                import numpy as np
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                db_path = os.path.join(base_dir, "cache", "cloud_llm_cache.db")
                if os.path.exists(db_path):
                    def run_sqlite_semantic():
                        conn = sqlite3.connect(db_path, timeout=10.0)
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT text_hash, encrypted_text, is_toxic, is_bully, reason, decision_source, confidence, probability_toxic, probability_bully, embedding
                            FROM classification_memory
                            WHERE embedding IS NOT NULL
                            ORDER BY timestamp DESC
                            LIMIT 1000
                        """)
                        rows = cursor.fetchall()
                        conn.close()
                        return rows

                    rows = await asyncio.to_thread(run_sqlite_semantic)
                    if rows:
                        best_sim = -1.0
                        best_row = None
                        query_vec = np.array(query_embedding)
                        query_norm = np.linalg.norm(query_vec)
                        
                        for r_row in rows:
                            emb_json = r_row[9]
                            if not emb_json:
                                continue
                            try:
                                emb_list = json.loads(emb_json)
                                r_vec = np.array(emb_list)
                                dot_product = np.dot(query_vec, r_vec)
                                r_norm = np.linalg.norm(r_vec)
                                if query_norm > 0 and r_norm > 0:
                                    sim = dot_product / (query_norm * r_norm)
                                    if sim > best_sim:
                                        best_sim = sim
                                        best_row = r_row
                            except Exception:
                                pass
                                
                        if best_row and best_sim >= 0.98:
                            is_toxic = bool(best_row[2])
                            is_bully = bool(best_row[3])
                            prob_toxic = best_row[7] if best_row[7] is not None else (best_row[6] if is_toxic else 0.0)
                            prob_bully = best_row[8] if best_row[8] is not None else (best_row[6] if is_bully else 0.0)
                            
                            decrypted_text = decrypt_text(best_row[1])
                            similarity_pct = round(best_sim * 100, 1)
                            
                            if r:
                                try:
                                    mem_data = {
                                        "is_toxic": is_toxic,
                                        "is_bully": is_bully,
                                        "reason": best_row[4],
                                        "decision_source": f"Semantic Cache Match ({similarity_pct}%)",
                                        "confidence": best_row[6],
                                        "probability_toxic": prob_toxic,
                                        "probability_bully": prob_bully
                                    }
                                    await r.set(f"mem:{text_hash}", json.dumps(mem_data), ex=2592000)
                                except Exception:
                                    pass
                                    
                            return HybridResponse(
                                text=text,
                                is_toxic=is_toxic,
                                is_bully=is_bully,
                                probability_toxic=prob_toxic,
                                probability_bully=prob_bully,
                                category=determine_category(is_toxic, is_bully),
                                decision_source=f"Semantic Cache Match ({similarity_pct}%)",
                                reason=f"[Cocok Semantik dengan '{decrypted_text}'] {best_row[4]}"
                            )
            except Exception as sq_sem_err:
                print(f"Warning: SQLite semantic cache lookup error: {sq_sem_err}")
    except Exception as general_sem_err:
        print(f"Warning: Semantic cache error: {general_sem_err}")
        
    return None

async def get_unvalidated_memory(limit: int = 50) -> List[Dict[str, Any]]:
    results = []
    pool = await get_pg_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT text_hash, encrypted_text, is_toxic, is_bully, reason, decision_source, confidence, timestamp, is_validated
                    FROM classification_memory
                    WHERE is_validated = 0
                    ORDER BY timestamp DESC
                    LIMIT $1
                """, limit)
                for r in rows:
                    row_dict = dict(r)
                    enc_text = row_dict.pop("encrypted_text", "")
                    decrypted = decrypt_text(enc_text)
                    # Jika dekripsi gagal, decrypt_text mengembalikan ciphertext mentah — filter agar tidak terekspos
                    if decrypted == enc_text and enc_text.startswith("gAAAAA"):
                        row_dict["text"] = "[Gagal mendekripsi — kunci tidak cocok]"
                    else:
                        row_dict["text"] = decrypted
                    results.append(row_dict)
            return results
        except Exception as e:
            print(f"Warning: PostgreSQL error pada get_unvalidated_memory: {e}")

    # SQLite fallback
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "cache", "cloud_llm_cache.db")
        if os.path.exists(db_path):
            def read_sqlite_unvalidated():
                conn = sqlite3.connect(db_path, timeout=10.0)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT text_hash, encrypted_text, is_toxic, is_bully, reason, decision_source, confidence, timestamp, is_validated
                    FROM classification_memory
                    WHERE is_validated = 0
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                res_list = [dict(r) for r in rows]
                conn.close()
                return res_list

            rows = await asyncio.to_thread(read_sqlite_unvalidated)
            for row_dict in rows:
                enc_text = row_dict.pop("encrypted_text", "")
                decrypted = decrypt_text(enc_text)
                # Jika dekripsi gagal, decrypt_text mengembalikan ciphertext mentah — filter agar tidak terekspos
                if decrypted == enc_text and enc_text.startswith("gAAAAA"):
                    row_dict["text"] = "[Gagal mendekripsi — kunci tidak cocok]"
                else:
                    row_dict["text"] = decrypted
                results.append(row_dict)
    except Exception as e:
        print(f"Warning: SQLite error pada get_unvalidated_memory: {e}")
    return results

async def get_categorized_memory(
    limit: int = 500,
    confidence_min: Optional[float] = None,
    confidence_max: Optional[float] = None,
    decision_source: Optional[str] = None,
    search: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """Mengambil memori klasifikasi terbaru, memfilter berdasarkan kriteria opsional, dan membaginya ke dalam 4 kuadran."""
    results = {
        "toxic_bully": [],
        "toxic_non_bully": [],
        "non_toxic_bully": [],
        "non_toxic_non_bully": []
    }
    
    fetch_limit = limit
    if confidence_min is not None or confidence_max is not None or decision_source or search:
        fetch_limit = max(1000, limit * 2)
        
    records = []
    pool = await get_pg_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT text_hash, encrypted_text, is_toxic, is_bully, reason, decision_source, confidence, timestamp, is_validated
                    FROM classification_memory
                    ORDER BY ABS(confidence - 0.5) ASC, timestamp DESC
                    LIMIT $1
                """, fetch_limit)
                for r in rows:
                    row_dict = dict(r)
                    enc_text = row_dict.pop("encrypted_text", "")
                    decrypted = decrypt_text(enc_text)
                    # Jika dekripsi gagal, decrypt_text mengembalikan ciphertext mentah — filter agar tidak terekspos
                    if decrypted == enc_text and enc_text.startswith("gAAAAA"):
                        row_dict["text"] = "[Gagal mendekripsi — kunci tidak cocok]"
                    else:
                        row_dict["text"] = decrypted
                    records.append(row_dict)
        except Exception as e:
            print(f"Warning: PostgreSQL error pada get_categorized_memory: {e}")
            
    if not records:
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "cache", "cloud_llm_cache.db")
            if os.path.exists(db_path):
                def read_sqlite_categorized():
                    conn = sqlite3.connect(db_path, timeout=10.0)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT text_hash, encrypted_text, is_toxic, is_bully, reason, decision_source, confidence, timestamp, is_validated
                        FROM classification_memory
                        ORDER BY abs(confidence - 0.5) ASC, timestamp DESC
                        LIMIT ?
                    """, (fetch_limit,))
                    rows = cursor.fetchall()
                    res_list = [dict(r) for r in rows]
                    conn.close()
                    return res_list

                rows = await asyncio.to_thread(read_sqlite_categorized)
                for row_dict in rows:
                    enc_text = row_dict.pop("encrypted_text", "")
                    decrypted = decrypt_text(enc_text)
                    # Jika dekripsi gagal, decrypt_text mengembalikan ciphertext mentah — filter agar tidak terekspos
                    if decrypted == enc_text and enc_text.startswith("gAAAAA"):
                        row_dict["text"] = "[Gagal mendekripsi — kunci tidak cocok]"
                    else:
                        row_dict["text"] = decrypted
                    records.append(row_dict)
        except Exception as e:
            print(f"Warning: SQLite error pada get_categorized_memory: {e}")
            
    filtered_records = []
    for r in records:
        conf = r.get("confidence", 1.0)
        if conf is None:
            conf = 1.0
        if confidence_min is not None and conf < confidence_min:
            continue
        if confidence_max is not None and conf > confidence_max:
            continue
            
        if decision_source:
            source = r.get("decision_source") or ""
            if decision_source.strip().lower() not in source.strip().lower():
                continue
                
        if search:
            text_val = r.get("text") or ""
            if search.strip().lower() not in text_val.strip().lower():
                continue
                
        filtered_records.append(r)
        
    for r in filtered_records:
        is_toxic = bool(r.get("is_toxic", 0))
        is_bully = bool(r.get("is_bully", 0))
        
        if r.get("timestamp"):
            r["timestamp"] = str(r["timestamp"])
            
        try:
            from classifier.predictor import explain_prediction
            importances = explain_prediction(r["text"])
            r["word_importances"] = [
                {"word": imp.word, "weight_toxic": imp.weight_toxic, "weight_bully": imp.weight_bully}
                for imp in importances
            ]
        except Exception:
            r["word_importances"] = []
            
        if is_toxic and is_bully:
            if len(results["toxic_bully"]) < limit:
                results["toxic_bully"].append(r)
        elif is_toxic and not is_bully:
            if len(results["toxic_non_bully"]) < limit:
                results["toxic_non_bully"].append(r)
        elif not is_toxic and is_bully:
            if len(results["non_toxic_bully"]) < limit:
                results["non_toxic_bully"].append(r)
        else:
            if len(results["non_toxic_non_bully"]) < limit:
                results["non_toxic_non_bully"].append(r)
                
    return results

async def update_validation_status(text: str, is_toxic: bool, is_bully: bool, is_validated: int = 1):
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    enc_text = encrypt_text(text)
    
    r = await get_redis()
    if r:
        try:
            mem_data = {
                "is_toxic": is_toxic,
                "is_bully": is_bully,
                "reason": "Umpan balik koreksi manusia (Validated)",
                "decision_source": "Koreksi Manusia",
                "confidence": 1.0,
                "probability_toxic": 1.0 if is_toxic else 0.0,
                "probability_bully": 1.0 if is_bully else 0.0
            }
            await r.set(f"mem:{text_hash}", json.dumps(mem_data), ex=2592000)
        except Exception:
            pass

    pool = await get_pg_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO classification_memory 
                    (text_hash, encrypted_text, is_toxic, is_bully, reason, decision_source, confidence, probability_toxic, probability_bully, is_validated) 
                    VALUES ($1, $2, $3, $4, $5, $6, 1.0, $7, $8, $9)
                    ON CONFLICT (text_hash) DO UPDATE SET
                        encrypted_text = EXCLUDED.encrypted_text,
                        is_toxic = EXCLUDED.is_toxic,
                        is_bully = EXCLUDED.is_bully,
                        reason = EXCLUDED.reason,
                        decision_source = EXCLUDED.decision_source,
                        confidence = EXCLUDED.confidence,
                        probability_toxic = EXCLUDED.probability_toxic,
                        probability_bully = EXCLUDED.probability_bully,
                        is_validated = EXCLUDED.is_validated
                """, 
                text_hash, 
                enc_text,
                1 if is_toxic else 0, 
                1 if is_bully else 0, 
                "Umpan balik koreksi manusia (Validated)", 
                "Koreksi Manusia",
                1.0 if is_toxic else 0.0,
                1.0 if is_bully else 0.0,
                is_validated)
            print(f"[HITL] Berhasil memvalidasi data di PostgreSQL untuk: '{text}'")
            return True
        except Exception as e:
            print(f"Warning: PostgreSQL error pada update_validation_status: {e}")

    # SQLite fallback
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "cache", "cloud_llm_cache.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        def write_validation_sqlite():
            conn = sqlite3.connect(db_path, timeout=30.0)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO classification_memory 
                (text_hash, encrypted_text, is_toxic, is_bully, reason, decision_source, confidence, probability_toxic, probability_bully, is_validated) 
                VALUES (?, ?, ?, ?, ?, ?, 1.0, ?, ?, ?)
                ON CONFLICT(text_hash) DO UPDATE SET
                    encrypted_text = excluded.encrypted_text,
                    is_toxic = excluded.is_toxic,
                    is_bully = excluded.is_bully,
                    reason = excluded.reason,
                    decision_source = excluded.decision_source,
                    confidence = excluded.confidence,
                    probability_toxic = excluded.probability_toxic,
                    probability_bully = excluded.probability_bully,
                    is_validated = excluded.is_validated
            """, (text_hash, enc_text, 1 if is_toxic else 0, 1 if is_bully else 0, "Umpan balik koreksi manusia (Validated)", "Koreksi Manusia", 1.0 if is_toxic else 0.0, 1.0 if is_bully else 0.0, is_validated))
            conn.commit()
            conn.close()

        async with SQLITE_WRITE_LOCK:
            await asyncio.to_thread(write_validation_sqlite)
        print(f"[HITL] Berhasil memvalidasi data di SQLite untuk: '{text}'")
        return True
    except Exception as e:
        print(f"Warning: SQLite error pada update_validation_status: {e}")
    return False

async def save_retraining_history(f1_toxic: float, f1_bully: float, threshold_toxic: float, threshold_bully: float, active_version: str):
    pool = await get_pg_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO retraining_history (f1_toxic, f1_bully, threshold_toxic, threshold_bully, active_version)
                    VALUES ($1, $2, $3, $4, $5)
                """, f1_toxic, f1_bully, threshold_toxic, threshold_bully, active_version)
                return
        except Exception as e:
            print(f"Warning: PostgreSQL error pada save_retraining_history: {e}")

    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "cache", "cloud_llm_cache.db")
        
        def save_history_sqlite():
            conn = sqlite3.connect(db_path, timeout=30.0)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO retraining_history (f1_toxic, f1_bully, threshold_toxic, threshold_bully, active_version)
                VALUES (?, ?, ?, ?, ?)
            """, (f1_toxic, f1_bully, threshold_toxic, threshold_bully, active_version))
            conn.commit()
            conn.close()

        async with SQLITE_WRITE_LOCK:
            await asyncio.to_thread(save_history_sqlite)
    except Exception as e:
        print(f"Warning: SQLite error pada save_retraining_history: {e}")

async def get_retraining_history(limit: int = 50) -> List[Dict[str, Any]]:
    pool = await get_pg_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, timestamp, f1_toxic, f1_bully, threshold_toxic, threshold_bully, active_version
                    FROM retraining_history
                    ORDER BY id ASC
                    LIMIT $1
                """, limit)
                return [dict(r) for r in rows]
        except Exception as e:
            print(f"Warning: PostgreSQL error pada get_retraining_history: {e}")

    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "cache", "cloud_llm_cache.db")
        
        def read_history_sqlite():
            conn = sqlite3.connect(db_path, timeout=30.0)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, f1_toxic, f1_bully, threshold_toxic, threshold_bully, active_version
                FROM retraining_history
                ORDER BY id ASC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            conn.close()
            return rows

        rows = await asyncio.to_thread(read_history_sqlite)
        
        result = []
        for r in rows:
            result.append({
                "id": r[0],
                "timestamp": str(r[1]),
                "f1_toxic": r[2],
                "f1_bully": r[3],
                "threshold_toxic": r[4],
                "threshold_bully": r[5],
                "active_version": r[6]
            })
        return result
    except Exception as e:
        print(f"Warning: SQLite error pada get_retraining_history: {e}")
        return []
