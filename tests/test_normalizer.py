from cyberbullying_api.normalizer import init_slang_map, normalize_text
import os

def test_normalize_text():
    # Inisialisasi slang map jika file tersedia
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alay_path = os.path.join(base_dir, "dataset", "ds_1", "new_kamusalay.csv")
    singkatan_path = os.path.join(base_dir, "dataset", "ds_2", "kamus_singkatan.csv")
    
    if os.path.exists(alay_path) and os.path.exists(singkatan_path):
        init_slang_map(alay_path, singkatan_path)
    
    # Test leetspeak replacement
    res = normalize_text("m4t1 lu anj1ng")
    assert "mati" in res["spaced"]
    assert "kamu" in res["spaced"]
    
    # Test lowercase
    res2 = normalize_text("GOBLOK")
    assert res2["spaced"] == "goblok"
