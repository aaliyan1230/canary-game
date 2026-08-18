from __future__ import annotations


class MemoryStore:
    """Per-agent memory with an optional shared pool (the coalition channel)."""

    def __init__(self, shared: bool) -> None:
        self.shared = shared
        self._shared_entries: list[str] = []
        self._agent_entries: dict[str, list[str]] = {}

    def read(self, agent: str) -> list[str]:
        entries = list(self._agent_entries.get(agent, []))
        if self.shared:
            entries.extend(self._shared_entries)
        return entries

    def write(self, agent: str, entry: str) -> None:
        self._agent_entries.setdefault(agent, []).append(entry)

    def share(self, agent: str, entry: str) -> None:
        if not self.shared:
            raise ValueError(f"memory is not shared: {agent}")
        self._shared_entries.append(entry)
