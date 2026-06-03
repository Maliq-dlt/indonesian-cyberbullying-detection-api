import os
import json
import httpx
import numpy as np
import asyncio
from typing import List, Dict, Any

from classifier.database import get_cached_response, save_cached_response, get_pg_pool
from normalizer import normalize_text

# Konfigurasi Ollama dinamis dari environment variables
OLLAMA_URL = os.getenv("OLLAMA_URL", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# Konfigurasi RAG Pool untuk Few-Shot LLM Dinamis
ABUSIVE_WORDS_SET = set()
RAG_POOL_TEXTS = []
RAG_POOL_VECTORS = None
RAG_POOL_LABELS = []

async def retrieve_relevant_examples(query: str, top_k: int = 3) -> str:
    """Mengambil contoh cyberbullying/non-cyberbullying yang secara semantik paling mirip
    menggunakan TF-IDF cosine similarity dari pool dataset dan memori SQLite (RAG dinamis berkelanjutan)."""
    global RAG_POOL_TEXTS, RAG_POOL_VECTORS, RAG_POOL_LABELS
    
    # Lazy import to avoid circular dependency
    from classifier.predictor import ML_VECTORIZER
    
    # Ambil memori klasifikasi terbaru dari database PostgreSQL secara real-time
    memory_texts = []
    memory_labels = []
    pool = await get_pg_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("SELECT text, is_bully FROM classification_memory ORDER BY timestamp DESC LIMIT 200")
                for r in rows:
                    memory_texts.append(r["text"])
                    memory_labels.append("Bullying" if r["is_bully"] else "Non-bullying")
        except Exception as e:
            print("Warning: Gagal membaca memori terbaru untuk RAG dari PostgreSQL:", e)
        
    # Gabungkan data baseline dengan data dinamis dari memori PostgreSQL
    all_texts = RAG_POOL_TEXTS + memory_texts
    all_labels = RAG_POOL_LABELS + memory_labels
    
    if not all_texts or ML_VECTORIZER is None:
        return ""
    
    try:
        # Vektorkan seluruh teks gabungan
        all_vectors = ML_VECTORIZER.transform(all_texts)
        query_vector = ML_VECTORIZER.transform([query])
        
        # Hitung kemiripan
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

async def query_ollama_async(text: str, model_name: str | None = None) -> Dict[str, Any]:
    # Cek cache terlebih dahulu
    cached = await get_cached_response(text)
    if cached:
        print(f"[CACHE HIT] Mengambil hasil analisis LLM dari cache untuk teks: '{text}'")
        return cached

    if not OLLAMA_URL:
        return {
            "is_toxic": False,
            "is_bully": False,
            "reason": "Ollama URL tidak dikonfigurasi.",
            "success": False
        }
    
    url = f"{OLLAMA_URL.rstrip('/')}/api/generate"
    
    if not model_name:
        model_name = OLLAMA_MODEL
    
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
    {system_instruction}
    
    Gunakan format JSON yang valid mengikuti skema ini secara ketat (isi field 'reasoning' terlebih dahulu untuk melakukan Chain-of-Thought):
    {json.dumps(schema, indent=2)}
    
    Teks yang dianalisis:
    "{text}"
    """
    
    # Payload dengan opsi temperature 0.0 untuk hasil deterministik (Opsi 2)
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "format": schema,
        "options": {
            "temperature": 0.0
        }
    }
    
    try:
        # Peningkatan timeout menjadi 15.0 detik untuk keandalan loading VRAM
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                res_json = response.json()
                content = json.loads(res_json["response"])
                
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
    except Exception as e:
        print("Warning: Gagal menghubungi Ollama dengan skema JSON:", e)
        
    return {
        "is_toxic": False,
        "is_bully": False,
        "reason": "Gagal terhubung ke Ollama lokal dengan format skema.",
        "success": False
    }
