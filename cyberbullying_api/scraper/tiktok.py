import re
import json
import urllib.parse
import httpx
import os
import time
import asyncio
from typing import List, Tuple


try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    async_playwright = None  # type: ignore
    PLAYWRIGHT_AVAILABLE = False

from scraper.templates import generate_dynamic_comments

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_TIKTOK_PATH = os.path.join(BASE_DIR, os.pardir, "cookies_tiktok.json")

def extract_tiktok_id(url: str) -> str:
    """Mengekstrak ID video dari URL TikTok."""
    match = re.search(r'/video/(\d+)', url)
    if match:
        return match.group(1)
    return ""

async def get_first_tiktok_video_from_search(search_url: str) -> str:
    """Mencari video pertama di TikTok berdasarkan halaman hasil pencarian."""
    if not PLAYWRIGHT_AVAILABLE or async_playwright is None:
        return ""
    video_url = ""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            # Muat cookie jika ada
            if os.path.exists(COOKIES_TIKTOK_PATH):
                with open(COOKIES_TIKTOK_PATH, "r") as f:
                    cookies = json.load(f)
                    await context.add_cookies(cookies)
            page = await context.new_page()
            await page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_selector("a[href*='/video/']", timeout=7000)
            links = await page.query_selector_all("a[href*='/video/']")
            for link in links:
                href = await link.get_attribute("href")
                if href and "/video/" in href:
                    # Pastikan URL absolut, bukan path relatif
                    if href.startswith("/"):
                        href = "https://www.tiktok.com" + href
                    video_url = href
                    break
            await browser.close()
    except Exception as e:
        print(f"Error mencari video TikTok via search: {e}")
    return video_url


async def scrape_tiktok_comments_playwright(url_or_id: str, max_comments: int = 20) -> List[str]:
    """Mengikis komentar TikTok menggunakan Playwright + Session Cookies."""
    if not PLAYWRIGHT_AVAILABLE or async_playwright is None:
        print("Warning: Playwright tidak terpasang. Menjalankan fallback.")
        return []
    if not os.path.exists(COOKIES_TIKTOK_PATH):
        print(f"Warning: Berkas {COOKIES_TIKTOK_PATH} tidak ditemukan. Silakan tambahkan cookie untuk scraping riil.")
        return []

    url = url_or_id
    if not url.startswith("http"):
        # Jika bukan tautan HTTP, anggap ini kata kunci pencarian
        # Tapi jika berupa digit saja, anggap ID video
        if url_or_id.isdigit():
            url = f"https://www.tiktok.com/@placeholder/video/{url_or_id}"
        else:
            print(f"Mencari video TikTok terpopuler untuk kata kunci: '{url_or_id}'")
            search_url = f"https://www.tiktok.com/search/video?q={urllib.parse.quote(url_or_id)}"
            url = await get_first_tiktok_video_from_search(search_url)
            if not url:
                print("Warning: Tidak menemukan video untuk kata kunci tersebut.")
                return []

    comments = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            with open(COOKIES_TIKTOK_PATH, "r") as f:
                cookies = json.load(f)
                await context.add_cookies(cookies)
                
            page = await context.new_page()
            
            # FITUR BARU: Mengambil video FYP teratas
            if url.lower() == "fyp":
                print("Membuka halaman FYP TikTok untuk mencari video trending...")
                await page.goto("https://www.tiktok.com/foryou", wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_selector("a[href*='/video/']", timeout=10000)
                links = await page.query_selector_all("a[href*='/video/']")
                if links:
                    url_attr = await links[0].get_attribute("href")
                    if url_attr:
                        url = url_attr
                        print(f"Video FYP teratas ditemukan: {url}")
                    else:
                        print("Gagal menemukan href video FYP, membatalkan scraping.")
                        await browser.close()
                        return comments
                else:
                    print("Gagal menemukan video FYP, membatalkan scraping.")
                    await browser.close()
                    return comments

            print(f"Membuka halaman video TikTok: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            # Tunggu elemen komentar dimuat
            try:
                await page.wait_for_selector("[data-e2e='comment-text']", timeout=7000)
            except Exception:
                pass
                
            # Scroll beberapa kali untuk lazy loading komentar
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(1.2)
                
            elements = await page.query_selector_all("[data-e2e='comment-text']")
            for el in elements:
                text = (await el.inner_text()).strip()
                # Menyaring komentar stiker/gambar (inner_text-nya kosong) dan memfilter duplikat
                if text and text not in comments:
                    comments.append(text)
                    if len(comments) >= max_comments:
                        break
            await browser.close()
    except Exception as e:
        print(f"Error scraping TikTok via Playwright: {e}")
    return comments

async def scrape_tiktok_comments(url_or_id: str, max_comments: int = 20) -> Tuple[List[str], bool]:
    """
    Melakukan scraping komentar dari video TikTok secara riil menggunakan Playwright (utama)
    atau rehidrasi script (fallback), lalu generator tiruan dinamis jika semuanya gagal.
    """
    print(f"Memulai scraping komentar TikTok untuk: {url_or_id}")
    
    # Coba Opsi Utama: Playwright dengan Session Cookies
    if PLAYWRIGHT_AVAILABLE and os.path.exists(COOKIES_TIKTOK_PATH):
        comments = await scrape_tiktok_comments_playwright(url_or_id, max_comments)
        if comments:
            print(f"Sukses mendapatkan {len(comments)} komentar asli dari TikTok via Playwright!")
            return comments, True

    # Coba Opsi Cadangan: HTTP Get rehydration data (hanya jika url)
    if url_or_id.startswith("http"):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
            }
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                response = await client.get(url_or_id, headers=headers)
                if response.status_code == 200:
                    json_matches = re.findall(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', response.text, re.DOTALL)
                    if json_matches:
                        raw_json = json_matches[0].strip()
                        comment_texts = re.findall(r'"text"\s*:\s*"([^"]+)"', raw_json)
                        comments = []
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
                            print(f"Sukses mendapatkan {len(comments)} komentar asli dari TikTok via HTTP Rehydration!")
                            return comments, True
        except Exception as e:
            print(f"Warning: Gagal scraping TikTok secara langsung via HTTP: {e}")

    # Fallback ke generator dinamis jika semuanya gagal
    return generate_dynamic_comments(url_or_id, max_comments), False

