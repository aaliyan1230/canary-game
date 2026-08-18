"""Batch rollout entrypoint.

Usage:
    uv run python scripts/run_experiment.py --condition coalition --seeds 0-9
    uv run python scripts/run_experiment.py --condition all --seeds 0-2 --backend mock
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from canarygame.config import load_conditions
from canarygame.harness import run_episode
from canarygame.metrics import summarize


def parse_seeds(spec: str) -> list[int]:
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-")
            out.extend(range(int(lo), int(hi) + 1))
        else:
            out.append(int(part))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", default="coalition")
    parser.add_argument("--seeds", default="0")
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--out", default="results")
    args = parser.parse_args()

    conditions = load_conditions()
    if args.condition == "all":
        names = list(conditions)
    else:
        names = [args.condition]

    for name in names:
        cfg = conditions[name]
        results = [
            run_episode(cfg, seed, episode)
            for seed in parse_seeds(args.seeds)
            for episode in range(args.episodes)
        ]
        report = summarize(results)
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{name}.json"
        path.write_text(
            json.dumps(report.__dict__, indent=2, default=str)
        )
        print(f"{name}: {report}")


if __name__ == "__main__":
    main()
