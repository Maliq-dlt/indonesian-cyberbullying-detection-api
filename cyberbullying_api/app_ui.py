import gradio as gr
import pandas as pd
import numpy as np
import os
import joblib

# Impor fungsi normalisasi & deteksi dari main.py
import main

# Memuat dependensi yang diperlukan pada saat startup UI
print("=== Mempersiapkan Gradio Web UI (Multilabel) ===")
main.startup_event()

def make_html_card(category, prob_toxic, prob_bully):
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
        <div style="display: flex; gap: 20px; font-size: 0.9rem; font-weight: bold;">
            <span>🔥 Skor Toksisitas: {prob_toxic*100:.1f}%</span>
            <span>🎯 Skor Intimidasi (Bully): {prob_bully*100:.1f}%</span>
        </div>
    </div>
    """
    return html

def predict_all(text):
    if not text.strip():
        empty_card = "<div style='padding:15px; border:1px dashed #ccc; border-radius:8px; text-align:center;'>Silakan masukkan teks terlebih dahulu.</div>"
        return empty_card, 0.0, 0.0, "Teks kosong", 0.0, 0.0, "Teks kosong", 0.0, 0.0, "Teks kosong"

    # 1. Evaluasi Leksikon
    lex_res = main.predict_lexicon(main.TextRequest(text=text))
    matches_text = ""
    if lex_res.matches:
        for idx, m in enumerate(lex_res.matches):
            matches_text += f"{idx+1}. kata: '{m.matched_phrase}' | Kategori: {m.category} | Tingkat: {m.severity}\n"
    else:
        matches_text = "Tidak ada kata kasar terdeteksi."
        
    lexicon_summary = (
        f"Status: {lex_res.risk_label.upper()}\n"
        f"Skor Leksikon: {lex_res.score}\n"
        f"Normalisasi (Spaced): '{lex_res.normalized_spaced}'\n"
        f"Normalisasi (Compact): '{lex_res.normalized_compact}'\n\n"
        f"Pencocokan Kata Kasar:\n{matches_text}"
    )

    # 2. Evaluasi ML
    try:
        ml_res = main.predict_ml(main.TextRequest(text=text))
        ml_cat = ml_res.category
        ml_toxic = ml_res.probability_toxic
        ml_bully = ml_res.probability_bully
    except Exception as e:
        ml_cat = f"Gagal: {e}"
        ml_toxic = 0.0
        ml_bully = 0.0

    # 3. Evaluasi Transformer
    try:
        tr_res = main.predict_transformers(main.TextRequest(text=text))
        tr_cat = tr_res.category
        tr_toxic = tr_res.probability_toxic
        tr_bully = tr_res.probability_bully
    except Exception as e:
        tr_cat = f"Gagal: {e}"
        tr_toxic = 0.0
        tr_bully = 0.0

    # 4. Ensemble
    try:
        ens_res = main.predict_ensemble(main.TextRequest(text=text))
        ens_cat = ens_res.category
        ens_toxic = ens_res.probability_toxic
        ens_bully = ens_res.probability_bully
    except Exception as e:
        ens_cat = f"Gagal: {e}"
        ens_toxic = 0.0
        ens_bully = 0.0

    html_card = make_html_card(ens_cat, ens_toxic, ens_bully)

    return (
        html_card,
        ens_toxic,
        ens_bully,
        
        ml_cat,
        ml_toxic,
        ml_bully,
        
        tr_cat,
        tr_toxic,
        tr_bully,
        
        lexicon_summary
    )

# Membangun antarmuka Gradio
theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="blue",
    neutral_hue="slate"
)

with gr.Blocks(theme=theme, title="Sistem Deteksi Cyberbullying Multilabel") as demo:
    gr.Markdown(
        """
        # 🛡️ Sistem Deteksi Cyberbullying Multilabel Bahasa Indonesia
        Aplikasi ini memadukan **Leksikon (Kamus Normalisasi Slang)**, **Machine Learning (Logistic Regression)**, dan **Deep Learning (Transformer XLM-RoBERTa)** dalam sistem **Weighted Ensemble** untuk mendeteksi:
        * **Toksisitas (Toxicity)**: Penggunaan kata-kata kotor, kasar, atau umpatan gaul.
        * **Perundungan (Bullying)**: Niat menyerang, merendahkan fisik, status sosial, atau sindiran (sarkasme).
        """
    )
    
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
            gr.Markdown("### 📊 Hasil Keputusan Sistem (Ensemble)")
            ens_html_out = gr.HTML(
                value="<div style='padding:15px; border:1px dashed #ccc; border-radius:8px; text-align:center;'>Hasil analisis akan ditampilkan di sini.</div>"
            )
            
            with gr.Row():
                ens_toxic_out = gr.Slider(
                    label="🔥 Probabilitas Toxicity (Ensemble)",
                    minimum=0.0,
                    maximum=1.0,
                    interactive=False
                )
                ens_bully_out = gr.Slider(
                    label="🎯 Probabilitas Bullying (Ensemble)",
                    minimum=0.0,
                    maximum=1.0,
                    interactive=False
                )
            
            with gr.Tabs():
                with gr.TabItem("📋 Laporan Detail Model"):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("#### 🤖 Machine Learning (Logistic Regression)")
                            ml_cat_out = gr.Textbox(label="Kategori Terdeteksi", interactive=False)
                            ml_toxic_out = gr.Slider(label="🔥 Skor Toxicity (ML)", minimum=0.0, maximum=1.0, interactive=False)
                            ml_bully_out = gr.Slider(label="🎯 Skor Bullying (ML)", minimum=0.0, maximum=1.0, interactive=False)
                        
                        with gr.Column():
                            gr.Markdown("#### 🧠 Deep Learning (XLM-RoBERTa)")
                            tr_cat_out = gr.Textbox(label="Kategori Terdeteksi", interactive=False)
                            tr_toxic_out = gr.Slider(label="🔥 Skor Toxicity (Transformer)", minimum=0.0, maximum=1.0, interactive=False)
                            tr_bully_out = gr.Slider(label="🎯 Skor Bullying (Transformer)", minimum=0.0, maximum=1.0, interactive=False)

                with gr.TabItem("🔍 Analisis Leksikon & Pencocokan Kata"):
                    lexicon_output = gr.Textbox(
                        label="Rangkuman Leksikon (Aturan)",
                        interactive=False,
                        lines=10
                    )

    # Menghubungkan tombol klik ke fungsi prediksi
    btn_detect.click(
        fn=predict_all,
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
            tr_bully_out,
            
            lexicon_output
        ]
    )
    
    # Fungsi tombol clear
    def clear_fields():
        empty_card = "<div style='padding:15px; border:1px dashed #ccc; border-radius:8px; text-align:center;'>Hasil analisis akan ditampilkan di sini.</div>"
        return "", empty_card, 0.0, 0.0, "", 0.0, 0.0, "", 0.0, 0.0, ""
        
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
            tr_bully_out,
            
            lexicon_output
        ]
    )

if __name__ == "__main__":
    print("Menjalankan Gradio Web UI di http://127.0.0.1:7860...")
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
