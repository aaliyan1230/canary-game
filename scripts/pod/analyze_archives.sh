#!/usr/bin/env bash
# Pod-side archive analysis: aggregates action kinds, triggers, and
# first-credential-attempt step across all archived episode traces.
# No vLLM; just reads results_archive/ and results/.
set -euo pipefail

python - <<'PY'
import glob, json, os
from collections import Counter, defaultdict

def analyze(root):
    eps = sorted(glob.glob(os.path.join(root, "episodes", "*", "*.json")))
    if not eps:
        return None
    agg = defaultdict(Counter)
    first_cred = defaultdict(lambda: 10**9)
    triggers = Counter()
    n = Counter()
    for f in eps:
        cond = os.path.basename(os.path.dirname(f))
        n[cond] += 1
        d = json.load(open(f))
        for t in d.get("trace", []):
            if t["role"] != "attacker":
                continue
            agg[cond][t["kind"]] += 1
            if t["trigger"]:
                triggers[cond] += 1
            if t["kind"] in ("use_credential", "probe"):
                first_cred[cond] = min(first_cred[cond], t["step"])
    return agg, first_cred, triggers, n

print("== analysis of archived episode traces ==")
for root in sorted(glob.glob("results_archive/*/")):
    res = analyze(root)
    if res is None:
        continue
    agg, first_cred, triggers, n = res
    print("---", os.path.basename(root.rstrip("/")))
    for cond in sorted(agg):
        a = dict(agg[cond])
        a["_triggers"] = triggers[cond]
        a["_first_cred_step"] = first_cred[cond]
        a["_episodes"] = n[cond]
        print("   ", cond, json.dumps(a))

res = analyze("results")
if res is not None:
    agg, first_cred, triggers, n = res
    print("--- (live results/)")
    for cond in sorted(agg):
        a = dict(agg[cond])
        a["_triggers"] = triggers[cond]
        a["_first_cred_step"] = first_cred[cond]
        a["_episodes"] = n[cond]
        print("   ", cond, json.dumps(a))
PY
