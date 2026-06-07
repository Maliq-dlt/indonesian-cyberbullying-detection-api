#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-change_this_to_a_long_random_secret}"

printf "Checking health endpoint...\n"
curl -fsS "$BASE_URL/health" >/dev/null
printf "OK: /health\n"

printf "Checking protected endpoint without API key...\n"
STATUS_NO_KEY=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/models/status" || true)
if [[ "$STATUS_NO_KEY" == "200" ]]; then
  printf "FAIL: /models/status allowed access without API key\n"
  exit 1
fi
printf "OK: /models/status blocks missing API key with status %s\n" "$STATUS_NO_KEY"

printf "Checking protected endpoint with API key...\n"
STATUS_WITH_KEY=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $API_KEY" "$BASE_URL/models/status" || true)
if [[ "$STATUS_WITH_KEY" != "200" ]]; then
  printf "WARN: /models/status returned %s with API key. Check endpoint path or backend config.\n" "$STATUS_WITH_KEY"
else
  printf "OK: /models/status accepts valid API key\n"
fi

printf "Checking prediction endpoint candidate paths...\n"
PAYLOAD='{"text":"contoh komentar untuk smoke test"}'
FOUND=0
for PATH in "/predict" "/api/predict" "/predict/hybrid" "/api/v1/predict"; do
  CODE=$(curl -s -o /tmp/bullyguard_smoke_response.json -w "%{http_code}" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d "$PAYLOAD" \
    "$BASE_URL$PATH" || true)
  if [[ "$CODE" == "200" || "$CODE" == "201" ]]; then
    printf "OK: prediction endpoint works at %s\n" "$PATH"
    FOUND=1
    break
  fi
done

if [[ "$FOUND" == "0" ]]; then
  printf "WARN: no common prediction path returned 200. Check your actual route definitions.\n"
fi

printf "Smoke test completed.\n"
