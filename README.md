# laya-eval

Evaluating `convaiinnovations/laya`, a multilingual, non-autoregressive
"System 1" decision model positioned as an open-weight alternative to
TypeSafe AI's hosted `Jev`. Run via `aac6fef/laya-typed-decisions-mlx`,
locally on an M4 MacBook Pro (Apple silicon / MLX).

Compared against: hosted Jev (TypeSafe's API) and jevmlx (the local Jev
clone in the sibling `../openjev/` repo).

## Claim boundaries

- Phase 1 results are **agreement with the GPT-6 Astra + Claude Fable 5.1
  consensus label**, not "accuracy" — currently on 45 public cases across
  four workflows, not
  TypeSafe's full private eval.
- Local laya-mlx latency is only compared to local jevmlx latency, both on
  the same M4. Hosted Jev latency is cited, never plotted against local
  numbers — a local forward pass and a network API call aren't comparable.
- No mechanism claims. No claims about either vendor's training process.
- Every result states its n and whether ground truth exists.

Full rationale: [`design.md`](design.md). Status: [`PLAN.md`](PLAN.md).

To run Phase 1, create a Python 3.12 environment and install the MLX runtime:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install laya-mlx
scripts/fetch_typesafe_cases.sh
.venv/bin/python scripts/run_phase1.py
```

Not affiliated with TypeSafe AI or Convai Innovations. Personal / CoRe
research-engineering experiment.
