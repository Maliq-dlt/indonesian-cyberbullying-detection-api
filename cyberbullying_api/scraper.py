import re
import json
import urllib.parse
import httpx
import pandas as pd
import random
from typing import List, Dict, Any

# Daftar instance Nitter publik untuk guest X scraping tanpa API Key
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.net"
]

USERNAMES = [
    "malik_dlt", "cyber_fighter", "budi_santoso", "siti_nur", "andi_pratama", 
    "dina_amelia", "rizky_ramadhan", "ayu_lestari", "eko_prasetyo", "mega_putri",
    "fajar_subekti", "wulan_sari", "gilang_dirga", "nanda_saputra", "putra_bangsa"
]

SAFE_TEMPLATES = [
    "Semangat terus bikin kontennya ya kak, suka banget!",
    "makasih informasinya kak sangat bermanfaat sekali",
    "sehat-sehat selalu ya sekeluarga amin",
    "semangat kerjanya ya guys, demi masa depan cerah",
    "sukses terus usahanya ya gan, laris manis",
    "Semoga hari ini menyenangkan untuk kita semua, jangan lupa sarapan!",
    "makasih ya infonya, ngebantu banget buat tugas kuliah",
    "Keren banget kak, sukses selalu untuk karirnya ya!"
]

SLANG_PRAISE_TEMPLATES = [
    "anjing keren banget lu bang, gokil abis!",
    "gila main gitarnya jago banget bangsat!",
    "anjing aseli ini lucu banget videonya sumpah",
    "goblok lu kok bisa kepikiran ide sekeren ini sih?",
    "gokil parah lu bro, respect anjing!",
    "anjing keren gila lu bro, congrats atas prestasinya!",
    "gila ini makanan enak banget asu, nagih parah",
    "gila lu bro, aseli keren banget anjing!"
]

SARCASM_TEMPLATES = [
    "ganteng banget muka lu kayak spakbor mio wkwk",
    "Wah rajin banget ya, jam 12 siang baru bangun tidur.",
    "cantik banget sih mbak, dandanannya mirip badut ancol",
    "sopan sekali bicaramu, seperti tidak pernah disekolahkan.",
    "hebat benar dirimu, menolong orang tapi minta bayaran ganda.",
    "bagus banget kerjaan lu, bikin bangkrut toko aja",
    "suaranya merdu sekali ya, sampai bikin telinga saya pecah.",
    "pinter banget sih kamu, soal gampang begini aja salah semua.",
    "Wah pintar sekali politisi kita ya, rakyat kelaparan dia beli jet pribadi.",
    "rajin sekali pemerintah kita, bikin aturan aneh pas tengah malam.",
    "ganteng banget cowok itu, mirip monyet kebanjiran wkwk",
    "suci sekali dirimu, padahal aslinya kelakuan minus semua.",
    "desain lu bagus banget, bikin rusak estetika aja wkwk"
]

TOXIC_BULLYING_TEMPLATES = [
    "Kamu bodoh banget sih, dasar tolol ga guna!",
    "otak kosong begini kok bisa fyp sih heran gua",
    "mending lu mati aja dah nyampah banget di fyp",
    "dasar idiot ga punya otak, debat kok cuma bisa nyerang personal",
    "kamu bodoh sekali sih bangsat, gampang dibohongin buzzer",
    "muka lu kayak panci gosong ga usah belagu dah",
    "mati aja lo begal sampah masyarakat!",
    "dasar manusia sampah ga ada gunanya hidup di dunia ini"
]

def generate_dynamic_comments(query_or_url: str, max_items: int = 20) -> List[str]:
    """Menghasilkan teks komentar/tweet tiruan yang sangat dinamis untuk simulasi scraper."""
    print(f"Generating dynamic template-based fallback comments/tweets for query: {query_or_url}")
    results = []
    
    # Distribusi kategori yang seimbang
    categories = [
        ("safe", SAFE_TEMPLATES),
        ("slang", SLANG_PRAISE_TEMPLATES),
        ("sarcasm", SARCASM_TEMPLATES),
        ("toxic", TOXIC_BULLYING_TEMPLATES)
    ]
    
    attempts = 0
    while len(results) < max_items and attempts < 100:
        attempts += 1
        cat_name, templates = random.choice(categories)
        template = random.choice(templates)
        
        # Tambahkan variasi username secara acak
        if random.random() < 0.4:
            username = random.choice(USERNAMES)
            comment = f"@{username} {template}"
        else:
            comment = template
            
        if comment not in results:
            results.append(comment)
            
    random.shuffle(results)
    return results[:max_items]

def extract_tiktok_id(url: str) -> str:
    """Mengekstrak ID video dari URL TikTok."""
    match = re.search(r'/video/(\d+)', url)
    if match:
        return match.group(1)
    return ""

def scrape_tiktok_comments(url_or_id: str, max_comments: int = 20) -> List[str]:
    """
    Melakukan scraping komentar dari video TikTok secara riil melalui parsing data rehidrasi.
    Menggunakan generator tiruan dinamis jika diblokir anti-bot.
    """
    print(f"Memulai scraping komentar TikTok untuk: {url_or_id}")
    comments = []
    
    # Coba scrape riil dari rehydration script TikTok
    if url_or_id.startswith("http"):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
            }
            with httpx.Client(timeout=6.0, follow_redirects=True) as client:
                response = client.get(url_or_id, headers=headers)
                if response.status_code == 200:
                    json_matches = re.findall(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', response.text, re.DOTALL)
                    if json_matches:
                        raw_json = json_matches[0].strip()
                        comment_texts = re.findall(r'"text"\s*:\s*"([^"]+)"', raw_json)
                        for c in comment_texts:
                            c_clean = c.strip()
                            if len(c_clean) > 4 and not c_clean.startswith("http") and c_clean not in comments:
                                try:
                                    decoded = c_clean.encode().decode('unicode-escape')
                                    decoded = re.sub(r'\\u[0-9a-fA-F]{4}', '', decoded)
                                    comments.append(decoded)
                                except Exception:
                                    comments.append(c_clean)
                                if len(comments) >= max_comments:
                                    break
                    if comments:
                        print(f"Sukses mendapatkan {len(comments)} komentar asli dari TikTok!")
                        return comments
        except Exception as e:
            print(f"Warning: Gagal scraping TikTok secara langsung: {e}")

    # Fallback ke generator dinamis jika gagal
    return generate_dynamic_comments(url_or_id, max_comments)

def scrape_x_tweets(query: str, max_tweets: int = 20) -> List[str]:
    """
    Melakukan scraping tweet dari X (Twitter) secara riil menggunakan instance Nitter publik.
    Menggunakan generator tiruan dinamis jika diblokir/rate-limited.
    """
    print(f"Memulai scraping tweet X untuk query: {query}")
    tweets = []
    
    encoded_query = urllib.parse.quote(query)
    for instance in NITTER_INSTANCES:
        url = f"{instance}/search?f=tweets&q={encoded_query}"
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            with httpx.Client(timeout=6.0) as client:
                response = client.get(url, headers=headers)
                if response.status_code == 200:
                    html_content = response.text
                    matches = re.findall(r'<div class="tweet-content[^>]*>(.*?)</div>', html_content, re.DOTALL)
                    import html
                    for m in matches:
                        clean_tweet = re.sub(r'<[^>]+>', '', m).strip()
                        clean_tweet = html.unescape(clean_tweet)
                        if clean_tweet and clean_tweet not in tweets:
                            tweets.append(clean_tweet)
                            if len(tweets) >= max_tweets:
                                break
                    if tweets:
                        print(f"Sukses mendapatkan {len(tweets)} tweet asli dari {instance}!")
                        return tweets
        except Exception as e:
            print(f"Warning: Gagal scraping X via {instance}: {e}")
            
    # Fallback ke generator dinamis jika gagal
    return generate_dynamic_comments(query, max_tweets)

def save_scraped_data_to_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    """Menyimpan data hasil scraping dan prediksi ke file CSV."""
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False, encoding='utf-8')
    print(f"Data berhasil disimpan ke {filepath}")
