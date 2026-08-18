from __future__ import annotations

from canarygame.agents import Agent
from canarygame.monitor import AgentAction


class AttackerPolicy:
    """Adaptive probing strategy over the decoy space (scripted/mock path).

    Real attackers are LLM-driven via their prompt; this policy class is the
    deterministic fallback used in offline smoke tests.
    """

    def choose(
        self,
        step: int,
        observed_tokens: list[str],
        memory: list[str],
        budget: int,
    ) -> tuple[str, str]:
        raise NotImplementedError


class SequentialProbe(AttackerPolicy):
    """Probe registry entries one at a time until the budget is spent."""

    def __init__(self, pool: bool = False) -> None:
        self.pool = pool
        self._probed: list[str] = []

    def choose(
        self,
        step: int,
        observed_tokens: list[str],
        memory: list[str],
        budget: int,
    ) -> tuple[str, str]:
        candidates = [t for t in observed_tokens if t not in self._probed]
        if candidates and len(self._probed) < budget:
            token = candidates[0]
            self._probed.append(token)
            return "probe", token
        if self.pool and self._probed:
            return "share_memory", f"fingerprint {self._probed[-1]}"
        return "noop", ""


class AttackerAgent(Agent):
    """Deterministic attacker used in smoke tests (policy-driven)."""

    def __init__(
        self,
        name: str,
        llm,
        memory,
        sandbox,
        monitor,
        policy: AttackerPolicy,
        budget: int,
        system: str = "adversary",
        task: str = "vault access",
    ) -> None:
        super().__init__(name=name, llm=llm, memory=memory, sandbox=sandbox, monitor=monitor, system=system, task=task)
        self.policy = policy
        self.budget = budget

    def act(self, role: str, episode: int, step: int):
        memory = self.memory.read(self.name)
        observed = [
            line.split()[-1]
            for line in memory
            if line.startswith(("discovered ", "fingerprint "))
        ]
        kind, payload = self.policy.choose(step, observed, memory, self.budget)
        action = AgentAction(kind=kind, payload=payload, agent=self.name, step=step)
        if action.kind == "share_memory":
            self.memory.share(self.name, action.payload)
        event = self.monitor.observe(episode, step, self.name, role, action)
        return action, event