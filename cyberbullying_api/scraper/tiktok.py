import re
import json
import hashlib
import urllib.parse
import os
import asyncio
from typing import List, Tuple
from datetime import datetime

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    async_playwright = None  # type: ignore
    PLAYWRIGHT_AVAILABLE = False

from scraper.templates import generate_dynamic_comments

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BROWSER_PROFILE_DIR = os.path.join(BASE_DIR, os.pardir, "tiktok_browser_profile")


def extract_tiktok_id(url: str) -> str:
    """Mengekstrak ID video dari URL TikTok."""
    match = re.search(r'/video/(\d+)', url)
    if match:
        return match.group(1)
    return ""


def clean_text(value) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.replace("\n", " ").split()).strip()


def get_first_str(data: dict, keys: list) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return clean_text(value)
    return ""


def looks_like_comment(item: dict) -> bool:
    """Mendeteksi apakah sebuah dict terlihat seperti objek komentar TikTok."""
    if not isinstance(item, dict):
        return False

    text = get_first_str(item, ["text", "comment", "content", "comment_text"])
    if not text:
        return False

    comment_signals = [
        "cid", "comment_id", "id", "user", "author",
        "digg_count", "like_count", "reply_comment_total",
        "reply_count", "create_time",
    ]
    return any(key in item for key in comment_signals)


def find_comment_objects(obj, results: list):
    """Rekursif mencari objek komentar di dalam struktur JSON."""
    if isinstance(obj, dict):
        if looks_like_comment(obj):
            results.append(obj)
            return
        for value in obj.values():
            find_comment_objects(value, results)
    elif isinstance(obj, list):
        for item in obj:
            find_comment_objects(item, results)


def normalize_comment(raw: dict, video_url: str, video_id: str) -> dict:
    """Normalisasi objek komentar mentah menjadi format standar."""
    user = raw.get("user") or raw.get("author") or {}
    if not isinstance(user, dict):
        user = {}

    comment_id = raw.get("cid") or raw.get("comment_id") or raw.get("id") or ""
    text = get_first_str(raw, ["text", "comment", "content", "comment_text"])

    username = (
        user.get("unique_id") or user.get("uniqueId")
        or user.get("username") or raw.get("unique_id") or ""
    )
    nickname = (
        user.get("nickname") or user.get("nickName")
        or raw.get("nickname") or ""
    )

    username = clean_text(str(username))
    nickname = clean_text(str(nickname))

    like_count = raw.get("digg_count") or raw.get("like_count") or raw.get("likes") or 0
    reply_count = raw.get("reply_comment_total") or raw.get("reply_count") or raw.get("replies") or 0
    create_time = raw.get("create_time") or raw.get("createTime") or ""

    return {
        "video_id": video_id,
        "comment_id": str(comment_id),
        "username": username,
        "nickname": nickname,
        "comment": text,
        "like_count": like_count,
        "reply_count": reply_count,
        "create_time": create_time,
        "video_url": video_url,
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


async def close_common_popups(page):
    """Menutup popup umum TikTok (cookie consent, login prompt, dll)."""
    selectors = [
        'button[aria-label="Close"]',
        'button[aria-label="Tutup"]',
        'button:has-text("Not now")',
        'button:has-text("Nanti saja")',
        'button:has-text("Accept all")',
        'button:has-text("Terima semua")',
        'button:has-text("Allow all")',
        'button:has-text("Izinkan semua")',
    ]
    for selector in selectors:
        try:
            btn = page.locator(selector).first
            if await btn.count() > 0 and await btn.is_visible(timeout=1200):
                await btn.click(timeout=1500)
                await page.wait_for_timeout(1000)
        except Exception:
            pass


async def auto_open_comment_panel(page):
    """Membuka panel komentar otomatis dengan klik tombol komentar."""
    await page.wait_for_timeout(3000)
    await close_common_popups(page)

    direct_selectors = [
        '[data-e2e="comment-icon"]',
        '[data-e2e="browse-comment"]',
        'button:has([data-e2e="comment-icon"])',
        'button[aria-label*="comment" i]',
        'button[aria-label*="komentar" i]',
        'div[role="button"][aria-label*="comment" i]',
        'div[role="button"][aria-label*="komentar" i]',
    ]

    for selector in direct_selectors:
        try:
            item = page.locator(selector).first
            if await item.count() > 0 and await item.is_visible(timeout=1500):
                await item.click(timeout=3000)
                await page.wait_for_timeout(4000)
                return True
        except Exception:
            pass

    # Fallback: cari elemen yang mengandung kata comment/komentar via JS
    try:
        clicked = await page.evaluate("""
            () => {
                const keywords = ["comment", "comments", "komentar"];
                const elements = Array.from(document.querySelectorAll(
                    'button, div[role="button"], span, div, a, [aria-label]'
                ));
                for (const el of elements) {
                    const text = ((el.innerText || el.textContent || "") + " " + (el.getAttribute("aria-label") || "")).toLowerCase();
                    if (keywords.some(k => text.includes(k))) {
                        const target = el.closest('button, div[role="button"], a') || el;
                        const rect = target.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            target.click();
                            return true;
                        }
                    }
                }
                return false;
            }
        """)
        if clicked:
            await page.wait_for_timeout(4000)
            return True
    except Exception:
        pass

    return False


async def smart_scroll_comment_panel(page):
    """Scroll container komentar yang benar, fallback ke mouse wheel."""
    try:
        scrolled = await page.evaluate("""
            () => {
                const elements = Array.from(document.querySelectorAll('div, section, aside, main'));
                const candidates = elements
                    .map(el => {
                        const style = window.getComputedStyle(el);
                        const rect = el.getBoundingClientRect();
                        const text = (el.innerText || "").toLowerCase();
                        const isScrollable =
                            el.scrollHeight > el.clientHeight + 80 &&
                            rect.height > 180 &&
                            rect.width > 220;
                        let score = 0;
                        if (text.includes("reply")) score += 4;
                        if (text.includes("balas")) score += 4;
                        if (text.includes("like")) score += 2;
                        if (text.includes("suka")) score += 2;
                        if (text.includes("comment")) score += 5;
                        if (text.includes("komentar")) score += 5;
                        if (rect.left > window.innerWidth * 0.35) score += 3;
                        if (rect.height > window.innerHeight * 0.95) score -= 2;
                        return { el, score, scrollHeight: el.scrollHeight, clientHeight: el.clientHeight };
                    })
                    .filter(x => x.score > 0 && x.scrollHeight > x.clientHeight)
                    .sort((a, b) => {
                        if (b.score !== a.score) return b.score - a.score;
                        return b.scrollHeight - a.scrollHeight;
                    });
                if (candidates.length > 0) {
                    const target = candidates[0].el;
                    target.scrollTop += Math.max(700, target.clientHeight * 0.85);
                    target.dispatchEvent(new Event("scroll", { bubbles: true }));
                    return true;
                }
                return false;
            }
        """)

        # Tambahan mouse wheel di area kanan agar request komentar terpancing
        await page.mouse.move(1100, 500)
        await page.mouse.wheel(0, 2200)
        await page.keyboard.press("PageDown")
        return scrolled

    except Exception:
        await page.mouse.move(1100, 500)
        await page.mouse.wheel(0, 2200)
        return False


async def scrape_tiktok_comments_playwright(url: str, max_comments: int = 20) -> List[str]:
    """
    Mengikis komentar TikTok menggunakan Playwright persistent context
    dan network response interception.
    """
    if not PLAYWRIGHT_AVAILABLE or async_playwright is None:
        print("Warning: Playwright tidak terpasang.")
        return []

    video_id = extract_tiktok_id(url)
    comments = []
    seen = set()
    max_scroll = min(max(max_comments // 2, 15), 60)

    # Pastikan direktori browser profile ada
    os.makedirs(BROWSER_PROFILE_DIR, exist_ok=True)

    try:
        async with async_playwright() as p:
            headless_mode = os.getenv("TIKTOK_HEADLESS", "True").lower() == "true"

            chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
            if not os.path.exists(chrome_path):
                chrome_path = None

            browser_context = await p.chromium.launch_persistent_context(
                user_data_dir=BROWSER_PROFILE_DIR,
                headless=headless_mode,
                executable_path=chrome_path,
                ignore_default_args=["--enable-automation"],
                args=[
                    "--disable-blink-features=AutomationControlled",
                ],
                viewport={"width": 1536, "height": 900},
                locale="id-ID",
            )

            # Inject script to bypass webdriver detection
            await browser_context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            page = await browser_context.new_page()

            def handle_response(response):
                """Intercept network responses yang berisi data komentar."""
                resp_url = response.url.lower()
                is_comment_response = (
                    "comment" in resp_url
                    and ("list" in resp_url or "reply" in resp_url
                         or "item" in resp_url or "detail" in resp_url)
                )
                if not is_comment_response:
                    return

                async def process_response():
                    try:
                        data = await response.json()
                    except Exception:
                        return

                    raw_comments = []
                    find_comment_objects(data, raw_comments)

                    for raw in raw_comments:
                        normalized = normalize_comment(
                            raw=raw,
                            video_url=url,
                            video_id=video_id,
                        )
                        text = normalized["comment"]
                        comment_id = normalized["comment_id"]

                        if not text:
                            continue

                        key = comment_id if comment_id else f'{normalized["username"]}|{text}'
                        if key in seen:
                            continue

                        seen.add(key)
                        comments.append(text)
                        print(f'  [Komentar #{len(comments)}] {normalized["username"]}: {text[:80]}')

                asyncio.ensure_future(process_response())

            page.on("response", handle_response)

            print(f"Membuka halaman video TikTok: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=90000)
            await page.wait_for_timeout(6000)

            await close_common_popups(page)

            print("Mencoba membuka panel komentar otomatis...")
            opened = await auto_open_comment_panel(page)
            if opened:
                print("Panel komentar berhasil diklik/dibuka.")
            else:
                print("Panel komentar tidak terdeteksi, lanjut mencoba scroll otomatis.")

            await page.wait_for_timeout(5000)

            # Scroll loop untuk memancing lazy loading komentar
            last_count = 0
            stagnant_round = 0

            for i in range(max_scroll):
                if len(comments) >= max_comments:
                    break

                await smart_scroll_comment_panel(page)
                await page.wait_for_timeout(2800)

                print(f"  Scroll {i + 1}/{max_scroll} | komentar terkumpul: {len(comments)}")

                if len(comments) == last_count:
                    stagnant_round += 1
                else:
                    stagnant_round = 0
                last_count = len(comments)

                if stagnant_round >= 8:
                    print("Tidak ada tambahan komentar setelah beberapa scroll. Berhenti.")
                    break

            await browser_context.close()

    except Exception as e:
        print(f"Error scraping TikTok via Playwright: {e}")

    return comments[:max_comments]


async def scrape_tiktok_comments(url_or_id: str, max_comments: int = 20) -> Tuple[List[str], bool]:
    """
    Melakukan scraping komentar dari video TikTok secara riil menggunakan
    Playwright persistent context + network interception (utama),
    lalu generator tiruan dinamis jika gagal.
    """
    print(f"Memulai scraping komentar TikTok untuk: {url_or_id}")

    url = url_or_id
    if not url.startswith("http"):
        if url_or_id.isdigit():
            url = f"https://www.tiktok.com/@placeholder/video/{url_or_id}"
        else:
            print(f"Mencari video TikTok terpopuler untuk kata kunci: '{url_or_id}'")
            search_url = f"https://www.tiktok.com/search/video?q={urllib.parse.quote(url_or_id)}"
            url = search_url

    # Coba Opsi Utama: Playwright dengan persistent context + network interception
    if PLAYWRIGHT_AVAILABLE:
        comments = await scrape_tiktok_comments_playwright(url, max_comments)
        if comments:
            print(f"Sukses mendapatkan {len(comments)} komentar asli dari TikTok!")
            return comments, True

    # Fallback ke generator dinamis jika semuanya gagal
    print("Gagal mendapatkan komentar asli. Menggunakan fallback template.")
    return generate_dynamic_comments(url_or_id, max_comments), False
