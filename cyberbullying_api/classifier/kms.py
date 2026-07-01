import os
import base64
import logging

logger = logging.getLogger("bullyguard")

def get_encryption_key() -> bytes | None:
    """
    Mengambil kunci enkripsi dari KMS eksternal (AWS KMS atau HashiCorp Vault)
    jika dikonfigurasi, jika tidak menggunakan fallback API_KEY dari .env.
    """
    provider = os.getenv("KMS_PROVIDER", "").strip().lower()
    
    # 1. Mock/Simulator untuk testing dan local run
    if provider == "mock" or provider == "vault-mock":
        return b"mock-vault-secret-key-value-12345"
    elif provider == "aws-mock":
        return b"mock-aws-kms-secret-key-value-12345"

    # 2. HashiCorp Vault Provider
    elif provider == "vault":
        vault_addr = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200").strip()
        vault_token = os.getenv("VAULT_TOKEN", "").strip()
        secret_path = os.getenv("VAULT_SECRET_PATH", "secret/data/bullyguard").strip()
        secret_key = os.getenv("VAULT_SECRET_KEY", "encryption_key").strip()
        
        if not vault_token:
            raise ValueError("KMS_PROVIDER='vault' diatur tetapi VAULT_TOKEN kosong.")
            
        try:
            import hvac
            client = hvac.Client(url=vault_addr, token=vault_token)
            try:
                response = client.secrets.kv.v2.read_secret_version(path=secret_path)
                key_data = response['data']['data'][secret_key]
            except Exception:
                response = client.read(secret_path)
                key_data = response['data'][secret_key]
            
            return key_data.encode("utf-8")
        except ImportError:
            logger.warning("hvac library not installed, failed to load key from Vault")
            raise ImportError("Pustaka 'hvac' diperlukan untuk integrasi HashiCorp Vault KMS.")
        except Exception as e:
            logger.error("Failed to fetch key from HashiCorp Vault", extra={"error": str(e)})
            raise

    # 3. AWS KMS Provider
    elif provider == "aws":
        key_id = os.getenv("AWS_KMS_KEY_ID", "").strip()
        if not key_id:
            raise ValueError("KMS_PROVIDER='aws' diatur tetapi AWS_KMS_KEY_ID kosong.")
            
        try:
            import boto3
            kms_client = boto3.client('kms')
            encrypted_key_b64 = os.getenv("AWS_KMS_ENCRYPTED_KEY", "").strip()
            if not encrypted_key_b64:
                # Generate a transient data key using GenerateDataKey
                response = kms_client.generate_data_key(KeyId=key_id, KeySpec='AES_256')
                return response['Plaintext']
            
            ciphertext = base64.b64decode(encrypted_key_b64)
            response = kms_client.decrypt(CiphertextBlob=ciphertext, KeyId=key_id)
            return response['Plaintext']
        except ImportError:
            logger.warning("boto3 library not installed, failed to load key from AWS KMS")
            raise ImportError("Pustaka 'boto3' diperlukan untuk integrasi AWS KMS.")
        except Exception as e:
            logger.error("Failed to fetch key from AWS KMS", extra={"error": str(e)})
            raise

    # 4. Fallback (tidak dikonfigurasi)
    return None
