# CanaryGame

Controlled empirical test of the shared-memory honeytoken boundary in
multi-agent LLM systems: do finite LLM-agent coalitions learn honeytoken
fingerprints before containment, and can an external provenance broker stop
the resulting damage?

Local, fully synthetic sandbox. 3+ open-weight agents share a tool registry
and memory; decoy credentials are planted; adaptive attackers probe the
decoy space and pool fingerprints; a private reference monitor, per-agent
isolated trap namespaces, and automatic quarantine restore detection.
Four conditions: `baseline`, `coalition`, `rotation`, `containment`.

## Quickstart

```sh
uv sync
uv run pytest
uv run ruff check
uv run python scripts/run_experiment.py --condition coalition --seeds 0-2 --backend mock
```

## Layout

- `src/canarygame/` — sandbox, decoys, broker, monitor, quarantine, agents,
  attackers, harness, metrics
- `configs/conditions.yaml` — per-condition parameters
- `scripts/` — batch rollout entrypoint
- `local/` — private working notes and experiment design (separate Git repo,
  never pushed here)

## Design

Experiment design lives in `local/docs/experiment-design.md` (private).
Safety: no live MCP servers, no external targets, no real credentials, no
network egress; the sandbox sink only mutates scored local state.
