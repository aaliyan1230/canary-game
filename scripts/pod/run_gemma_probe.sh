#!/usr/bin/env bash
# Pod-side Gemma-3-4B behavior probe + archive viewer.
# 1) Prints every results_archive/* summary (sweep v2 cells + any matrices).
# 2) Serves Gemma-3-4B and runs a tiny attacker probe (coalition+containment,
#    seeds 0-1, trace) with RAW model outputs captured, so attacker behavior
#    can be diagnosed from the exact tokens the model emits.
# Requires HF_TOKEN in the environment (gated model).
set -euo pipefail

MODEL="${CANARY_MODEL:-google/gemma-3-4b-it}"
PORT="${CANARY_PORT:-8000}"
SEEDS="${CANARY_SEEDS:-0-1}"
BASE="http://localhost:$PORT/v1"

echo "== all archived summaries (results_archive/) =="
python - <<'PY'
import glob, json, os
for root in sorted(glob.glob("results_archive/*/")):
    print("---", os.path.basename(root.rstrip("/")))
    for f in sorted(glob.glob(os.path.join(root, "*", "*.json"))):
        try:
            d = json.load(open(f))
        except Exception as e:
            print("   unreadable", os.path.basename(f), e)
            continue
        keys = {k: d[k] for k in ("condition","seeds","activation_rate","attack_coverage","benign_fpr","benign_success","post_trigger_harm","contagion")}
        print("   ", os.path.basename(os.path.dirname(f)), json.dumps(keys))
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

echo "== direct prompt framing probe =="
python scripts/pod/gemma_prompt_probe.py "$BASE" "$MODEL"

echo "== probe: coalition =="
OUT="results/gemma_probe"
mkdir -p "$OUT"
for cond in coalition containment; do
  echo "== probe: $cond =="
  python scripts/run_experiment.py \
    --condition "$cond" --seeds "$SEEDS" --episodes 1 \
    --backend vllm --attacker-mode llm --trace \
    --base-url "$BASE" --model "$MODEL" \
    --intents high,high --attackers 2 \
    --out "$OUT/$cond" || echo "probe cell failed (see above)"
done

kill "$VPID" 2>/dev/null || true

echo "== raw attacker outputs (probe traces) =="
python - "$OUT" <<'PY'
import glob, json, sys
root = sys.argv[1]
for f in sorted(glob.glob(f"{root}/*/episodes/*/*.json")):
    d = json.load(open(f))
    print("=====", f)
    for t in d.get("trace", []):
        if t["role"] == "attacker" and t["text"]:
            print(f"[{t['step']} {t['kind']} {t['payload']!r}]")
            print("   RAW:", t["text"].replace(chr(10), " / ")[:300])
PY

echo "== probe summary =="
python - "$OUT" <<'PY'
import glob, json, os, sys
root = sys.argv[1]
for f in sorted(glob.glob(f"{root}/*/*.json")):
    d = json.load(open(f))
    keys = {k: d[k] for k in ("condition","seeds","activation_rate","attack_coverage","post_trigger_harm","contagion")}
    print(os.path.basename(os.path.dirname(f)), json.dumps(keys))
PY
