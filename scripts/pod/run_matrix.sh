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
nohup vllm serve "$MODEL" --port "$PORT" --max-model-len 8192 --gpu-memory-utilization 0.9 >/tmp/vllm.log 2>&1 &
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
python scripts/run_experiment.py \
  --condition "$CONDITIONS" \
  --seeds "$SEEDS" \
  --episodes "$EPISODES" \
  --backend vllm \
  --base-url "http://localhost:$PORT/v1" \
  --model "$MODEL" \
  --out results

kill "$VPID" 2>/dev/null || true

echo "== results (results/*.json) =="
for f in results/*.json; do echo "--- $f ---"; cat "$f"; done