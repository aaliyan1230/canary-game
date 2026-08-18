from __future__ import annotations

import re
from typing import Protocol

from canarygame.monitor import AgentAction


class LLMBackend(Protocol):
    def complete(self, prompt: str) -> str: ...


ACTION_RE = re.compile(r"^(\w+)\s*(.*)$")


def parse_action(text: str, agent: str, step: int) -> AgentAction:
    match = ACTION_RE.match(text.strip().splitlines()[0])
    if match is None:
        return AgentAction(kind="noop", agent=agent, step=step)
    kind, payload = match.group(1), match.group(2).strip()
    return AgentAction(kind=kind, payload=payload, agent=agent, step=step)


class MockLLM:
    """Deterministic scripted backend for offline smoke tests."""

    def __init__(self, script: list[str]) -> None:
        self._script = list(script)
        self.calls: list[str] = []

    def complete(self, prompt: str) -> str:
        self.calls.append(prompt)
        return self._script.pop(0) if self._script else "noop"


def build_prompt(role: str, task: str, memory: list[str], step: int) -> str:
    mem = "\n".join(f"- {entry}" for entry in memory) or "(empty)"
    return (
        f"role: {role}\ntask: {task}\nstep: {step}\n"
        f"shared context:\n{mem}\n"
        "respond with one line: <action> <payload>"
    )


class Agent:
    def __init__(self, name: str, llm: LLMBackend, memory, sandbox, monitor) -> None:
        self.name = name
        self.llm = llm
        self.memory = memory
        self.sandbox = sandbox
        self.monitor = monitor

    def act(self, task: str, role: str, episode: int, step: int):
        prompt = build_prompt(role, task, self.memory.read(self.name), step)
        action = parse_action(self.llm.complete(prompt), self.name, step)
        self.memory.write(self.name, f"{action.kind} {action.payload}".strip())
        if action.kind == "share_memory":
            self.memory.share(self.name, action.payload)
        event = self.monitor.observe(episode, step, self.name, role, action)
        return action, event
