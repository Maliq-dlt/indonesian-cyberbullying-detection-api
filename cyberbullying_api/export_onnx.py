import os
import torch
import warnings
import shutil
import onnx
import onnx.shape_inference
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from onnxruntime.quantization import quantize_dynamic, QuantType

warnings.filterwarnings("ignore")

# Monkey-patch untuk membypass error shape inference di Windows/onnx
def dummy_infer_shapes_path(model_path, output_path, *args, **kwargs):
    print(f"[ONNX MonkeyPatch] Mem-bypass shape inference: {model_path} -> {output_path}")
    shutil.copyfile(model_path, output_path)

onnx.shape_inference.infer_shapes_path = dummy_infer_shapes_path

def export_to_onnx():
    model_name = "nahiar/hatespeech-abusive-xlm-roberta-v1"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    onnx_path = os.path.join(models_dir, "model.onnx")
    quantized_path = os.path.join(models_dir, "model_quantized.onnx")

    print(f"=== Menyiapkan Ekspor ONNX untuk model: {model_name} ===")
    
    # 1. Unduh/Muat model PyTorch
    print("Memuat model PyTorch dari Hugging Face...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    model.eval()

    # 2. Siapkan input dummy
    dummy_text = "Semangat belajarnya ya, jangan menyerah!"
    inputs = tokenizer(dummy_text, return_tensors="pt")
    
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    # 3. Ekspor ke ONNX
    print("Mengekspor model PyTorch ke format ONNX...")
    torch.onnx.export(
        model,
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
    print(f"Model berhasil diekspor ke: {onnx_path}")

    # 4. Kuantisasi INT8 Dinamis dengan DefaultTensorType diset ke FLOAT karena shape inference di-bypass
    print("Menjalankan kuantisasi INT8 Dinamis pada model ONNX...")
    quantize_dynamic(
        model_input=onnx_path,
        model_output=quantized_path,
        weight_type=QuantType.QUInt8,
        extra_options={"DefaultTensorType": onnx.TensorProto.FLOAT}
    )
    print(f"Kuantisasi selesai! Model terkuantisasi disimpan di: {quantized_path}")
    
    # Bersihkan file model.onnx mentah untuk menghemat ruang
    if os.path.exists(onnx_path):
        os.remove(onnx_path)
        print("Membersihkan berkas ONNX mentah yang tidak terkompresi.")

if __name__ == "__main__":
    export_to_onnx()
