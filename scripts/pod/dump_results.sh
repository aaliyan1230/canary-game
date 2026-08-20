#!/usr/bin/env bash
# Pod-side dump of every condition-report JSON across all archives + live
# results, so authoritative numbers can be captured locally for figures.
set -euo pipefail

python - <<'PY'
import glob, json, os
seen = set()
for f in sorted(glob.glob("results_archive/*/*.json")) + sorted(glob.glob("results/*.json")):
    try:
        d = json.load(open(f))
    except Exception as e:
        print(f"###{os.path.abspath(f)} (unreadable: {e})")
        continue
    key = (os.path.abspath(f), json.dumps(d, sort_keys=True))
    if key in seen:
        continue
    seen.add(key)
    print(f"###{os.path.abspath(f)}")
    print(json.dumps(d, indent=2, default=str))
PY
