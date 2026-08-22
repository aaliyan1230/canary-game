from canarygame.environment import decoy_labels, generate_store


def test_fixed_policy_persists_across_episodes():
    a = generate_store(seed=1, episode=0, policy="fixed")
    b = generate_store(seed=1, episode=5, policy="fixed")
    assert [e.secret for e in a.entries] == [e.secret for e in b.entries]
    assert a.decoy_indices == b.decoy_indices


def test_per_episode_policy_rotates():
    a = generate_store(seed=1, episode=0, policy="per_episode")
    b = generate_store(seed=1, episode=1, policy="per_episode")
    assert [e.secret for e in a.entries] != [e.secret for e in b.entries]
    assert len(a.entries) == len(b.entries)
    assert a.decoy_indices != b.decoy_indices


def test_private_policy_per_agent_variants():
    store = generate_store(seed=2, episode=0, policy="private")
    base = {i: e.secret for i, e in enumerate(store.entries)}
    for i in store.decoy_indices:
        assert store.surface("agent-a")[i]["secret"] != base[i]
        assert store.surface("agent-a")[i]["secret"] != store.surface("agent-b")[i]["secret"]


def test_label_not_in_surface():
    store = generate_store(seed=2, episode=0, policy="fixed")
    labels = decoy_labels(store)
    import json

    surface = json.dumps(store.surface())
    for label in labels:
        assert label not in surface


def test_private_decoy_labels_follow_agent_surfaces():
    store = generate_store(seed=2, episode=0, policy="private")
    for agent in ("agent-a", "agent-b"):
        labels = decoy_labels(store, agent)
        for trap, secret in labels.items():
            index = int(trap.removeprefix("trap_"))
            assert secret == store.surface(agent)[index]["secret"]
