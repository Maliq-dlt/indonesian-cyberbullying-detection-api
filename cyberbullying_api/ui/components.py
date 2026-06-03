import re

# Pengaturan backend Matplotlib agar ramah server headless
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def highlight_toxic_words(text, matches):
    if not matches or not text:
        return f"<div style='padding:10px; border:1px solid #ccc; border-radius:6px; background-color:#fff;'>{text}</div>"
        
    intervals = []
    seen_phrases = set()
    
    for match in matches:
        phrase = match["matched_phrase"]
        if phrase in seen_phrases:
            continue
        seen_phrases.add(phrase)
        
        severity = match["severity"]
        if severity == "tinggi":
            color = "#c5221f"  # Merah
            bg_color = "rgba(197, 34, 31, 0.15)"
        elif severity == "sedang":
            color = "#c26401"  # Oranye
            bg_color = "rgba(194, 100, 1, 0.15)"
        else:
            color = "#b06000"  # Kuning
            bg_color = "rgba(176, 96, 0, 0.15)"
            
        try:
            pattern = re.compile(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", re.IGNORECASE)
            for m in pattern.finditer(text):
                intervals.append((m.start(), m.end(), color, bg_color))
        except Exception:
            start = 0
            while True:
                idx = text.lower().find(phrase.lower(), start)
                if idx == -1:
                    break
                intervals.append((idx, idx + len(phrase), color, bg_color))
                start = idx + len(phrase)
                
    if not intervals:
        return f"<div style='padding:10px; border:1px solid #ccc; border-radius:6px; background-color:#fff;'>{text}</div>"
        
    intervals.sort(key=lambda x: (x[0], -x[1]))
    
    merged = []
    for current in intervals:
        if not merged:
            merged.append(current)
        else:
            prev_start, prev_end, prev_color, prev_bg = merged[-1]
            curr_start, curr_end, curr_color, curr_bg = current
            
            if curr_start < prev_end:
                severity_map = {"#c5221f": 3, "#c26401": 2, "#b06000": 1}
                color_val = prev_color if severity_map.get(prev_color, 0) >= severity_map.get(curr_color, 0) else curr_color
                bg_val = prev_bg if severity_map.get(prev_color, 0) >= severity_map.get(curr_color, 0) else curr_bg
                merged[-1] = (prev_start, max(prev_end, curr_end), color_val, bg_val)
            else:
                merged.append(current)
                
    result = []
    last_idx = 0
    for start, end, color, bg_color in merged:
        result.append(text[last_idx:start])
        matched_segment = text[start:end]
        result.append(f"<span style='color: {color}; background-color: {bg_color}; font-weight: bold; border-bottom: 2px solid {color}; padding: 0 4px; border-radius: 4px;'>{matched_segment}</span>")
        last_idx = end
    result.append(text[last_idx:])
    
    highlighted = "".join(result)
    return f"<div style='padding:10px; border:1px solid #ccc; border-radius:6px; background-color:#fff; font-family: sans-serif; line-height: 1.6;'>{highlighted}</div>"


def generate_batch_pie_chart(df):
    if df is None or df.empty or "Kategori" not in df.columns:
        return None
        
    try:
        # Hitung sebaran data kategori
        counts = df["Kategori"].value_counts()
        
        # Pemetaan warna harmonis sesuai dengan kategori UI
        colors_map = {
            "Non-Toxic & Non-Bully (Aman)": "#81c995",
            "Toxic but Non-Bully (Casual Slang / Swearing)": "#fdd663",
            "Non-Toxic but Bully (Sarcasm / Insult)": "#fcad70",
            "Toxic & Bully (Serangan Langsung)": "#f28b82"
        }
        
        colors = [colors_map.get(cat, "#bdc1c6") for cat in counts.index]
        
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        pie_result = ax.pie(
            counts.values, 
            labels=counts.index, 
            autopct='%1.1f%%',
            startangle=140,
            colors=colors,
            textprops=dict(color="black", fontsize=9)
        )
        # Unpack safely to satisfy type checker
        wedges = pie_result[0]
        texts = pie_result[1]
        autotexts = pie_result[2] if len(pie_result) > 2 else []
        
        # Percantik label persentase
        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_fontweight('bold')
            
        ax.axis('equal')
        plt.title("Distribusi Kategori Analisis Massal (Batch)", fontsize=11, weight='bold', pad=15)
        plt.tight_layout()
        return fig
    except Exception as e:
        print(f"Error membuat diagram lingkaran: {e}")
        return None


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
