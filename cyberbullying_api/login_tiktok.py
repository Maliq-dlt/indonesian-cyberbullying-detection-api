import asyncio
import contextlib
import os
import sys

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Error: Playwright tidak terinstal. Pastikan untuk menjalankan pip install playwright.")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BROWSER_PROFILE_DIR = os.path.join(BASE_DIR, "tiktok_browser_profile")


def get_chrome_path():
    paths = [
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    ]
    # Tambahkan path AppData lokal jika ada
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        paths.append(os.path.join(local_app_data, "Google", "Chrome", "Application", "chrome.exe"))

    for p in paths:
        if os.path.exists(p):
            return p
    return None


async def main():
    print("=" * 60)
    print("TikTok Interactive Session Login Utility")
    print("=" * 60)
    print("Skrip ini membantu Anda login ke TikTok untuk menyimpan sesi pencarian.")
    print("Anda dapat login menggunakan Google, QR code, nomor telepon, atau metode lainnya.")
    print("Setelah login berhasil, sesi akan otomatis tersimpan di browser profile.")
    print("-" * 60)

    os.makedirs(BROWSER_PROFILE_DIR, exist_ok=True)

    chrome_path = get_chrome_path()

    print("Pilih Metode Login:")
    if chrome_path:
        print("1. Chrome Mode Normal (Direkomendasikan - Bypass Blokir Google Login)")
        print("2. Playwright Mode (Otomatisasi Standar)")
        try:
            choice = input("Pilih metode (1/2) [Default: 1]: ").strip()
        except (KeyboardInterrupt, EOFError):
            choice = "1"
        if not choice:
            choice = "1"
    else:
        print("Google Chrome tidak terdeteksi di lokasi standar Windows.")
        print("Menggunakan Playwright Mode secara default...")
        choice = "2"

    print("-" * 60)

    if choice == "1" and chrome_path:
        print("Membuka Google Chrome secara normal...")
        print("Silakan lakukan login di jendela browser Chrome yang baru dibuka.")
        print("PENTING: Jangan tutup jendela Chrome tersebut sebelum Anda sukses masuk ke TikTok.")
        print("Setelah sukses login, silakan TUTUP jendela Chrome tersebut untuk menyimpan sesi.")
        print("-" * 60)

        # Hapus file SingletonLock jika ada dari sesi sebelumnya agar Chrome tidak bentrok
        lock_file = os.path.join(BROWSER_PROFILE_DIR, "SingletonLock")
        if os.path.exists(lock_file):
            with contextlib.suppress(Exception):
                os.remove(lock_file)

        import subprocess

        # Jalankan Chrome secara independen dengan profil persisten
        cmd = [
            chrome_path,
            f"--user-data-dir={BROWSER_PROFILE_DIR}",
            "--no-first-run",
            "--no-default-browser-check",
            "https://www.tiktok.com/login",
        ]

        # Jalankan proses
        p_chrome = subprocess.Popen(cmd)
        print("Menunggu jendela Chrome ditutup oleh Anda...")

        # Tunggu hingga selesai
        while p_chrome.poll() is None:
            await asyncio.sleep(1)

        print("\nGoogle Chrome ditutup. Memverifikasi status login dengan Playwright...")

        # Verifikasi cookie dengan Playwright secara headless
        async with async_playwright() as p:
            try:
                browser_context = await p.chromium.launch_persistent_context(
                    user_data_dir=BROWSER_PROFILE_DIR,
                    headless=True,
                    executable_path=chrome_path,
                )
                cookies = await browser_context.cookies()
                has_session = any(c["name"] in ("sessionid", "sessionid_ss") for c in cookies)
                await browser_context.close()

                if has_session:
                    print("\n[SUKSES] Login berhasil dideteksi!")
                    print(f"[INFO] Sesi login tersimpan otomatis di: {BROWSER_PROFILE_DIR}")
                    print("Scraper dapat langsung menggunakan sesi ini.")
                else:
                    print("\n[PERINGATAN] Sesi login TikTok tidak terdeteksi.")
                    print("Pastikan Anda sudah berhasil masuk/login di halaman TikTok sebelum menutup browser Chrome.")
            except Exception as e:
                print(f"\nGagal melakukan verifikasi otomatis: {e}")
                print(f"Silakan periksa apakah sesi tersimpan di folder profile: {BROWSER_PROFILE_DIR}")
    else:
        # Playwright Mode (Standard)
        print("Membuka browser Chromium dengan profil persisten via Playwright...")
        print("Silakan lakukan login akun TikTok Anda secara manual pada jendela browser.")
        print("Jika Google memblokir login Anda, silakan gunakan metode QR code atau email/password biasa.")
        print("-" * 60)

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
                has_session = any(c["name"] in ("sessionid", "sessionid_ss") for c in cookies)

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
