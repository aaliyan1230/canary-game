from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QuarantineRecord:
    agent: str
    trigger_step: int
    released_step: int | None = None


class QuarantineManager:
    """Per-agent isolation on trigger, with timed recovery."""

    def __init__(self, hold_steps: int = 10) -> None:
        self.hold_steps = hold_steps
        self.records: dict[str, QuarantineRecord] = {}

    def quarantine(self, agent: str, trigger_step: int) -> None:
        self.records[agent] = QuarantineRecord(agent, trigger_step)

    def release(self, agent: str, step: int) -> None:
        record = self.records.get(agent)
        if record is not None:
            record.released_step = step

    def is_quarantined(self, agent: str, step: int) -> bool:
        record = self.records.get(agent)
        if record is None:
            return False
        return step - record.trigger_step < self.hold_steps

    def release_due(self, step: int) -> list[str]:
        return [
            agent
            for agent, record in self.records.items()
            if record.released_step is None and not self.is_quarantined(agent, step)
        ]
