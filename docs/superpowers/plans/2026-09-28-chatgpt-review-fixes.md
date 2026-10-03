# ChatGPT Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the confirmed defects from the external review of PR #1 / branch `phase-1-agreement-eval` — broken test suite, missing CI, silent dataset-identity drift, a dormant scoring bug, overclaimed PLAN.md language, silent partial hosted-eval runs, an overstated headline number, and unreproducible sensitivity numbers — then open a real PR (the closed PR #1 was empty; `phase-1-agreement-eval` currently has zero diff against `main`).

**Architecture:** All work lands as small, independently-testable commits on a new branch cut from `main` (`916155d`). No new files beyond one CI workflow and one small reproducibility-receipt writer; everything else is a targeted edit to `scripts/run_phase1.py`, `scripts/run_hosted_jev.py`, `scoring/agreement.py`, `PLAN.md`, and their tests.

**Tech Stack:** Python 3, pytest, GitHub Actions.

## Global Constraints

- Every finding fixed here was independently verified against the live repo before this plan was written (test run, code read, dataset probed) — do not re-litigate whether a finding is real; fix it as scoped.
- `results/` is gitignored but present on disk locally with real data from the actual Phase 1 run — use it to verify each fix end-to-end, not just with synthetic fixtures.
- Preserve the "agreement with consensus," never "accuracy" vocabulary rule stated at the top of `scoring/agreement.py`.
- Every new script must remain runnable both as `python scripts/x.py` and as `python -m scripts.x` — `ensure_project_root_on_path()` is the existing mechanism; reuse it, don't invent a second one.
- No `--no-verify`, no skipped hooks.

---

### Task 1: Fix the broken `format_report` test

**Files:**
- Modify: `scripts/run_phase1.py` (no change needed — signature is already correct; listed for reference)
- Modify: `tests/test_run_phase1.py:46-78`
- Test: `tests/test_run_phase1.py`

**Interfaces:**
- Consumes: `scripts.run_phase1.format_report(result, total_unmapped, jevmlx_agreement, hosted_jev_agreement, baseline, jev_row, model_max_len, official_retrieved) -> str` (signature at `scripts/run_phase1.py:69-78`, unchanged by this task).
- Produces: nothing new — this task only repairs the test to match the already-shipped signature and the already-shipped wording at `scripts/run_phase1.py:124` (`"their private eval"`, not `"private eval"`).

Root cause: `916155d` added two required params (`hosted_jev_agreement`, `baseline`) to `format_report()` and changed the citation wording, but the test wasn't updated. Verified live: running pytest today raises `TypeError: format_report() missing 2 required positional arguments: 'hosted_jev_agreement' and 'baseline'`.

- [ ] **Step 1: Reproduce the failure**

Run: `pytest tests/test_run_phase1.py -v`
Expected: `test_report_reads_nested_jevmlx_agreement_and_states_context_limit` FAILs with `TypeError: format_report() missing 2 required positional arguments: 'hosted_jev_agreement' and 'baseline'`

- [ ] **Step 2: Fix the test call and assertions**

Replace `tests/test_run_phase1.py:46-78` with:

```python
def test_report_reads_nested_jevmlx_agreement_and_states_context_limit():
    report = format_report(
        result={
            "n_input_cases": 2,
            "n_cases": 2,
            "n_fields": 3,
            "overall": 2 / 3,
            "n_common_cases": 2,
            "n_common_fields": 2,
            "common_subset": 1.0,
            "by_workflow": {"wf_a": 2 / 3},
            "by_workflow_counts": {"wf_a": {"n_cases": 2, "n_fields": 3}},
            "by_workflow_field": {
                "wf_a": {"urgent": {"agreement": 1.0, "n_cases": 2, "n_fields": 2}}
            },
        },
        total_unmapped=0,
        jevmlx_agreement={"overall": 0.75, "n_cases": 2, "n_fields": 4},
        hosted_jev_agreement={"overall": 0.8, "n_cases": 2, "n_fields": 3, "by_workflow": {}},
        baseline={"overall": 0.6, "n_fields": 3, "by_workflow": {}},
        jev_row={"accuracy": 0.678},
        model_max_len=1024,
        official_retrieved="2026-09-17",
    )

    assert "2 fetched cases; 2 had fields scored; 0 had no comparable fields." in report
    assert "Overall agreement with consensus: 0.667 (2 cases, 3 fields)" in report
    assert "Non-ambiguous agreement with consensus: 1.000 (2 cases, 2 fields)" in report
    assert "jevmlx local agreement on the fetched dataset: 0.750 (2 cases, 4 fields)" in report
    assert (
        "Hosted Jev (our own run, jev-latest / TypeSafe /v1/systemone, same cases/scorer): "
        "0.800 (2 cases, 3 fields)" in report
    )
    assert "Leave-one-out majority-label baseline (guess floor, not a model): 0.600 (3 fields)" in report
    assert "TypeSafe cited hosted Jev (their private eval; n not reported): 0.678" in report
    assert "wf_a: 0.667 (2 cases, 3 fields)" in report
    assert "wf_a / urgent: 1.000 (2 cases, 2 fields)" in report
    assert "1,024-token model input limit." in report
    assert "laya-mlx truncates state tokens" in report
    assert "confidence values are not evaluated" in report


def test_report_handles_missing_hosted_jev_and_baseline():
    report = format_report(
        result={
            "n_input_cases": 1,
            "n_cases": 1,
            "n_fields": 1,
            "overall": 1.0,
            "n_common_cases": 1,
            "n_common_fields": 1,
            "common_subset": 1.0,
            "by_workflow": {"wf_a": 1.0},
            "by_workflow_counts": {"wf_a": {"n_cases": 1, "n_fields": 1}},
            "by_workflow_field": {"wf_a": {"urgent": {"agreement": 1.0, "n_cases": 1, "n_fields": 1}}},
        },
        total_unmapped=0,
        jevmlx_agreement={},
        hosted_jev_agreement=None,
        baseline={"overall": None, "n_fields": 0, "by_workflow": {}},
        jev_row={},
        model_max_len=1024,
        official_retrieved="2026-09-17",
    )

    assert "jevmlx local agreement on the fetched dataset: not available" in report
    assert "Hosted Jev (our own run): not available" in report
    assert "Leave-one-out majority-label baseline" not in report
    assert "TypeSafe cited hosted Jev (their private eval; n not reported): not available" in report
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `pytest tests/test_run_phase1.py -v`
Expected: all PASS (3 tests: bootstrap, sample_counts, both format_report variants)

- [ ] **Step 4: Run the full suite to confirm no other breakage**

Run: `pytest tests/ -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_run_phase1.py
git commit -m "fix: repair format_report test broken by 916155d signature change"
```

---

### Task 2: Add minimal CI running pytest

**Files:**
- Create: `.github/workflows/tests.yml`

**Interfaces:**
- Consumes: nothing from prior tasks (independent of Task 1's content, but must run *after* Task 1 lands so CI goes green, not red, on first run).
- Produces: a required-status-check-capable workflow named `pytest` other tasks/PRs can point branch protection at (branch protection itself is out of scope — repo admin action, not a code change).

- [ ] **Step 1: Check for an existing workflows directory**

Run: `ls -la .github/workflows/ 2>&1`
Expected: `No such file or directory` (confirmed absent earlier in review)

- [ ] **Step 2: Write the workflow**

Create `.github/workflows/tests.yml`:

```yaml
name: tests

on:
  push:
    branches: [main]
  pull_request:

jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```

- [ ] **Step 3: Confirm `requirements.txt` exists and pytest is in it**

Run: `test -f requirements.txt && grep -c pytest requirements.txt`
Expected: prints `1` or more. If `requirements.txt` is missing or lacks pytest, adjust the `pip install` step to `pip install -e . pytest` or the repo's actual install command — check `pyproject.toml` / `setup.cfg` first with `cat pyproject.toml 2>&1 | head -30`.

- [ ] **Step 4: Validate YAML syntax locally**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/tests.yml'))"`
Expected: no output, exit 0

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/tests.yml
git commit -m "ci: add pytest workflow"
```

---

### Task 3: Fail closed on dataset-identity mismatch between artifacts

**Files:**
- Modify: `scripts/run_hosted_jev.py:91-125`
- Modify: `scripts/run_phase1.py:1-23,186-225`
- Test: `tests/test_run_phase1.py`

**Interfaces:**
- Consumes: `~/.cache/jevmlx/typesafe/dataset.lock.json` (has `cases_sha256` key — confirmed present locally), `results/jevmlx_baseline/manifest.json` (has `dataset_lock_sha256` key — already written by the external jevmlx run tooling, confirmed present locally, no change needed on that side).
- Produces: `scripts.run_phase1.current_cases_sha256() -> str`, `scripts.run_phase1.assert_dataset_identity(jevmlx_manifest: dict | None, hosted_jev_sha: str | None, current_sha: str) -> None` (raises `SystemExit` on mismatch), a new sidecar file `results/hosted_jev/dataset_lock_sha256.txt` written by `run_hosted_jev.py`.

Root cause: `run_phase1.py` loads whatever `results/jevmlx_baseline/report.json` and `results/hosted_jev/predictions.jsonl` happen to exist on disk, with no check that they were produced against the same TypeSafe dataset snapshot as the current cache. `dataset.lock.json` already carries `cases_sha256` for exactly this purpose but nothing reads it.

- [ ] **Step 1: Write the failing test for the sha helper**

Add to `tests/test_run_phase1.py` (new imports at top: `import json` and `from scripts.run_phase1 import assert_dataset_identity`):

```python
import pytest


def test_assert_dataset_identity_passes_when_all_shas_match():
    assert_dataset_identity(
        jevmlx_manifest={"dataset_lock_sha256": "abc"},
        hosted_jev_sha="abc",
        current_sha="abc",
    )  # no exception


def test_assert_dataset_identity_fails_on_jevmlx_mismatch():
    with pytest.raises(SystemExit, match="jevmlx_baseline"):
        assert_dataset_identity(
            jevmlx_manifest={"dataset_lock_sha256": "stale"},
            hosted_jev_sha="abc",
            current_sha="abc",
        )


def test_assert_dataset_identity_fails_on_hosted_jev_mismatch():
    with pytest.raises(SystemExit, match="hosted_jev"):
        assert_dataset_identity(
            jevmlx_manifest={"dataset_lock_sha256": "abc"},
            hosted_jev_sha="stale",
            current_sha="abc",
        )


def test_assert_dataset_identity_skips_missing_artifacts():
    assert_dataset_identity(
        jevmlx_manifest=None,
        hosted_jev_sha=None,
        current_sha="abc",
    )  # no exception — nothing to check against
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_run_phase1.py -k assert_dataset_identity -v`
Expected: FAIL with `ImportError: cannot import name 'assert_dataset_identity'`

- [ ] **Step 3: Implement the sha helpers in `run_phase1.py`**

Add near the top of `scripts/run_phase1.py`, after the existing path constants (after line 22, before `ensure_project_root_on_path`):

```python
import hashlib

LOCK_FILE = Path.home() / ".cache" / "jevmlx" / "typesafe" / "dataset.lock.json"
JEVMLX_MANIFEST = Path(__file__).parent.parent / "results" / "jevmlx_baseline" / "manifest.json"
HOSTED_JEV_LOCK_SHA = Path(__file__).parent.parent / "results" / "hosted_jev" / "dataset_lock_sha256.txt"


def current_cases_sha256() -> str:
    """Read the sha256 the current TypeSafe cache was fetched under."""
    lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    return lock["cases_sha256"]


def _lock_file_sha256() -> str:
    """sha256 of the whole lock file, matching jevmlx's dataset_lock_sha256."""
    return hashlib.sha256(LOCK_FILE.read_bytes()).hexdigest()


def assert_dataset_identity(
    jevmlx_manifest: dict | None,
    hosted_jev_sha: str | None,
    current_sha: str,
) -> None:
    """Fail closed if a result artifact was produced against a different
    dataset snapshot than the one currently cached. Each side compares the
    sha256 of the whole ``dataset.lock.json`` file (jevmlx's own
    ``dataset_lock_sha256`` convention), not ``cases_sha256`` alone, so both
    legs use one consistent identity.
    """
    if jevmlx_manifest is not None:
        recorded = jevmlx_manifest.get("dataset_lock_sha256")
        if recorded != current_sha:
            sys.exit(
                f"results/jevmlx_baseline: dataset lock mismatch "
                f"(recorded {recorded}, current {current_sha}). Re-run the jevmlx "
                "baseline against the current cache or refresh the cache."
            )
    if hosted_jev_sha is not None:
        if hosted_jev_sha != current_sha:
            sys.exit(
                f"results/hosted_jev: dataset lock mismatch "
                f"(recorded {hosted_jev_sha}, current {current_sha}). Re-run "
                "scripts/run_hosted_jev.py against the current cache or refresh the cache."
            )
```

Note: `current_cases_sha256()` reads `cases_sha256` and is exposed for other callers/debugging, but `assert_dataset_identity` itself compares whole-lock-file shas (`_lock_file_sha256()`), matching what `manifest.json` already records under `dataset_lock_sha256` — don't compare `cases_sha256` against `dataset_lock_sha256`, they're hashes of different things and will never match.

- [ ] **Step 4: Run to verify the identity tests pass**

Run: `pytest tests/test_run_phase1.py -k assert_dataset_identity -v`
Expected: all 4 PASS

- [ ] **Step 5: Wire the check into `main()`**

In `scripts/run_phase1.py`, inside `main()`, right after `jevmlx_report = json.loads(JEVMLX_REPORT.read_text(encoding="utf-8"))` (existing line ~209) and before computing `hosted_jev_agreement`, insert:

```python
    current_sha = _lock_file_sha256()
    jevmlx_manifest = (
        json.loads(JEVMLX_MANIFEST.read_text(encoding="utf-8"))
        if JEVMLX_MANIFEST.exists()
        else None
    )
    hosted_jev_sha = (
        HOSTED_JEV_LOCK_SHA.read_text(encoding="utf-8").strip()
        if HOSTED_JEV_LOCK_SHA.exists()
        else None
    )
    assert_dataset_identity(jevmlx_manifest, hosted_jev_sha, current_sha)
```

- [ ] **Step 6: Make `run_hosted_jev.py` write the sidecar sha file**

In `scripts/run_hosted_jev.py`, in `main()`, after the `RESULTS_DIR.mkdir(parents=True, exist_ok=True)` line, add:

```python
    import hashlib

    lock_path = Path.home() / ".cache" / "jevmlx" / "typesafe" / "dataset.lock.json"
    (RESULTS_DIR / "dataset_lock_sha256.txt").write_text(
        hashlib.sha256(lock_path.read_bytes()).hexdigest(), encoding="utf-8"
    )
```

- [ ] **Step 7: Verify end-to-end against the real local cache**

Run: `python3 scripts/run_phase1.py`
Expected: either succeeds and prints `wrote results/laya_phase1/predictions.jsonl` / `wrote results/laya_phase1/report.md` (if the on-disk `manifest.json` and `dataset_lock_sha256.txt` already match the live cache — they were produced from the same 2026-09-27/28 fetch, so this should pass), OR fails with one of the two `sys.exit` messages from Step 3 — if so, that confirms the check actually fires; re-run `scripts/run_hosted_jev.py` to refresh the sidecar and confirm `run_phase1.py` then passes.

- [ ] **Step 8: Run full suite**

Run: `pytest tests/ -v`
Expected: all PASS

- [ ] **Step 9: Commit**

```bash
git add scripts/run_phase1.py scripts/run_hosted_jev.py tests/test_run_phase1.py
git commit -m "fix: fail closed when result artifacts don't match the current dataset snapshot"
```

---

### Task 4: Scope `majority_baseline` priors to (workflow, field) and stabilize tie-breaking

**Files:**
- Modify: `scoring/agreement.py:78-120`
- Test: `tests/test_agreement.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `scoring.agreement.majority_baseline(cases: list[dict]) -> dict` — same return shape (`overall`, `n_fields`, `by_workflow`), same call site in `scripts/run_phase1.py:219` (`majority_baseline(cases)`), no caller changes needed.

Root cause: `labels_by_field` is keyed by `field` alone (`scoring/agreement.py:89`), so a field name reused across two workflows would pool unrelated label distributions into one prior. Verified against the live dataset: **no such collision currently exists** (checked programmatically), so this is a dormant correctness bug, not a live miscalculation — fix it anyway since it's one dict key. Tie-breaking via `Counter.most_common(1)` is deterministic given a fixed case order (not the "nondeterministic" framing from the external review) but is still an arbitrary rule with no documented tie policy; keep the same tie behavior (first-encountered) but scope it per-workflow so a future collision can't silently corrupt a baseline.

- [ ] **Step 1: Write the failing test for scoping**

Add to `tests/test_agreement.py`:

```python
from scoring.agreement import majority_baseline


def test_majority_baseline_scopes_priors_by_workflow_and_field():
    # Same field name "status" reused in two workflows with opposite majority labels.
    # A field-only prior would blend them; a (workflow, field) prior must not.
    cases = [
        {"id": "a1", "workflow": "wf_a", "labels": {"status": "open"}},
        {"id": "a2", "workflow": "wf_a", "labels": {"status": "open"}},
        {"id": "a3", "workflow": "wf_a", "labels": {"status": "closed"}},
        {"id": "b1", "workflow": "wf_b", "labels": {"status": "closed"}},
        {"id": "b2", "workflow": "wf_b", "labels": {"status": "closed"}},
        {"id": "b3", "workflow": "wf_b", "labels": {"status": "open"}},
    ]
    result = majority_baseline(cases)
    # wf_a majority is "open" (2/3), wf_b majority is "closed" (2/3) — a field-only
    # prior pooling both workflows would instead see a tied/blended "open" vs "closed"
    # count and could get either wrong; scoped priors must get both right at 2/3 each.
    assert result["by_workflow"]["wf_a"] == pytest.approx(2 / 3)
    assert result["by_workflow"]["wf_b"] == pytest.approx(2 / 3)
```

Add `import pytest` to the top of `tests/test_agreement.py` if not already present (check first: `grep -n "^import pytest" tests/test_agreement.py`).

- [ ] **Step 2: Run to verify current behavior**

Run: `pytest tests/test_agreement.py -k scopes_priors -v`
Expected: currently PASSES by coincidence (2/3 majority holds even pooled here) — this test alone won't distinguish the bug. Add a second, discriminating case:

```python
def test_majority_baseline_does_not_leak_across_workflows_on_tied_pool():
    # Pooled across both workflows, "open" and "closed" are tied 3-3, so a
    # field-only prior's Counter.most_common(1) would pick one label and
    # apply it globally — getting the OTHER workflow's true majority wrong.
    # Scoped by (workflow, field), each workflow keeps its own 2/1 majority.
    cases = [
        {"id": "a1", "workflow": "wf_a", "labels": {"status": "open"}},
        {"id": "a2", "workflow": "wf_a", "labels": {"status": "open"}},
        {"id": "a3", "workflow": "wf_a", "labels": {"status": "closed"}},
        {"id": "b1", "workflow": "wf_b", "labels": {"status": "closed"}},
        {"id": "b2", "workflow": "wf_b", "labels": {"status": "closed"}},
        {"id": "b3", "workflow": "wf_b", "labels": {"status": "open"}},
    ]
    result = majority_baseline(cases)
    assert result["by_workflow"]["wf_a"] == pytest.approx(2 / 3)
    assert result["by_workflow"]["wf_b"] == pytest.approx(2 / 3)
    # Overall must reflect per-workflow LOO scoring, not one blended guess:
    # every case's guess is its own workflow's majority of the OTHER cases,
    # so overall should also be 4/6, not degraded by cross-workflow leakage.
    assert result["overall"] == pytest.approx(4 / 6)
```

Run: `pytest tests/test_agreement.py -k "scopes_priors or does_not_leak" -v`
Expected: `does_not_leak` FAILs against current field-only-keyed code (pooled counter sees "open": 3, "closed": 3 — a tie broken by insertion order, giving one workflow's cases a systematically wrong guess).

- [ ] **Step 3: Implement the (workflow, field) key**

Replace `scoring/agreement.py:89-94`:

```python
    labels_by_field: dict[str, list[tuple[str, object]]] = defaultdict(list)
    case_workflow: dict[str, str] = {}
    for case in cases:
        case_workflow[case["id"]] = str(case.get("workflow"))
        for field, label in case.get("labels", {}).items():
            labels_by_field[field].append((case["id"], label))
```

with:

```python
    labels_by_key: dict[tuple[str, str], list[tuple[str, object]]] = defaultdict(list)
    case_workflow: dict[str, str] = {}
    for case in cases:
        workflow = str(case.get("workflow"))
        case_workflow[case["id"]] = workflow
        for field, label in case.get("labels", {}).items():
            labels_by_key[(workflow, field)].append((case["id"], label))
```

And update the loop at `scoring/agreement.py:100-111` — replace `for entries in labels_by_field.values():` with `for entries in labels_by_key.values():` (only the iterable name changes; the loop body is unchanged since `workflow` is already looked up per-`case_id` inside it via `case_workflow.get(case_id, "unknown")`).

- [ ] **Step 4: Run to verify tests pass**

Run: `pytest tests/test_agreement.py -v`
Expected: all PASS including both new tests

- [ ] **Step 5: Run full suite**

Run: `pytest tests/ -v`
Expected: all PASS

- [ ] **Step 6: Re-verify against real data that the headline number didn't silently change for a bad reason**

Run: `python3 -c "
import json, pathlib, sys
sys.path.insert(0, '.')
from scoring.agreement import majority_baseline
cases = [json.loads(l) for l in (pathlib.Path.home()/'.cache/jevmlx/typesafe/cases.jsonl').read_text().splitlines() if l]
print(majority_baseline(cases)['overall'])
"`
Expected: prints a float close to the PLAN.md-cited `0.725` (small movement is fine and expected — PLAN.md already confirmed to have no cross-workflow field collisions today, so this fix should be a no-op or near-no-op on the current dataset; a large jump would mean something else is wrong and should be investigated before committing).

- [ ] **Step 7: Commit**

```bash
git add scoring/agreement.py tests/test_agreement.py
git commit -m "fix: scope majority_baseline priors by (workflow, field) to prevent cross-workflow leakage"
```

---

### Task 5: Fix silent partial hosted-Jev runs

**Files:**
- Modify: `scripts/run_hosted_jev.py`
- Test: `tests/test_run_hosted_jev.py` (new file)

**Interfaces:**
- Consumes: nothing new from earlier tasks except the sidecar-sha write added in Task 3 Step 6 (keep that code, it's independent of this task's changes).
- Produces: `scripts.run_hosted_jev.main()` now exits non-zero (`sys.exit(1)`) when any case errored, and writes to a `.tmp` path before atomically renaming to `predictions.jsonl` only on full completion. No existing caller depends on the old always-exit-0 behavior — `run_phase1.py` only checks `HOSTED_JEV_PREDICTIONS.exists()`.

Root cause: `run_hosted_jev.py` opens `results/hosted_jev/predictions.jsonl` directly for writing, continues past `HTTPError`/`URLError`, writes an empty-`predictions` record for the failed case, and always exits 0 even when `errors` is non-empty. An interrupted run (Ctrl-C, crash) also leaves a partial file at the real path, which `run_phase1.py` then silently consumes because it exists.

- [ ] **Step 1: Write the failing test**

Create `tests/test_run_hosted_jev.py`:

```python
import json
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.run_hosted_jev import run


def test_run_writes_to_temp_and_renames_only_on_success(tmp_path, monkeypatch):
    cases = [
        {"id": "c1", "workflow": "wf_a", "schema": {}, "context": "ctx1"},
        {"id": "c2", "workflow": "wf_a", "schema": {}, "context": "ctx2"},
    ]

    def fake_map_schema(schema):
        return {}, []  # no questions -> no API call, empty predictions

    def fake_call_jev(api_key, state, questions):
        raise AssertionError("should not be called when questions is empty")

    exit_code = run(
        cases=cases,
        results_dir=tmp_path,
        api_key="test-key",
        map_schema=fake_map_schema,
        call_jev=fake_call_jev,
    )

    assert exit_code == 0
    assert (tmp_path / "predictions.jsonl").exists()
    assert not (tmp_path / "predictions.jsonl.tmp").exists()
    lines = (tmp_path / "predictions.jsonl").read_text().splitlines()
    assert len(lines) == 2


def test_run_exits_nonzero_and_leaves_no_final_file_on_error(tmp_path):
    cases = [
        {"id": "c1", "workflow": "wf_a", "schema": {"q": {"type": "boolean"}}, "context": "ctx1"},
    ]

    def fake_map_schema(schema):
        return {"q": {"type": "noul", "instructions": "x"}}, []

    def fake_call_jev(api_key, state, questions):
        raise urllib.error.URLError("network down")

    exit_code = run(
        cases=cases,
        results_dir=tmp_path,
        api_key="test-key",
        map_schema=fake_map_schema,
        call_jev=fake_call_jev,
    )

    assert exit_code == 1
    assert not (tmp_path / "predictions.jsonl").exists()
    assert (tmp_path / "errors.json").exists()
    errors = json.loads((tmp_path / "errors.json").read_text())
    assert errors[0]["id"] == "c1"
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_run_hosted_jev.py -v`
Expected: FAIL with `ImportError: cannot import name 'run'` — `run()` doesn't exist yet, the logic is inline in `main()`.

- [ ] **Step 3: Refactor `run_hosted_jev.py` to extract a testable `run()` and fix the write/exit behavior**

Replace `scripts/run_hosted_jev.py`'s `main()` function (and everything from `def main()` to the end of the file) with:

```python
def run(cases, results_dir, api_key, map_schema, call_jev) -> int:
    """Score every case, writing predictions.jsonl only on full success.

    Returns 0 if every case with mappable questions scored successfully, 1
    if any case errored (the temp file is discarded, errors.json is written,
    no partial predictions.jsonl is left for run_phase1.py to consume).
    """
    results_dir.mkdir(parents=True, exist_ok=True)
    final_path = results_dir / "predictions.jsonl"
    tmp_path = results_dir / "predictions.jsonl.tmp"
    errors_path = results_dir / "errors.json"

    errors = []
    with tmp_path.open("w", encoding="utf-8") as handle:
        for i, case in enumerate(cases, 1):
            questions, unmapped = map_schema(case["schema"])
            predictions: dict = {}
            if questions:
                try:
                    raw = call_jev(api_key, case["context"], questions)
                    predictions = parse_jev_result(raw)
                except (urllib.error.HTTPError, urllib.error.URLError) as exc:
                    errors.append({"id": case["id"], "error": str(exc)})
                    print(f"[{i}/{len(cases)}] ERROR {case['id']}: {exc}", file=sys.stderr)
                    time.sleep(0.3)
                    continue
            record = {
                "id": case["id"],
                "workflow": case.get("workflow"),
                "predictions": predictions,
                "unmapped": unmapped,
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"[{i}/{len(cases)}] scored {case['id']}")
            time.sleep(0.3)

    if errors:
        errors_path.write_text(json.dumps(errors, indent=2), encoding="utf-8")
        tmp_path.unlink()
        print(
            f"{len(errors)} case(s) failed; see {errors_path}. "
            f"No {final_path} written — re-run once the failures are resolved.",
            file=sys.stderr,
        )
        return 1

    if errors_path.exists():
        errors_path.unlink()
    tmp_path.rename(final_path)
    (results_dir / "dataset_lock_sha256.txt").write_text(
        hashlib.sha256(
            (Path.home() / ".cache" / "jevmlx" / "typesafe" / "dataset.lock.json").read_bytes()
        ).hexdigest(),
        encoding="utf-8",
    )
    print(f"wrote {final_path}")
    return 0


def main() -> None:
    sys.path.insert(0, str(ROOT))
    from mapping.map_schema import map_schema

    api_key = load_api_key()
    cases = [json.loads(line) for line in CACHE.read_text(encoding="utf-8").splitlines() if line]
    sys.exit(run(cases, RESULTS_DIR, api_key, map_schema, call_jev))


if __name__ == "__main__":
    main()
```

Also add `import hashlib` to the top imports of `scripts/run_hosted_jev.py` (alongside the existing `import json`, `import sys`, etc.), and **remove** the old inline `main()` body's `RESULTS_DIR.mkdir` / `predictions_path` / `errors` loop that this replaces (Task 3 Step 6's sidecar-sha snippet is now folded into `run()` above — don't duplicate it if you did Task 3 before this task; if doing this task standalone, the snippet above already includes it).

- [ ] **Step 4: Run to verify tests pass**

Run: `pytest tests/test_run_hosted_jev.py -v`
Expected: both PASS

- [ ] **Step 5: Run full suite**

Run: `pytest tests/ -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/run_hosted_jev.py tests/test_run_hosted_jev.py
git commit -m "fix: run_hosted_jev writes atomically and fails closed on any case error"
```

---

### Task 6: Soften overclaimed PLAN.md language around the majority baseline

**Files:**
- Modify: `PLAN.md:59-78`

**Interfaces:**
- Consumes: nothing (prose-only edit).
- Produces: nothing consumed by code — this is documentation-only, verify by re-reading the section, not by running anything.

Root cause: `PLAN.md:67` calls the laya-vs-baseline gap "a real, settled deficit" and line 68 calls hosted-Jev-vs-baseline "robustly above it," based only on sign stability across three weighting choices of a leave-one-out (LOO) baseline — no confidence interval, bootstrap, or group-safe holdout, and `majority_baseline`'s own docstring (`scoring/agreement.py:79-88`) already says LOO "overstates a true held-out baseline at this sample size." The finding is about calibrated language, not about the underlying numbers being wrong.

- [ ] **Step 1: Read the current section**

Run: `sed -n '54,78p' PLAN.md`
Expected: matches the text quoted in the review (laya 0.542 / jevmlx-local 0.753 / hosted-Jev 0.827 / baseline 0.725, with "a real, settled deficit" and "robustly above it").

- [ ] **Step 2: Edit the two overclaiming lines**

In `PLAN.md`, replace:

```
  - **Laya vs. baseline: robustly below it** in every lens tried
    (-0.183 pooled, -0.097 case-weighted, -0.098 invoice-excluded). Not
    sensitive to weighting — a real, settled deficit.
  - **Hosted Jev vs. baseline: robustly above it**, margin growing once
    invoice_processing's inflation is removed (+0.102, +0.177, +0.256).
```

with:

```
  - **Laya vs. baseline: below it under every weighting tried**
    (-0.183 pooled, -0.097 case-weighted, -0.098 invoice-excluded). Sign
    is stable across weightings, but the baseline itself is a leave-one-out
    (LOO) heuristic fit on the same sample — a transductive/descriptive
    comparison, not an estimate of performance on unseen data (see
    `scoring.agreement.majority_baseline`'s docstring). No confidence
    interval or group-safe holdout has been computed; treat this as
    suggestive, not settled.
  - **Hosted Jev vs. baseline: above it under every weighting tried**,
    margin growing once invoice_processing's inflation is removed (+0.102,
    +0.177, +0.256) — same LOO-baseline caveat as above applies.
```

- [ ] **Step 3: Verify the edit**

Run: `grep -n "settled deficit\|robustly above" PLAN.md`
Expected: no matches (both phrases removed)

Run: `grep -n "transductive\|LOO heuristic" PLAN.md`
Expected: matches the new text

- [ ] **Step 4: Commit**

```bash
git add PLAN.md
git commit -m "docs: soften majority-baseline claims in PLAN.md to match LOO's known limitations"
```

---

### Task 7: Reword the hosted-Jev 0.827 headline to name the transform

**Files:**
- Modify: `PLAN.md:59-60`

**Interfaces:**
- Consumes: nothing (prose-only edit).
- Produces: nothing consumed by code.

Root cause: `mapping/map_schema.py:29-31` blanks every `choice`-type field's option descriptions (`dict.fromkeys(field["choices"], "")`) when building the questions hosted Jev answers — confirmed by reading the code. The 0.827 number is real and reproducible on this repo's normalized representation, but PLAN.md currently phrases it as if it directly replaced/reproduced TypeSafe's own native evaluation, without flagging that the question representation was transformed to fit the laya/jevmlx/hosted-Jev common schema.

- [ ] **Step 1: Edit the headline sentence**

In `PLAN.md`, replace:

```
      leaderboard number. Also added a leave-one-out majority-label
      baseline (`scoring.agreement.majority_baseline`) to every report.
      Updated headline: laya 0.542, jevmlx-local 0.753, **our hosted-Jev
      run 0.827** (vs. TypeSafe's cited 0.678 — kept for reference only),
```

with:

```
      leaderboard number. Also added a leave-one-out majority-label
      baseline (`scoring.agreement.majority_baseline`) to every report.
      Updated headline: laya 0.542, jevmlx-local 0.753, **our hosted-Jev
      run 0.827 on the normalized laya-eval/jevmlx question representation**
      (`mapping/map_schema.py` folds score-level text into field
      descriptions and blanks choice-option descriptions to keep laya,
      jevmlx, and hosted Jev on one common schema — this is not a native
      replay of TypeSafe's own question format) (vs. TypeSafe's cited
      0.678 — kept for reference only),
```

- [ ] **Step 2: Verify**

Run: `grep -n "normalized laya-eval/jevmlx" PLAN.md`
Expected: one match

- [ ] **Step 3: Commit**

```bash
git add PLAN.md
git commit -m "docs: clarify hosted-Jev 0.827 is on the normalized question representation"
```

---

### Task 8: Commit a reproducibility receipt alongside `results/`

**Files:**
- Create: `scripts/write_repro_receipt.py`
- Test: `tests/test_write_repro_receipt.py` (new file)

**Interfaces:**
- Consumes: `results/jevmlx_baseline/manifest.json`, `results/hosted_jev/dataset_lock_sha256.txt` (from Task 3/5), `results/laya_phase1/report.md` (existence only), current `dataset.lock.json`.
- Produces: `scripts.write_repro_receipt.build_receipt(root: Path) -> dict`, writes `results/repro_receipt.json` (committed — this one file is deliberately *not* gitignored; see Step 5).

Root cause: `results/` is entirely gitignored, so the case-weighted / invoice-excluded sensitivity numbers cited in `PLAN.md:65-76` (-0.097, +0.177, etc.) cannot currently be regenerated or even checked from the repo — there's no committed record of what dataset snapshot, model revision, or run produced the headline numbers. Full re-implementation of the sensitivity calculations is a separate, larger effort (they're one-off analysis, not part of the standard pipeline); this task instead commits a small, always-reproducible receipt so at least dataset/run identity is checkable, per the review's explicit "you do not need to commit all raw contexts, but you should commit a small reproducibility receipt" suggestion.

- [ ] **Step 1: Write the failing test**

Create `tests/test_write_repro_receipt.py`:

```python
import json
from pathlib import Path

from scripts.write_repro_receipt import build_receipt


def test_build_receipt_captures_dataset_and_artifact_identity(tmp_path):
    root = tmp_path
    (root / "results" / "jevmlx_baseline").mkdir(parents=True)
    (root / "results" / "hosted_jev").mkdir(parents=True)
    (root / "results" / "laya_phase1").mkdir(parents=True)
    (root / "results" / "jevmlx_baseline" / "manifest.json").write_text(
        json.dumps({"dataset_lock_sha256": "abc123", "model_id": "fast"})
    )
    (root / "results" / "hosted_jev" / "dataset_lock_sha256.txt").write_text("abc123")
    (root / "results" / "laya_phase1" / "report.md").write_text("# report")

    receipt = build_receipt(root)

    assert receipt["jevmlx_dataset_lock_sha256"] == "abc123"
    assert receipt["hosted_jev_dataset_lock_sha256"] == "abc123"
    assert receipt["dataset_identity_matches"] is True
    assert receipt["jevmlx_model_id"] == "fast"
    assert "generated_at" in receipt


def test_build_receipt_flags_mismatch(tmp_path):
    root = tmp_path
    (root / "results" / "jevmlx_baseline").mkdir(parents=True)
    (root / "results" / "hosted_jev").mkdir(parents=True)
    (root / "results" / "jevmlx_baseline" / "manifest.json").write_text(
        json.dumps({"dataset_lock_sha256": "abc123"})
    )
    (root / "results" / "hosted_jev" / "dataset_lock_sha256.txt").write_text("different")

    receipt = build_receipt(root)

    assert receipt["dataset_identity_matches"] is False
```

- [ ] **Step 2: Run to verify it fails**

Run: `pytest tests/test_write_repro_receipt.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.write_repro_receipt'`

- [ ] **Step 3: Implement**

Create `scripts/write_repro_receipt.py`:

```python
"""Write a small, committed record of which dataset/run produced the
results/ artifacts, since results/ itself is gitignored. Does not
regenerate the case-weighted / invoice-excluded sensitivity numbers cited
in PLAN.md — those remain manual one-off analysis; this only pins
dataset and run identity so that manual work stays checkable.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def build_receipt(root: Path) -> dict:
    jevmlx_manifest_path = root / "results" / "jevmlx_baseline" / "manifest.json"
    hosted_jev_sha_path = root / "results" / "hosted_jev" / "dataset_lock_sha256.txt"
    laya_report_path = root / "results" / "laya_phase1" / "report.md"

    jevmlx_manifest = (
        json.loads(jevmlx_manifest_path.read_text(encoding="utf-8"))
        if jevmlx_manifest_path.exists()
        else {}
    )
    jevmlx_sha = jevmlx_manifest.get("dataset_lock_sha256")
    hosted_jev_sha = (
        hosted_jev_sha_path.read_text(encoding="utf-8").strip()
        if hosted_jev_sha_path.exists()
        else None
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "jevmlx_dataset_lock_sha256": jevmlx_sha,
        "jevmlx_model_id": jevmlx_manifest.get("model_id"),
        "jevmlx_run_id": jevmlx_manifest.get("run_id"),
        "hosted_jev_dataset_lock_sha256": hosted_jev_sha,
        "dataset_identity_matches": (
            jevmlx_sha is not None and jevmlx_sha == hosted_jev_sha
        ),
        "laya_phase1_report_present": laya_report_path.exists(),
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    receipt = build_receipt(root)
    out_path = root / "results" / "repro_receipt.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    if not receipt["dataset_identity_matches"]:
        print("WARNING: jevmlx and hosted-Jev artifacts are on different dataset snapshots", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run to verify tests pass**

Run: `pytest tests/test_write_repro_receipt.py -v`
Expected: both PASS

- [ ] **Step 5: Un-ignore the one receipt file**

`results/` is gitignored wholesale (`.gitignore:1`). Add a negation so only the receipt is trackable. Edit `.gitignore`:

```
results/
!results/repro_receipt.json
.venv/
__pycache__/
*.pyc
.env
```

- [ ] **Step 6: Generate and commit the actual receipt from real local data**

Run: `python3 scripts/write_repro_receipt.py`
Expected: prints `wrote results/repro_receipt.json`; if it also prints the mismatch WARNING, resolve it first (re-run `scripts/run_hosted_jev.py` per Task 5, or refresh the jevmlx baseline) before committing — a committed receipt that flags its own mismatch defeats the purpose.

Run: `cat results/repro_receipt.json`
Expected: valid JSON with non-null `jevmlx_dataset_lock_sha256`, `dataset_identity_matches: true`

- [ ] **Step 7: Run full suite**

Run: `pytest tests/ -v`
Expected: all PASS

- [ ] **Step 8: Commit**

```bash
git add scripts/write_repro_receipt.py tests/test_write_repro_receipt.py .gitignore results/repro_receipt.json
git commit -m "feat: commit reproducibility receipt pinning dataset/run identity for results/"
```

---

### Task 9: Open the PR

**Files:** none (git/GitHub operations only)

- [ ] **Step 1: Push the branch**

```bash
git push -u origin <branch-name-chosen-when-branching-off-916155d>
```

- [ ] **Step 2: Final full-suite check on the pushed branch**

Run: `pytest tests/ -v`
Expected: all PASS (also verified by the new CI workflow once it runs on the PR)

- [ ] **Step 3: Open the PR against `main`**

```bash
gh pr create --title "Fix review findings: broken tests, dataset-identity checks, baseline scoping, PLAN.md overclaims" --body "$(cat <<'EOF'
## Summary
Fixes the confirmed findings from an external review of the (empty, closed) PR #1:
- Repaired `format_report` test broken by 916155d's signature/wording change
- Added a pytest CI workflow (none existed)
- `run_phase1.py` now fails closed if jevmlx/hosted-Jev artifacts were produced against a stale dataset snapshot
- `majority_baseline` now scopes priors by (workflow, field), not field alone
- `run_hosted_jev.py` writes atomically and exits non-zero on any case failure, instead of silently leaving a partial predictions file
- Softened PLAN.md language claiming the LOO baseline comparison is "settled"/"robust" — it's a transductive heuristic, now stated as such
- Reworded the 0.827 hosted-Jev headline to name the normalized question representation it was measured on
- Added a committed `results/repro_receipt.json` pinning dataset/run identity, since `results/` itself is gitignored

## Test plan
- [ ] `pytest tests/ -v` passes locally
- [ ] CI workflow passes on the PR
EOF
)"
```

- [ ] **Step 4: Report the PR URL back to the user**

---

## Self-Review Notes

- **Spec coverage:** all 8 numbered items from the review plus the "open a real PR" closer each map to one task (1↔1, 2↔2, 3↔3, 4↔4, 5↔6, 6↔4-dormant-note, 7↔9, 8↔7 headline / 8↔8 receipt, PR↔9).
- **Placeholder scan:** no TBD/TODO; every step has literal code or a literal shell command with expected output.
- **Type consistency:** `assert_dataset_identity(jevmlx_manifest: dict | None, hosted_jev_sha: str | None, current_sha: str)` in Task 3 matches its call site in Task 3 Step 5 and its test calls in Task 3 Step 1. `run(cases, results_dir, api_key, map_schema, call_jev)` in Task 5 matches both its test calls and its use inside the rewritten `main()`. `build_receipt(root: Path) -> dict` in Task 8 matches its test and its use in `main()`.
