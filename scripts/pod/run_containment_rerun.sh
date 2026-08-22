#!/usr/bin/env bash
# Rerun only the containment cells after the private-namespace fix.
set -euo pipefail

SEEDS="${CANARY_SEEDS:-0-4}"
EPISODES="${CANARY_EPISODES:-2}"
BASE_URL="http://localhost:8000/v1"
OUT="results/rerun_containment"

python scripts/dataset/build_dataset.py \
  --seeds "$SEEDS" --episodes 3 \
  --conditions baseline,coalition,rotation,containment
python scripts/dataset/acceptance.py

run_model() (
  local model="$1" tag="$2" steps="$3" thinking="$4" out_dir="$5"
  shift 5
  local model_pid=""
  cleanup() {
    if [ -n "$model_pid" ]; then
      kill "$model_pid" 2>/dev/null || true
      wait "$model_pid" 2>/dev/null || true
    fi
  }
  trap cleanup EXIT

  echo "== serving $model =="
  python - "$model" <<'PY'
import sys
from huggingface_hub import snapshot_download
print("model cached at", snapshot_download(sys.argv[1]))
PY
  nohup vllm serve "$model" --port 8000 --max-model-len 16384 \
    --gpu-memory-utilization 0.9 >/tmp/canary-vllm.log 2>&1 &
  model_pid=$!
  for _ in $(seq 1 240); do
    if curl -sf "$BASE_URL/v1/models" >/dev/null; then break; fi
    sleep 5
  done
  curl -sf "$BASE_URL/v1/models" >/dev/null

  local args=(
    --condition containment --seeds "$SEEDS" --episodes "$EPISODES"
    --backend vllm --attacker-mode llm --trace --max-steps "$steps"
    --base-url "$BASE_URL" --model "$model" --out "$out_dir"
  )
  if [ "$thinking" = "off" ]; then args+=(--no-thinking); fi
  python scripts/run_experiment.py "${args[@]}" "$@"
  echo "== $tag containment summary =="
  cat "$out_dir/containment.json"
)

run_model "Qwen/Qwen3-4B-Instruct-2507" qwen4b 40 on "$OUT/qwen4b/core"

run_model "Qwen/Qwen3-4B-Instruct-2507" qwen4b 40 on \
  "$OUT/qwen4b/containment_high" --episodes 1 --intents high,high --attackers 2

run_model "Qwen/Qwen3-4B-Instruct-2507" qwen4b 40 on \
  "$OUT/qwen4b/containment_medium" --episodes 1 --intents medium,medium --attackers 2

run_model "Qwen/Qwen3-8B" qwen8b 40 off "$OUT/qwen8b/core"

run_model "google/gemma-3-4b-it" gemma4b_80 80 on "$OUT/gemma4b_80/core"

echo "== rerun files =="
find "$OUT" -name '*.json' -print | sort
