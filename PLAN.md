# laya-eval plan status

See `design.md` for full rationale. Detailed implementation plan for
Phase 1: `docs/superpowers/plans/2026-09-27-laya-phase1-agreement.md`.

- [x] Phase 1 — Agreement on TypeSafe public eval (4 real workflows, not
      the bundled demo presets — see design.md's correction note) vs.
      jevmlx's own local run and TypeSafe's cited hosted-Jev row
  - [x] Task 1: fetch cases + jevmlx baseline run
  - [x] Task 2: install laya-typed-decisions-mlx, capture real output fixture
  - [x] Task 3: schema mapping module + tests
  - [x] Task 4: laya adapter + tests
  - [x] Task 5: agreement scorer + tests
  - [x] Task 6: end-to-end run, fill mapping table, report
  - Result: Laya agreement with consensus was 0.542 (44 scored cases, 365
    fields); non-ambiguous agreement was 0.554 (44 cases, 343 fields).
    jevmlx reported 0.753 (44 cases, 365 fields). TypeSafe's cited hosted
    Jev value is 0.678 (private eval; sample size not reported). Full report:
    `results/laya_phase1/report.md` (gitignored).
  - The fetch produced 45 cases; one has no schema or labels. All 365 fields
    mapped. The Laya checkpoint's 1,024-token limit truncates long contexts;
    see the report.
  - Methodology audit (2026-09-28), triggered by a suspicious bimodal
    0.000/1.000 per-field distribution: no parsing/type bug found; scoring
    reproduces jevmlx's own 0.753 exactly from its raw predictions (0.7534),
    so the 0.542-vs-0.753 gap is real. But two corrections to the original
    write-up: (1) truncation does NOT explain the per-workflow ranking —
    invoice_processing has the longest, most-truncated contexts and scores
    best; customer_service has the shortest, untruncated contexts and
    scores worst — that causal claim is retracted; (2) effective sample
    size is smaller than "365 fields" suggests, since invoice_processing's
    184 fields come from only 5 cases via repeated near-identical
    per-line sub-questions. Full detail in
    `results/laya_phase1/report.md`'s "Methodology audit" section.
- [x] Phase 1.5 — Root-caused the constant-answer fields (2026-09-28). No
      adapter bug: traced through `laya_mlx.common.build_sequence` /
      `build_prefix` directly. Two distinct, separately-verified causes:
  - **Truncation-starved fields** (invoice_processing `scope`/`kind`,
    every line index): the checkpoint's default `truncate_left=False`
    keeps the front of the document and drops the tail. On the longest
    case (34,166 chars / 10,358 tokens) only the first 906 of 1,024
    available tokens reach the model — the invoice's own line-item list
    survives, but the PO/contract terms needed to judge `scope`/`kind`
    sit later in the packet and never arrive. Verified by decoding the
    actual truncated state fed to the model.
  - **Genuine model default, not truncation** (customer_service `intent`/
    `churn_risk`, agent_trace_observability `attribution`/
    `first_bad_step`): these come from 406-1,381-char contexts, far under
    the token budget and never truncated, yet show the same
    constant-wrong-answer pattern. The checkpoint just defaults to one
    answer for these question types regardless of context.
  - No code fix applied or needed — this is a checkpoint/task-fit finding,
    not an implementation error. Full writeup in `results/laya_phase1/report.md`.
- [x] Phase 1 hosted-Jev leg + baseline (2026-09-28) — ran TypeSafe's
      hosted `jev-latest` ourselves via `/v1/systemone` on the same 45
      cases (`scripts/run_hosted_jev.py`), replacing the opaque cited
      leaderboard number. Also added a leave-one-out majority-label
      baseline (`scoring.agreement.majority_baseline`) to every report.
      Updated headline: laya 0.542, jevmlx-local 0.753, **our hosted-Jev
      run 0.827** (vs. TypeSafe's cited 0.678 — kept for reference only),
      **leave-one-out majority baseline 0.725**. Since invoice_processing's
      184 fields (5 cases) dominate a pooled-field total, re-ran all four
      numbers under case-weighted averaging and with invoice_processing
      excluded (2026-09-28) to check which comparisons hold up:
  - **Laya vs. baseline: robustly below it** in every lens tried
    (-0.183 pooled, -0.097 case-weighted, -0.098 invoice-excluded). Not
    sensitive to weighting — a real, settled deficit.
  - **Hosted Jev vs. baseline: robustly above it**, margin growing once
    invoice_processing's inflation is removed (+0.102, +0.177, +0.256).
  - **jevmlx-local vs. baseline: sign-flips** (+0.028 pooled, -0.019
    case-weighted, +0.073 invoice-excluded) — not a settled result at
    n=44-45; report as inconclusive, not as "jevmlx beats guessing."
  - On invoice_processing specifically, the baseline (0.891) beats both
    jevmlx-local (0.880) and hosted-Jev (0.848) pooled — a workflow-
    specific artifact of the repeated near-constant per-line sub-questions
    noted above, not evidence either model adds value there.
      Full table in `results/laya_phase1/report.md`'s "Weighting
      sensitivity" section.
- [ ] Phase 2 — Latency/throughput on M4 (laya-mlx vs. jevmlx, local only)
- [ ] Phase 3 — Option-order robustness (repeat jev-position-test method;
      hosted-Jev leg now unblocked — same `TYPESAFE_API_KEY` already in
      use for the Phase 1 hosted run, `.env` at repo root, gitignored)
- [ ] Phase 4 — CoRe-relevant task (deferred, own session)

Next step: Phase 2 — latency/throughput on the M4, laya-mlx vs. jevmlx,
local only. Phase 1's prediction path is now verified bug-free and the
hosted-Jev comparison is self-produced rather than cited, so Phase 2 can
build on a trustworthy baseline.
