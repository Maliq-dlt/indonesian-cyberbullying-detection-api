import os
import sys
import torch
import pandas as pd
import numpy as np
import warnings
import shutil
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    Trainer, 
    TrainingArguments,
    DataCollatorWithPadding
)

# Konfigurasikan encoding output konsol ke UTF-8 di Windows agar tidak crash saat mencetak karakter Unicode
if sys.platform.startswith('win'):
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            getattr(sys.stdout, 'reconfigure')(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            getattr(sys.stderr, 'reconfigure')(encoding='utf-8')
    except Exception:
        pass

if __name__ != "__main__":
    raise ImportError("This script is intended to be run as a standalone script, not imported.")

# Tambahkan base_dir ke sys.path agar impor lokal berfungsi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from normalizer import init_slang_map, normalize_text
from training import (
    load_twitter_dataset, 
    load_instagram_dataset, 
    load_combined_dataset, 
    load_mendeley_dataset, 
    load_tiktok_rhiosutoyo_dataset
)

print("=== Skrip Pelatihan Mandiri Model Transformer (Fine-Tuning) & Auto-Export ONNX ===")

# 1. Konfigurasi
MODEL_NAME = os.getenv("BASE_MODEL_NAME", "nahiar/hatespeech-abusive-xlm-roberta-v1")
OUTPUT_DIR = os.path.join(BASE_DIR, "models", "fine_tuned_transformer")

ALAY_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_1", "new_kamusalay.csv")
SINGKATAN_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_2", "kamus_singkatan.csv")
ABUSIVE_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_1", "abusive.csv")

DATASET_TWITTER_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_1", "data.csv")
DATASET_INSTAGRAM_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_instagram", "DATASET CYBERBULLYING INSTAGRAM - FINAL.xlsx")
DATASET_COMBINED_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_2", "combined_dataset.csv")
DATASET_MENDELEY_DIR = os.path.join(BASE_DIR, "..", "dataset", "ds_mendeley")
DATASET_TIKTOK_RHIOSUTOYO_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_tiktok_rhiosutoyo", "Dataset-Research.csv")

# Inisialisasi slang
init_slang_map(ALAY_PATH, SINGKATAN_PATH)

def clean_text(text: str) -> str:
    return normalize_text(text)["spaced"]

# Muat Leksikon Abusive
if os.path.exists(ABUSIVE_PATH):
    try:
        df_abusive = pd.read_csv(ABUSIVE_PATH)
        abusive_words = set(df_abusive['ABUSIVE'].dropna().str.strip().str.lower().unique().tolist())
    except Exception:
        abusive_words = set()
else:
    abusive_words = set()

def check_toxic_by_lexicon(norm_text: str) -> bool:
    words = set(norm_text.split())
    return any(w in abusive_words for w in words)

# 2. Muat Seluruh Dataset
print("Memuat seluruh dataset untuk pelatihan...")
datasets_loaded = []

df_twitter = load_twitter_dataset(DATASET_TWITTER_PATH, clean_text)
if df_twitter is not None:
    datasets_loaded.append(df_twitter)
    print(f"Berhasil memuat dataset Twitter ({len(df_twitter)} baris).")

df_instagram = load_instagram_dataset(DATASET_INSTAGRAM_PATH, clean_text, check_toxic_by_lexicon)
if df_instagram is not None:
    datasets_loaded.append(df_instagram)
    print(f"Berhasil memuat dataset Instagram ({len(df_instagram)} baris).")

df_combined = load_combined_dataset(DATASET_COMBINED_PATH, clean_text, check_toxic_by_lexicon)
if df_combined is not None:
    datasets_loaded.append(df_combined)
    print(f"Berhasil memuat dataset kombinasi ({len(df_combined)} baris).")

df_mendeley = load_mendeley_dataset(DATASET_MENDELEY_DIR, clean_text, check_toxic_by_lexicon)
if df_mendeley is not None:
    datasets_loaded.append(df_mendeley)
    print(f"Berhasil memuat dataset Mendeley ({len(df_mendeley)} baris).")

df_tiktok = load_tiktok_rhiosutoyo_dataset(DATASET_TIKTOK_RHIOSUTOYO_PATH, clean_text, check_toxic_by_lexicon)
if df_tiktok is not None:
    datasets_loaded.append(df_tiktok)
    print(f"Berhasil memuat dataset TikTok Rhiosutoyo ({len(df_tiktok)} baris).")

if not datasets_loaded:
    print("Error: Tidak ada dataset yang berhasil dimuat.")
    exit(1)

df = pd.concat(datasets_loaded, ignore_index=True)
df = df.dropna()
df = df[df['text_clean'] != ""]

# Mengubah tipe data label ke float untuk Binary Cross Entropy
df["is_bully"] = df["is_bully"].astype(float)
df["is_toxic"] = df["is_toxic"].astype(float)

labels = df[["is_bully", "is_toxic"]].values.tolist()

# Terapkan QUICK_TRAIN jika CUDA tidak tersedia agar tidak timeout di CPU
quick_train = os.getenv("QUICK_TRAIN", "true").lower() in ("true", "1", "yes")
if not torch.cuda.is_available() and quick_train:
    print("\n[INFO] CUDA tidak terdeteksi. Menggunakan QUICK_TRAIN=True dengan mengambil subset data (200 sampel) agar training di CPU selesai cepat.")
    df = df.sample(n=min(200, len(df)), random_state=42)
    labels = df[["is_bully", "is_toxic"]].values.tolist()

# Split train & val
stratify_key = df["is_bully"].astype(int).astype(str) + "_" + df["is_toxic"].astype(int).astype(str)
min_class_count = stratify_key.value_counts().min()

if min_class_count >= 2:
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        df["text_clean"].tolist(),
        labels,
        test_size=0.15,
        random_state=42,
        stratify=stratify_key.tolist()
    )
else:
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        df["text_clean"].tolist(),
        labels,
        test_size=0.15,
        random_state=42
    )

print(f"Jumlah data latih: {len(train_texts)} | Jumlah data validasi: {len(val_texts)}")

# 3. Tokenisasi
print(f"Memuat tokenizer untuk model: {MODEL_NAME}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=128)
val_encodings = tokenizer(val_texts, truncation=True, padding=True, max_length=128)

class CyberDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx], dtype=torch.float)
        return item

    def __len__(self):
        return len(self.labels)

train_dataset = CyberDataset(train_encodings, train_labels)
val_dataset = CyberDataset(val_encodings, val_labels)

# 4. Inisialisasi Model
print(f"Memuat model klasifikasi dari {MODEL_NAME}...")
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device yang digunakan: {device.upper()}")

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME, 
    num_labels=2, 
    problem_type="multi_label_classification"
)
model.to(device)

# 5. Metrik Evaluasi
def compute_metrics(pred):
    labels = pred.label_ids
    logits = pred.predictions[0] if isinstance(pred.predictions, tuple) else pred.predictions
    probs = 1 / (1 + np.exp(-logits))
    preds = (probs >= 0.5).astype(int)
    
    acc = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds, average='macro', zero_division=0)
    precision = precision_score(labels, preds, average='macro', zero_division=0)
    recall = recall_score(labels, preds, average='macro', zero_division=0)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

# 6. Argumen Pelatihan
training_args_dict = {
    "output_dir": os.path.join(BASE_DIR, "models", "results"),
    "num_train_epochs": int(os.getenv("NUM_TRAIN_EPOCHS", "3")),
    "per_device_train_batch_size": int(os.getenv("PER_DEVICE_TRAIN_BATCH_SIZE", "8" if not torch.cuda.is_available() else "16")),
    "per_device_eval_batch_size": int(os.getenv("PER_DEVICE_EVAL_BATCH_SIZE", "8" if not torch.cuda.is_available() else "16")),
    "warmup_steps": 20 if (not torch.cuda.is_available() and quick_train) else 100,
    "weight_decay": 0.01,
    "logging_dir": os.path.join(BASE_DIR, "models", "logs"),
    "logging_steps": 5 if (not torch.cuda.is_available() and quick_train) else 50,
    "eval_strategy": "epoch",
    "save_strategy": "epoch",
    "load_best_model_at_end": True,
    "metric_for_best_model": "f1",
    "greater_is_better": True,
    "learning_rate": 3e-5,
    "report_to": "none"
}
training_args = TrainingArguments(**training_args_dict)  # type: ignore

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
    data_collator=DataCollatorWithPadding(tokenizer=tokenizer)
)

# 7. Pelatihan
print("Memulai proses fine-tuning model...")
trainer.train()

print(f"Menyimpan model terbaik di: {OUTPUT_DIR}...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

# 8. Ekspor ke ONNX & Kuantisasi
def export_fine_tuned_to_onnx(model_dir, output_dir):
    try:
        import onnx
        import onnx.shape_inference
        from onnxruntime.quantization import quantize_dynamic, QuantType
    except ImportError as e:
        print(f"Warning: onnx / onnxruntime tidak tersedia untuk ekspor langsung ({e})")
        return
        
    print("\n=== Mengekspor model hasil fine-tuning ke ONNX & Kuantisasi INT8 ===")
    
    # Bypass shape inference wrapper robust untuk Windows
    original_infer_shapes_path = onnx.shape_inference.infer_shapes_path
    def robust_infer_shapes_path(model_path, output_path, *args, **kwargs):
        try:
            original_infer_shapes_path(model_path, output_path, *args, **kwargs)
        except Exception as err:
            print(f"[ONNX Warning] Shape inference gagal ({err}). Fallback bypass shape inference: {model_path} -> {output_path}")
            shutil.copyfile(model_path, output_path)
    onnx.shape_inference.infer_shapes_path = robust_infer_shapes_path

    # Load model PyTorch hasil fine-tuning
    print(f"Memuat model fine-tuned PyTorch dari: {model_dir}")
    ft_tokenizer = AutoTokenizer.from_pretrained(model_dir)
    ft_model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    ft_model.eval()

    # Ekspor ONNX mentah
    onnx_path = os.path.join(output_dir, "model.onnx")
    dummy_text = "Semangat belajarnya ya, jangan menyerah!"
    inputs = ft_tokenizer(dummy_text, return_tensors="pt")
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    print("Mengekspor model PyTorch ke format ONNX...")
    torch.onnx.export(
        ft_model,
        (input_ids, attention_mask),
        onnx_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        dynamic_axes={
            "input_ids": {0: "batch_size", 1: "sequence_length"},
            "attention_mask": {0: "batch_size", 1: "sequence_length"},
            "logits": {0: "batch_size"}
        },
        opset_version=14
    )
    print(f"Model berhasil diekspor ke ONNX mentah: {onnx_path}")

    # Jalankan kuantisasi INT8 Dinamis
    temp_quantized_path = os.path.join(output_dir, "model_quantized.onnx")
    print("Menjalankan kuantisasi INT8 Dinamis pada model ONNX...")
    quantize_dynamic(
        model_input=onnx_path,
        model_output=temp_quantized_path,
        weight_type=QuantType.QUInt8,
        extra_options={"DefaultTensorType": onnx.TensorProto.FLOAT}
    )
    print(f"Kuantisasi selesai! Model terkuantisasi disimpan sementara di: {temp_quantized_path}")

    # Hapus model ONNX mentah
    if os.path.exists(onnx_path):
        os.remove(onnx_path)

    # Sebarkan ke beberapa slug agar otomatis dikenali oleh predictor.py
    slugs = [
        "nahiar_hatespeech-abusive-xlm-roberta-v1",
        "fine_tuned_transformer"
    ]
    
    # Tambahkan absolute path slug
    abs_dir = os.path.abspath(model_dir)
    slugs.append(abs_dir.replace("/", "_").replace("\\", "_").replace(".", "_"))
    
    # Tambahkan relative path slug dari base dan parent
    parent_dir = os.path.dirname(BASE_DIR)
    rel_dir_base = os.path.relpath(model_dir, BASE_DIR)
    rel_dir_parent = os.path.relpath(model_dir, parent_dir)
    slugs.append(rel_dir_base.replace("/", "_").replace("\\", "_").replace(".", "_"))
    slugs.append(rel_dir_parent.replace("/", "_").replace("\\", "_").replace(".", "_"))

    unique_slugs = sorted(list(set(slugs)))
    for slug in unique_slugs:
        target_filename = f"model_{slug}_quantized.onnx"
        target_path = os.path.join(output_dir, target_filename)
        shutil.copyfile(temp_quantized_path, target_path)
        print(f"Model terkuantisasi ONNX berhasil disimpan untuk slug '{slug}': {target_path}")

    # Bersihkan file temp quantized
    if os.path.exists(temp_quantized_path):
        os.remove(temp_quantized_path)
    print("Selesai mengekspor seluruh model ONNX terkuantisasi.")

export_fine_tuned_to_onnx(OUTPUT_DIR, os.path.join(BASE_DIR, "models"))

print("\n🎉 Proses pelatihan & auto-export ONNX sukses! Untuk menggunakan model baru ini di API/UI Anda, atur variabel lingkungan berikut:")
print(f"  set TRANSFORMER_MODEL_PATH={OUTPUT_DIR}")
print("  Atau jalankan uvicorn/app_ui.py dengan env tersebut.")
