# Session handoff context — laya-eval

Read `design.md` first. This file is the fast-orientation seed for a new
Claude Code session started in this folder.

## What this project is

Evaluating `convaiinnovations/laya` (via `aac6fef/laya-typed-decisions-mlx`,
local on an M4 MacBook Pro) against TypeSafe's hosted `Jev` and against the
local jevmlx Jev-clone already built in the sibling `openjev/` repo. Staged
in 4 phases (see `design.md`); Phase 1 (agreement on the public 20) is
first up.

## Sibling repos (read-only references, do not modify)

- `../openjev/` — jevmlx: local Jev clone (MLX, Qwen backbones). Has the
  benchmark harness this project reuses: `benchmarks/typesafe/` (public-20
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
  public-20. Local-vs-local latency only; local-vs-hosted latency is cited,
  never compared numerically.
- Multi-select and inter-field constraints (implies/excludes/
  requires_parent) don't map to laya's primitives — logged as unmapped in
  `mapping/schema_mapping.md`, not approximated.

## Environment notes

- `TYPESAFE_API_KEY` needed for hosted-Jev calls in Phases 1 and 3. User
  confirmed it's already set in the shell. Scripts must check
  `os.environ` and fail with a clear message if absent — never print the
  key.
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

## Not yet done

- `mapping/schema_mapping.md` is a stub — the actual jevmlx-field-type →
  laya-primitive table is Phase 1's first real deliverable.
- `adapters/laya_adapter.py` is a stub.
- No laya-mlx install/inference has been run yet in this session — verify
  `pip install laya-mlx` (or the MLX-native package per the HF card) and a
  sanity `predict()` call before starting Phase 1 proper.
- `writing-plans` skill has not been run yet for this project — do that
  next, from `design.md`, before touching Phase 1 code.
