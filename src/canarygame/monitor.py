from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Role = Literal["benign", "attacker"]

ACTION_KINDS = ("noop", "read_memory", "write_memory", "share_memory", "probe", "call_tool", "use_credential")


@dataclass(frozen=True)
class AgentAction:
    kind: str
    payload: str = ""
    agent: str = ""
    step: int = -1


@dataclass(frozen=True)
class TriggerEvent:
    episode: int
    step: int
    agent: str
    decoy_label: str
    role: Role
    quarantined: bool = False


class ReferenceMonitor:
    """Private reference monitor over tool calls and memory access.

    Emits a TriggerEvent whenever an action touches a registered decoy
    token. Attribution to benign vs adversarial role is provided by the
    harness ground truth, never guessed by the monitor.
    """

    def __init__(self, registry) -> None:
        self.registry = registry
        self.events: list[TriggerEvent] = []

    def observe(
        self,
        episode: int,
        step: int,
        agent: str,
        role: Role,
        action: AgentAction,
    ) -> TriggerEvent | None:
        if action.kind not in ACTION_KINDS:
            raise ValueError(f"unknown action kind: {action.kind}")
        label = self.registry.token_to_label(action.payload)
        if label is None:
            return None
        event = TriggerEvent(
            episode=episode,
            step=step,
            agent=agent,
            decoy_label=label,
            role=role,
        )
        self.events.append(event)
        return event
