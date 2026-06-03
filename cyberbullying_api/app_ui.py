import os
import gradio as gr
import classifier

# Memuat dependensi yang diperlukan pada saat startup UI
print("=== Mempersiapkan Gradio Web UI (Hybrid & Scraper) ===")
classifier.init_models()

from ui import (
    predict_single_hybrid,
    run_scraper_and_batch_classify
)

# Membangun antarmuka Gradio
theme = gr.themes.Soft(  # type: ignore
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
                    
                    highlight_out = gr.HTML(
                        label="🔍 Teks yang Disorot (Leksikon)",
                        value="<div style='padding:10px; border:1px dashed #ccc; border-radius:6px; color:#666;'>Kata kasar yang terdeteksi akan disorot di sini.</div>"
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
                    highlight_out,
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
                empty_highlight = "<div style='padding:10px; border:1px dashed #ccc; border-radius:6px; color:#666;'>Kata kasar yang terdeteksi akan disorot di sini.</div>"
                return "", empty_card, empty_highlight, 0.0, 0.0, "", 0.0, 0.0, "", 0.0, 0.0
                
            btn_clear.click(
                fn=clear_fields,
                inputs=[],
                outputs=[
                    input_text,
                    ens_html_out,
                    highlight_out,
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
                
                🚀 **Peningkatan Scraper (Otomatisasi Playwright + Cookies)**:
                Sistem kini mendukung **Live Scraping tingkat lanjut** menggunakan browser otomatis (Playwright) dengan cookie autentikasi untuk hasil scraping yang sangat akurat dan riil!
                
                ...
                
                *Catatan: Jika file cookie tidak ditemukan atau pustaka Playwright belum dipasang, sistem secara otomatis akan beralih ke **Simulasi Fallback** berbasis komentar alay/cyberbullying dinamis agar fitur ekspor CSV tetap dapat diuji. Komentar gambar/stiker tanpa teks akan disaring secara otomatis.*
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
                    plot_output = gr.Plot(label="📊 Diagram Distribusi Kategori")
            
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
                    plot_output,
                    status_output
                ]
            )

if __name__ == "__main__":
    print("Menjalankan Gradio Web UI di http://0.0.0.0:7860...")
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
