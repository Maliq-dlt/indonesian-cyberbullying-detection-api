import pandas as pd
import os

import main
import scraper
import classifier

from ui.components import highlight_toxic_words, make_html_card, generate_batch_pie_chart


async def predict_single_hybrid(text):
    if not text.strip():
        empty_card = "<div style='padding:15px; border:1px dashed #ccc; border-radius:8px; text-align:center;'>Silakan masukkan teks terlebih dahulu.</div>"
        empty_highlight = "<div style='padding:10px; border:1px dashed #ccc; border-radius:6px; color:#666;'>Teks kosong.</div>"
        yield (
            empty_card, "", empty_highlight, 0.0, 0.0,
            "Teks kosong", 0.0, 0.0,
            "Teks kosong", 0.0, 0.0,
            "👍 Akurat", gr.update(visible=False), ""
        )
        return

    # Yield initial state
    loading_card = "<div style='padding:15px; border:1px dashed #ccc; border-radius:8px; text-align:center;'>Menunggu analisis...</div>"
    yield (
        loading_card, "*Memulai penalaran AI...*", "", 0.0, 0.0,
        "Menunggu...", 0.0, 0.0,
        "Menunggu...", 0.0, 0.0,
        "👍 Akurat", gr.update(visible=False), ""
    )

    try:
        req = main.TextRequest(text=text)
        
        # Ambil juga hasil individual secara sinkron untuk tab detail
        try:
            ml_res = main.predict_ml(req)
            ml_cat = ml_res.category
            ml_toxic = ml_res.probability_toxic
            ml_bully = ml_res.probability_bully
        except Exception as ml_err:
            ml_cat, ml_toxic, ml_bully = "Error", 0.0, 0.0
            
        try:
            tr_res = main.predict_transformers(req)
            tr_cat = tr_res.category
            tr_toxic = tr_res.probability_toxic
            tr_bully = tr_res.probability_bully
        except Exception as tr_err:
            tr_cat, tr_toxic, tr_bully = "Error", 0.0, 0.0

        lex_res = main.classifier.predict_lexicon(text)
        highlighted_html = highlight_toxic_words(text, lex_res.matches)

        # Proses generator stream hybrid
        current_reasoning = ""
        final_res = None
        
        async for state in main.classifier.predict_hybrid_stream(text):
            if state["chunk"]:
                current_reasoning += state["chunk"]
                
            if state["done"]:
                final_res = state["final_data"]
                break
            else:
                # Yield intermediate updates (real-time typing)
                formatted_reasoning = f"**Analisis LLM (Real-time):**\n\n{current_reasoning}"
                yield (
                    loading_card,
                    formatted_reasoning,
                    highlighted_html,
                    0.0, 0.0,
                    ml_cat, ml_toxic, ml_bully,
                    tr_cat, tr_toxic, tr_bully,
                    "👍 Akurat", gr.update(visible=False), ""
                )

        if final_res:
            html_card = make_html_card(final_res.category, final_res.probability_toxic, final_res.probability_bully, final_res.decision_source, final_res.reason)
            
            # If reasoning was streamed, keep it shown, otherwise show the reason
            final_reasoning = current_reasoning if current_reasoning else final_res.reason
            
            yield (
                html_card,
                f"**Analisis Selesai:**\n\n{final_reasoning}",
                highlighted_html,
                final_res.probability_toxic,
                final_res.probability_bully,
                ml_cat, ml_toxic, ml_bully,
                tr_cat, tr_toxic, tr_bully,
                "👍 Akurat", gr.update(visible=False), ""
            )

    except Exception as e:
        html_card = f"<div style='color:red; padding:10px; border:1px solid red; border-radius:8px;'>Gagal memproses: {str(e)}</div>"
        highlighted_html = f"<div style='color:red; padding:10px;'>Gagal memproses: {str(e)}</div>"
        yield (
            html_card,
            f"**Error:** {str(e)}",
            highlighted_html,
            0.0, 0.0,
            "Gagal", 0.0, 0.0,
            "Gagal", 0.0, 0.0,
            "👍 Akurat", gr.update(visible=False), ""
        )

async def run_scraper_and_batch_classify(platform, target, max_items):
    if not target.strip():
        return None, None, None, "Silakan masukkan URL video TikTok atau Kata Kunci X terlebih dahulu."
    
    # 1. Scraping data mentah
    if platform == "TikTok Video Comments":
        raw_texts, is_real = await scraper.scrape_tiktok_comments(target, max_comments=max_items)
    else:
        raw_texts, is_real = await scraper.scrape_x_tweets(target, max_tweets=max_items)

        
    if not raw_texts:
        return None, None, None, f"Tidak ada data yang berhasil diambil dari {platform}."
        
    # 2. Klasifikasi Batch secara otomatis menggunakan API bertingkat
    classified_data = []
    print(f"Memulai proses batch klasifikasi untuk {len(raw_texts)} teks...")
    
    try:
        batch_req = main.BatchTextRequest(texts=raw_texts)
        batch_res = await main.predict_batch(batch_req)
        
        for pred in batch_res.results:
            classified_data.append({
                "Teks": pred.text,
                "Is_Toxic": "Ya" if pred.is_toxic else "Tidak",
                "Is_Bully": "Ya" if pred.is_bully else "Tidak",
                "Prob_Toxicity": f"{pred.probability_toxic*100:.1f}%",
                "Prob_Bullying": f"{pred.probability_bully*100:.1f}%",
                "Kategori": pred.category,
                "Sumber_Keputusan": pred.decision_source,
                "Alasan": pred.reason
            })
    except Exception as e:
        print(f"Error dalam batch klasifikasi: {e}. Menggunakan fallback pemrosesan sekuensial.")
        for text in raw_texts:
            try:
                pred = await main.predict_hybrid(main.TextRequest(text=text))
                classified_data.append({
                    "Teks": pred.text,
                    "Is_Toxic": "Ya" if pred.is_toxic else "Tidak",
                    "Is_Bully": "Ya" if pred.is_bully else "Tidak",
                    "Prob_Toxicity": f"{pred.probability_toxic*100:.1f}%",
                    "Prob_Bullying": f"{pred.probability_bully*100:.1f}%",
                    "Kategori": pred.category,
                    "Sumber_Keputusan": pred.decision_source,
                    "Alasan": pred.reason
                })
            except Exception as ex:
                classified_data.append({
                    "Teks": text,
                    "Is_Toxic": "Error",
                    "Is_Bully": "Error",
                    "Prob_Toxicity": "0%",
                    "Prob_Bullying": "0%",
                    "Kategori": f"Gagal: {ex}",
                    "Sumber_Keputusan": "None",
                    "Alasan": str(ex)
                })
            
    # 3. Konversi ke DataFrame
    df = pd.DataFrame(classified_data)
    
    # 4. Simpan ke CSV di direktori lokal untuk diunduh user
    filename = f"classified_{platform.lower().split()[0]}_data.csv"
    filepath = os.path.join(os.getcwd(), filename)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    # 5. Buat Diagram Distribusi Kategori
    fig = generate_batch_pie_chart(df)
    
    source_type = "Riil (Live Scraping)" if is_real else "Simulasi / Fallback (Diblokir oleh Platform)"
    status_msg = f"Sukses! Berhasil mengambil dan mengklasifikasikan {len(df)} data dari {platform}.\n[Sumber Data: {source_type}]"
    return df, filepath, fig, status_msg


async def submit_user_feedback(text, status, correction_val=None):
    if not text.strip():
        return "<div style='color:red; padding:5px;'>Teks kosong.</div>"
        
    try:
        is_toxic, is_bully = False, False
        if status == "👍 Akurat":
            # Ambil prediksi saat ini dari database
            res = await classifier.get_classification_memory(text)
            if not res:
                # Fallback run prediction
                req = main.TextRequest(text=text)
                res = await main.predict_hybrid(req)
            is_toxic = res.is_toxic
            is_bully = res.is_bully
        else: # Koreksi
            if not correction_val:
                return "<div style='color:red; padding:5px;'>Silakan pilih label koreksi terlebih dahulu.</div>"
            if "Aman" in correction_val:
                is_toxic, is_bully = False, False
            elif "Casual Slang" in correction_val:
                is_toxic, is_bully = True, False
            elif "Sarcasm" in correction_val:
                is_toxic, is_bully = False, True
            elif "Serangan Langsung" in correction_val:
                is_toxic, is_bully = True, True

        await classifier.update_validation_status(text, is_toxic, is_bully, is_validated=1)
        return "<div style='color:green; font-weight:bold; padding:8px; border:1px solid #137333; background-color:#e6f4ea; border-radius:6px;'>✔️ Koreksi tersimpan! Data ditandai sebagai Validated untuk Active Learning berikutnya.</div>"
    except Exception as e:
        return f"<div style='color:red; padding:5px;'>Gagal menyimpan feedback: {str(e)}</div>"


import sys
import subprocess

admin_password_env = os.getenv("ADMIN_PASSWORD", "admin123")

def admin_login(password: str) -> tuple[bool, str]:
    if password == admin_password_env:
        return True, "Login Sukses! Akses Admin Dashboard diberikan."
    return False, "Password Admin salah. Akses ditolak."

async def load_unvalidated_logs_df() -> pd.DataFrame:
    try:
        logs = await classifier.get_unvalidated_memory(limit=100)
        if not logs:
            return pd.DataFrame(columns=["Teks", "Is_Toxic (Prediksi)", "Is_Bully (Prediksi)", "Sumber", "Keyakinan", "Waktu"])
        
        df_list = []
        for l in logs:
            df_list.append({
                "Teks": l["text"],
                "Is_Toxic (Prediksi)": "Ya" if l["is_toxic"] else "Tidak",
                "Is_Bully (Prediksi)": "Ya" if l["is_bully"] else "Tidak",
                "Sumber": l["decision_source"],
                "Keyakinan": f"{l['confidence']*100:.1f}%" if l["confidence"] else "0%",
                "Waktu": str(l["timestamp"])[:19]
            })
        return pd.DataFrame(df_list)
    except Exception as e:
        print(f"Error loading admin logs: {e}")
        return pd.DataFrame(columns=["Error"])

async def admin_bulk_validate(text: str, label: str):
    if not text:
        return "Teks kosong."
    try:
        is_toxic, is_bully = False, False
        if "Aman" in label:
            is_toxic, is_bully = False, False
        elif "Casual Slang" in label:
            is_toxic, is_bully = True, False
        elif "Sarcasm" in label:
            is_toxic, is_bully = False, True
        elif "Serangan Langsung" in label:
            is_toxic, is_bully = True, True
            
        await classifier.update_validation_status(text, is_toxic, is_bully, is_validated=1)
        return f"Berhasil memvalidasi '{text[:30]}...' sebagai '{label}'"
    except Exception as e:
        return f"Error: {e}"

def run_retrain_script_async() -> str:
    try:
        retrain_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "retrain.py")
        subprocess.Popen([sys.executable, retrain_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Siklus pelatihan ulang (Active Learning) telah dimulai di background. Proses ini memakan waktu sekitar 10-30 detik. Silakan periksa file log konsol untuk detailnya."        
    except Exception as e:
        return f"Gagal memicu pelatihan ulang: {e}"


def reload_models_handler() -> str:
    try:
        classifier.init_models()
        return "✔️ Seluruh model (Lexicon, ML, Transformer) berhasil dimuat ulang ke dalam memori aplikasi!"
    except Exception as e:
        return f"❌ Gagal memuat ulang model: {e}"
