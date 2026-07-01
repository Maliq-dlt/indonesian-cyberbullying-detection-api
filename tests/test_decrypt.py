import pytest
from cyberbullying_api.classifier.db_config import decrypt_text

def test_decrypt_text_corruption():
    # Ordinary unencrypted text should fallback to itself
    assert decrypt_text("halo dunia") == "halo dunia"

    # Encrypted text starting with Fernet header gAAAA but with wrong key should throw ValueError
    with pytest.raises(ValueError, match="Gagal mendekripsi data terenkripsi"):
        decrypt_text("gAAAAB_invalid_ciphertext_fernet")
