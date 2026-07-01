#!/usr/bin/env python
"""
rotate_key.py
~~~~~~~~~~~~~
Utilitas untuk merotasi kunci enkripsi data komentar pada database PostgreSQL & SQLite.
Mendekripsi data lama menggunakan kunci Fernet lama, dan mengenkripsinya kembali dengan kunci Fernet baru.
Semua pesan log menggunakan Bahasa Indonesia.
"""

import argparse
import asyncio
import base64
import hashlib
import os
import sqlite3

from cryptography.fernet import Fernet


def derive_fernet_key(api_key: str) -> bytes:
    # Menggunakan logika turunan kunci yang persis sama dengan database.py
    key_source = api_key.encode("utf-8")
    return base64.urlsafe_b64encode(hashlib.sha256(key_source).digest())

def get_fernet_cipher(api_key: str) -> Fernet:
    return Fernet(derive_fernet_key(api_key))

async def rotate_pg_database(old_key: str, new_key: str, pg_url: str):
    try:
        import asyncpg
    except ImportError:
        print("[PG] asyncpg tidak terinstal. Melewati rotasi PostgreSQL.")
        return

    print("[PG] Menghubungkan ke PostgreSQL...")
    try:
        conn = await asyncpg.connect(pg_url)
    except Exception as e:
        print(f"[PG] Gagal terhubung ke PostgreSQL: {e}")
        return

    try:
        # Ambil semua data dari classification_memory
        rows = await conn.fetch("SELECT text_hash, encrypted_text FROM classification_memory")
        if not rows:
            print("[PG] Tidak ada data ditemukan untuk dirotasi.")
            await conn.close()
            return

        print(f"[PG] Ditemukan {len(rows)} baris data. Memulai rotasi kunci...")
        old_cipher = get_fernet_cipher(old_key)
        new_cipher = get_fernet_cipher(new_key)

        success_count = 0
        error_count = 0

        for r in rows:
            text_hash = r["text_hash"]
            enc_text = r["encrypted_text"]
            if not enc_text:
                continue

            try:
                # Dekripsi dengan kunci lama
                decrypted_bytes = old_cipher.decrypt(enc_text.encode("utf-8"))

                # Enkripsi dengan kunci baru
                new_enc_text = new_cipher.encrypt(decrypted_bytes).decode("utf-8")

                # Update ke database
                await conn.execute(
                    "UPDATE classification_memory SET encrypted_text = $1 WHERE text_hash = $2",
                    new_enc_text, text_hash
                )
                success_count += 1
            except Exception as row_err:
                print(f"[PG] Gagal memproses baris dengan hash {text_hash}: {row_err}")
                error_count += 1

        print(f"[PG] Rotasi selesai. Sukses: {success_count}, Gagal: {error_count}")
    except Exception as e:
        print(f"[PG] Terjadi kesalahan selama rotasi PostgreSQL: {e}")
    finally:
        await conn.close()

def rotate_sqlite_database(old_key: str, new_key: str, db_path: str):
    if not os.path.exists(db_path):
        print(f"[SQLite] File database tidak ditemukan di: {db_path}")
        return

    print(f"[SQLite] Menghubungkan ke database {db_path}...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    except Exception as e:
        print(f"[SQLite] Gagal terhubung ke SQLite: {e}")
        return

    try:
        cursor.execute("SELECT text_hash, encrypted_text FROM classification_memory")
        rows = cursor.fetchall()
        if not rows:
            print("[SQLite] Tidak ada data ditemukan untuk dirotasi.")
            conn.close()
            return

        print(f"[SQLite] Ditemukan {len(rows)} baris data. Memulai rotasi kunci...")
        old_cipher = get_fernet_cipher(old_key)
        new_cipher = get_fernet_cipher(new_key)

        success_count = 0
        error_count = 0

        for r in rows:
            text_hash = r[0]
            enc_text = r[1]
            if not enc_text:
                continue

            try:
                # Dekripsi dengan kunci lama
                decrypted_bytes = old_cipher.decrypt(enc_text.encode("utf-8"))

                # Enkripsi dengan kunci baru
                new_enc_text = new_cipher.encrypt(decrypted_bytes).decode("utf-8")

                # Update ke database
                cursor.execute(
                    "UPDATE classification_memory SET encrypted_text = ? WHERE text_hash = ?",
                    (new_enc_text, text_hash)
                )
                success_count += 1
            except Exception as row_err:
                print(f"[SQLite] Gagal memproses baris dengan hash {text_hash}: {row_err}")
                error_count += 1

        conn.commit()
        print(f"[SQLite] Rotasi selesai. Sukses: {success_count}, Gagal: {error_count}")
    except Exception as e:
        print(f"[SQLite] Terjadi kesalahan selama rotasi SQLite: {e}")
    finally:
        conn.close()

async def clear_redis_cache(redis_url: str):
    try:
        import redis.asyncio as redis
    except ImportError:
        print("[Redis] redis-py tidak terinstal. Melewati pembersihan cache Redis.")
        return

    print("[Redis] Menghubungkan ke Redis...")
    try:
        r = redis.from_url(redis_url, decode_responses=True)
        # Ambil keys cache memori dan cache opencode_go
        keys = await r.keys("mem:*") + await r.keys("cloud_llm:*")
        if keys:
            await r.delete(*keys)
            print(f"[Redis] Berhasil menghapus {len(keys)} cache keys lama yang terpengaruh rotasi.")
        else:
            print("[Redis] Tidak ada cache keys lama yang ditemukan.")
        await r.close()
    except Exception as e:
        print(f"[Redis] Gagal membersihkan cache Redis: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Rotasi kunci enkripsi data komentar BullyGuard ID.")
    parser.add_argument("--old-key", required=True, help="Kunci API lama / API_KEY yang digunakan saat ini.")
    parser.add_argument("--new-key", required=True, help="Kunci API baru / API_KEY yang akan digunakan.")

    args = parser.parse_args()

    # Load konfigurasi dari variabel lingkungan
    pg_url = os.getenv("PG_URL", "postgresql://cyber_user:cyber_password@127.0.0.1:5432/cyberbullying_db")
    redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    sqlite_db_path = os.path.join(base_dir, "cache", "cloud_llm_cache.db")

    print("\n=== Memulai Utilitas Rotasi Kunci Enkripsi BullyGuard ID ===\n")

    # 1. Jalankan rotasi SQLite
    rotate_sqlite_database(args.old_key, args.new_key, sqlite_db_path)

    # 2. Jalankan rotasi PostgreSQL
    await rotate_pg_database(args.old_key, args.new_key, pg_url)

    # 3. Bersihkan Redis cache agar terhindar dari ketidakcocokan keputusan
    await clear_redis_cache(redis_url)

    print("\n=== Proses Rotasi Kunci Selesai ===\n")
    print("PENTING: Jangan lupa untuk mengubah nilai variabel lingkungan API_KEY pada file .env atau konfigurasi server Anda ke kunci yang baru.")

if __name__ == "__main__":
    asyncio.run(main())
