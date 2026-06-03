"""
training/augmentation.py
~~~~~~~~~~~~~~~~~~~~~~~~
Reusable text-augmentation utilities extracted from retrain.py.

Provides:
  - LLM-based paraphrase augmentation via a local Ollama instance.
  - Rule-based perturbation (leetspeak, censoring, typos, character
    repetition) targeting abusive words.
  - Ready-made template lists for sarcasm and slang-praise patterns
    used during data-augmentation rounds.
"""

import os
import json
import random

import httpx

from normalizer import normalize_text

# ---------------------------------------------------------------------------
# Ollama configuration (read from environment at import time)
# ---------------------------------------------------------------------------
OLLAMA_URL: str = os.getenv("OLLAMA_URL", "")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# ---------------------------------------------------------------------------
# Leetspeak substitution map used by perturb_text
# ---------------------------------------------------------------------------
PERTURB_LEET: dict[str, str] = {
    'a': '4', 'i': '1', 'e': '3', 'o': '0', 's': '5', 'g': '9',
}

# ---------------------------------------------------------------------------
# Template data – sarcasm & slang-praise sentences for augmentation
# ---------------------------------------------------------------------------
sarcasm_raw: list[str] = [
    "Wah pintar sekali kamu ya, sampai nilai ujianmu nol.",
    "ganteng banget mukalu kaya spakbor mio",
    "rajin banget sih jam 12 siang baru bangun tidur",
    "bagus banget kerjaan lu, bikin rugi perusahaan aja",
    "wah hebat sekali, rancangan kamu sukses merusak sistem",
    "cantik banget sih mbak, dandanannya kayak badut ancol",
    "suaranya bagus sekali ya, sampai bikin telinga pecah",
    "bersih sekali kamarmu, sampai tikus pun betah di situ",
    "baik sekali kamu ya, suka membicarakan orang di belakang",
    "ganteng banget, mirip monyet kebanjiran",
    "pintar banget sih kamu, soal gampang begini aja salah semua",
    "wah wangi sekali badanmu, sampai semua orang pingsan",
    "cepat sekali kerjamu, proyek sebulan selesai setahun",
    "suci sekali kamu, padahal kelakuan minus semua",
    "sopan sekali bicaramu, seperti tidak pernah disekolahkan",
    "hebat sekali kau, selalu berhasil mengecewakan orang tua",
    "rajin sekali dia, tugas satu semester dikerjakan semenit sebelum deadline",
    "baik benar dirimu, menolong orang tapi minta bayaran ganda",
    "pemandangan indah sekali, penuh sampah berserakan di mana-mana",
    "ganteng banget mukamu, kayak panci gosong",
]

slang_praise_raw: list[str] = [
    "kamu hebat banget sih anjing",
    "gila keren banget lu bajingan",
    "goblok lu lucu banget sumpah",
    "anjing ganteng banget cowok itu",
    "hebat banget sih monyet, jago mainnya",
    "gila mainnya jago banget bangsat",
    "kamu pintar banget sih bajingan",
    "gila ini makanan enak banget asu",
    "cantik banget kamu bangsat",
    "keren gila lu bro, mantap anjing",
    "gila lu bro, aseli keren banget anjing",
    "muka lu ganteng gila babi",
    "goblok lu kok bisa kepikiran ide sekeren ini",
    "anjing aseli ini film seru banget",
    "jago bangsat main gitarnya",
    "gokil parah lu bro, respect anjing",
    "gila desain lu keren banget asu",
    "anjing suaranya merdu banget",
    "gila jagoan banget lu bangsat",
    "goblok lu pinter banget bikin presentasi",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def augment_text_with_llm(text: str, is_bully: bool) -> list[str]:
    """Use a local Ollama instance to generate paraphrase variations.

    Returns up to 2 paraphrased versions of *text*, preserving the
    original register (slang / harsh / polite) and label semantics.
    Returns an empty list when ``OLLAMA_URL`` is not configured or
    when the request fails for any reason.
    """
    if not OLLAMA_URL:
        return []

    label_desc = (
        "cyberbullying/perundungan" if is_bully
        else "komentar aman/bukan perundungan"
    )
    prompt = (
        f"Sebagai ahli bahasa Indonesia, berikan 2 variasi atau parafrase "
        f"alternatif untuk kalimat berikut.\n"
        f"Variasi harus tetap mempertahankan gaya bahasa "
        f"(gaul/kasar/sopan) dan makna aslinya sebagai {label_desc}.\n"
        f"Keluaran harus berupa daftar string mentah JSON tanpa markdown, "
        f'seperti: ["variasi 1", "variasi 2"]\n\n'
        f'Kalimat asli: "{text}"'
    )

    url = f"{OLLAMA_URL.rstrip('/')}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": {
            "type": "array",
            "items": {"type": "string"},
        },
        "options": {
            "temperature": 0.5,  # slightly creative for paraphrase variety
        },
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(url, json=payload)
            if response.status_code == 200:
                res_json = response.json()
                variations = json.loads(res_json["response"])
                if isinstance(variations, list):
                    return [str(v).strip() for v in variations if str(v).strip()]
    except Exception as e:
        print(f"Warning: Gagal menghasilkan augmentasi LLM untuk '{text}': {e}")

    return []


def perturb_text(text: str, abusive_words: set) -> str:
    """Apply random perturbations to abusive words in *text*.

    Perturbation types (chosen at random per word):
      - **leet**: substitute characters using ``PERTURB_LEET``.
      - **censor**: replace inner characters with ``*``.
      - **repeat**: duplicate the last character 1–3 times.
      - **typo**: swap two adjacent interior characters.

    Parameters
    ----------
    text:
        The input string to perturb.
    abusive_words:
        A set of known abusive words.  A word is only perturbed when it
        appears in this set *and* a random check (p=0.6) passes.

    Returns
    -------
    str
        The perturbed text, or an empty string if *text* is falsy / not
        a string.
    """
    if not text or not isinstance(text, str):
        return ""

    words = text.split()
    new_words: list[str] = []

    for w in words:
        if w in abusive_words and random.random() < 0.6:
            p_type = random.choice(["leet", "censor", "repeat", "typo"])

            if p_type == "leet":
                w = "".join(PERTURB_LEET.get(c, c) for c in w)
            elif p_type == "censor":
                if len(w) > 2:
                    w = w[0] + "*" * (len(w) - 2) + w[-1]
            elif p_type == "repeat":
                w = w + w[-1] * random.randint(1, 3)
            elif p_type == "typo":
                if len(w) > 3:
                    idx = random.randint(1, len(w) - 2)
                    w_list = list(w)
                    w_list[idx], w_list[idx + 1] = w_list[idx + 1], w_list[idx]
                    w = "".join(w_list)

        new_words.append(w)

    return " ".join(new_words)
