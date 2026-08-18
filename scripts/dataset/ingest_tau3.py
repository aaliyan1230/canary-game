"""Ingest a curated benign-task subset from a local tau2-bench (tau3-bench) checkout.

Outputs `data/benign_tasks_tau3.jsonl` + a provenance meta file. The subset
keeps tasks whose goal is self-contained and whose required action count is
within SLM feasibility bounds. Provenance (source commit, license) is
recorded for audit.

Usage:
    TAU3_PATH=/path/to/tau2-bench uv run python scripts/dataset/ingest_tau3.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOMAINS = ["retail", "airline", "banking_knowledge"]
MAX_ACTIONS = int(os.environ.get("TAU3_MAX_ACTIONS", "5"))
SOURCE_URL = "https://github.com/sierra-research/tau2-bench"


def source_commit(path: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def load_tasks(path: Path, domain: str) -> list[dict]:
    task_file = path / "data" / "tau2" / "domains" / domain / "tasks.json"
    with task_file.open() as f:
        tasks = json.load(f)
    return tasks


def main() -> int:
    path = Path(os.environ.get("TAU3_PATH", "vendor/tau2-bench"))
    if not (path / "data").exists():
        print(f"tau2-bench checkout not found at {path}", file=sys.stderr)
        return 1

    out_dir = ROOT / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    counts: dict[str, int] = {}
    for domain in DOMAINS:
        kept = 0
        for task in load_tasks(path, domain):
            actions = task.get("evaluation_criteria", {}).get("actions", [])
            if not actions or len(actions) > MAX_ACTIONS:
                continue
            instructions = task.get("user_scenario", {}).get("instructions", "")
            if isinstance(instructions, dict):
                instructions = instructions.get("task_instructions", "")
            if not isinstance(instructions, str) or not instructions:
                continue
            records.append(
                {
                    "dataset_id": f"tau3/{domain}/task_{task['id']}",
                    "domain": domain,
                    "instructions": instructions,
                    "required_actions": [a["name"] for a in actions],
                    "n_actions": len(actions),
                }
            )
            kept += 1
        counts[domain] = kept

    out_jsonl = out_dir / "benign_tasks_tau3.jsonl"
    with out_jsonl.open("w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    meta = {
        "source": {"url": SOURCE_URL, "commit": source_commit(path)},
        "license": "MIT",
        "subset": {"max_actions": MAX_ACTIONS, "per_domain": counts, "total": len(records)},
        "generated": "2026-08-19",
    }
    (out_dir / "benign_tasks_tau3.meta.json").write_text(
        json.dumps(meta, indent=2) + "\n"
    )
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())