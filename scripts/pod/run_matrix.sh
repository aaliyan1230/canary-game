#!/usr/bin/env bash
# Pod-side runner for the Phase 2 simulation matrix.
# Runs inside the repo clone on the Lambda shared FS, with the project venv
# active (installed by bootstrap_pod.sh via uv sync --frozen).
#
# Steps: (1) build the dataset deterministically (clone tau2-bench to /tmp,
# ingest + build + acceptance), (2) serve the SLM with vLLM, (3) run the
# condition slice, (4) print results. The pod is stopped by run.sh's trap.
set -euo pipefail

MODEL="${CANARY_MODEL:-Qwen/Qwen3-4B-Instruct-2507}"
PORT="${CANARY_PORT:-8000}"
CONDITIONS="${CANARY_CONDITIONS:-baseline,coalition,containment}"
SEEDS="${CANARY_SEEDS:-0-1}"
EPISODES="${CANARY_EPISODES:-1}"
TAU3_URL="https://github.com/sierra-research/tau2-bench.git"

echo "== dataset prep =="
TAU3_DIR=/tmp/tau2-bench
if [ ! -d "$TAU3_DIR/.git" ]; then
  git clone --depth 1 "$TAU3_URL" "$TAU3_DIR"
fi
TAU3_PATH="$TAU3_DIR" python scripts/dataset/ingest_tau3.py
python scripts/dataset/build_dataset.py --seeds 0-4 --episodes 3
python scripts/dataset/acceptance.py

echo "== serving $MODEL on :$PORT =="
echo "pre-downloading model (hf_transfer off for reliability)"
export HF_HUB_ENABLE_HF_TRANSFER=0
ok=0
for attempt in 1 2 3; do
  if python - "$MODEL" <<'PY'
import sys
from huggingface_hub import snapshot_download
p = snapshot_download(sys.argv[1])
print("model cached at", p)
PY
  then
    ok=1
    break
  fi
  echo "model download attempt $attempt failed; retrying" >&2
  sleep 5
done
if [ "$ok" != "1" ]; then
  echo "model download failed after 3 attempts" >&2
  exit 1
fi

nohup vllm serve "$MODEL" --port "$PORT" --max-model-len 16384 --gpu-memory-utilization 0.9 >/tmp/vllm.log 2>&1 &
VPID=$!
for _ in $(seq 1 240); do
  if curl -sf "http://localhost:$PORT/v1/models" >/dev/null; then break; fi
  sleep 5
  tail -n 3 /tmp/vllm.log 2>/dev/null || true
done
if ! curl -sf "http://localhost:$PORT/v1/models" >/dev/null; then
  echo "vLLM failed to come up" >&2
  tail -40 /tmp/vllm.log >&2 || true
  kill "$VPID" 2>/dev/null || true
  exit 1
fi
echo "vLLM ready"

echo "== running matrix: conditions=$CONDITIONS seeds=$SEEDS episodes=$EPISODES =="
ARGS=(
  --condition "$CONDITIONS"
  --seeds "$SEEDS"
  --episodes "$EPISODES"
  --backend vllm
  --attacker-mode llm
  --base-url "http://localhost:$PORT/v1"
  --model "$MODEL"
  --out results
)
if [ "${CANARY_TRACE:-0}" = "1" ]; then ARGS+=(--trace); fi
python scripts/run_experiment.py "${ARGS[@]}"

kill "$VPID" 2>/dev/null || true

echo "== results summary (results/*.json) =="
python - <<'PY'
import glob, json, os
for f in sorted(glob.glob("results/*.json")):
    d = json.load(open(f))
    keys = {k: d[k] for k in ("condition","seeds","activation_rate","attack_coverage","benign_fpr","benign_success","post_trigger_harm","contagion","mean_time_to_trigger")}
    print(json.dumps(keys))
eps = sorted(glob.glob("results/episodes/*/seed0_ep0.json"))
for f in eps[:2]:
    d = json.load(open(f))
    print(f"== trace sample: {os.path.basename(os.path.dirname(f))} ==")
    for t in d.get("trace", [])[:8]:
        print("   ", t)
PY