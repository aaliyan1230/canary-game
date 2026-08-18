"""Dataset v1 acceptance checks.

Checks: determinism (re-run -> same hash), no internal-label leakage into
surface text, benign-task referential integrity, and secret hygiene scan
(no real credential patterns in generated content).

Usage:
    uv run python scripts/dataset/acceptance.py
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECORDS = ROOT / "data" / "dataset_v1" / "records.jsonl"

REAL_SECRET_PATTERNS = [
    re.compile(r"hf_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}"),
]


def load_records() -> list[dict]:
    with RECORDS.open() as f:
        return [json.loads(line) for line in f]


def check_determinism(records: list[dict]) -> bool:
    fresh = subprocess.check_output(
        [sys.executable, "build_dataset.py", "--seeds", "0-4", "--episodes", "3"],
        cwd=Path(__file__).parent,
        text=True,
    )
    manifest = json.loads(fresh)
    current = hashlib.sha256(RECORDS.read_bytes()).hexdigest()
    ok = current == manifest["records_sha256"]
    print(f"[{'PASS' if ok else 'FAIL'}] determinism: {current}")
    return ok


def check_label_leak(records: list[dict]) -> bool:
    ok = True
    for rec in records:
        labels = set(rec["internal"]["decoy_labels"])
        surface = json.dumps(rec["surface"])
        leaked = {lbl for lbl in labels if lbl in surface}
        if leaked:
            ok = False
            print(f"[FAIL] label leak in {rec['condition']}/{rec['seed']}/{rec['episode']}: {leaked}")
    if ok:
        print("[PASS] no internal label leakage into surface")
    return ok


def check_task_integrity(records: list[dict]) -> bool:
    tasks = set()
    with (ROOT / "data" / "benign_tasks_tau3.jsonl").open() as f:
        for line in f:
            tasks.add(json.loads(line)["dataset_id"])
    ok = True
    for rec in records:
        missing = [t for t in rec["benign_tasks"] if t not in tasks]
        if missing:
            ok = False
            print(f"[FAIL] unknown task ids {missing}")
    if ok:
        print(f"[PASS] benign tasks reference {len(records)} records consistently")
    return ok


def check_secret_hygiene(records: list[dict]) -> bool:
    ok = True
    blob = json.dumps(records)
    for pat in REAL_SECRET_PATTERNS:
        if pat.search(blob):
            ok = False
            print(f"[FAIL] real-secret pattern matched: {pat.pattern}")
    if ok:
        print("[PASS] no real credential patterns in dataset")
    return ok


def check_schema(records: list[dict]) -> bool:
    required = {"condition", "policy", "seed", "episode", "surface", "internal", "benign_tasks", "attacker_prompts"}
    ok = all(required <= set(r) for r in records)
    for r in records:
        if r["attacker_prompts"].keys() != {"low", "medium", "high"}:
            ok = False
    print(f"[{'PASS' if ok else 'FAIL'}] schema (all records carry required keys + 3 intent levels)")
    return ok


def main() -> int:
    records = load_records()
    checks = [
        check_schema(records),
        check_task_integrity(records),
        check_label_leak(records),
        check_secret_hygiene(records),
        check_determinism(records),
    ]
    passed = sum(checks)
    print(f"\n{passed}/{len(checks)} checks passed")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())