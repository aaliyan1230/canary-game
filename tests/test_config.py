from canarygame.config import load_conditions


def test_conditions_loaded():
    conditions = load_conditions()
    assert set(conditions) == {"baseline", "coalition", "rotation", "containment"}


def test_containment_flags():
    cfg = load_conditions()["containment"]
    assert cfg.broker and cfg.quarantine and cfg.shared_memory
    assert cfg.decoy_policy == "private"


def test_baseline_isolated():
    cfg = load_conditions()["baseline"]
    assert not cfg.shared_memory and not cfg.broker
    assert cfg.decoy_policy == "fixed"
