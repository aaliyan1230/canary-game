from canarygame.decoys import DecoyRegistry


def test_from_labels_roundtrip():
    labels = {"trap_a": "vlt_secret_abc", "trap_b": "vlt_secret_def"}
    reg = DecoyRegistry.from_labels(labels)
    assert reg.token_to_label("vlt_secret_abc") == "trap_a"
    assert reg.token_to_label("vlt_secret_def") == "trap_b"
    assert reg.token_to_label("not-a-trap") is None


def test_generator_registry_roundtrip():
    reg = DecoyRegistry(seed=2, n_decoys=2, policy="fixed")
    decoy = reg.decoys()[0]
    assert reg.token_to_label(decoy.token) == decoy.label
    assert reg.token_to_label("not-a-trap") is None