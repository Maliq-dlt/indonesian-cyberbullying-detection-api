from pathlib import Path

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

for f in files:
    p = Path(f)
    if p.exists():
        raw = p.read_bytes()
        text_lines = p.read_text(encoding="utf-8").splitlines()
        cr_only = raw.count(b'\r') - raw.count(b'\r\n')
        crlf = raw.count(b'\r\n')
        lf_only = raw.count(b'\n') - raw.count(b'\r\n')
        print(f"{f}: {len(text_lines)} lines | LF={lf_only} CRLF={crlf} CR_only={cr_only} | {len(raw)} bytes")
    else:
        print(f"{f}: NOT FOUND")
