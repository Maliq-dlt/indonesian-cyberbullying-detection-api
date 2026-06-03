"""
Verifikasi file dari fresh clone — ini PERSIS apa yang akan diterima siapa pun yang clone repo.
"""
from pathlib import Path
import os

clone_dir = "verify_clone"
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

print(f"=== Verifikasi Fresh Clone ({clone_dir}) ===\n")

for f in files:
    p = Path(clone_dir) / f
    if not p.exists():
        print(f"  NOT FOUND: {f}")
        continue
    
    raw = p.read_bytes()
    text_lines = len(raw.split(b'\n'))
    crlf = raw.count(b'\r\n')
    lf_only = raw.count(b'\n') - crlf
    cr_only = raw.count(b'\r') - crlf
    
    # Show first 2 lines
    first_lines = raw.split(b'\n')[:3]
    
    status = "OK" if text_lines > 1 else "FATAL"
    print(f"  [{status}] {f}: {text_lines} lines | LF={lf_only} CRLF={crlf} CR={cr_only} | {len(raw)} bytes")
    for i, line in enumerate(first_lines):
        print(f"         line {i+1}: {line[:100]}")

# Also check if .gitattributes exists
ga = Path(clone_dir) / ".gitattributes"
print(f"\n  .gitattributes exists: {ga.exists()}")
if ga.exists():
    print(f"  Content:\n{ga.read_text()}")
