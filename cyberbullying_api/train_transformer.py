import os
import torch
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    Trainer, 
    TrainingArguments,
    DataCollatorWithPadding
)
from normalizer import init_slang_map, normalize_text

print("=== Skrip Pelatihan Mandiri Model Transformer (Distilasi/Fine-Tuning) ===")

# 1. Konfigurasi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_NAME = os.getenv("BASE_MODEL_NAME", "wans/distilroberta-indo") # Default model ringan terdistilasi
OUTPUT_DIR = os.path.join(BASE_DIR, "models", "fine_tuned_transformer")
DATASET_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_2", "combined_dataset.csv")

# Inisialisasi slang
ALAY_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_1", "new_kamusalay.csv")
SINGKATAN_PATH = os.path.join(BASE_DIR, "..", "dataset", "ds_2", "kamus_singkatan.csv")
init_slang_map(ALAY_PATH, SINGKATAN_PATH)

def clean_text(text: str) -> str:
    return normalize_text(text)["spaced"]

# 2. Muat Dataset
if not os.path.exists(DATASET_PATH):
    print(f"Error: Dataset tidak ditemukan di {DATASET_PATH}")
    exit(1)

print(f"Memuat dataset dari {DATASET_PATH}...")
df = pd.read_csv(DATASET_PATH)
df = df.dropna(subset=["String", "Label"])

# Buat kolom teks bersih
df["text_clean"] = df["String"].apply(clean_text)

# Label multi-output: kita asumsikan klasifikasi biner untuk cyberbullying/bullying
df["label"] = df["Label"].isin(["Bullying", "negatif", "negative"]).astype(int)

# Split train & val
train_texts, val_texts, train_labels, val_labels = train_test_split(
    df["text_clean"].tolist(),
    df["label"].tolist(),
    test_size=0.15,
    random_state=42,
    stratify=df["label"].tolist()
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
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

train_dataset = CyberDataset(train_encodings, train_labels)
val_dataset = CyberDataset(val_encodings, val_labels)

# 4. Inisialisasi Model
print(f"Memuat model klasifikasi dari {MODEL_NAME}...")
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device yang digunakan: {device.upper()}")

model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)
model.to(device)

# 5. Metrik Evaluasi
def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    acc = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds, average='binary', zero_division=0)
    precision = precision_score(labels, preds, average='binary', zero_division=0)
    recall = recall_score(labels, preds, average='binary', zero_division=0)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

# 6. Argumen Pelatihan
training_args = TrainingArguments(
    output_dir=os.path.join(BASE_DIR, "models", "results"),
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    warmup_steps=100,
    weight_decay=0.01,
    logging_dir=os.path.join(BASE_DIR, "models", "logs"),
    logging_steps=50,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    greater_is_better=True,
    learning_rate=3e-5,
    report_to="none"
)

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

print("\n🎉 Proses pelatihan sukses! Untuk menggunakan model baru ini di API/UI Anda, atur variabel lingkungan berikut:")
print(f"  set TRANSFORMER_MODEL_PATH={OUTPUT_DIR}")
print("  Atau jalankan uvicorn/app_ui.py dengan env tersebut.")
