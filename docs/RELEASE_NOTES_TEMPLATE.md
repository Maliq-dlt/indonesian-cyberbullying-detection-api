# Release Notes Template

## Version

`v0.2.0-hardening-preview`

## Summary

Rilis ini memperbaiki dokumentasi, security backend, confidence handling ML, frontend detector refactor, dan workflow integration testing.

## Added

- Model evaluation template.
- Production checklist.
- Security hardening guide.
- ML confidence helper.
- Threshold evaluation script.
- Frontend detector modular structure.
- Final integration and testing checklist.

## Changed

- Project positioning dibuat lebih realistis sebagai advanced MVP/research-oriented prototype.
- API key handling diperketat untuk staging/production.
- Rate limit behavior diperjelas.
- CORS configuration diperketat.
- Detector UI dipecah menjadi komponen kecil.

## Security

- Production/staging wajib API key.
- Credential production diarahkan ke environment variable.
- Webhook validation diperketat.
- Rate limit tidak fail-open di production.

## ML

- LLM decision tidak lagi dianggap probabilitas absolut.
- Lexicon boost dibuat lebih konservatif.
- Threshold evaluation workflow ditambahkan.

## Known limitations

- Model accuracy masih harus dibuktikan dengan validation/test set yang jelas.
- Benchmark latency belum tersedia.
- Full production deployment belum divalidasi di cloud environment.
- Human-in-the-loop workflow masih perlu diuji dengan data nyata.

## Upgrade notes

1. Update `.env` dari `.env.example`.
2. Jalankan backend tests.
3. Jalankan frontend build.
4. Jalankan Docker smoke test.
5. Review manual patch untuk `predictor.py`.
