"""Batch rollout entrypoint.

Offline smoke (default):
    uv run python scripts/run_experiment.py --condition coalition --seeds 0-2 --backend mock

SLM simulation on a served vLLM endpoint (GPU pod):
    uv run python scripts/run_experiment.py --condition containment --seeds 0-4 \
        --backend vllm --base-url http://localhost:8000/v1 --model Qwen/Qwen3-4B-Instruct-2507 \
        --intents high medium
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from canarygame.agents import MockLLM, VLLMBackend
from canarygame.config import load_conditions
from canarygame.harness import run_episode
from canarygame.metrics import summarize

DATA = Path(__file__).resolve().parents[1] / "data"


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


def load_records() -> dict[tuple[str, int, int], dict]:
    path = DATA / "dataset_v1" / "records.jsonl"
    if not path.exists():
        return {}
    records = {}
    with path.open() as f:
        for line in f:
            r = json.loads(line)
            records[(r["condition"], r["seed"], r["episode"])] = r
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", default="coalition")
    parser.add_argument("--seeds", default="0")
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--backend", choices=["mock", "vllm"], default="mock")
    parser.add_argument("--base-url", default="http://localhost:8000/v1")
    parser.add_argument("--model", default="Qwen/Qwen3-4B-Instruct-2507")
    parser.add_argument("--intents", default=None, help="comma list, e.g. high,medium")
    parser.add_argument("--attacker-mode", choices=["scripted", "llm"], default="scripted",
                        help="scripted=deterministic smoke; llm=real model-driven attackers")
    parser.add_argument("--trace", action="store_true", help="record per-step action traces")
    parser.add_argument("--out", default="results")
    args = parser.parse_args()

    conditions = load_conditions()
    if args.condition == "all":
        names = list(conditions)
    else:
        names = [c.strip() for c in args.condition.split(",")]

    if args.backend == "vllm":
        backend = lambda script: VLLMBackend(base_url=args.base_url, model=args.model)
    else:
        backend = MockLLM
    intents = args.intents.split(",") if args.intents else None
    records = load_records()

    for name in names:
        cfg = conditions[name]
        results = []
        for seed in parse_seeds(args.seeds):
            for episode in range(args.episodes):
                record = records.get((name, seed, episode))
                results.append(run_episode(cfg, seed, episode, record=record, llm_factory=backend, attacker_intents=intents, attacker_mode=args.attacker_mode, record_trace=args.trace))
        report = summarize(results)
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"{name}.json"
        path.write_text(json.dumps(report.__dict__, indent=2, default=str))
        ep_dir = out / "episodes" / name
        ep_dir.mkdir(parents=True, exist_ok=True)
        for r in results:
            (ep_dir / f"seed{r.seed}_ep{r.episode}.json").write_text(
                json.dumps(dataclasses.asdict(r), indent=2, default=str)
            )
        print(f"{name}: {report}")


if __name__ == "__main__":
    main()