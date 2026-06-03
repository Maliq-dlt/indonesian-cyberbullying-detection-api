import re
import json
import urllib.parse
import httpx
import html
import pandas as pd
import os
import time
import asyncio
from typing import List, Dict, Any, Tuple

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    async_playwright = None  # type: ignore
    PLAYWRIGHT_AVAILABLE = False

from scraper.templates import NITTER_INSTANCES, generate_dynamic_comments

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_X_PATH = os.path.join(BASE_DIR, os.pardir, "cookies_x.json")


async def scrape_x_tweets_playwright(query: str, max_tweets: int = 20) -> List[str]:
    """Mengikis tweet X menggunakan Playwright + Session Cookies."""
    if not PLAYWRIGHT_AVAILABLE or async_playwright is None:
        print("Warning: Playwright tidak terpasang. Menjalankan fallback.")
        return []
    if not os.path.exists(COOKIES_X_PATH):
        print(f"Warning: Berkas {COOKIES_X_PATH} tidak ditemukan. Silakan tambahkan cookie untuk scraping riil.")
        return []

    search_query = f"{query} lang:id"
    search_url = f"https://x.com/search?q={urllib.parse.quote(search_query)}&f=live"
    tweets = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            with open(COOKIES_X_PATH, "r") as f:
                cookies = json.load(f)
                await context.add_cookies(cookies)
                
            page = await context.new_page()
            print(f"Membuka halaman pencarian X: {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
            
            try:
                await page.wait_for_selector("[data-testid='tweetText']", timeout=7000)
            except Exception:
                pass
                
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(1.2)
                
            elements = await page.query_selector_all("[data-testid='tweetText']")
            for el in elements:
                text = (await el.inner_text()).strip()
                if text and text not in tweets:
                    text_clean = " ".join(text.split())
                    tweets.append(text_clean)
                    if len(tweets) >= max_tweets:
                        break
            await browser.close()
    except Exception as e:
        print(f"Error scraping X via Playwright: {e}")
    return tweets

async def scrape_x_tweets(query: str, max_tweets: int = 20) -> Tuple[List[str], bool]:
    """
    Melakukan scraping tweet dari X secara riil menggunakan Playwright (utama)
    atau Nitter instances (fallback), lalu generator tiruan dinamis jika semuanya gagal.
    """
    print(f"Memulai scraping tweet X untuk query: {query}")
    
    # Coba Opsi Utama: Playwright dengan Session Cookies
    if PLAYWRIGHT_AVAILABLE and os.path.exists(COOKIES_X_PATH):
        tweets = await scrape_x_tweets_playwright(query, max_tweets)
        if tweets:
            print(f"Sukses mendapatkan {len(tweets)} tweet asli dari X via Playwright!")
            return tweets, True

    # Coba Opsi Cadangan: Scraping gratis via Nitter instances
    tweets = []
    encoded_query = urllib.parse.quote(query)
    for instance in NITTER_INSTANCES:
        url = f"{instance}/search?f=tweets&q={encoded_query}"
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            async with httpx.AsyncClient(timeout=6.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    html_content = response.text
                    matches = re.findall(r'<div class="tweet-content[^>]*>(.*?)</div>', html_content, re.DOTALL)
                    for m in matches:
                        clean_tweet = re.sub(r'<[^>]+>', '', m).strip()
                        clean_tweet = html.unescape(clean_tweet)
                        if clean_tweet and clean_tweet not in tweets:
                            tweets.append(clean_tweet)
                            if len(tweets) >= max_tweets:
                                break
                    if tweets:
                        print(f"Sukses mendapatkan {len(tweets)} tweet asli dari X via {instance} (Nitter)!")
                        return tweets, True
        except Exception as e:
            print(f"Warning: Gagal scraping X via {instance}: {e}")
            
    # Fallback ke generator dinamis jika semuanya gagal
    return generate_dynamic_comments(query, max_tweets), False


def save_scraped_data_to_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    """Menyimpan data hasil scraping dan prediksi ke file CSV."""
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False, encoding='utf-8')
    print(f"Data berhasil disimpan ke {filepath}")
