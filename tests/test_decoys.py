from canarygame.decoys import DecoyRegistry


def test_fixed_policy_persists_across_episodes():
    reg = DecoyRegistry(seed=1, n_decoys=4, policy="fixed")
    reg.begin_episode(0)
    fixed = {d.label: d.token for d in reg.decoys()}
    reg.begin_episode(1)
    assert {d.label: d.token for d in reg.decoys()} == fixed


def test_per_episode_policy_rotates():
    reg = DecoyRegistry(seed=1, n_decoys=4, policy="per_episode")
    reg.begin_episode(0)
    first = {d.label: d.token for d in reg.decoys()}
    reg.begin_episode(1)
    second = {d.label: d.token for d in reg.decoys()}
    assert set(first) == set(second)
    assert all(first[label] != second[label] for label in first)


def test_token_to_label_roundtrip():
    reg = DecoyRegistry(seed=2, n_decoys=2, policy="fixed")
    reg.begin_episode(0)
    decoy = reg.decoys()[0]
    assert reg.token_to_label(decoy.token) == decoy.label
    assert reg.token_to_label("not-a-trap") is None
