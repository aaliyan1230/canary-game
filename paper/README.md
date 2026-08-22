# Paper build

```sh
cd paper
pdflatex paper.tex && pdflatex paper.tex   # run twice for refs
open paper.pdf
```

Output: 6 pages total = 4 pages main text + references + 2 appendices.
Figures live in `figures/` (regenerate via `uv run python scripts/figures/plot_results.py`
from `local/results/*/` JSONs).

# Pre-submission checklist (red TODOs in the PDF)

1. **Workshop name**: verify exact `\workshoptitle{}` string from the CFP.
2. **Blind policy**: currently `sglblindworkshop`. If the workshop is
   double-blind, swap to `\usepackage[dblblindworkshop]{neurips_2025}`
   (one line, top of paper.tex).
3. **"When Agents Talk" citation**: the theory we test has a red TODO where
   its citation belongs. Insert the real reference.
4. **25–53% benign-FPR comparison** needs a citation.
5. **Authors**: confirm names, affiliation line, email addresses, and final
   author order.
6. **Style year**: `neurips_2025.sty` is the current official file; when the
   workshop ships a 2026 style, drop it in and update `\usepackage`.
7. **Verify arXiv IDs** in the bibliography (tau2-bench 2506.07982,
   Qwen3 2505.09388, Gemma3 2503.19786).
8. **Dataset flip**: make `ic-org/canarygame-dataset` public right before
   submission (user-owned action).

# Data sources behind every number

- Table 1 / Fig 1: `local/results/qwen_core_matrix/*.json`
- Table 2: `local/results/sweep_v2/*.json`
- Fig 2 (appendix): same sweep JSONs; Fig 3: `gemma_80_step/` + Qwen core
- Fig 4 (appendix): Qwen core + 8B sanity archive (Lambda FS
  `results_archive/20260820T140833Z/`)
