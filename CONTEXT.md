# Session handoff context — laya-eval

Read `design.md` first. This file is the fast-orientation seed for a new
Claude Code session started in this folder.

## What this project is

Evaluating `convaiinnovations/laya` (via `aac6fef/laya-typed-decisions-mlx`,
local on an M4 MacBook Pro) against TypeSafe's hosted `Jev` and against the
local jevmlx Jev-clone already built in the sibling `openjev/` repo. Staged
in 4 phases (see `design.md`); Phase 1 (agreement on the fetched public eval) is
first up.

## Sibling repos (read-only references, do not modify)

- `../openjev/` — jevmlx: local Jev clone (MLX, Qwen backbones). Has the
  benchmark harness this project reuses: `benchmarks/typesafe/` (public eval
  fetch + consensus labels via `official.json`), `benchmarks/public/`,
  and `jevmlx/presets/*.json` (6 bundled schemas — `high_cardinality_255`
  is excluded from the laya run, see design.md).
- `../jev-position-test/` — the prior option-order-bias experiment against
  jevmlx and hosted Jev. Phase 3 here repeats its exact method (same 6
  messages, 3 orderings) against laya's `choice` primitive. Its
  `results/jev-run.txt` has prior hosted-Jev answers for reference, though
  Phase 3 will call hosted Jev fresh per the approved design.

## Decisions already made (don't re-litigate without new evidence)

- Model variant: `aac6fef/laya-typed-decisions-mlx`, not `laya-mlx` or
  `laya-multilingual-mlx`. Rationale in design.md.
- `high_cardinality_255` preset excluded from laya runs (255 choices vs.
  laya's ~20-option guidance for `choice`).
- Vocabulary: "agreement with consensus," never "accuracy," for the
  public TypeSafe cases. Local-vs-local latency only; local-vs-hosted latency
  is cited,
  never compared numerically.
- Multi-select and inter-field constraints (implies/excludes/
  requires_parent) don't map to laya's primitives — logged as unmapped in
  `mapping/schema_mapping.md`, not approximated.

## Environment notes

- `TYPESAFE_API_KEY` is needed for hosted-Jev calls in Phase 3, not Phase 1
  (which cites `openjev/benchmarks/typesafe/official.json`). Phase 3 scripts
  must check `os.environ` and fail with a clear message if absent; never print
  the key.
- Apple Silicon / MLX required for laya-typed-decisions-mlx and jevmlx
  local runs (M4 MacBook Pro, macOS 14+, Python 3.11+/3.12+ per jevmlx's
  own requirement).
- **`second-brain` MCP server is scoped to this project directory, not the
  actual Obsidian vault.** If a future session needs vault context (e.g.
  for Phase 4's CoRe-task shape, or before any public write-up), read
  `/Users/imadeddine/Documents/2ndBrain` directly via Read/Bash/Grep, not
  the MCP tool. Do not write anything to the vault — read-only.
- Relevant vault notes (read-only, if needed later): `Areas/CoRe Research
  Engineering.md`, `Areas/Cadence and Evidence Log.md`, `Areas/Professional
  Visibility and Communication.md` (has the prior Jev post's exact claim
  boundaries and publishing pattern to mirror if this becomes a write-up).

## Correction found after the initial brainstorm (already folded into design.md)

The real TypeSafe public eval is `openjev/benchmarks/typesafe/fetch.py`'s
output (4 workflows), not the 6 bundled demo presets in
`openjev/jevmlx/presets/*.json` (those back `jevmlx decide --preset`, a
different, general-purpose demo — and include `high_cardinality_255`,
which was wrongly assumed to be part of the eval set). The fetcher's schema
only ever produces boolean/enum fields, so the multi-select/constraints
mapping gap doesn't bite on this dataset.

## Current status

- Phase 1 is complete. The six-task implementation plan is
  `docs/superpowers/plans/2026-09-27-laya-phase1-agreement.md`; status and
  reported results are in `PLAN.md`.
- The generated prediction and report artifacts are gitignored under
  `results/laya_phase1/`; the TypeSafe cases remain in
  `~/.cache/jevmlx/typesafe/cases.jsonl`.
- Phase 1 review fixes are merged to `main` (PR #2). Headline numbers
  (agreement with consensus): hosted Jev 0.822, jevmlx 0.753, leave-one-out
  majority baseline 0.725, Laya 0.542 (below baseline under every weighting).
- Phase 3 Laya `choice` probe is done (`scripts/run_position_laya.py`, branch
  `feat/position-laya-probe`): 6 messages x 3 orders x 2 passes, 2 of 6
  answers changed with option order when descriptions were kept, 0 of 6 when
  blanked. Exploratory (n=6, no ground truth); raw records gitignored under
  `results/position_laya/`. Hosted Jev (2026-10-03 rerun): 0 of 6 changed.
  Phase 3 is done; see `PLAN.md`.
- Phase 2 (latency/throughput) and Phase 4 remain unplanned. Use the design
  and claim boundaries in `design.md` before planning Phase 2.
