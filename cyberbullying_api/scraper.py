import re
import json
import urllib.parse
import httpx
import pandas as pd
from typing import List, Dict, Any

# Daftar instance Nitter publik untuk guest X scraping tanpa API Key
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.net"
]

def extract_tiktok_id(url: str) -> str:
    """Mengekstrak ID video dari URL TikTok."""
    match = re.search(r'/video/(\d+)', url)
    if match:
        return match.group(1)
    return ""

def scrape_tiktok_comments(url_or_id: str, max_comments: int = 20) -> List[str]:
    """
    Melakukan scraping komentar dari video TikTok secara riil melalui parsing data rehidrasi.
    Menggunakan fallback data jika diblokir anti-bot.
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
                    # Mencari Universal Data Rehydration script
                    json_matches = re.findall(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', response.text, re.DOTALL)
                    if json_matches:
                        raw_json = json_matches[0].strip()
                        # Ekstrak teks komentar secara kasar melalui pola Regex '"text":"value"'
                        comment_texts = re.findall(r'"text"\s*:\s*"([^"]+)"', raw_json)
                        for c in comment_texts:
                            c_clean = c.strip()
                            # Abaikan string teknis/pendek
                            if len(c_clean) > 4 and not c_clean.startswith("http") and c_clean not in comments:
                                try:
                                    decoded = c_clean.encode().decode('unicode-escape')
                                    # Hapus unicode escape karakter yang tidak perlu
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

    # Realistis komentar TikTok Indonesia (beragam kelas: toxic, sarcasm, slang, aman)
    fallback_comments = [
        "Semangat terus bikin kontennya ya kak, suka banget!",
        "anjing keren banget lu bang, gokil abis!",
        "ganteng banget muka lu kayak spakbor mio wkwk",
        "Kamu bodoh banget sih, dasar tolol ga guna!",
        "Wah rajin banget ya, jam 12 siang baru bangun tidur.",
        "cantik banget sih mbak, dandanannya mirip badut ancol",
        "gila main gitarnya jago banget bangsat!",
        "sopan sekali bicaramu, seperti tidak pernah disekolahkan.",
        "anjing aseli ini lucu banget videonya sumpah",
        "makasih informasinya kak sangat bermanfaat sekali",
        "otak kosong begini kok bisa fyp sih heran gua",
        "hebat benar dirimu, menolong orang tapi minta bayaran ganda.",
        "bagus banget kerjaan lu, bikin bangkrut toko aja",
        "sehat-sehat selalu ya sekeluarga amin",
        "goblok lu kok bisa kepikiran ide sekeren ini sih?",
        "suaranya merdu sekali ya, sampai bikin telinga saya pecah.",
        "mending lu mati aja dah nyampah banget di fyp",
        "rajin sekali dia, tugas satu semester dikerjakan semenit sebelum deadline.",
        "gokil parah lu bro, respect anjing!",
        "pinter banget sih kamu, soal gampang begini aja salah semua."
    ]
    
    print(f"Menggunakan {len(fallback_comments[:max_comments])} data fallback TikTok.")
    return fallback_comments[:max_comments]

def scrape_x_tweets(query: str, max_tweets: int = 20) -> List[str]:
    """
    Melakukan scraping tweet dari X (Twitter) secara riil menggunakan instance Nitter publik.
    Menggunakan fallback data jika diblokir/rate-limited.
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
                    # Cari tweet-content menggunakan regex
                    matches = re.findall(r'<div class="tweet-content[^>]*>(.*?)</div>', html_content, re.DOTALL)
                    for m in matches:
                        clean_tweet = re.sub(r'<[^>]+>', '', m).strip() # bersihkan tag HTML
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
            
    # Realistis tweet X Indonesia (beragam kelas)
    import html # Pastikan modul diimpor
    fallback_tweets = [
        "Wah pintar sekali politisi kita ya, rakyat kelaparan dia beli jet pribadi.",
        "Semoga hari ini menyenangkan untuk kita semua, jangan lupa sarapan!",
        "dasar idiot ga punya otak, debat kok cuma bisa nyerang personal",
        "anjing keren gila lu bro, congrats atas prestasinya!",
        "ganteng banget cowok itu, mirip monyet kebanjiran wkwk",
        "makasih ya infonya, ngebantu banget buat tugas kuliah",
        "rajin sekali pemerintah kita, bikin aturan aneh pas tengah malam.",
        "gila ini makanan enak banget asu, nagih parah",
        "kamu bodoh sekali sih bangsat, gampang dibohongin buzzer",
        "sukses terus usahanya ya gan, laris manis",
        "sopan sekali bicaranya, ketahuan tidak berpendidikan",
        "gila lu kok pinter banget bikin analisis ginian anjing",
        "muka lu kayak panci gosong ga usah belagu dah",
        "suci sekali dirimu, padahal aslinya kelakuan minus semua.",
        "semangat kerjanya ya guys, demi masa depan cerah",
        "desain lu bagus banget, bikin rusak estetika aja wkwk",
        "mati aja lo begal sampah masyarakat!",
        "hebat sekali kau, selalu berhasil mengecewakan orang tua.",
        "gokil parah analisisnya, informatif banget bangsat!",
        "rajin sekali dia, bangun jam 1 siang terus minta warisan."
    ]
    
    print(f"Menggunakan {len(fallback_tweets[:max_tweets])} data fallback X.")
    return fallback_tweets[:max_tweets]

def save_scraped_data_to_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    """Menyimpan data hasil scraping dan prediksi ke file CSV."""
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False, encoding='utf-8')
    print(f"Data berhasil disimpan ke {filepath}")
