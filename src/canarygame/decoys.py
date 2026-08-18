from __future__ import annotations

import random
from dataclasses import dataclass

CANARY_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"


@dataclass(frozen=True)
class Decoy:
    label: str
    kind: str
    token: str


def _token(rng: random.Random, length: int = 32) -> str:
    return "".join(rng.choice(CANARY_ALPHABET) for _ in range(length))


class DecoyRegistry:
    """Maps decoy secrets to internal trap labels.

    In the real experiment the registry is built from the dataset's internal
    decoy labels (D3): decoys share the surface form of real credentials and
    only the monitor knows the label mapping. The seeded generator exists for
    mock/test plumbing only.
    """

    def __init__(
        self,
        seed: int | None = None,
        n_decoys: int = 4,
        policy: str = "fixed",
        labels: dict[str, str] | None = None,
    ) -> None:
        self.policy = policy
        if labels is not None:
            self._decoy_map = {label: Decoy(label, "unbrokered_credential", secret) for label, secret in labels.items()}
            return
        self._rng = random.Random(seed)
        self._decoy_map = {
            f"trap-{i}": Decoy(f"trap-{i}", "unbrokered_credential", f"vlt_{_token(self._rng)}")
            for i in range(n_decoys)
        }

    @classmethod
    def from_labels(cls, labels: dict[str, str], policy: str = "fixed") -> DecoyRegistry:
        return cls(policy=policy, labels=labels)

    def decoys(self) -> list[Decoy]:
        return list(self._decoy_map.values())

    def token_to_label(self, token: str) -> str | None:
        for decoy in self._decoy_map.values():
            if decoy.token == token:
                return decoy.label
        return None

    def labels(self) -> dict[str, str]:
        return {label: decoy.token for label, decoy in self._decoy_map.items()}