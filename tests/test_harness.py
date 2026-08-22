from itertools import pairwise

from canarygame.agents import build_messages, normalize_action, parse_action
from canarygame.broker import CapabilityBroker
from canarygame.config import load_conditions
from canarygame.decoys import DecoyRegistry
from canarygame.environment import decoy_labels, generate_store
from canarygame.harness import build_mock_record, run_episode
from canarygame.monitor import AgentAction, ReferenceMonitor
from canarygame.sandbox import Sandbox


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
    assert all(a != b for a, b in pairwise(tail))
    assert tail[-1] == "user"


def test_normalize_action_wrapped_verbs():
    cases = [
        ("call_tool use_credential secret=key_abc123", "use_credential", "key_abc123"),
        ('call_tool use_credential credential="tok_xyz"', "use_credential", "tok_xyz"),
        ("call_tool probe probe=abc", "probe", "abc"),
        ("call_tool use_credential vlt_deadbeef", "use_credential", "vlt_deadbeef"),
        ("use_credential secret=key_abc", "use_credential", "key_abc"),
        ("call_tool list_entries service=vault", "call_tool", "list_entries service=vault"),
    ]
    for raw, kind, payload in cases:
        act = normalize_action(parse_action(raw, "a", 0))
        assert act.kind == kind, raw
        assert act.payload == payload, raw


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


def test_private_mock_record_has_isolated_agent_surfaces():
    cfg = load_conditions()["containment"]
    record = build_mock_record(cfg, seed=0, episode=0)
    stores = record["surface"]["stores"]
    assert set(stores) == {"agent-0", "agent-1", "agent-2", "attacker-0", "attacker-1"}
    for trap, base_secret in record["internal"]["decoy_labels"].items():
        index = int(trap.removeprefix("trap_"))
        secrets = {entries[index]["secret"] for entries in stores.values()}
        assert len(secrets) == len(stores)
        assert base_secret not in secrets


def test_private_namespace_isolation_reaches_sink_and_monitor():
    store = generate_store(seed=0, episode=0, policy="private")
    names = ("agent-0", "agent-1")
    stores = {name: store.surface(name) for name in names}
    registries = {
        name: DecoyRegistry.from_labels(decoy_labels(store, name), policy="private")
        for name in names
    }
    sandbox = Sandbox(
        0,
        registries,
        broker=CapabilityBroker(0),
        tools=["list_entries"],
        store_entries=stores,
    )
    token_a = decoy_labels(store, "agent-0").popitem()[1]
    assert token_a in sandbox.execute_tool("agent-0", "list_entries")
    assert token_a not in sandbox.execute_tool("agent-1", "list_entries")
    assert sandbox.sink("agent-1", token_a, 0)[0] == "blocked"
    monitor = ReferenceMonitor(registries)
    assert monitor.observe(0, 0, "agent-1", "benign", AgentAction("probe", token_a)) is None
    assert monitor.observe(0, 0, "agent-0", "benign", AgentAction("probe", token_a)) is not None
