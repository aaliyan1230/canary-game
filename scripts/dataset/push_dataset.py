"""Push dataset v1 to ic-org/canarygame-dataset (private).

Per AGENTS.md: the dataset is private during development; the public flip is
user-owned and happens only right before submission. This script never
publishes.

Usage:
    uv run python scripts/dataset/push_dataset.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
REPO_ID = "ic-org/canarygame-dataset"


def main() -> int:
    from huggingface_hub import HfApi

    api = HfApi()
    who = api.whoami()
    print(f"authenticated as: {who['name']}")

    manifest = json.loads((DATA / "dataset_v1" / "manifest.json").read_text())

    api.create_repo(
        repo_id=REPO_ID,
        repo_type="dataset",
        private=True,
        exist_ok=True,
    )
    print(f"repo ready: {REPO_ID} (private={api.repo_info(REPO_ID, repo_type='dataset').private})")

    card = f"""# CanaryGame dataset v1

Fully synthetic environment + task data for the CanaryGame experiment.

- `records.jsonl` — per (condition, seed, episode) surface + internal decoy
  labels + benign task assignments + attacker prompts (low/medium/high intent).
- `benign_tasks_tau3.jsonl` — curated subset of τ³-bench
  (sierra-research/tau2-bench, MIT) task goals used as the benign baseline.
- `manifest.json` — version, seeds, episodes, content hash:
  {json.dumps(manifest)}.

No real credentials, targets, or PII. Private during development; flipped
public by the project owners before paper submission for open audit.
"""
    artifacts = {
        "records.jsonl": DATA / "dataset_v1" / "records.jsonl",
        "benign_tasks_tau3.jsonl": DATA / "benign_tasks_tau3.jsonl",
        "manifest.json": DATA / "dataset_v1" / "manifest.json",
        "README.md": None,
    }
    for path_in_repo, local in artifacts.items():
        content = card.encode() if local is None else None
        api.upload_file(
            path_or_fileobj=local.open("rb").read() if local else content,
            path_in_repo=path_in_repo,
            repo_id=REPO_ID,
            repo_type="dataset",
        )
        print(f"uploaded {path_in_repo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())