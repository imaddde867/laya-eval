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
- [ ] Phase 2 — Latency/throughput on M4 (laya-mlx vs. jevmlx, local only)
- [ ] Phase 3 — Option-order robustness (repeat jev-position-test method,
      needs `TYPESAFE_API_KEY` for the hosted-Jev leg)
- [ ] Phase 4 — CoRe-relevant task (deferred, own session)

Next step: open a new Claude Code session in this folder (`laya-eval/`),
read `CONTEXT.md` and the Phase 1 plan, then execute Task 1.
