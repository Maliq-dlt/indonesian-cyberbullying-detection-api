"""
Verifikasi bahwa git blob yang akan diterima clone/pull benar-benar multiline.
Ini membaca langsung dari git object store, bukan dari working directory.
"""
import subprocess

files = [
    "cyberbullying_api/main.py",
    "cyberbullying_api/models.py",
    "cyberbullying_api/normalizer.py",
    "cyberbullying_api/requirements.txt",
    "cyberbullying_api/Dockerfile",
    "cyberbullying_api/retrain.py",
    "cyberbullying_api/train_and_export.py",
    "cyberbullying_api/tests/test_api.py",
    "cyberbullying_api/classifier/__init__.py",
    "cyberbullying_api/classifier/database.py",
    "cyberbullying_api/classifier/llm.py",
    "cyberbullying_api/classifier/predictor.py",
    "cyberbullying_api/scraper/__init__.py",
    "cyberbullying_api/scraper/templates.py",
    "cyberbullying_api/scraper/tiktok.py",
    "cyberbullying_api/scraper/twitter.py",
    "cyberbullying_api/ui/__init__.py",
    "cyberbullying_api/ui/components.py",
    "cyberbullying_api/ui/handlers.py",
    "cyberbullying_api/training/__init__.py",
    "cyberbullying_api/training/augmentation.py",
    "cyberbullying_api/training/data_loader.py",
]

print("=== Verifikasi Git Blob (apa yang dikirim ke GitHub) ===\n")

all_ok = True
for f in files:
    result = subprocess.run(
        ["git", "cat-file", "-p", f"HEAD:{f}"],
        capture_output=True
    )
    data = result.stdout
    if not data:
        print(f"  ERROR: {f} - tidak ditemukan di HEAD")
        all_ok = False
        continue
    
    lines = data.count(b'\n')
    crlf = data.count(b'\r\n')
    lf_only = lines - crlf
    cr_only = data.count(b'\r') - crlf
    has_bom = data[:3] == b'\xef\xbb\xbf'
    
    status = "OK" if lines > 1 and cr_only == 0 else "PROBLEM"
    if status == "PROBLEM":
        all_ok = False
    
    print(f"  [{status}] {f}: {lines} lines | LF={lf_only} CRLF={crlf} CR={cr_only} BOM={has_bom} | {len(data)} bytes")

print()
if all_ok:
    print("RESULT: Semua git blob multiline dan valid.")
else:
    print("RESULT: Ada masalah! Lihat baris [PROBLEM] di atas.")
