import pandas as pd
import os

import main
import scraper

from ui.components import highlight_toxic_words, make_html_card, generate_batch_pie_chart


async def predict_single_hybrid(text):
    if not text.strip():
        empty_card = "<div style='padding:15px; border:1px dashed #ccc; border-radius:8px; text-align:center;'>Silakan masukkan teks terlebih dahulu.</div>"
        empty_highlight = "<div style='padding:10px; border:1px dashed #ccc; border-radius:6px; color:#666;'>Teks kosong.</div>"
        return empty_card, empty_highlight, 0.0, 0.0, "Teks kosong", 0.0, 0.0, "Teks kosong", 0.0, 0.0

    # Prediksi menggunakan hybrid bertingkat
    try:
        req = main.TextRequest(text=text)
        res = await main.predict_hybrid(req)
        
        html_card = make_html_card(res.category, res.probability_toxic, res.probability_bully, res.decision_source, res.reason)
        
        # Dapatkan kata kasar terdeteksi dari leksikon untuk disorot
        lex_res = main.classifier.predict_lexicon(text)
        highlighted_html = highlight_toxic_words(text, lex_res.matches)
        
        # Ambil juga hasil individual untuk tab detail dengan penanganan eror mandiri
        try:
            ml_res = main.predict_ml(req)
            ml_cat = ml_res.category
            ml_toxic = ml_res.probability_toxic
            ml_bully = ml_res.probability_bully
        except Exception as ml_err:
            print(f"Warning: Gagal mengambil hasil detail ML: {ml_err}")
            ml_cat = "Gagal memuat / Error"
            ml_toxic = 0.0
            ml_bully = 0.0
            
        try:
            tr_res = main.predict_transformers(req)
            tr_cat = tr_res.category
            tr_toxic = tr_res.probability_toxic
            tr_bully = tr_res.probability_bully
        except Exception as tr_err:
            print(f"Warning: Gagal mengambil hasil detail Transformer: {tr_err}")
            tr_cat = "Gagal memuat / Error"
            tr_toxic = 0.0
            tr_bully = 0.0
            
    except Exception as e:
        html_card = f"<div style='color:red; padding:10px; border:1px solid red; border-radius:8px;'>Gagal memproses: {str(e)}</div>"
        highlighted_html = f"<div style='color:red; padding:10px;'>Gagal memproses: {str(e)}</div>"
        ml_cat, ml_toxic, ml_bully = "Gagal", 0.0, 0.0
        tr_cat, tr_toxic, tr_bully = "Gagal", 0.0, 0.0
        # Initialize res fallback to avoid NameError
        class FallbackRes:
            probability_toxic = 0.0
            probability_bully = 0.0
        res = FallbackRes()

    return (
        html_card,
        highlighted_html,
        res.probability_toxic,
        res.probability_bully,
        
        ml_cat,
        ml_toxic,
        ml_bully,
        
        tr_cat,
        tr_toxic,
        tr_bully
    )

async def run_scraper_and_batch_classify(platform, target, max_items):
    if not target.strip():
        return None, None, None, "Silakan masukkan URL video TikTok atau Kata Kunci X terlebih dahulu."
    
    # 1. Scraping data mentah
    if platform == "TikTok Video Comments":
        raw_texts, is_real = scraper.scrape_tiktok_comments(target, max_comments=max_items)
    else:
        raw_texts, is_real = scraper.scrape_x_tweets(target, max_tweets=max_items)
        
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
