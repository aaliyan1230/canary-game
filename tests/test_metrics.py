import random

from canarygame.metrics import bootstrap_ci, summarize
from canarygame.monitor import TriggerEvent


def test_bootstrap_ci_contains_sample_mean():
    samples = [random.gauss(5.0, 1.0) for _ in range(200)]
    lo, hi = bootstrap_ci(samples, sum, seed=0)
    assert lo <= sum(samples) <= hi


def test_summarize_basic_metrics():
    from canarygame.metrics import EpisodeResult

    r1 = EpisodeResult(
        condition="coalition",
        seed=0,
        episode=0,
        triggers=[TriggerEvent(0, 5, "attacker", "trap-0-0", "attacker")],
        harmful_sink_attempts=[6],
        benign_success=1.0,
        benign_false_alarms=0,
        steps=40,
    )
    r2 = EpisodeResult(
        condition="coalition",
        seed=0,
        episode=1,
        triggers=[],
        benign_success=1.0,
        benign_false_alarms=1,
        steps=40,
    )
    report = summarize([r1, r2])
    assert report.activation_rate == 0.5
    assert report.attack_coverage == 0.5
    assert report.post_trigger_harm == 0.5
    assert "time_to_trigger" in report.ci
