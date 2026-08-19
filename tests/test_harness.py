from itertools import pairwise

from canarygame.agents import build_messages
from canarygame.config import load_conditions
from canarygame.harness import run_episode


def test_build_messages_roles_alternate():
    messages = build_messages(
        "sys",
        "task",
        ["read_file"],
        ["note"],
        2,
        history=[(0, "call_tool list_entries"), (1, "share_memory hi")],
    )
    roles = [m["role"] for m in messages]
    assert roles[0] == "system"
    tail = roles[1:]
    assert all(a != b for a, b in pairwise(tail))    assert tail[-1] == "user"


def test_episode_smoke_all_conditions():
    conditions = load_conditions()
    for name, cfg in conditions.items():
        result = run_episode(cfg, seed=0, episode=0)
        assert result.condition == name
        assert result.steps >= 0


def test_unbrokered_attacker_hits_decoys():
    cfg = load_conditions()["coalition"]
    result = run_episode(cfg, seed=0, episode=0)
    assert result.triggers
    assert result.harmful_sink_attempts


def test_containment_blocks_harm():
    cfg = load_conditions()["containment"]
    result = run_episode(cfg, seed=0, episode=0)
    assert result.harmful_sink_attempts == []
