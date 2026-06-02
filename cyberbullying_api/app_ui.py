import gradio as gr
import pandas as pd
import numpy as np
import os
import joblib

# Impor fungsi normalisasi & deteksi dari main.py
import main
import scraper

# Memuat dependensi yang diperlukan pada saat startup UI
print("=== Mempersiapkan Gradio Web UI (Hybrid & Scraper) ===")
main.startup_event()

def make_html_card(category, prob_toxic, prob_bully, decision_source, reason):
    # Set warna dan konten berdasarkan kombinasi kategori
    if "Aman" in category:
        bg_color = "#e6f4ea"
        text_color = "#137333"
        border_color = "#81c995"
        emoji = "🟢"
        desc = "Komentar ini tergolong aman, tidak mengandung kata kasar maupun niat intimidasi/bullying secara personal."
    elif "Casual Slang" in category:
        bg_color = "#fef7e0"
        text_color = "#b06000"
        border_color = "#fdd663"
        emoji = "🟡"
        desc = "Komentar mengandung kata kasar/slang umpatan gaul secara kasual, namun <b>tidak terindikasi</b> bertujuan untuk merundung atau menindas seseorang secara personal (hanya ungkapan ekspresif/pujian gaul)."
    elif "Sarcasm" in category:
        bg_color = "#feefe3"
        text_color = "#c26401"
        border_color = "#fcad70"
        emoji = "🟠"
        desc = "Komentar terindikasi kuat bermakna <b>sarkasme/cemoohan halus</b> (bullying terselubung), meskipun tidak tertulis kata-kata kotor/abusive secara harfiah."
    else: # Toxic & Bully
        bg_color = "#fce8e6"
        text_color = "#c5221f"
        border_color = "#f28b82"
        emoji = "🔴"
        desc = "Komentar terindikasi kuat sebagai <b>cyberbullying aktif</b> dengan penggunaan kata-kata kasar eksplisit yang diarahkan untuk menyerang seseorang."
    
    html = f"""
    <div style="background-color: {bg_color}; color: {text_color}; border: 2px solid {border_color}; border-radius: 8px; padding: 15px; font-family: 'Outfit', sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 15px;">
        <h3 style="margin-top: 0; margin-bottom: 8px; font-size: 1.25rem; display: flex; align-items: center; gap: 8px;">
            {emoji} {category}
        </h3>
        <p style="font-size: 0.95rem; margin-bottom: 12px; line-height: 1.45; color: #333333;">{desc}</p>
        <div style="font-size: 0.9rem; margin-bottom: 10px; padding: 6px 10px; background-color: rgba(255,255,255,0.6); border-radius: 4px; display: inline-block;">
            🎯 <b>Sumber Keputusan:</b> <span style="text-decoration: underline;">{decision_source}</span>
        </div>
        <p style="font-size: 0.88rem; font-style: italic; color: #555555; margin-top: 5px; margin-bottom: 12px;"><b>Alasan:</b> {reason}</p>
        <div style="display: flex; gap: 20px; font-size: 0.9rem; font-weight: bold;">
            <span>🔥 Skor Toksisitas: {prob_toxic*100:.1f}%</span>
            <span>🎯 Skor Intimidasi (Bully): {prob_bully*100:.1f}%</span>
        </div>
    </div>
    """
    return html

async def predict_single_hybrid(text):
    if not text.strip():
        empty_card = "<div style='padding:15px; border:1px dashed #ccc; border-radius:8px; text-align:center;'>Silakan masukkan teks terlebih dahulu.</div>"
        return empty_card, 0.0, 0.0, "Teks kosong", 0.0, 0.0, "Teks kosong", 0.0, 0.0

    # Prediksi menggunakan hybrid bertingkat
    try:
        req = main.TextRequest(text=text)
        res = await main.predict_hybrid(req)
        
        html_card = make_html_card(res.category, res.probability_toxic, res.probability_bully, res.decision_source, res.reason)
        
        # Ambil juga hasil individual untuk tab detail
        ml_res = main.predict_ml(req)
        ml_cat = ml_res.category
        ml_toxic = ml_res.probability_toxic
        ml_bully = ml_res.probability_bully
        
        tr_res = main.predict_transformers(req)
        tr_cat = tr_res.category
        tr_toxic = tr_res.probability_toxic
        tr_bully = tr_res.probability_bully
        
    except Exception as e:
        html_card = f"<div style='color:red; padding:10px; border:1px solid red; border-radius:8px;'>Gagal memproses: {str(e)}</div>"
        ml_cat, ml_toxic, ml_bully = "Gagal", 0.0, 0.0
        tr_cat, tr_toxic, tr_bully = "Gagal", 0.0, 0.0
        # Initialize res fallback to avoid NameError
        class FallbackRes:
            probability_toxic = 0.0
            probability_bully = 0.0
        res = FallbackRes()

    return (
        html_card,
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
        return None, None, "Silakan masukkan URL video TikTok atau Kata Kunci X terlebih dahulu."
    
    # 1. Scraping data mentah
    if platform == "TikTok Video Comments":
        raw_texts = scraper.scrape_tiktok_comments(target, max_comments=max_items)
    else:
        raw_texts = scraper.scrape_x_tweets(target, max_tweets=max_items)
        
    if not raw_texts:
        return None, None, f"Tidak ada data yang berhasil diambil dari {platform}."
        
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
    
    status_msg = f"Sukses! Berhasil mengambil dan mengklasifikasikan {len(df)} data dari {platform}."
    return df, filepath, status_msg

# Membangun antarmuka Gradio
theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="blue",
    neutral_hue="slate"
)

with gr.Blocks(theme=theme, title="Sistem Deteksi Cyberbullying Multilabel & Scraper") as demo:
    gr.Markdown(
        """
        # 🛡️ Sistem Deteksi Cyberbullying Multilabel, Scraper Media Sosial & Batch Processor
        Aplikasi ini memadukan **ML Klasik**, **Transformer**, dan **Ollama LLM Lokal** dalam arsitektur bertingkat (**Tiered Hybrid**) untuk menganalisis komentar secara presisi dan efisien.
        """
    )
    
    with gr.Tabs():
        # TAB 1: DETEKSI INTERAKTIF TEKS TUNGGAL
        with gr.TabItem("🔍 Analisis Teks Tunggal"):
            with gr.Row():
                with gr.Column(scale=2):
                    input_text = gr.Textbox(
                        label="Masukkan Komentar / Tweet",
                        placeholder="Ketik komentar di sini untuk dianalisis...",
                        lines=5
                    )
                    
                    with gr.Row():
                        btn_clear = gr.Button("Clear", variant="secondary")
                        btn_detect = gr.Button("Analisis Komentar", variant="primary")
                    
                    gr.Examples(
                        examples=[
                            ["Semangat belajarnya ya, jangan menyerah!"],
                            ["Kamu bodoh banget sih, dasar tolol!"],
                            ["kamu hebat banget sih anjing"],
                            ["Wah pintar sekali kamu ya, sampai nilai ujianmu nol."],
                            ["ganteng banget mukalu kaya spakbor mio"]
                        ],
                        inputs=input_text
                    )

                with gr.Column(scale=3):
                    gr.Markdown("### 📊 Hasil Keputusan Sistem (Hybrid Cascading)")
                    ens_html_out = gr.HTML(
                        value="<div style='padding:15px; border:1px dashed #ccc; border-radius:8px; text-align:center;'>Hasil analisis akan ditampilkan di sini.</div>"
                    )
                    
                    with gr.Row():
                        ens_toxic_out = gr.Slider(
                            label="🔥 Probabilitas Toxicity",
                            minimum=0.0,
                            maximum=1.0,
                            interactive=False
                        )
                        ens_bully_out = gr.Slider(
                            label="🎯 Probabilitas Bullying",
                            minimum=0.0,
                            maximum=1.0,
                            interactive=False
                        )
                    
                    with gr.Tabs():
                        with gr.TabItem("📋 Detail Perbandingan Model"):
                            with gr.Row():
                                with gr.Column():
                                    gr.Markdown("#### 🤖 Machine Learning (Logistic Regression)")
                                    ml_cat_out = gr.Textbox(label="Kategori Terdeteksi (ML)", interactive=False)
                                    ml_toxic_out = gr.Slider(label="Skor Toxicity (ML)", minimum=0.0, maximum=1.0, interactive=False)
                                    ml_bully_out = gr.Slider(label="Skor Bullying (ML)", minimum=0.0, maximum=1.0, interactive=False)
                                
                                with gr.Column():
                                    gr.Markdown("#### 🧠 Deep Learning (XLM-RoBERTa)")
                                    tr_cat_out = gr.Textbox(label="Kategori Terdeteksi (Transformer)", interactive=False)
                                    tr_toxic_out = gr.Slider(label="Skor Toxicity (Transformer)", minimum=0.0, maximum=1.0, interactive=False)
                                    tr_bully_out = gr.Slider(label="Skor Bullying (Transformer)", minimum=0.0, maximum=1.0, interactive=False)

            # Menghubungkan tombol klik ke fungsi prediksi tunggal
            btn_detect.click(
                fn=predict_single_hybrid,
                inputs=input_text,
                outputs=[
                    ens_html_out,
                    ens_toxic_out,
                    ens_bully_out,
                    
                    ml_cat_out,
                    ml_toxic_out,
                    ml_bully_out,
                    
                    tr_cat_out,
                    tr_toxic_out,
                    tr_bully_out
                ]
            )
            
            # Fungsi tombol clear
            def clear_fields():
                empty_card = "<div style='padding:15px; border:1px dashed #ccc; border-radius:8px; text-align:center;'>Hasil analisis akan ditampilkan di sini.</div>"
                return "", empty_card, 0.0, 0.0, "", 0.0, 0.0, "", 0.0, 0.0
                
            btn_clear.click(
                fn=clear_fields,
                inputs=[],
                outputs=[
                    input_text,
                    ens_html_out,
                    ens_toxic_out,
                    ens_bully_out,
                    
                    ml_cat_out,
                    ml_toxic_out,
                    ml_bully_out,
                    
                    tr_cat_out,
                    tr_toxic_out,
                    tr_bully_out
                ]
            )

        # TAB 2: SCRAPER & BATCH PROCESSOR (EKSPOR CSV LABELED)
        with gr.TabItem("📥 Scraper Media Sosial & Batch Ekspor CSV"):
            gr.Markdown(
                """
                ### 🔗 Ambil Data & Klasifikasikan Komentar Secara Massal
                Masukkan URL video TikTok atau Kata Kunci Topik X (Twitter), sistem akan otomatis mengambil komentar terbaru, menjalankannya lewat arsitektur Hybrid, dan mengelompokkannya ke dalam berkas CSV berlabel yang siap diunduh.
                """
            )
            
            with gr.Row():
                with gr.Column(scale=2):
                    platform_input = gr.Radio(
                        choices=["TikTok Video Comments", "X (Twitter) Tweets"],
                        label="Pilih Platform",
                        value="TikTok Video Comments"
                    )
                    target_input = gr.Textbox(
                        label="Tautan URL Video / Kata Kunci Pencarian",
                        placeholder="Contoh: https://www.tiktok.com/@username/video/123456789 atau kata kunci 'politik'",
                        lines=2
                    )
                    max_items_input = gr.Slider(
                        label="Jumlah Maksimal Teks Diambil",
                        minimum=5,
                        maximum=50,
                        step=5,
                        value=20
                    )
                    btn_batch = gr.Button("Scrap & Klasifikasikan Secara Batch", variant="primary")
                    
                with gr.Column(scale=3):
                    status_output = gr.Textbox(label="Status Pemrosesan", interactive=False)
                    download_file = gr.File(label="📥 Unduh CSV Hasil Klasifikasi", interactive=False)
            
            with gr.Row():
                df_output = gr.Dataframe(
                    label="Pratinjau Hasil Klasifikasi Batch",
                    interactive=False,
                    wrap=True
                )
                
            # Menghubungkan fungsi batch processing
            btn_batch.click(
                fn=run_scraper_and_batch_classify,
                inputs=[
                    platform_input,
                    target_input,
                    max_items_input
                ],
                outputs=[
                    df_output,
                    download_file,
                    status_output
                ]
            )

if __name__ == "__main__":
    print("Menjalankan Gradio Web UI di http://127.0.0.1:7860...")
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
