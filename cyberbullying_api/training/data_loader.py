"""
training/data_loader.py
~~~~~~~~~~~~~~~~~~~~~~~
Dataset-loading and database-ingestion utilities extracted from retrain.py.

Every ``load_*`` helper returns a :class:`~pandas.DataFrame` with exactly
three columns – ``text_clean``, ``is_toxic``, ``is_bully`` – or ``None``
when the source file is missing or cannot be parsed.

The two ``ingest_*`` helpers retrieve new records from scraped CSV files
or from the application's classification-memory database (PostgreSQL with
an automatic SQLite fallback).
"""

from __future__ import annotations

import os
import glob
import sqlite3
import asyncio
from typing import Callable, Optional

import pandas as pd

try:
    import asyncpg  # type: ignore[import-untyped]
except ImportError:
    asyncpg = None  # type: ignore[assignment]

from normalizer import init_slang_map, normalize_text


# ---------------------------------------------------------------------------
# Dataset loaders – each returns a uniform 3-column DataFrame or None
# ---------------------------------------------------------------------------

def load_twitter_dataset(
    path: str,
    clean_fn: Callable[[str], str],
) -> Optional[pd.DataFrame]:
    """Load the Twitter hate-speech CSV (``data.csv``).

    Expected columns in the source file: ``Tweet``, ``Abusive``, ``HS``.

    Parameters
    ----------
    path:
        Absolute path to the CSV file (latin-1 encoded).
    clean_fn:
        A text-normalisation callable applied to every tweet.

    Returns
    -------
    DataFrame | None
        Columns: ``text_clean``, ``is_toxic``, ``is_bully``.
    """
    try:
        df = pd.read_csv(path, encoding="latin-1")
        df = df.dropna(subset=["Tweet"])
        df["text_clean"] = df["Tweet"].apply(clean_fn)
        df["is_toxic"] = df["Abusive"] == 1
        df["is_bully"] = df["HS"] == 1
        return df[["text_clean", "is_toxic", "is_bully"]]
    except Exception as e:
        print(f"Warning: Gagal memuat dataset Twitter ({path}): {e}")
        return None


def load_instagram_dataset(
    path: str,
    clean_fn: Callable[[str], str],
    check_toxic_fn: Callable[[str], bool],
) -> Optional[pd.DataFrame]:
    """Load the Instagram cyberbullying XLSX dataset.

    Expected columns: ``Komentar``, ``Kategori`` (``Bullying`` /
    ``Non-bullying``).

    Parameters
    ----------
    path:
        Absolute path to the ``.xlsx`` file.
    clean_fn:
        A text-normalisation callable.
    check_toxic_fn:
        A callable that returns ``True`` when the normalised text
        contains at least one abusive-lexicon word.

    Returns
    -------
    DataFrame | None
        Columns: ``text_clean``, ``is_toxic``, ``is_bully``.
    """
    if not os.path.exists(path):
        print(f"Informasi: Dataset Instagram tidak ditemukan di {path}, dilewati.")
        return None
    try:
        df = pd.read_excel(path)
        df = df.dropna(subset=["Komentar", "Kategori"])
        df["text_clean"] = df["Komentar"].apply(clean_fn)
        df["is_bully"] = df["Kategori"].map(
            {"Bullying": True, "Non-bullying": False}
        )
        df["is_toxic"] = df["text_clean"].apply(check_toxic_fn)
        return df[["text_clean", "is_toxic", "is_bully"]]
    except Exception as e:
        print(f"Warning: Gagal memuat dataset Instagram ({path}): {e}")
        return None


def load_combined_dataset(
    path: str,
    clean_fn: Callable[[str], str],
    check_toxic_fn: Callable[[str], bool],
) -> Optional[pd.DataFrame]:
    """Load the combined / merged CSV dataset.

    Expected columns: ``String``, ``Label`` (e.g. ``Bullying``,
    ``negatif``, ``negative``).

    Parameters
    ----------
    path:
        Absolute path to the CSV file.
    clean_fn:
        A text-normalisation callable.
    check_toxic_fn:
        A callable that returns ``True`` when the normalised text
        contains at least one abusive-lexicon word.

    Returns
    -------
    DataFrame | None
        Columns: ``text_clean``, ``is_toxic``, ``is_bully``.
    """
    try:
        df = pd.read_csv(path)
        df = df.dropna(subset=["String", "Label"])
        df["text_clean"] = df["String"].apply(clean_fn)
        df["is_bully"] = df["Label"].isin(["Bullying", "negatif", "negative"])
        df["is_toxic"] = df["text_clean"].apply(check_toxic_fn)
        return df[["text_clean", "is_toxic", "is_bully"]]
    except Exception as e:
        print(f"Warning: Gagal memuat dataset kombinasi ({path}): {e}")
        return None


# ---------------------------------------------------------------------------
# Ingestion helpers – pull new labelled data from external sources
# ---------------------------------------------------------------------------

def ingest_scraped_csv(
    base_dir: str,
) -> tuple[list[dict], list[str]]:
    """Read ``classified_*_data.csv`` files produced by the scraper.

    Parameters
    ----------
    base_dir:
        The directory to scan for ``classified_*_data.csv`` files.

    Returns
    -------
    (new_records, file_paths)
        *new_records* is a list of dicts with keys ``String`` and
        ``Label`` (``"Bullying"`` / ``"Non-bullying"``).
        *file_paths* is the list of matched CSV paths (useful for
        post-processing, e.g. renaming after ingestion).
    """
    new_files = glob.glob(os.path.join(base_dir, "classified_*_data.csv"))
    new_records: list[dict] = []

    if not new_files:
        print("Tidak ditemukan berkas data baru (*.csv hasil scraper).")
        return new_records, []

    for file_path in new_files:
        print(f"Membaca data baru dari: {file_path}")
        try:
            df_new = pd.read_csv(file_path)
            if "Teks" in df_new.columns and "Is_Bully" in df_new.columns:
                df_valid = df_new[df_new["Is_Bully"] != "Error"].copy()
                for _idx, row in df_valid.iterrows():
                    raw_text = str(row["Teks"]).strip()
                    is_bully = row["Is_Bully"] == "Ya"
                    label_str = "Bullying" if is_bully else "Non-bullying"
                    if raw_text:
                        new_records.append({
                            "String": raw_text,
                            "Label": label_str,
                        })
            else:
                print(
                    f"Warning: Kolom tidak cocok di {file_path}. "
                    "Memerlukan 'Teks' dan 'Is_Bully'."
                )
        except Exception as e:
            print(f"Error membaca {file_path}: {e}")

    return new_records, new_files


def ingest_database_memory(base_dir: str) -> list[dict]:
    """Retrieve validated records from the classification-memory DB.

    Tries PostgreSQL first (via :pypi:`asyncpg`).  Falls back to a local
    SQLite database at ``<base_dir>/cache/ollama_cache.db`` when
    ``asyncpg`` is unavailable or the connection fails.

    Parameters
    ----------
    base_dir:
        Project base directory (used to locate the SQLite fallback).

    Returns
    -------
    list[dict]
        Each dict has keys ``String`` and ``Label``.
    """
    new_records: list[dict] = []
    pg_url = os.getenv(
        "PG_URL",
        "postgresql://cyber_user:cyber_password@127.0.0.1:5432/cyberbullying_db",
    )
    pg_records_loaded = False

    # --- PostgreSQL attempt ---------------------------------------------------
    if asyncpg is not None:
        print(f"Mencari data baru dari basis data memori PostgreSQL ({pg_url})...")

        async def _fetch_pg() -> list | None:
            if asyncpg is None:
                return None
            try:
                conn = await asyncpg.connect(pg_url)
                rows = await conn.fetch(
                    "SELECT text, is_bully FROM classification_memory "
                    "WHERE is_validated = 1 OR decision_source LIKE 'Tier 3%'"
                )
                await conn.close()
                return rows
            except Exception as e:
                print(f"Warning: Gagal menghubungkan ke PostgreSQL: {e}")
                return None

        try:
            pg_rows = asyncio.run(_fetch_pg())
            if pg_rows is not None:
                for row in pg_rows:
                    raw_text = str(row["text"]).strip()
                    is_bully = bool(row["is_bully"])
                    label_str = "Bullying" if is_bully else "Non-bullying"
                    if raw_text:
                        new_records.append({"String": raw_text, "Label": label_str})
                print(f"Berhasil memuat {len(pg_rows)} data dari PostgreSQL.")
                pg_records_loaded = True
        except Exception as e:
            print(f"Warning: Gagal memproses data dari PostgreSQL: {e}")

    # --- SQLite fallback -------------------------------------------------------
    if not pg_records_loaded:
        print("Mencari data baru dari basis data memori SQLite (classification_memory)...")
        try:
            db_path = os.path.join(base_dir, "cache", "ollama_cache.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path, timeout=10.0)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT text, is_bully FROM classification_memory "
                    "WHERE is_validated = 1 OR decision_source LIKE 'Tier 3%'"
                )
                rows = cursor.fetchall()
                conn.close()
                for row in rows:
                    raw_text = str(row[0]).strip()
                    is_bully = bool(row[1])
                    label_str = "Bullying" if is_bully else "Non-bullying"
                    if raw_text:
                        new_records.append({"String": raw_text, "Label": label_str})
                print(
                    f"Berhasil memuat {len(rows)} data dari basis data memori SQLite."
                )
            else:
                print("Basis data memori SQLite belum dibuat atau tidak ditemukan.")
        except Exception as e:
            print(f"Warning: Gagal memuat data dari basis data memori SQLite: {e}")

    return new_records
