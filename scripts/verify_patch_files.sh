#!/usr/bin/env bash
set -euo pipefail

missing=0

check_file() {
  local path="$1"
  if [[ ! -e "$path" ]]; then
    printf "MISSING: %s\n" "$path"
    missing=1
  else
    printf "OK: %s\n" "$path"
  fi
}

printf "Verifying Stage 1 files...\n"
check_file "README.md"
check_file ".env.example"
check_file "MODEL_EVALUATION.md"
check_file "docs/LOCAL_SETUP.md"
check_file "docs/PRODUCTION_CHECKLIST.md"
check_file "docs/PROJECT_POSITIONING.md"

printf "\nVerifying Stage 2 files...\n"
check_file "cyberbullying_api/routes/deps.py"
check_file "cyberbullying_api/main.py"
check_file "docker-compose.yml"
check_file "docker-compose.prod.yml"
check_file "docs/SECURITY_HARDENING.md"

printf "\nVerifying Stage 3 files...\n"
check_file "cyberbullying_api/classifier/confidence.py"
check_file "cyberbullying_api/classifier/evaluate_thresholds.py"
check_file "tests/test_confidence.py"
check_file "docs/ML_CONFIDENCE_GUIDE.md"
check_file "docs/ERROR_ANALYSIS_GUIDE.md"

printf "\nVerifying Stage 4 files...\n"
check_file "frontend/src/components/Detector.tsx"
check_file "frontend/src/components/Detector/Detector.tsx"
check_file "frontend/src/components/Detector/useDetector.ts"
check_file "docs/FRONTEND_REFACTOR_GUIDE.md"

printf "\nVerifying Stage 5 files...\n"
check_file "docs/FINAL_INTEGRATION_GUIDE.md"
check_file "docs/FINAL_TESTING_CHECKLIST.md"
check_file "docs/APPLY_PATCH_ORDER.md"
check_file "docs/ROLLBACK_PLAN.md"
check_file "scripts/smoke_test_api.sh"
check_file "scripts/smoke_test_api.ps1"

if [[ "$missing" == "1" ]]; then
  printf "\nSome files are missing. Review copied patch contents.\n"
  exit 1
fi

printf "\nAll expected patch files are present.\n"
