import gradio as gr
import pandas as pd
import numpy as np
import os
import joblib

# Impor fungsi normalisasi & deteksi dari main.py
import main

# Memuat dependensi yang diperlukan pada saat startup UI
print("=== Mempersiapkan Gradio Web UI ===")

# Pemicu memuat kamus dan model secara langsung dari main.py
main.startup_event()

def predict_all(text):
    if not text.strip():
        return "Teks kosong", "Aman", "0%", "Aman", "0%"

    # 1. Evaluasi Leksikon
    lex_res = main.predict_lexicon(main.TextRequest(text=text))
    
    # Format hasil leksikon
    matches_text = ""
    if lex_res.matches:
        for idx, m in enumerate(lex_res.matches):
            matches_text += f"{idx+1}. kata: '{m.matched_phrase}' | Kategori: {m.category} | Tingkat: {m.severity}\n"
    else:
        matches_text = "Tidak ada kata kasar terdeteksi."
        
    lexicon_summary = (
        f"Status: {lex_res.risk_label.upper()}\n"
        f"Skor Keparahan: {lex_res.score}\n"
        f"Teks Dinormalisasi (Spaced): '{lex_res.normalized_spaced}'\n"
        f"Teks Dinormalisasi (Compact): '{lex_res.normalized_compact}'\n\n"
        f"Kata Kasar yang Terdeteksi:\n{matches_text}"
    )

    # 2. Evaluasi Machine Learning (Logistic Regression)
    try:
        ml_res = main.predict_ml(main.TextRequest(text=text))
        ml_label = "TOXIC / BULLYING" if ml_res.is_cyberbullying else "AMAN / NON-TOXIC"
        ml_prob_pct = f"{ml_res.probability * 100:.2f}%"
        ml_prob = ml_res.probability
    except Exception as e:
        ml_label = "Model ML gagal memproses"
        ml_prob_pct = "0%"
        ml_prob = 0.0

    # 3. Evaluasi Deep Learning Transformer (XLM-RoBERTa)
    try:
        transformer_res = main.predict_transformers(main.TextRequest(text=text))
        trans_label = transformer_res.label
        trans_prob_pct = f"{transformer_res.score * 100:.2f}%"
        trans_prob = transformer_res.score
    except Exception as e:
        trans_label = "Model Transformer gagal memproses"
        trans_prob_pct = "0%"
        trans_prob = 0.0

    return (
        lexicon_summary,
        ml_label,
        ml_prob,
        trans_label,
        trans_prob
    )

# Membangun antarmuka Gradio
theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="blue",
    neutral_hue="slate"
)

with gr.Blocks(theme=theme, title="Deteksi Cyberbullying & Ujaran Kebencian") as demo:
    gr.Markdown(
        """
        # 🛡️ Deteksi Cyberbullying & Ujaran Kebencian (Indonesian)
        Aplikasi ini memadukan 3 metode deteksi: **Leksikon (Aturan Normalisasi Teks)**, **Machine Learning (Logistic Regression)**, dan **Deep Learning (Transformer XLM-RoBERTa)**.
        """
    )
    
    with gr.Row():
        with gr.Column(scale=2):
            input_text = gr.Textbox(
                label="Masukkan Komentar / Tweet",
                placeholder="Ketik komentar di sini untuk dianalisis...",
                lines=5
            )
            btn_detect = gr.Button("Analisis Komentar", variant="primary")
            
            gr.Examples(
                examples=[
                    ["Semangat belajarnya ya, jangan menyerah!"],
                    ["Kamu bodoh banget sih, dasar tolol!"],
                    ["d4s4r gblk lu anjg"],
                    ["Wah pintar sekali kamu ya, sampai nilai ujianmu nol."],
                    ["kamu hebat banget sih anjing"]
                ],
                inputs=input_text
            )

        with gr.Column(scale=3):
            with gr.Tabs():
                with gr.TabItem("📋 Deteksi Leksikon (Aturan + Normalisasi)"):
                    lexicon_output = gr.Textbox(
                        label="Laporan Analisis Leksikon",
                        interactive=False,
                        lines=8
                    )
                
                with gr.TabItem("🤖 Deteksi Machine Learning (Logistic Regression)"):
                    ml_label_out = gr.Label(label="Hasil Prediksi AI")
                    ml_prob_out = gr.Slider(
                        label="Probabilitas Cyberbullying/Toxic",
                        minimum=0.0,
                        maximum=1.0,
                        interactive=False
                    )

                with gr.TabItem("🧠 Deteksi Deep Learning (Transformer XLM-RoBERTa)"):
                    trans_label_out = gr.Label(label="Hasil Prediksi Transformer")
                    trans_prob_out = gr.Slider(
                        label="Skor Keyakinan (Confidence Score)",
                        minimum=0.0,
                        maximum=1.0,
                        interactive=False
                    )

    # Menghubungkan tombol klik ke fungsi prediksi
    btn_detect.click(
        fn=predict_all,
        inputs=input_text,
        outputs=[
            lexicon_output,
            ml_label_out,
            ml_prob_out,
            trans_label_out,
            trans_prob_out
        ]
    )

if __name__ == "__main__":
    print("Menjalankan Gradio Web UI di http://127.0.0.1:7860...")
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
