# Paper build

```sh
cd paper
pdflatex paper.tex && pdflatex paper.tex   # run twice for refs
open paper.pdf
```

Output: 6 pages total = 4 pages main text + references + 2 appendices.
Figures live in `figures/` (regenerate via `uv run python scripts/figures/plot_results.py`
from `local/results/*/` JSONs).

# Submission status

- Target: **Third Workshop on Agents in the Wild: Safety, Security, and
  Beyond**, NeurIPS 2026 short-paper track.
- Review policy: double-blind. `paper.tex` uses `dblblindworkshop`; author
  metadata remains in the source for the camera-ready version but is hidden in
  the submission PDF.
- Format: the workshop accepts NeurIPS, ICLR, ICML, ACL, and CVPR templates.
  This paper uses the included NeurIPS workshop style and omits the main-track
  checklist, as the workshop instructions allow.
- Bibliography IDs and the two comparison citations were checked against their
  arXiv records.
- Keep `ic-org/canarygame-dataset` private during double-blind review. If data
  accompanies the submission, upload an anonymized supplementary copy; the
  public release after review remains a user-owned action.

# Data sources behind every number

- Table 1 / Fig 1: `local/results/qwen_core_matrix/*.json`
- Table 2: `local/results/sweep_v2/*.json`
- Fig 2 (appendix): same sweep JSONs; Fig 3: `gemma_80_step/` + Qwen core
- Fig 4 (appendix): Qwen core + 8B sanity archive (Lambda FS
  `results_archive/20260820T140833Z/`)
