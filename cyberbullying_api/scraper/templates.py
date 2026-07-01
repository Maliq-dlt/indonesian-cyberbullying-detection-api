import random

# Daftar instance Nitter publik untuk guest X scraping tanpa API Key
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.net"
]

USERNAMES = [
    "malik_dlt", "cyber_fighter", "budi_santoso", "siti_nur", "andi_pratama",
    "dina_amelia", "rizky_ramadhan", "ayu_lestari", "eko_prasetyo", "mega_putri",
    "fajar_subekti", "wulan_sari", "gilang_dirga", "nanda_saputra", "putra_bangsa"
]

SAFE_TEMPLATES = [
    "Semangat terus bikin kontennya ya kak, suka banget!",
    "makasih informasinya kak sangat bermanfaat sekali",
    "sehat-sehat selalu ya sekeluarga amin",
    "semangat kerjanya ya guys, demi masa depan cerah",
    "sukses terus usahanya ya gan, laris manis",
    "Semoga hari ini menyenangkan untuk kita semua, jangan lupa sarapan!",
    "makasih ya infonya, ngebantu banget buat tugas kuliah",
    "Keren banget kak, sukses selalu untuk karirnya ya!"
]

SLANG_PRAISE_TEMPLATES = [
    "anjing keren banget lu bang, gokil abis!",
    "gila main gitarnya jago banget bangsat!",
    "anjing aseli ini lucu banget videonya sumpah",
    "goblok lu kok bisa kepikiran ide sekeren ini sih?",
    "gokil parah lu bro, respect anjing!",
    "anjing keren gila lu bro, congrats atas prestasinya!",
    "gila ini makanan enak banget asu, nagih parah",
    "gila lu bro, aseli keren banget anjing!"
]

SARCASM_TEMPLATES = [
    "ganteng banget muka lu kayak spakbor mio wkwk",
    "Wah rajin banget ya, jam 12 siang baru bangun tidur.",
    "cantik banget sih mbak, dandanannya mirip badut ancol",
    "sopan sekali bicaramu, seperti tidak pernah disekolahkan.",
    "hebat benar dirimu, menolong orang tapi minta bayaran ganda.",
    "bagus banget kerjaan lu, bikin bangkrut toko aja",
    "suaranya merdu sekali ya, sampai bikin telinga saya pecah.",
    "pinter banget sih kamu, soal gampang begini aja salah semua.",
    "Wah pintar sekali politisi kita ya, rakyat kelaparan dia beli jet pribadi.",
    "rajin sekali pemerintah kita, bikin aturan aneh pas tengah malam.",
    "ganteng banget cowok itu, mirip monyet kebanjiran wkwk",
    "suci sekali dirimu, padahal aslinya kelakuan minus semua.",
    "desain lu bagus banget, bikin rusak estetika aja wkwk"
]

TOXIC_BULLYING_TEMPLATES = [
    "Kamu bodoh banget sih, dasar tolol ga guna!",
    "otak kosong begini kok bisa fyp sih heran gua",
    "mending lu mati aja dah nyampah banget di fyp",
    "dasar idiot ga punya otak, debat kok cuma bisa nyerang personal",
    "kamu bodoh sekali sih bangsat, gampang dibohongin buzzer",
    "muka lu kayak panci gosong ga usah belagu dah",
    "mati aja lo begal sampah masyarakat!",
    "dasar manusia sampah ga ada gunanya hidup di dunia ini"
]

def generate_dynamic_comments(query_or_url: str, max_items: int = 20) -> list[str]:
    """Menghasilkan teks komentar/tweet tiruan yang sangat dinamis untuk simulasi scraper."""
    print(f"Generating dynamic template-based fallback comments/tweets for query: {query_or_url}")
    results = []

    # Distribusi kategori yang seimbang
    categories = [
        ("safe", SAFE_TEMPLATES),
        ("slang", SLANG_PRAISE_TEMPLATES),
        ("sarcasm", SARCASM_TEMPLATES),
        ("toxic", TOXIC_BULLYING_TEMPLATES)
    ]

    attempts = 0
    while len(results) < max_items and attempts < 100:
        attempts += 1
        cat_name, templates = random.choice(categories)
        template = random.choice(templates)

        # Tambahkan variasi username secara acak
        if random.random() < 0.4:
            username = random.choice(USERNAMES)
            comment = f"@{username} {template}"
        else:
            comment = template

        if comment not in results:
            results.append(comment)

    random.shuffle(results)
    return results[:max_items]
