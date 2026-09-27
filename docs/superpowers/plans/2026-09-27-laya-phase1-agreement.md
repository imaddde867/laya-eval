# Laya Phase 1 — Agreement on the TypeSafe Public Eval Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure `aac6fef/laya-typed-decisions-mlx`'s agreement with TypeSafe's published consensus labels on the real public eval dataset (4 workflows fetched via `openjev/benchmarks/typesafe/fetch.py`), reported next to jevmlx's own local run on the same cases and TypeSafe's cited hosted-Jev leaderboard row.

**Architecture:** A one-way adapter (`adapters/laya_adapter.py`) maps each fetched case's jevmlx-shaped schema (boolean/enum, occasionally `ordered`) into laya's three primitives (noul/choice/score), calls the local laya-typed-decisions-mlx model once per field, and writes one prediction record per case. A separate scorer (`scoring/agreement.py`) computes agreement-with-consensus against the fetcher's labels, independent of jevmlx's internal `evalmetrics` module (which expects jevmlx's own per-field "line" format from its eval pipeline — not worth coupling to for an external comparison). jevmlx's own number for the same cases comes from its unmodified `jevmlx eval` + `jevmlx report` CLI, run as a subprocess, not reimplemented.

**Tech Stack:** Python 3.12, `laya-mlx` (pip package, MLX backend), openjev's existing `benchmarks.typesafe` module (imported, not copied), pytest.

## Global Constraints

- Apple Silicon required (M4 MacBook Pro, macOS 14+, Python 3.11+) — both `laya-mlx` and jevmlx's MLX backend need it.
- `TYPESAFE_API_KEY` is out of scope for Phase 1 (no hosted-Jev calls here — TypeSafe's Jev row comes from the already-cited `openjev/benchmarks/typesafe/official.json`, not a fresh API call). Phase 3's plan will need it.
- Never commit anything fetched from TypeSafe (`openjev/benchmarks/typesafe/fetch.py`'s own docstring: "Nothing from TypeSafe is committed to this repository"). `laya-eval/results/` stays gitignored (already set in `.gitignore`); raw `cases.jsonl` lives in the fetch's own cache dir (`~/.cache/jevmlx/typesafe/`), never inside `laya-eval/`.
- Vocabulary: every report/output must say "agreement with consensus," never "accuracy." State the case/field count on every reported number.
- `laya-typed-decisions-mlx` is the only checkpoint used this phase (per `design.md`); do not substitute `laya-mlx` or `laya-multilingual-mlx`.

---

### Task 1: Fetch the TypeSafe public eval dataset and get jevmlx's own baseline

**Files:**
- Create: `laya-eval/scripts/fetch_typesafe_cases.sh`
- Create: `laya-eval/results/.keep` (results dir exists but stays empty/gitignored otherwise)

**Interfaces:**
- Produces: `~/.cache/jevmlx/typesafe/cases.jsonl` (via openjev's fetcher) and `laya-eval/results/jevmlx_baseline/predictions.jsonl` + `report.json` — later tasks read both by these exact paths.

- [ ] **Step 1: Write the fetch + baseline script**

```bash
#!/usr/bin/env bash
set -euo pipefail

OPENJEV_DIR="$(cd "$(dirname "$0")/../../openjev" && pwd)"
CACHE_DIR="${HOME}/.cache/jevmlx/typesafe"
RESULTS_DIR="$(cd "$(dirname "$0")/.." && pwd)/results/jevmlx_baseline"

cd "$OPENJEV_DIR"
.venv/bin/python -m benchmarks.typesafe.fetch --out "$CACHE_DIR/cases.jsonl"

mkdir -p "$RESULTS_DIR"
.venv/bin/jevmlx eval \
  --data "$CACHE_DIR/cases.jsonl" \
  --model fast \
  --track parallel \
  --scoring labels \
  --split all \
  --out "$RESULTS_DIR"

.venv/bin/jevmlx report \
  --predictions "$RESULTS_DIR/predictions.jsonl" \
  --out "$RESULTS_DIR/report.json"

echo "cases: $CACHE_DIR/cases.jsonl"
echo "jevmlx baseline: $RESULTS_DIR/report.json"
```

- [ ] **Step 2: Make it executable and run it**

Run: `chmod +x laya-eval/scripts/fetch_typesafe_cases.sh && laya-eval/scripts/fetch_typesafe_cases.sh`

Expected: prints the two paths above; `~/.cache/jevmlx/typesafe/cases.jsonl` and `laya-eval/results/jevmlx_baseline/report.json` both exist. If `openjev/.venv` lacks `jevmlx` installed as a CLI, run `cd ../openjev && ./setup.sh` first (per `openjev/README.md`), then re-run this script.

- [ ] **Step 3: Inspect the fetched case shape**

Run: `head -1 ~/.cache/jevmlx/typesafe/cases.jsonl | python3 -m json.tool`

Expected: a JSON object with keys `id`, `group_id`, `source` (`"typesafe"`), `workflow`, `benchmark_only`, `schema` (dict of `{field_name: {type, description, choices?, ordered?}}`), `context` (string), `labels` (dict of `{field_name: value}`), `split`, `meta` (`consensus`, `margin`, `ambiguous`).

- [ ] **Step 4: Commit**

```bash
cd laya-eval
git add scripts/fetch_typesafe_cases.sh results/.keep
git commit -m "feat: add TypeSafe fetch + jevmlx baseline script"
```

---

### Task 2: Install laya-typed-decisions-mlx and capture its real output shape

**Files:**
- Create: `laya-eval/scripts/inspect_laya_output.py`
- Create: `laya-eval/tests/fixtures/laya_raw_response.json` (committed — small, no TypeSafe content, safe to commit)

**Interfaces:**
- Produces: `tests/fixtures/laya_raw_response.json`, the exact real return shape of `agent.predict()` for one `choice` + one `score` + one `noul` field. Task 3 reads this fixture's keys to write the parser.

- [ ] **Step 1: Install laya-mlx**

Run: `pip install laya-mlx`
Expected: installs cleanly on the M4 (Apple Silicon, macOS 14+, Python 3.11+ per the package's own requirement).

- [ ] **Step 2: Write the inspection script**

```python
"""One-off: capture laya-typed-decisions-mlx's real predict() output shape.

Run once; the printed/saved JSON becomes tests/fixtures/laya_raw_response.json,
which adapters/laya_adapter.py's parser is written and tested against.
"""

import json
from pathlib import Path

import laya_mlx as laya

agent = laya.load("aac6fef/laya-typed-decisions-mlx", dtype="float16")

state = "Customer was charged twice and wants the duplicate refunded."
questions = {
    "department": {
        "type": "choice",
        "instructions": "Which team should handle this?",
        "criteria": {
            "billing": "invoices, payments, refunds",
            "technical": "bugs and outages",
            "sales": "new purchases",
        },
    },
    "urgency": {
        "type": "score",
        "instructions": "How urgent is this request?",
        "criteria": ["not urgent", "soon", "critical"],
    },
    "refund": {
        "type": "noul",
        "instructions": "Does the customer ask for money back?",
    },
}

result = agent.predict(state, questions)
print(json.dumps(result, indent=2, default=str))

out_path = Path(__file__).parent.parent / "tests" / "fixtures" / "laya_raw_response.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
print(f"wrote {out_path}")
```

- [ ] **Step 3: Run it and read the real shape**

Run: `python3 laya-eval/scripts/inspect_laya_output.py`

Expected: no crash, prints a JSON object, writes `laya-eval/tests/fixtures/laya_raw_response.json`. Read the written file and note the exact top-level and per-field keys (e.g. whether it's `result["answers"]["department"]["value"]` and `["probability"]`, or a different shape) — Task 3's parser is written against these exact keys, not guessed ones.

- [ ] **Step 4: Commit the fixture**

```bash
cd laya-eval
git add scripts/inspect_laya_output.py tests/fixtures/laya_raw_response.json
git commit -m "feat: capture laya-typed-decisions-mlx real output shape as a fixture"
```

---

### Task 3: Schema mapping module (pure function, no model needed)

**Files:**
- Create: `laya-eval/mapping/map_schema.py`
- Test: `laya-eval/tests/test_map_schema.py`

**Interfaces:**
- Consumes: a jevmlx-shaped `schema` dict as read from `cases.jsonl` (Task 1, Step 3's shape: `{field_name: {"type": "boolean"|"enum", "description": str, "choices": list[str]?, "ordered": bool?}}`).
- Produces: `map_schema(schema: dict) -> tuple[dict, list[str]]` — `(laya_questions, unmapped_field_names)`. `laya_questions` is a dict shaped for `agent.predict()`'s `questions` argument (Task 2's `choice`/`score`/`noul` shape). Task 4's adapter calls this directly.

- [ ] **Step 1: Write the failing tests**

```python
from mapping.map_schema import map_schema


def test_boolean_maps_to_noul():
    schema = {"is_urgent": {"type": "boolean", "description": "Is this urgent?"}}
    questions, unmapped = map_schema(schema)
    assert unmapped == []
    assert questions["is_urgent"] == {
        "type": "noul",
        "instructions": "Is this urgent?",
    }


def test_plain_enum_maps_to_choice():
    schema = {
        "category": {
            "type": "enum",
            "description": "Which category?",
            "choices": ["billing", "technical", "sales"],
        }
    }
    questions, unmapped = map_schema(schema)
    assert unmapped == []
    assert questions["category"] == {
        "type": "choice",
        "instructions": "Which category?",
        "criteria": {"billing": "", "technical": "", "sales": ""},
    }


def test_ordered_enum_maps_to_score():
    schema = {
        "severity": {
            "type": "enum",
            "description": "How severe?",
            "choices": ["0", "1", "2", "3"],
            "ordered": True,
        }
    }
    questions, unmapped = map_schema(schema)
    assert unmapped == []
    assert questions["severity"] == {
        "type": "score",
        "instructions": "How severe?",
        "criteria": ["0", "1", "2", "3"],
    }


def test_unknown_type_is_unmapped():
    schema = {"tags": {"type": "multi-select", "description": "Which tags?", "choices": ["a", "b"]}}
    questions, unmapped = map_schema(schema)
    assert unmapped == ["tags"]
    assert questions == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd laya-eval && python3 -m pytest tests/test_map_schema.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'mapping.map_schema'`

- [ ] **Step 3: Write the implementation**

```python
"""jevmlx schema field -> laya question mapping (see mapping/schema_mapping.md).

boolean -> noul; enum -> choice; enum with ordered=True -> score. Anything
else (multi-select, constraint-bearing fields) is unmapped and returned by
name, never silently dropped or approximated.
"""

from __future__ import annotations


def map_schema(schema: dict) -> tuple[dict, list[str]]:
    """Map one case's jevmlx schema to laya questions.

    Returns (laya_questions, unmapped_field_names).
    """
    questions: dict = {}
    unmapped: list[str] = []
    for name, field in schema.items():
        ftype = field.get("type")
        if ftype == "boolean":
            questions[name] = {"type": "noul", "instructions": field["description"]}
        elif ftype == "enum" and field.get("ordered"):
            questions[name] = {
                "type": "score",
                "instructions": field["description"],
                "criteria": list(field["choices"]),
            }
        elif ftype == "enum":
            questions[name] = {
                "type": "choice",
                "instructions": field["description"],
                "criteria": dict.fromkeys(field["choices"], ""),
            }
        else:
            unmapped.append(name)
    return questions, unmapped
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd laya-eval && python3 -m pytest tests/test_map_schema.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
cd laya-eval
git add mapping/map_schema.py tests/test_map_schema.py
git commit -m "feat: map jevmlx schema fields to laya question primitives"
```

---

### Task 4: Laya adapter (real model calls, parser verified against Task 2's fixture)

**Files:**
- Modify: `laya-eval/adapters/laya_adapter.py`
- Test: `laya-eval/tests/test_laya_adapter.py`

**Interfaces:**
- Consumes: `map_schema()` from Task 3; `laya.load()`/`agent.predict()` from the `laya_mlx` package.
- Produces: `LayaAdapter.predict_case(case: dict) -> dict` — `case` is one record from `cases.jsonl` (Task 1's shape). Returns `{"id": case["id"], "workflow": case["workflow"], "predictions": {field_name: predicted_label}, "unmapped": list[str]}`. Task 5's runner calls this per case.

- [ ] **Step 1: Write the failing test using Task 2's fixture**

```python
import json
from pathlib import Path

from adapters.laya_adapter import parse_laya_result

FIXTURE = Path(__file__).parent / "fixtures" / "laya_raw_response.json"


def test_parse_laya_result_matches_captured_fixture():
    raw = json.loads(FIXTURE.read_text())
    parsed = parse_laya_result(raw)
    # These three field names come from scripts/inspect_laya_output.py (Task 2).
    assert set(parsed) == {"department", "urgency", "refund"}
    assert parsed["department"] in {"billing", "technical", "sales"}
    assert parsed["urgency"] in {"not urgent", "soon", "critical"}
    assert isinstance(parsed["refund"], bool)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd laya-eval && python3 -m pytest tests/test_laya_adapter.py -v`
Expected: FAIL with `ImportError: cannot import name 'parse_laya_result'`

- [ ] **Step 3: Write `parse_laya_result` against the real fixture keys**

Open `tests/fixtures/laya_raw_response.json` from Task 2 and read its actual keys first. Implement `parse_laya_result(raw: dict) -> dict[str, object]` in `adapters/laya_adapter.py` using those exact keys — for a `choice`/`score` field, take the winning option's text; for `noul`, take the boolean. If the fixture's shape differs from `{"answers": {name: {"value": ...}}}`, use the fixture's real structure, not this placeholder shape.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd laya-eval && python3 -m pytest tests/test_laya_adapter.py -v`
Expected: PASS

- [ ] **Step 5: Add `LayaAdapter.predict_case` (loads the model once, calls per case)**

```python
class LayaAdapter:
    """Wraps laya-typed-decisions-mlx: one model load, many predict_case() calls."""

    def __init__(self, model_id: str = "aac6fef/laya-typed-decisions-mlx"):
        import laya_mlx as laya

        self._agent = laya.load(model_id, dtype="float16")

    def predict_case(self, case: dict) -> dict:
        from mapping.map_schema import map_schema

        questions, unmapped = map_schema(case["schema"])
        predictions: dict = {}
        if questions:
            raw = self._agent.predict(case["context"], questions)
            predictions = parse_laya_result(raw)
        return {
            "id": case["id"],
            "workflow": case.get("workflow"),
            "predictions": predictions,
            "unmapped": unmapped,
        }
```

- [ ] **Step 6: Run the full adapter test file**

Run: `cd laya-eval && python3 -m pytest tests/test_laya_adapter.py -v`
Expected: all pass (the fixture-based parser test from Step 4; `LayaAdapter.__init__` itself is exercised end-to-end in Task 5, not unit-tested here, since it requires the real model load).

- [ ] **Step 7: Commit**

```bash
cd laya-eval
git add adapters/laya_adapter.py tests/test_laya_adapter.py
git commit -m "feat: laya adapter — predict_case() over real laya-typed-decisions-mlx"
```

---

### Task 5: Agreement scorer (pure function, tested without any model)

**Files:**
- Create: `laya-eval/scoring/agreement.py`
- Test: `laya-eval/tests/test_agreement.py`

**Interfaces:**
- Consumes: a list of `case` records (Task 1's shape: has `labels`, `meta.ambiguous`, `workflow`) each paired with a `prediction` dict (Task 4's `predict_case()` output's `"predictions"` value).
- Produces: `score_agreement(cases: list[dict], predictions: list[dict]) -> dict` — `{"overall": float, "n_fields": int, "n_cases": int, "common_subset": float, "by_workflow": dict[str, float]}`. Task 6's report-writer calls this directly.

- [ ] **Step 1: Write the failing tests**

```python
from scoring.agreement import score_agreement


def _case(id_, workflow, labels, ambiguous=None):
    return {
        "id": id_,
        "workflow": workflow,
        "labels": labels,
        "meta": {"ambiguous": ambiguous or []},
    }


def test_overall_agreement_counts_matching_fields():
    cases = [
        _case("c1", "wf_a", {"urgent": True, "category": "billing"}),
        _case("c2", "wf_a", {"urgent": False}),
    ]
    predictions = [
        {"id": "c1", "predictions": {"urgent": True, "category": "technical"}},
        {"id": "c2", "predictions": {"urgent": False}},
    ]
    result = score_agreement(cases, predictions)
    assert result["n_fields"] == 3
    assert result["overall"] == 2 / 3
    assert result["n_cases"] == 2


def test_common_subset_excludes_ambiguous_fields():
    cases = [_case("c1", "wf_a", {"urgent": True, "category": "billing"}, ambiguous=["category"])]
    predictions = [{"id": "c1", "predictions": {"urgent": True, "category": "technical"}}]
    result = score_agreement(cases, predictions)
    assert result["overall"] == 1 / 2
    assert result["common_subset"] == 1 / 1


def test_by_workflow_breakdown():
    cases = [
        _case("c1", "wf_a", {"x": True}),
        _case("c2", "wf_b", {"x": False}),
    ]
    predictions = [
        {"id": "c1", "predictions": {"x": True}},
        {"id": "c2", "predictions": {"x": True}},
    ]
    result = score_agreement(cases, predictions)
    assert result["by_workflow"] == {"wf_a": 1.0, "wf_b": 0.0}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd laya-eval && python3 -m pytest tests/test_agreement.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scoring.agreement'`

- [ ] **Step 3: Write the implementation**

```python
"""Agreement-with-consensus scoring, independent of jevmlx's internal
evalmetrics (which expects jevmlx's own per-field eval-pipeline "line"
format). Vocabulary: always "agreement with consensus," never "accuracy" —
see design.md.
"""

from __future__ import annotations
from collections import defaultdict


def score_agreement(cases: list[dict], predictions: list[dict]) -> dict:
    """Compare each case's labels to its matching prediction by id.

    Only fields present in both a case's ``labels`` and its prediction's
    ``predictions`` are scored (unmapped fields, from map_schema, are absent
    from predictions and therefore excluded, not counted wrong).
    """
    preds_by_id = {p["id"]: p["predictions"] for p in predictions}
    total = 0
    correct = 0
    common_total = 0
    common_correct = 0
    by_workflow_totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    case_ids: set[str] = set()

    for case in cases:
        pred = preds_by_id.get(case["id"])
        if pred is None:
            continue
        ambiguous = set(case.get("meta", {}).get("ambiguous", []))
        for field, label in case["labels"].items():
            if field not in pred:
                continue
            case_ids.add(case["id"])
            is_correct = pred[field] == label
            total += 1
            correct += int(is_correct)
            workflow = str(case.get("workflow"))
            by_workflow_totals[workflow][0] += 1
            by_workflow_totals[workflow][1] += int(is_correct)
            if field not in ambiguous:
                common_total += 1
                common_correct += int(is_correct)

    return {
        "overall": (correct / total) if total else None,
        "common_subset": (common_correct / common_total) if common_total else None,
        "n_fields": total,
        "n_cases": len(case_ids),
        "by_workflow": {
            workflow: (c / t if t else None) for workflow, (t, c) in by_workflow_totals.items()
        },
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd laya-eval && python3 -m pytest tests/test_agreement.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
cd laya-eval
git add scoring/agreement.py tests/test_agreement.py
git commit -m "feat: agreement-with-consensus scorer, independent of jevmlx internals"
```

---

### Task 6: End-to-end Phase 1 runner and report

**Files:**
- Create: `laya-eval/scripts/run_phase1.py`
- Modify: `laya-eval/mapping/schema_mapping.md` (fill in the real per-workflow table)
- Modify: `laya-eval/PLAN.md` (mark Phase 1 sub-items done)

**Interfaces:**
- Consumes: `LayaAdapter` (Task 4), `score_agreement` (Task 5), `~/.cache/jevmlx/typesafe/cases.jsonl` (Task 1), `results/jevmlx_baseline/report.json` (Task 1).
- Produces: `results/laya_phase1/predictions.jsonl`, `results/laya_phase1/report.md` — the final deliverable this task is judged on.

- [ ] **Step 1: Write the runner**

```python
"""Phase 1: run laya-typed-decisions-mlx over the TypeSafe public eval and
report agreement-with-consensus next to jevmlx's own local run and
TypeSafe's cited hosted-Jev row.
"""

import json
from pathlib import Path

from adapters.laya_adapter import LayaAdapter
from scoring.agreement import score_agreement

CACHE = Path.home() / ".cache" / "jevmlx" / "typesafe" / "cases.jsonl"
RESULTS_DIR = Path(__file__).parent.parent / "results" / "laya_phase1"
JEVMLX_REPORT = Path(__file__).parent.parent / "results" / "jevmlx_baseline" / "report.json"
OFFICIAL = (
    Path(__file__).parent.parent.parent
    / "openjev"
    / "benchmarks"
    / "typesafe"
    / "official.json"
)


def main() -> None:
    cases = [json.loads(line) for line in CACHE.read_text(encoding="utf-8").splitlines() if line]

    adapter = LayaAdapter()
    predictions = [adapter.predict_case(case) for case in cases]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    predictions_path = RESULTS_DIR / "predictions.jsonl"
    with predictions_path.open("w", encoding="utf-8") as handle:
        for pred in predictions:
            handle.write(json.dumps(pred, ensure_ascii=False) + "\n")

    result = score_agreement(cases, predictions)
    jevmlx_report = json.loads(JEVMLX_REPORT.read_text()) if JEVMLX_REPORT.exists() else {}
    official = json.loads(OFFICIAL.read_text()) if OFFICIAL.exists() else {}
    jev_row = next((m for m in official.get("models", []) if m["name"] == "Jev"), {})

    total_unmapped = sum(len(p["unmapped"]) for p in predictions)
    lines = [
        "# Phase 1 — Agreement with TypeSafe consensus",
        "",
        f"laya-typed-decisions-mlx, {result['n_cases']} cases, {result['n_fields']} fields "
        f"scored (unmapped fields excluded from scoring: {total_unmapped}).",
        "",
        f"- laya agreement (overall): {result['overall']}",
        f"- laya agreement (common subset, non-ambiguous): {result['common_subset']}",
        f"- jevmlx local report (same cases): {jevmlx_report.get('agreement', 'not available')}",
        f"- TypeSafe cited hosted Jev (private eval, not this dataset): "
        f"{jev_row.get('accuracy', 'not available')}",
        "",
        "By workflow (laya):",
    ]
    for workflow, rate in sorted(result["by_workflow"].items()):
        lines.append(f"- {workflow}: {rate}")

    (RESULTS_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {predictions_path}")
    print(f"wrote {RESULTS_DIR / 'report.md'}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `cd laya-eval && python3 scripts/run_phase1.py`
Expected: no crash; prints the two output paths; `results/laya_phase1/report.md` exists and reads sensibly (agreement values between 0 and 1, case/field counts matching the fetched dataset's size).

- [ ] **Step 3: Fill in the real per-workflow mapping table**

Read `results/laya_phase1/predictions.jsonl`, count total vs. unmapped fields per workflow (cross-reference `case["workflow"]` from `cases.jsonl` against each prediction's `unmapped` list), and fill in the real numbers in `mapping/schema_mapping.md`'s "Per-workflow comparable-field fraction" table, replacing the blank cells.

- [ ] **Step 4: Update PLAN.md**

Check off Phase 1's sub-items in `laya-eval/PLAN.md` and add one line noting the final agreement numbers and where the full report lives (`results/laya_phase1/report.md`).

- [ ] **Step 5: Commit**

```bash
cd laya-eval
git add scripts/run_phase1.py mapping/schema_mapping.md PLAN.md
git commit -m "feat: run Phase 1 end-to-end, report laya agreement vs jevmlx and cited Jev"
```

(`results/laya_phase1/` itself stays gitignored per `design.md`'s "nothing from TypeSafe is committed" constraint — the committed artifact is the code that produces it, plus the filled-in mapping table and PLAN.md summary, not the raw predictions/report files.)

---

## Self-review notes (already applied above)

- Spec coverage: `design.md`'s Phase 1 bullets (fetch real dataset, adapter, mapping table, scorer, jevmlx-own-run comparison, vocabulary discipline) each map to Tasks 1–6.
- No placeholders: Task 2/4's uncertainty about laya's exact return shape is handled by an empirical capture step (Task 2) that Task 4's parser is then written and tested against — not a "TBD."
- Type consistency: `map_schema()` (Task 3) → `LayaAdapter.predict_case()` (Task 4) → `score_agreement()` (Task 5) → `run_phase1.py` (Task 6) all agree on the `{"id", "workflow", "predictions", "unmapped"}` prediction shape.
