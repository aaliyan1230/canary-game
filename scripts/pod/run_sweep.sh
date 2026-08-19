#!/usr/bin/env bash
# Pod-side sweep: attacker intent gradient x attacker count (D1/D2).
# Starts its own vLLM server (model pre-downloaded), runs the cells, stops it.
set -euo pipefail

MODEL="${CANARY_MODEL:-Qwen/Qwen3-4B-Instruct-2507}"
PORT="${CANARY_PORT:-8000}"
SEEDS="${CANARY_SEEDS:-0-1}"
EPISODES="${CANARY_EPISODES:-1}"
BASE="http://localhost:$PORT/v1"

echo "== pre-downloading model =="
export HF_HUB_ENABLE_HF_TRANSFER=0
python - "$MODEL" <<'PY'
import sys
from huggingface_hub import snapshot_download
print("model cached at", snapshot_download(sys.argv[1]))
PY

echo "== serving $MODEL on :$PORT =="
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

run_cell() {
  local tag="$1"; shift
  local cond="$1"; shift
  local intents="$1"; shift
  local attackers="$1"
  echo "== cell $tag: $cond intents=$intents attackers=$attackers =="
  python scripts/run_experiment.py \
    --condition "$cond" --seeds "$SEEDS" --episodes "$EPISODES" \
    --backend vllm --attacker-mode llm --trace \
    --base-url "$BASE" --model "$MODEL" \
    --intents "$intents" --attackers "$attackers" \
    --out "results/$tag"
}

run_cell low_low        coalition low,low         2
run_cell medium_medium  coalition medium,medium   2
run_cell high_high      coalition high,high       2
run_cell high_medium    coalition high,medium     2
run_cell high3          coalition high,high,high  3
run_cell low3           coalition low,low,low     3
run_cell containment_high   containment high,high     2
run_cell containment_medium containment medium,medium 2

kill "$VPID" 2>/dev/null || true

echo "== archiving results (results_archive/) =="
ARCHIVE="results_archive/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$ARCHIVE"
cp -r results/sweep* "$ARCHIVE"/ 2>/dev/null || true
echo "archived to $ARCHIVE"

echo "== sweep summary =="
python - <<'PY'
import glob, json, os
for f in sorted(glob.glob("results/*/*.json")):
    d = json.load(open(f))
    keys = {k: d[k] for k in ("condition","seeds","activation_rate","attack_coverage","benign_fpr","benign_success","post_trigger_harm","contagion")}
    print(os.path.basename(os.path.dirname(f)), json.dumps(keys))
for tag in ("high_high", "containment_high"):
    eps = sorted(glob.glob(f"results/{tag}/episodes/*/*.json"))
    if eps:
        d = json.load(open(eps[0]))
        print(f"== trace sample: {tag} ({os.path.basename(eps[0])}) ==")
        atk = [t for t in d.get("trace", []) if t["role"] == "attacker"][:10]
        for t in atk:
            print("   ", t)
PY