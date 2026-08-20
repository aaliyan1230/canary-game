#!/usr/bin/env bash
# Pod-side Gemma-3-4B robustness subset.
# 1) Preserves + prints the current results tree (incl. any sweep cells) into
#    results_archive before the matrix run touches results/.
# 2) Runs the 4-condition core matrix on Gemma-3-4B-IT, mirroring the Qwen
#    core matrix (seeds 0-4 x 2 episodes = n=10/condition) for a direct
#    cross-model comparison.
# Requires HF_TOKEN in the environment (gated model).
set -euo pipefail

echo "== preserving current results tree =="
ARCHIVE="results_archive/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$ARCHIVE"
cp -r results/* "$ARCHIVE"/ 2>/dev/null || true
echo "preserved to $ARCHIVE"

echo "== sweep cells found (pre-matrix) =="
python - <<'PY'
import glob, json, os
for f in sorted(glob.glob("results/*/*.json")):
    d = json.load(open(f))
    keys = {k: d[k] for k in ("condition","seeds","activation_rate","attack_coverage","benign_fpr","benign_success","post_trigger_harm","contagion")}
    print(os.path.basename(os.path.dirname(f)), json.dumps(keys))
PY

export CANARY_MODEL="${CANARY_MODEL:-google/gemma-3-4b-it}"
export CANARY_CONDITIONS="${CANARY_CONDITIONS:-baseline,coalition,rotation,containment}"
export CANARY_SEEDS="${CANARY_SEEDS:-0-4}"
export CANARY_EPISODES="${CANARY_EPISODES:-2}"
export CANARY_TRACE="${CANARY_TRACE:-1}"
if [ -n "${CANARY_STEPS:-}" ]; then
  export RUN_ARGS="--max-steps $CANARY_STEPS"
else
  export RUN_ARGS=""
fi
bash scripts/pod/run_matrix.sh
