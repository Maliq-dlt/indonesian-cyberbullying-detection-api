import os
import sys
import time
import statistics

# Ensure local packages are in path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "cyberbullying_api"))

try:
    from cyberbullying_api.classifier.predictor import init_models, predict_ml, explain_prediction
    from cyberbullying_api.normalizer import normalize_text
except ImportError as e:
    print(f"Error: Harap jalankan script dari root direktori proyek. (Detail: {e})")
    sys.exit(1)

print("Inisialisasi model untuk pengujian performa...")
init_models()

test_comments = [
    "halo selamat pagi kakak",
    "goblok banget sih kamu jadi orang!",
    "kamu pintar sekali ya, sampai ujian pun nilainya nol wkwk",
    "muka kamu mirip spakbor motor bego banget",
    "terima kasih banyak informasinya, sangat bermanfaat dan menginspirasi."
]

print("\n=== Memulai Benchmark Evaluasi Model ===")
runs = 100
latencies = []

# Warmup
_ = predict_ml(test_comments[0])

for i in range(runs):
    comment = test_comments[i % len(test_comments)]
    start = time.perf_counter()
    _ = predict_ml(comment)
    _ = explain_prediction(comment)
    latencies.append((time.perf_counter() - start) * 1000)

mean_lat = statistics.mean(latencies)
median_lat = statistics.median(latencies)
p95_lat = statistics.quantiles(latencies, n=20)[18]  # p95

print(f"Total Uji Coba: {runs} iterasi")
print(f"Rata-rata Latensi: {mean_lat:.2f} ms")
print(f"Median Latensi: {median_lat:.2f} ms")
print(f"p95 Latensi: {p95_lat:.2f} ms")
print("=======================================")
