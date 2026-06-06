import asyncio
import os
import sys

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Error: Playwright tidak terinstal. Pastikan untuk menjalankan pip install playwright.")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BROWSER_PROFILE_DIR = os.path.join(BASE_DIR, "tiktok_browser_profile")


async def main():
    print("=" * 60)
    print("TikTok Interactive Session Login Utility")
    print("=" * 60)
    print("Skrip ini akan membuka browser Chromium dengan profil persisten.")
    print("Silakan lakukan login akun TikTok Anda secara manual pada jendela browser.")
    print("Anda dapat login menggunakan Google, QR code, nomor telepon, atau metode lainnya.")
    print("Setelah login berhasil, sesi akan otomatis tersimpan di browser profile.")
    print("Scraper akan menggunakan profil yang sama untuk scraping komentar.")
    print("-" * 60)

    os.makedirs(BROWSER_PROFILE_DIR, exist_ok=True)

    async with async_playwright() as p:
        chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        if not os.path.exists(chrome_path):
            chrome_path = None

        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir=BROWSER_PROFILE_DIR,
            headless=False,
            executable_path=chrome_path,
            ignore_default_args=["--enable-automation"],
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
            viewport={"width": 1280, "height": 800},
            locale="id-ID",
        )

        # Inject script to bypass webdriver detection
        await browser_context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = browser_context.pages[0] if browser_context.pages else await browser_context.new_page()

        print("Membuka halaman login TikTok...")
        await page.goto("https://www.tiktok.com/login", wait_until="domcontentloaded")

        print("\nMenunggu proses login...")
        print("TIPS: Selesaikan Captcha/Puzzle di browser jika muncul.")

        # Loop untuk mendeteksi apakah login berhasil
        logged_in = False
        for attempt in range(300):  # Batas waktu 5 menit
            await asyncio.sleep(1)
            cookies = await browser_context.cookies()

            # Cari cookie 'sessionid' atau 'sessionid_ss' yang menandakan login sukses
            has_session = any(c['name'] in ('sessionid', 'sessionid_ss') for c in cookies)

            # Alternatif: cek jika elemen profil sudah muncul di halaman
            profile_visible = False
            try:
                profile_el = await page.query_selector("[data-e2e='profile-icon']")
                if profile_el:
                    profile_visible = True
            except Exception:
                pass

            if has_session or profile_visible:
                logged_in = True
                print("\n[SUKSES] Login terdeteksi!")
                break

            # Cetak indikator menunggu setiap 15 detik
            if attempt % 15 == 0 and attempt > 0:
                print(f"Masih menunggu login... ({attempt} detik berlalu)")

        if logged_in:
            print(f"\n[INFO] Sesi login tersimpan otomatis di: {BROWSER_PROFILE_DIR}")
            print("Profil ini akan digunakan oleh scraper untuk mengakses TikTok.")
            print("Anda sekarang dapat menutup jendela browser.")

            # Beri waktu sebentar agar sesi tersimpan sempurna
            await asyncio.sleep(3)
        else:
            print("\n[GAGAL] Waktu tunggu habis. Login tidak terdeteksi dalam 5 menit.")

        print("Menutup browser...")
        await browser_context.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProses dibatalkan oleh pengguna.")
