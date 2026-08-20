#!/usr/bin/env bash
# Pod-side 8B sanity cell (cross-size check of H1/H3) + sweep v2 dump.
# 1) Prints authoritative sweep v2 (n=5) cell JSONs from the archives.
# 2) Serves Qwen3-8B and runs coalition + containment (seeds 0-4 x 2 eps,
#    n=10), mirroring the core matrix (only the model changes), so 4B vs 8B
#    is a clean cross-size comparison.
set -euo pipefail

MODEL="${CANARY_MODEL:-Qwen/Qwen3-8B}"
PORT="${CANARY_PORT:-8000}"
SEEDS="${CANARY_SEEDS:-0-4}"
EPISODES="${CANARY_EPISODES:-2}"
BASE="http://localhost:$PORT/v1"

echo "== sweep v2 cells (seeds=5) across archives =="
python - <<'PY'
import glob, json, os
for f in sorted(glob.glob("results_archive/*/*/*.json")):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    if d.get("seeds") != 5:
        continue
    keys = {k: d[k] for k in ("condition","seeds","activation_rate","attack_coverage","benign_fpr","benign_success","post_trigger_harm","contagion")}
    print(os.path.basename(os.path.dirname(os.path.dirname(f))), "->", os.path.basename(os.path.dirname(f)), json.dumps(keys))
PY

echo "== serving $MODEL on :$PORT =="
export HF_HUB_ENABLE_HF_TRANSFER=0
python - "$MODEL" <<'PY'
import sys
from huggingface_hub import snapshot_download
print("model cached at", snapshot_download(sys.argv[1]))
PY
nohup vllm serve "$MODEL" --port "$PORT" --max-model-len 16384 --gpu-memory-utilization 0.9 >/tmp/vllm.log 2>&1 &
VPID=$!
for _ in $(seq 1 240); do
  if curl -sf "http://localhost:$PORT/v1/models" >/dev/null; then break; fi
  sleep 5
  tail -n 2 /tmp/vllm.log 2>/dev/null || true
done
if ! curl -sf "http://localhost:$PORT/v1/models" >/dev/null; then
  echo "vLLM failed to come up" >&2
  tail -40 /tmp/vllm.log >&2 || true
  kill "$VPID" 2>/dev/null || true
  exit 1
fi
echo "vLLM ready"

OUT="results/8b_sanity"
mkdir -p "$OUT"
for cond in coalition containment; do
  echo "== 8B $cond =="
  python scripts/run_experiment.py \
    --condition "$cond" --seeds "$SEEDS" --episodes "$EPISODES" \
    --backend vllm --attacker-mode llm --trace \
    --base-url "$BASE" --model "$MODEL" \
    --out "$OUT/$cond"
done

kill "$VPID" 2>/dev/null || true

echo "== archiving (results_archive/) =="
ARCHIVE="results_archive/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$ARCHIVE"
cp -r results/* "$ARCHIVE"/ 2>/dev/null || true
echo "archived to $ARCHIVE"

echo "== 8B summary =="
python - "$OUT" <<'PY'
import glob, json, os, sys
root = sys.argv[1]
for f in sorted(glob.glob(f"{root}/*/*.json")):
    d = json.load(open(f))
    keys = {k: d[k] for k in ("condition","seeds","activation_rate","attack_coverage","benign_fpr","benign_success","post_trigger_harm","contagion")}
    print(os.path.basename(os.path.dirname(f)), json.dumps(keys))
PY
