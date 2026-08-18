from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "conditions.yaml"


@dataclass(frozen=True)
class ConditionConfig:
    name: str
    shared_memory: bool
    decoy_policy: str
    broker: bool
    quarantine: bool
    n_agents: int
    n_attackers: int
    attacker_intents: tuple[str, ...]
    n_decoys: int
    max_steps: int
    action_budget: int
    benign_tasks: int

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> ConditionConfig:
        return cls(name=name, **data)


def load_conditions(path: Path = CONFIG_PATH) -> dict[str, ConditionConfig]:
    raw = yaml.safe_load(path.read_text())
    return {
        name: ConditionConfig.from_dict(name, data)
        for name, data in raw["conditions"].items()
    }
