from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class Credential:
    task: str
    secret: str
    issued_step: int
    ttl_steps: int

    @property
    def expired(self) -> bool:
        return False  # expiry is evaluated against a step, see CapabilityBroker


class CapabilityBroker:
    """The only legitimate source of credentials.

    Issues short-lived, task-scoped credentials. A credential is valid only
    if issued by the broker and not yet expired at the given step.
    """

    def __init__(self, seed: int, ttl_steps: int = 5) -> None:
        self._rng = random.Random(seed)
        self.ttl_steps = ttl_steps
        self._issued: list[Credential] = []

    def issue(self, task: str, step: int) -> Credential:
        cred = Credential(
            task=task,
            secret=f"brk-{self._rng.randrange(10**12):012x}",
            issued_step=step,
            ttl_steps=self.ttl_steps,
        )
        self._issued.append(cred)
        return cred

    def is_valid(self, secret: str, step: int) -> bool:
        return any(
            c.secret == secret and step - c.issued_step < c.ttl_steps
            for c in self._issued
        )

    def revoke_all(self) -> None:
        self._issued.clear()
