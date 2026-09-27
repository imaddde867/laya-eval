# laya-eval plan status

See `design.md` for full rationale. Detailed implementation plan for
Phase 1: `docs/superpowers/plans/2026-09-27-laya-phase1-agreement.md`.

- [ ] Phase 1 — Agreement on TypeSafe public eval (4 real workflows, not
      the bundled demo presets — see design.md's correction note) vs.
      jevmlx's own local run and TypeSafe's cited hosted-Jev row
  - [ ] Task 1: fetch cases + jevmlx baseline run
  - [ ] Task 2: install laya-typed-decisions-mlx, capture real output fixture
  - [ ] Task 3: schema mapping module + tests
  - [ ] Task 4: laya adapter + tests
  - [ ] Task 5: agreement scorer + tests
  - [ ] Task 6: end-to-end run, fill mapping table, report
- [ ] Phase 2 — Latency/throughput on M4 (laya-mlx vs. jevmlx, local only)
- [ ] Phase 3 — Option-order robustness (repeat jev-position-test method,
      needs `TYPESAFE_API_KEY` for the hosted-Jev leg)
- [ ] Phase 4 — CoRe-relevant task (deferred, own session)

Next step: open a new Claude Code session in this folder (`laya-eval/`),
read `CONTEXT.md` and the Phase 1 plan, then execute Task 1.
