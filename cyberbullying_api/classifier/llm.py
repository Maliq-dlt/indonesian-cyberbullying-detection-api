import os
import json
import httpx
import numpy as np
import asyncio
from typing import List, Dict, Any, AsyncGenerator

from classifier.database import get_cached_response, save_cached_response, get_pg_pool, decrypt_text
from normalizer import normalize_text

# Konfigurasi OpenCode Go dinamis dari environment variables
OPENCODE_API_KEY = os.getenv("OPENCODE_API_KEY", "")
OPENCODE_BASE_URL = os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/go/v1")
OPENCODE_MODEL = os.getenv("OPENCODE_MODEL", "opencode-go/kimi-k2.6")

# Konfigurasi RAG Pool untuk Few-Shot LLM Dinamis
ABUSIVE_WORDS_SET = set()
RAG_POOL_TEXTS = []
RAG_POOL_VECTORS = None
RAG_POOL_LABELS = []

CLOUD_LLM_SEM = asyncio.Semaphore(3)

async def retrieve_relevant_examples(query: str, top_k: int = 3) -> str:
    """Mengambil contoh relevan menggunakan pencarian vektor (pgvector) jika tersedia,
    atau fallback ke TF-IDF di memori."""
    global RAG_POOL_TEXTS, RAG_POOL_VECTORS, RAG_POOL_LABELS
    
    from classifier.predictor import EMBEDDING_MODEL, ML_VECTORIZER
    
    pool = await get_pg_pool()
    if pool and EMBEDDING_MODEL is not None:
        try:
            # Hitung embedding kueri
            query_embedding = EMBEDDING_MODEL.encode([query])[0]
            query_embedding_list = query_embedding.tolist()
            
            # Cari 3 terdekat di PostgreSQL
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT encrypted_text, is_toxic, is_bully 
                    FROM classification_memory 
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <-> $1::vector LIMIT $2
                """, str(query_embedding_list), top_k)
                
                if rows:
                    examples_str = "\n--- Contoh Kontekstual Relevan (Vector Search) ---\n"
                    for i, r in enumerate(rows):
                        decrypted_text = decrypt_text(r['encrypted_text'])
                        examples_str += (
                            f"Contoh {i+1}:\n"
                            f"Teks: \"{decrypted_text}\"\n"
                            f"Hasil: is_toxic={'true' if r['is_toxic'] else 'false'}, is_bully={'true' if r['is_bully'] else 'false'}\n"
                        )
                    return examples_str
        except Exception as e:
            print("Warning: Gagal menggunakan pgvector, fallback ke TF-IDF:", e)

    # Fallback ke TF-IDF
    memory_texts = []
    memory_labels = []
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT encrypted_text, is_bully FROM classification_memory ORDER BY timestamp DESC LIMIT 200")
                for r in rows:
                    memory_texts.append(decrypt_text(r["encrypted_text"]))
                    memory_labels.append("Bullying" if r["is_bully"] else "Non-bullying")
        except Exception as e:
            pass
        
    all_texts = RAG_POOL_TEXTS + memory_texts
    all_labels = RAG_POOL_LABELS + memory_labels
    
    if not all_texts or ML_VECTORIZER is None:
        return ""
    
    try:
        all_vectors = ML_VECTORIZER.transform(all_texts)
        query_vector = ML_VECTORIZER.transform([query])
        
        similarities = (all_vectors * query_vector.T).toarray().flatten()
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        examples_str = "\n--- Contoh Kontekstual Relevan (Hasil Memori & Baseline) ---\n"
        for i, idx in enumerate(top_indices):
            orig_text = all_texts[idx]
            label = all_labels[idx]
            is_bully = label in ["Bullying", "negatif", "negative"]
            is_toxic = any(w in ABUSIVE_WORDS_SET for w in normalize_text(orig_text)["spaced"].split())
            
            toxic_str = "true" if is_toxic else "false"
            bully_str = "true" if is_bully else "false"
            
            examples_str += (
                f"Contoh {i+1}:\n"
                f"Teks: \"{orig_text}\"\n"
                f"Hasil: is_toxic={toxic_str}, is_bully={bully_str}\n"
            )
        return examples_str
    except Exception as e:
        print("Warning: Gagal melakukan RAG retrieval:", e)
        return ""

async def query_cloud_llm_async(text: str, model_name: str | None = None) -> Dict[str, Any]:
    # Cek cache terlebih dahulu
    cached = await get_cached_response(text)
    if cached:
        print(f"[CACHE HIT] Mengambil hasil analisis LLM dari cache untuk teks: '{text}'")
        return cached

    async with CLOUD_LLM_SEM:
        return await _query_cloud_llm_async_raw(text, model_name)

async def _query_cloud_llm_async_raw(text: str, model_name: str | None = None) -> Dict[str, Any]:

    if not OPENCODE_API_KEY:
        return {
            "is_toxic": False,
            "is_bully": False,
            "reason": "OpenCode API Key tidak dikonfigurasi.",
            "success": False
        }
    
    url = f"{OPENCODE_BASE_URL.rstrip('/')}/chat/completions"
    
    if not model_name:
        model_name = OPENCODE_MODEL
    
    # Skema output terstruktur yang formal dengan Chain-of-Thought (reasoning diletakkan pertama)
    schema = {
        "type": "object",
        "properties": {
            "reasoning": {"type": "string"},
            "is_toxic": {"type": "boolean"},
            "is_bully": {"type": "boolean"},
            "reason": {"type": "string"}
        },
        "required": ["reasoning", "is_toxic", "is_bully", "reason"]
    }
    
    # Ambil contoh kontekstual dinamis menggunakan Few-Shot RAG (Opsi 3)
    dynamic_examples = await retrieve_relevant_examples(text, top_k=3)
    
    # System prompt linguistik Indonesia yang mendalam dengan Few-Shot examples
    system_instruction = (
        "Sistem: Anda adalah ahli sosiolinguistik bahasa Indonesia yang spesifik mendeteksi cyberbullying, hate speech, dan sarkasme.\n"
        "Tugas: Analisis teks secara objektif dan klasifikasikan ke parameter 'is_toxic' dan 'is_bully' menggunakan pemikiran sosiolinguistik.\n\n"
        "Panduan Nuansa Bahasa Gaul Indonesia:\n"
        "1. CASUAL SLANG (Aman tapi Kasar): Penggunaan kata kasar seperti 'anjing', 'bangsat', 'bego', 'goblok' jika digunakan sebagai pujian/casual slang/keakraban -> is_toxic=true, is_bully=false.\n"
        "   Contoh: 'anjing keren banget lu bang, gokil abis!'\n"
        "2. SARKASME/EJEKAN HALUS (Bullying): Sindiran halus, ejekan personal, atau makian tidak langsung tanpa kata kotor -> is_toxic=false, is_bully=true.\n"
        "   Contoh: 'ganteng banget muka lu kayak spakbor mio wkwk' atau 'pintar sekali kamu, nilai ujianmu nol'.\n"
        "3. PERUNDUNGAN DIRECT (Kasar & Bullying): Serangan verbal kasar langsung yang menyerang/menghina pribadi -> is_toxic=true, is_bully=true.\n"
        "   Contoh: 'goblok banget sih lu jadi orang, gak berguna!'\n"
        "4. NEUTRAL/AMAN: Teks ramah atau komentar biasa -> is_toxic=false, is_bully=false.\n"
        "   Contoh: 'Terima kasih informasinya kak, sangat bermanfaat.'\n\n"
        f"{dynamic_examples}\n"
        "PENTING: Lakukan penalaran/analisis nuansa kata di bidang 'reasoning' terlebih dahulu sebelum mengisi 'is_toxic', 'is_bully', dan 'reason' (ringkasan penjelasan)."
    )
    
    prompt = f"""
    Gunakan format JSON yang valid mengikuti skema ini secara ketat (isi field 'reasoning' terlebih dahulu untuk melakukan Chain-of-Thought):
    {json.dumps(schema, indent=2)}
    
    Teks yang dianalisis:
    "{text}"
    """
    
    # Payload OpenAI-compatible format
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
        "stream": False
    }
    
    headers = {
        "Authorization": f"Bearer {OPENCODE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Timeout 15 detik cukup untuk API cloud
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                res_json = response.json()
                content_str = res_json["choices"][0]["message"]["content"]
                content = json.loads(content_str)
                
                # Menggabungkan reasoning dan summary untuk visualisasi penjelasan yang kaya di UI
                reasoning = content.get("reasoning", "").strip()
                summary_reason = content.get("reason", "").strip()
                combined_reason = f"Analisis: {reasoning} - Kesimpulan: {summary_reason}" if reasoning else summary_reason
                
                result = {
                    "is_toxic": bool(content.get("is_toxic", False)),
                    "is_bully": bool(content.get("is_bully", False)),
                    "reason": combined_reason,
                    "success": True
                }
                await save_cached_response(text, result)
                return result
            else:
                print(f"Warning: Cloud LLM API Error: {response.status_code} - {response.text}")
    except Exception as e:
        print("Warning: Gagal menghubungi Cloud LLM:", e)
        
    return {
        "is_toxic": False,
        "is_bully": False,
        "reason": "Gagal terhubung ke Cloud LLM.",
        "success": False
    }

async def query_cloud_llm_stream_async(text: str, model_name: str | None = None) -> AsyncGenerator[Dict[str, Any], None]:
    # Cek cache terlebih dahulu
    cached = await get_cached_response(text)
    if cached:
        print(f"[CACHE HIT] Mengambil hasil analisis LLM dari cache untuk teks: '{text}'")
        # Yield the cached result directly
        yield {"chunk": cached.get("reason", ""), "done": True, "final_data": cached}
        return

    async with CLOUD_LLM_SEM:
        async for chunk in _query_cloud_llm_stream_async_raw(text, model_name):
            yield chunk

async def _query_cloud_llm_stream_async_raw(text: str, model_name: str | None = None) -> AsyncGenerator[Dict[str, Any], None]:

    if not OPENCODE_API_KEY:
        yield {
            "chunk": "OpenCode API Key tidak dikonfigurasi.", 
            "done": True, 
            "final_data": {"is_toxic": False, "is_bully": False, "reason": "OpenCode API Key tidak dikonfigurasi.", "success": False}
        }
        return
    
    url = f"{OPENCODE_BASE_URL.rstrip('/')}/chat/completions"
    
    if not model_name:
        model_name = OPENCODE_MODEL
    
    schema = {
        "type": "object",
        "properties": {
            "reasoning": {"type": "string"},
            "is_toxic": {"type": "boolean"},
            "is_bully": {"type": "boolean"},
            "reason": {"type": "string"}
        },
        "required": ["reasoning", "is_toxic", "is_bully", "reason"]
    }
    
    dynamic_examples = await retrieve_relevant_examples(text, top_k=3)
    
    system_instruction = (
        "Sistem: Anda adalah ahli sosiolinguistik bahasa Indonesia yang spesifik mendeteksi cyberbullying, hate speech, dan sarkasme.\n"
        "Tugas: Analisis teks secara objektif dan klasifikasikan ke parameter 'is_toxic' dan 'is_bully' menggunakan pemikiran sosiolinguistik.\n\n"
        "Panduan Nuansa Bahasa Gaul Indonesia:\n"
        "1. CASUAL SLANG (Aman tapi Kasar): Penggunaan kata kasar seperti 'anjing', 'bangsat', 'bego', 'goblok' jika digunakan sebagai pujian/casual slang/keakraban -> is_toxic=true, is_bully=false.\n"
        "   Contoh: 'anjing keren banget lu bang, gokil abis!'\n"
        "2. SARKASME/EJEKAN HALUS (Bullying): Sindiran halus, ejekan personal, atau makian tidak langsung tanpa kata kotor -> is_toxic=false, is_bully=true.\n"
        "   Contoh: 'ganteng banget muka lu kayak spakbor mio wkwk' atau 'pintar sekali kamu, nilai ujianmu nol'.\n"
        "3. PERUNDUNGAN DIRECT (Kasar & Bullying): Serangan verbal kasar langsung yang menyerang/menghina pribadi -> is_toxic=true, is_bully=true.\n"
        "   Contoh: 'goblok banget sih lu jadi orang, gak berguna!'\n"
        "4. NEUTRAL/AMAN: Teks ramah atau komentar biasa -> is_toxic=false, is_bully=false.\n"
        "   Contoh: 'Terima kasih informasinya kak, sangat bermanfaat.'\n\n"
        f"{dynamic_examples}\n"
        "PENTING: Lakukan penalaran/analisis nuansa kata di bidang 'reasoning' terlebih dahulu sebelum mengisi 'is_toxic', 'is_bully', dan 'reason' (ringkasan penjelasan)."
    )
    
    prompt = f"""
    Gunakan format JSON yang valid mengikuti skema ini secara ketat (isi field 'reasoning' terlebih dahulu untuk melakukan Chain-of-Thought):
    {json.dumps(schema, indent=2)}
    
    Teks yang dianalisis:
    "{text}"
    """
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
        "stream": True
    }
    
    headers = {
        "Authorization": f"Bearer {OPENCODE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    full_response = ""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code != 200:
                     yield {"chunk": f"Error: {response.status_code}", "done": True, "final_data": {"is_toxic": False, "is_bully": False, "reason": f"Gagal terhubung ke Cloud LLM: {response.status_code}", "success": False}}
                     return

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                        
                    if line == "data: [DONE]":
                        break
                        
                    if line.startswith("data: "):
                        json_str = line[6:]
                        try:
                            data = json.loads(json_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                chunk = delta.get("content", "")
                                if chunk:
                                    full_response += chunk
                                    yield {"chunk": chunk, "done": False, "final_data": None}
                        except json.JSONDecodeError:
                            pass
                
                # Parsing the final complete JSON
                try:
                    content = json.loads(full_response)
                    reasoning = content.get("reasoning", "").strip()
                    summary_reason = content.get("reason", "").strip()
                    combined_reason = f"Analisis: {reasoning} - Kesimpulan: {summary_reason}" if reasoning else summary_reason
                    
                    result = {
                        "is_toxic": bool(content.get("is_toxic", False)),
                        "is_bully": bool(content.get("is_bully", False)),
                        "reason": combined_reason,
                        "success": True
                    }
                    await save_cached_response(text, result)
                    yield {"chunk": "", "done": True, "final_data": result}
                except json.JSONDecodeError:
                    yield {"chunk": "", "done": True, "final_data": {"is_toxic": False, "is_bully": False, "reason": "Gagal memparsing JSON balasan dari Cloud LLM.", "success": False}}

    except Exception as e:
        print("Warning: Gagal menghubungi Cloud LLM secara streaming:", e)
        yield {
            "chunk": "", 
            "done": True, 
            "final_data": {"is_toxic": False, "is_bully": False, "reason": f"Error streaming LLM: {str(e)}", "success": False}
        }
