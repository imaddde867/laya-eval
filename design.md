# laya-eval design

Date: 2026-09-27

## Goal

Evaluate `convaiinnovations/laya` (via `aac6fef/laya-typed-decisions-mlx`, run
locally on an M4 MacBook Pro) as a System-1 decision model, staged across
three phases: agreement with a reference consensus, latency/throughput on
Apple silicon, and robustness to option ordering. A fourth phase (a
CoRe-relevant task) is deferred to a later session. Deliverable form
(personal exploration vs. public write-up vs. CoRe pilot) is decided after
results land, not up front.

## Model variant

`aac6fef/laya-typed-decisions-mlx`: ModernBERT-large backbone, 400M params,
1024-token context, MLX-native (no PyTorch/Transformers dependency).

Not used:
- `aac6fef/laya-mlx` — same backbone family, general-purpose port; the
  typed-decisions checkpoint is the closer match to jevmlx's `decide()` use
  case.
- `aac6fef/laya-multilingual-mlx` — different backbone (mmBERT-base, 322M).
  Multilingual capability was explicitly de-scoped as a comparison axis this
  round (see brainstorm). Revisit only if Phase 4's CoRe task needs
  non-English input (e.g. Finnish, TEHAA-shaped).

## Token budget (checked before committing to this design)

jevmlx's 6 bundled presets (`openjev/jevmlx/presets/*.json`) have context
strings of 600–1300 characters (~150–350 tokens) — comfortably inside laya's
1024-token window even with schema/question text appended per call.

Exception: `high_cardinality_255` (a 255-choice enum, jevmlx's own "latency
scaling demo"). Laya's docs recommend `choice` under ~20 options. This
preset is **excluded** from the laya run and logged as a documented
limitation, not silently dropped.

## Schema mapping

jevmlx schema fields: enum, multi-select, boolean, `ordered` enums,
`allow_none_of_above`, and constraints (`implies`/`excludes`/
`requires_parent`).

Laya primitives: `choice` (categorical), `score` (ordinal), `noul`
(calibrated boolean).

Mapping table lives at `mapping/schema_mapping.md`, with an explicit
"does not map" column. Multi-select and inter-field constraints have no
laya equivalent — they get logged as unmapped, not approximated. The
resulting comparable-field fraction per preset is itself a finding.

## Vocabulary discipline (carried from `jev-position-test`)

- Public-20 result = **agreement with the GPT-6 Astra + Claude Fable 5.1
  consensus label**, never "accuracy." TypeSafe's cited leaderboard numbers
  are on a private eval; ours are on the 20 public cases — indicative, not
  the same test.
- Local laya-mlx latency vs. hosted Jev latency is **not a valid
  comparison** (local forward pass vs. network API round-trip). Only
  laya-mlx vs. jevmlx, both local on the same M4, is a fair latency
  comparison. Hosted Jev's published/measured latency is cited separately,
  never plotted against local numbers.
- No mechanism claims. No claims about TypeSafe's or Convai's training.
  State n and lack of ground truth wherever it applies.
- Cost, openness, and raw latency favor laya near-trivially (Apache-2.0,
  local, small model). The only genuinely contested axis is agreement with
  consensus — that's where the careful design effort goes.

## Phases

### Phase 1 — Agreement on the public 20 (first, most detail)

**Correction from the original brainstorm:** the real TypeSafe public eval
is not the 6 bundled demo presets (`jevmlx/presets/*.json` — those back
`jevmlx decide --preset`, a general-purpose demo, and include
`high_cardinality_255` at 255 choices). The actual public eval is
`openjev/benchmarks/typesafe/fetch.py`'s output: 4 workflows
(`security_incidents`, `agent_trace_observability`, `invoice_processing`,
`customer_service`), each case converted to a record with `schema`
(boolean/enum fields only, `enum` sometimes `ordered=True` for score
questions — confirmed via `benchmarks/typesafe/questions.py:field_schema`,
which never emits multi-select or constraint fields), `context`, `labels`
(consensus label), and `meta.consensus`/`margin`/`ambiguous`. This is what
`jevmlx bench` itself fetches. Consequence: the schema-mapping "does not
map" concern (multi-select, constraints) doesn't bite on this dataset —
expect it to show 0% unmapped, not an open question, since this data only
ever has the three field shapes laya already covers.

- Fetch: `python -m benchmarks.typesafe.fetch --out cases.jsonl` from
  within `openjev/` (its own venv), producing `cases.jsonl` +
  `dataset.lock.json`. Nothing from TypeSafe gets committed to
  `laya-eval/`; the fetch's own cache
  (`~/.cache/jevmlx/typesafe/`) is offline-reusable.
- Build `adapters/laya_adapter.py`: per case record, map each schema field
  via `mapping/schema_mapping.md` (boolean→noul, enum→choice,
  `ordered`-enum→score), call laya-typed-decisions-mlx's `predict()`.
- Score with a small purpose-built scorer in `laya-eval` (predicted label
  vs. the fetcher's consensus `labels` value, plus a common-subset rate
  excluding `meta.ambiguous` fields) — not jevmlx's internal
  `evalmetrics.typesafe_agreement`, which expects jevmlx's own per-field
  "line" format from its eval pipeline; coupling to that internal shape
  isn't worth it for an independent comparison.
- For the vs-jevmlx-on-M4 comparison: run jevmlx's own `jevmlx eval` /
  `jevmlx report` CLI (already built, unmodified) on the same
  `cases.jsonl`, so both models are scored on identical cases and the
  jevmlx number is jevmlx's own reported metric, not a reimplementation.
- Output: per-workflow, per-field agreement-with-consensus for laya, next
  to jevmlx's own local report and TypeSafe's cited Jev row
  (`openjev/benchmarks/typesafe/official.json`).

### Phase 2 — Latency/throughput on the M4

- Unit = one decision record (all fields for one context), reported both
  per-record and per-field. Laya calls once per field; jevmlx does one pass
  for all fields on a shared KV cache — raw ms would just measure that
  architectural difference unless normalized this way.
- laya-mlx vs. jevmlx, same M4, same 5 presets. Hosted Jev latency cited
  separately (see vocabulary discipline above), never plotted against local
  numbers.

### Phase 3 — Robustness / option-order sensitivity

- Repeat `jev-position-test`'s method (same options and descriptions, only
  order changes) against laya's `choice` primitive, using the same 6
  messages and 3 orderings for direct comparability with the existing
  results.
- Open question, not an assumption: laya scores via an option-marker head on
  a bidirectional encoder, which *could* be order-invariant by
  construction — or not. Either result is a valid, publishable finding.

### Phase 4 — CoRe-relevant task (deferred)

- A small labeled set shaped like a real CoRe decision task (e.g. incident
  triage). Explicitly deferred to a later session, after Phases 1–3 land.
  Not built today.

## Repo / handoff structure

```
laya-eval/
├── README.md              # what/why, claim boundaries up front
├── design.md               # this file
├── PLAN.md                 # phase checklist + status
├── CONTEXT.md              # session handoff seed
├── mapping/
│   └── schema_mapping.md
├── adapters/
│   └── laya_adapter.py      # stub now, built during Phase 1 execution
├── results/                 # gitignored raw outputs per phase
└── .gitignore
```

## Open items carried into the plan

- `TYPESAFE_API_KEY` must already be set in the shell (user confirmed it
  is); scripts check `os.environ` and fail clearly if missing, never print
  it.
- `second-brain` MCP server is scoped to this project directory only, not
  the actual vault — any future vault reads must use plain filesystem
  tools (Read/Bash) against `/Users/imadeddine/Documents/2ndBrain`.
