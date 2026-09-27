# jevmlx field type → laya primitive mapping

Status: stub. Fill in during Phase 1 while building `adapters/laya_adapter.py`.

| jevmlx field type | laya primitive | Notes |
|---|---|---|
| `enum` (mutually exclusive) | `choice` | Direct mapping when option count is under laya's ~20-option guidance. |
| `boolean` | `noul` | Direct mapping. |
| `enum` with `ordered=True` | `score` | jevmlx's ordinal telemetry (`argmax_level`, `expected_index`) has no laya equivalent — check what `score` returns and note the gap. |
| `enum` with `allow_none_of_above=True` | — | Does not map. Laya's `choice` has no built-in "none of these" option; would need an explicit extra choice, changing the schema, not just the primitive. Log as unmapped unless a workaround is added and documented as a deviation. |
| `multi-select` | — | Does not map. No laya primitive picks more than one option. Log as unmapped. |
| constraints (`implies` / `excludes` / `requires_parent`) | — | Does not map. Laya has no cross-field constraint mechanism; each question is scored independently. Log as unmapped. |

## Per-preset comparable-field fraction

Fill in once the table above is applied to each of the 5 usable presets
(`code_security`, `content_moderation`, `fintech_fraud`, `inbound_email`,
`support_triage` — `high_cardinality_255` excluded, see design.md).

| Preset | Total fields | Comparable | Unmapped | Unmapped reason(s) |
|---|---|---|---|---|
| code_security | | | | |
| content_moderation | | | | |
| fintech_fraud | | | | |
| inbound_email | | | | |
| support_triage | | | | |
