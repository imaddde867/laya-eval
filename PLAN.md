# laya-eval plan status

See `design.md` for full rationale. `writing-plans` skill output (detailed
step-by-step implementation plan) to be added here once run.

- [ ] Phase 1 — Agreement on public 20 vs. jevmlx + hosted Jev
  - [ ] Fill `mapping/schema_mapping.md` per-preset table
  - [ ] Build `adapters/laya_adapter.py`
  - [ ] Install + sanity-check `laya-typed-decisions-mlx` locally
  - [ ] Run laya-mlx on 5 usable presets
  - [ ] Run hosted Jev fresh on same presets (`TYPESAFE_API_KEY`)
  - [ ] Report: agreement-with-consensus, laya vs. jevmlx vs. cited hosted Jev
- [ ] Phase 2 — Latency/throughput on M4 (laya-mlx vs. jevmlx, local only)
- [ ] Phase 3 — Option-order robustness (repeat jev-position-test method)
- [ ] Phase 4 — CoRe-relevant task (deferred, own session)

Next step: run `writing-plans` skill against `design.md` to produce the
detailed implementation plan for Phase 1.
