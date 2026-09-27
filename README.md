# laya-eval

Evaluating `convaiinnovations/laya`, a multilingual, non-autoregressive
"System 1" decision model positioned as an open-weight alternative to
TypeSafe AI's hosted `Jev`. Run via `aac6fef/laya-typed-decisions-mlx`,
locally on an M4 MacBook Pro (Apple silicon / MLX).

Compared against: hosted Jev (TypeSafe's API) and jevmlx (the local Jev
clone in the sibling `../openjev/` repo).

## Claim boundaries

- Public-20 results are **agreement with the GPT-6 Astra + Claude Fable 5.1
  consensus label**, not "accuracy" — and on 20 public cases, not
  TypeSafe's full private eval.
- Local laya-mlx latency is only compared to local jevmlx latency, both on
  the same M4. Hosted Jev latency is cited, never plotted against local
  numbers — a local forward pass and a network API call aren't comparable.
- No mechanism claims. No claims about either vendor's training process.
- Every result states its n and whether ground truth exists.

Full rationale: [`design.md`](design.md). Status: [`PLAN.md`](PLAN.md).

Not affiliated with TypeSafe AI or Convai Innovations. Personal / CoRe
research-engineering experiment.
