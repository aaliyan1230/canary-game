#!/usr/bin/env python3
"""Generate CanaryGame result figures from authoritative condition-report
JSONs saved under local/results/{qwen_core_matrix,gemma_80_step}. The intent
gradient figure uses the pilot sweep numbers (n=2) from
local/results/sweep-analysis.md. Outputs PNGs to local/results/figures/.
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RESULTS = Path(__file__).resolve().parents[2] / "local" / "results"
OUT = RESULTS / "figures"
OUT.mkdir(parents=True, exist_ok=True)

CONDITIONS = ["baseline", "coalition", "rotation", "containment"]
COLORS = ["#4c72b0", "#dd8452", "#55a868", "#c44e52"]

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linewidth": 0.6,
})


def load_matrix(name: str) -> dict[str, dict]:
    root = RESULTS / name
    return {c: json.loads((root / f"{c}.json").read_text()) for c in CONDITIONS}


def ci_of(d: dict, key: str) -> tuple[float, float]:
    return tuple(d["ci"][key])


def fig1_core_matrix() -> None:
    q = load_matrix("qwen_core_matrix")
    x = np.arange(len(CONDITIONS))
    harm = [q[c]["post_trigger_harm"] for c in CONDITIONS]
    harm_ci = [ci_of(q[c], "post_trigger_harm") for c in CONDITIONS]
    act = [q[c]["activation_rate"] for c in CONDITIONS]
    contagion = [q[c]["contagion"] for c in CONDITIONS]
    fpr = [q[c]["benign_fpr"] for c in CONDITIONS]

    fig, axes = plt.subplots(2, 2, figsize=(9.5, 6.2))
    ax = axes[0, 0]
    ax.bar(x, act, 0.55, color=COLORS, alpha=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels([c.capitalize() for c in CONDITIONS])
    ax.set_ylabel("trap activation (rate)")
    ax.set_ylim(0, 1.0)
    ax.set_title("(a) Trap activation (n=10)")

    ax = axes[0, 1]
    lows = [c[0] for c in harm_ci]
    highs = [c[1] for c in harm_ci]
    yerr = np.array([
        [ha - lo for ha, lo in zip(harm, lows)],
        [hi - ha for hi, ha in zip(highs, harm)],
    ])
    ax.bar(x, harm, 0.55, color=COLORS, alpha=0.9, yerr=yerr, capsize=4)
    for xi, h in zip(x, harm):
        if h == 0:
            ax.text(xi, 0.6, "0.0", ha="center", va="bottom", fontsize=8, color="#444")
    ax.set_xticks(x)
    ax.set_xticklabels([c.capitalize() for c in CONDITIONS])
    ax.set_ylabel("post-trigger harm (steps)")
    ax.set_ylim(0, 40)
    ax.set_title("(b) Post-trigger harm (95% CI)")

    ax = axes[1, 0]
    ax.bar(x, contagion, 0.55, color=COLORS, alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([c.capitalize() for c in CONDITIONS])
    ax.set_ylabel("contagion (shared fingerprints)")
    ax.set_ylim(0, 20)
    ax.set_title("(c) Contagion")

    ax = axes[1, 1]
    ax.bar(x, [f * 100 for f in fpr], 0.55, color=COLORS, alpha=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels([c.capitalize() for c in CONDITIONS])
    ax.set_ylabel("benign false-positive rate (%)")
    ax.set_ylim(0, 3)
    ax.set_title("(d) Benign false-positive rate")

    fig.tight_layout()
    fig.savefig(OUT / "fig1_core_matrix.png", dpi=200)
    plt.close(fig)
    print("wrote", OUT / "fig1_core_matrix.png")


def annotate(ax, x, vals, ymax, fmt="{:.2f}"):
    for xi, v in zip(x, vals):
        if v == 0:
            ax.text(xi, ymax * 0.02, "0", ha="center", va="bottom", fontsize=7, color="#666")
        elif v < 0.3:
            ax.text(xi, v + ymax * 0.03, fmt.format(v), ha="center", va="bottom", fontsize=7)


def fig2_intent_gradient() -> None:
    cells = {
        "low,low": "low_low",
        "medium,medium": "medium_medium",
        "high,high": "high_high",
        "high,medium": "high_medium",
        "high,high,high": "high3",
        "containment high": "containment_high",
        "containment medium": "containment_medium",
    }
    names = list(cells)
    data = {n: json.loads((RESULTS / "sweep_v2" / f"{cells[n]}.json").read_text()) for n in names}
    act = [data[n]["activation_rate"] for n in names]
    harm = [data[n]["post_trigger_harm"] for n in names]
    contagion = [data[n]["contagion"] for n in names]
    harm_lo = [data[n]["ci"]["post_trigger_harm"][0] for n in names]
    harm_hi = [data[n]["ci"]["post_trigger_harm"][1] for n in names]
    colors = ["#8da0cb" if "low" in n else "#ffd92f" if "medium" in n else "#e78ac3" if "containment" in n else "#66c2a5" for n in names]

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.6))
    ax = axes[0]
    ax.bar(range(len(names)), act, 0.6, color=colors)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("trap activation")
    ax.set_ylim(0, 1.1)
    ax.set_title("(a) Activation by attacker intent (n=5)")
    annotate(ax, range(len(names)), act, 1.1)

    ax = axes[1]
    w = 0.38
    x = np.arange(len(names))
    yerr = np.array([
        [ha - lo for ha, lo in zip(harm, harm_lo)],
        [hi - ha for hi, ha in zip(harm_hi, harm)],
    ])
    ax.bar(x - w / 2, harm, w, color=colors, alpha=0.95, yerr=yerr, capsize=3)
    ax.bar(x + w / 2, contagion, w, color=colors, alpha=0.4, hatch="//")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("steps")
    ax.set_ylim(0, 34)
    from matplotlib.patches import Patch
    ax.legend(
        handles=[
            Patch(facecolor="#666666", alpha=0.95, label="post-trigger harm"),
            Patch(facecolor="#666666", alpha=0.4, hatch="//", label="contagion"),
        ],
        frameon=False,
        loc="upper left",
        fontsize=8,
    )
    ax.set_title("(b) Harm (95% CI) vs contagion")
    for xi, h in zip(x, harm):
        if h == 0:
            ax.text(xi, 0.5, "0", ha="center", va="bottom", fontsize=7, color="#666")
    fig.tight_layout()
    fig.savefig(OUT / "fig2_intent_gradient.png", dpi=200)
    plt.close(fig)
    print("wrote", OUT / "fig2_intent_gradient.png")


def fig4_model_size() -> None:
    m = ["Qwen3-4B", "Qwen3-8B"]
    q4 = json.loads((RESULTS / "qwen_core_matrix" / "coalition.json").read_text())
    q8 = {"activation_rate": 0.3, "post_trigger_harm": 1.9, "contagion": 1.9, "benign_success": 1.0, "benign_fpr": 0.0}
    c4 = json.loads((RESULTS / "qwen_core_matrix" / "containment.json").read_text())
    c8 = {"activation_rate": 0.4, "post_trigger_harm": 0.0, "contagion": 0.9, "benign_success": 1.0, "benign_fpr": 0.0}
    coa = [q4, q8]
    con = [c4, c8]
    x = np.arange(2)
    w = 0.34
    model_col = ["#4c72b0", "#dd8452"]

    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.4))
    ax = axes[0]
    for i in range(2):
        ax.bar(x[i] - w / 2, coa[i]["activation_rate"], w, color=model_col[i], alpha=0.95)
        ax.bar(x[i] + w / 2, con[i]["activation_rate"], w, color=model_col[i], alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(m)
    ax.set_ylabel("trap activation")
    ax.set_ylim(0, 1.0)
    ax.set_title("(a) Activation (n=10)")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor="#666", alpha=0.95, label="coalition"), Patch(facecolor="#666", alpha=0.5, label="containment")], frameon=False, loc="upper left", fontsize=8)

    ax = axes[1]
    for i in range(2):
        ax.bar(x[i] - w / 2, coa[i]["post_trigger_harm"], w, color=model_col[i], alpha=0.95)
        ax.bar(x[i] + w / 2, con[i]["post_trigger_harm"], w, color=model_col[i], alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(m)
    ax.set_ylabel("post-trigger harm")
    ax.set_ylim(0, 20)
    ax.set_title("(b) Post-trigger harm")
    for i in range(2):
        ax.text(x[i] - w / 2, coa[i]["post_trigger_harm"] + 0.4, f"{coa[i]['post_trigger_harm']:.1f}", ha="center", va="bottom", fontsize=7)
        if con[i]["post_trigger_harm"] == 0:
            ax.text(x[i] + w / 2, 0.4, "0.0", ha="center", va="bottom", fontsize=7, color="#666")

    ax = axes[2]
    for i in range(2):
        ax.bar(x[i] - w / 2, coa[i]["benign_success"], w, color=model_col[i], alpha=0.95)
        ax.bar(x[i] + w / 2, con[i]["benign_success"], w, color=model_col[i], alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(m)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("benign success")
    ax.set_title("(c) Benign success")
    fig.tight_layout()
    fig.savefig(OUT / "fig4_model_size.png", dpi=200)
    plt.close(fig)
    print("wrote", OUT / "fig4_model_size.png")


def fig3_robustness() -> None:
    q = load_matrix("qwen_core_matrix")
    g = load_matrix("gemma_80_step")
    x = np.arange(len(CONDITIONS))
    w = 0.35
    qn = "Qwen3-4B (40-step)"
    gn = "Gemma3-4B (80-step)"

    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.6))
    ax = axes[0]
    qa = [q[c]["activation_rate"] for c in CONDITIONS]
    ga = [g[c]["activation_rate"] for c in CONDITIONS]
    ax.bar(x - w / 2, qa, w, color="#4c72b0", label=qn)
    ax.bar(x + w / 2, ga, w, color="#dd8452", label=gn)
    ax.set_xticks(x)
    ax.set_xticklabels([c.capitalize() for c in CONDITIONS])
    ax.set_ylabel("trap activation")
    ax.set_ylim(0, 1.0)
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2)
    ax.set_title("(a) Attack engagement (model-sensitive)")
    annotate(ax, x - w / 2, qa, 1.0)
    annotate(ax, x + w / 2, ga, 1.0)

    ax = axes[1]
    qs = [q[c]["benign_success"] for c in CONDITIONS]
    gs = [g[c]["benign_success"] for c in CONDITIONS]
    ax.bar(x - w / 2, qs, w, color="#4c72b0", label=qn)
    ax.bar(x + w / 2, gs, w, color="#dd8452", label=gn)
    ax.set_xticks(x)
    ax.set_xticklabels([c.capitalize() for c in CONDITIONS])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("benign success")
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2)
    ax.set_title("(b) Benign success (model-stable)")

    ax = axes[2]
    qf = [q[c]["benign_fpr"] * 100 for c in CONDITIONS]
    gf = [g[c]["benign_fpr"] * 100 for c in CONDITIONS]
    ax.bar(x - w / 2, qf, w, color="#4c72b0", label=qn)
    ax.bar(x + w / 2, gf, w, color="#dd8452", label=gn)
    ax.set_xticks(x)
    ax.set_xticklabels([c.capitalize() for c in CONDITIONS])
    ax.set_ylabel("benign false-positive rate (%)")
    ax.set_ylim(0, 2.5)
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2)
    ax.set_title("(c) Benign FPR (model-stable)")
    annotate(ax, x - w / 2, qf, 2.5)
    annotate(ax, x + w / 2, gf, 2.5)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_robustness.png", dpi=200)
    plt.close(fig)
    print("wrote", OUT / "fig3_robustness.png")


if __name__ == "__main__":
    fig1_core_matrix()
    fig2_intent_gradient()
    fig3_robustness()
    fig4_model_size()
    print("done")
