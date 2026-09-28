"""Run Laya over the TypeSafe public eval and report agreement with consensus."""

from __future__ import annotations

import json
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

CACHE = Path.home() / ".cache" / "jevmlx" / "typesafe" / "cases.jsonl"
RESULTS_DIR = Path(__file__).parent.parent / "results" / "laya_phase1"
JEVMLX_REPORT = Path(__file__).parent.parent / "results" / "jevmlx_baseline" / "report.json"
HOSTED_JEV_PREDICTIONS = (
    Path(__file__).parent.parent / "results" / "hosted_jev" / "predictions.jsonl"
)
LOCK_FILE = Path.home() / ".cache" / "jevmlx" / "typesafe" / "dataset.lock.json"
JEVMLX_MANIFEST = Path(__file__).parent.parent / "results" / "jevmlx_baseline" / "manifest.json"
HOSTED_JEV_LOCK_SHA = Path(__file__).parent.parent / "results" / "hosted_jev" / "dataset_lock_sha256.txt"
OFFICIAL = (
    Path(__file__).parent.parent.parent
    / "openjev"
    / "benchmarks"
    / "typesafe"
    / "official.json"
)


def current_cases_sha256() -> str:
    """Return the case digest recorded in the current TypeSafe cache lock."""
    return json.loads(LOCK_FILE.read_text(encoding="utf-8"))["cases_sha256"]


def _lock_file_sha256() -> str:
    """Hash the whole lock file, as the jevmlx manifest does."""
    return hashlib.sha256(LOCK_FILE.read_bytes()).hexdigest()


def assert_dataset_identity(
    jevmlx_manifest: dict | None, hosted_jev_sha: str | None, current_sha: str
) -> None:
    """Reject artifacts tied to a different dataset lock."""
    if jevmlx_manifest is not None and jevmlx_manifest.get("dataset_lock_sha256") != current_sha:
        sys.exit("results/jevmlx_baseline: dataset lock mismatch; rerun against the current cache")
    if hosted_jev_sha is not None and hosted_jev_sha != current_sha:
        sys.exit("results/hosted_jev: dataset lock mismatch; rerun against the current cache")


def ensure_project_root_on_path() -> None:
    """Make project packages importable when this file is run as a script."""
    project_root = str(Path(__file__).resolve().parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


def sample_counts(cases: list[dict], predictions: list[dict]) -> dict:
    """Count scored and non-ambiguous fields for each report denominator."""
    predictions_by_id = {prediction["id"]: prediction["predictions"] for prediction in predictions}
    common_case_ids: set[str] = set()
    common_fields = 0
    workflow_case_ids: dict[str, set[str]] = defaultdict(set)
    workflow_fields: dict[str, int] = defaultdict(int)

    for case in cases:
        pred = predictions_by_id.get(case["id"])
        if pred is None:
            continue
        matched = [field for field in case["labels"] if field in pred]
        if not matched:
            continue
        workflow = str(case.get("workflow"))
        workflow_case_ids[workflow].add(case["id"])
        workflow_fields[workflow] += len(matched)
        ambiguous = set(case.get("meta", {}).get("ambiguous", []))
        non_ambiguous = [field for field in matched if field not in ambiguous]
        if non_ambiguous:
            common_case_ids.add(case["id"])
            common_fields += len(non_ambiguous)

    return {
        "n_common_cases": len(common_case_ids),
        "n_common_fields": common_fields,
        "by_workflow_counts": {
            workflow: {
                "n_cases": len(case_ids),
                "n_fields": workflow_fields[workflow],
            }
            for workflow, case_ids in workflow_case_ids.items()
        },
    }


def format_report(
    result: dict,
    total_unmapped: int,
    jevmlx_agreement: dict,
    hosted_jev_agreement: dict | None,
    baseline: dict,
    jev_row: dict,
    model_max_len: int,
    official_retrieved: str,
) -> str:
    """Render Phase 1 results with their sample sizes and claim boundaries."""
    common_cases = result["n_common_cases"]
    common_fields = result["n_common_fields"]
    lines = [
        "# Phase 1 — Agreement with TypeSafe consensus",
        "",
        f"{result['n_input_cases']} fetched cases; {result['n_cases']} had fields scored; "
        f"{result['n_input_cases'] - result['n_cases']} had no comparable fields.",
        f"Laya scored {result['n_cases']} cases and {result['n_fields']} fields; "
        f"{total_unmapped} schema fields were unmapped.",
        "",
        f"- Overall agreement with consensus: {result['overall']:.3f} "
        f"({result['n_cases']} cases, {result['n_fields']} fields)",
        f"- Non-ambiguous agreement with consensus: {result['common_subset']:.3f} "
        f"({common_cases} cases, {common_fields} fields)",
    ]

    if jevmlx_agreement:
        lines.append(
            f"- jevmlx local agreement on the fetched dataset: "
            f"{jevmlx_agreement['overall']:.3f} "
            f"({jevmlx_agreement['n_cases']} cases, {jevmlx_agreement['n_fields']} fields)"
        )
    else:
        lines.append("- jevmlx local agreement on the fetched dataset: not available")

    if hosted_jev_agreement and hosted_jev_agreement["overall"] is not None:
        lines.append(
            f"- Hosted Jev (our own run, jev-latest / TypeSafe /v1/systemone, same cases/scorer): "
            f"{hosted_jev_agreement['overall']:.3f} "
            f"({hosted_jev_agreement['n_cases']} cases, {hosted_jev_agreement['n_fields']} fields)"
        )
    else:
        lines.append("- Hosted Jev (our own run): not available")

    if baseline["overall"] is not None:
        lines.append(
            f"- Leave-one-out majority-label baseline (guess floor, not a model): "
            f"{baseline['overall']:.3f} ({baseline['n_fields']} fields)"
        )

    jev_value = jev_row.get("accuracy")
    cited_value = f"{jev_value:.3f}" if isinstance(jev_value, (int, float)) else "not available"
    lines.extend(
        [
            f"- TypeSafe cited hosted Jev (their private eval; n not reported): {cited_value} "
            "— kept for reference only; the hosted-Jev row above is our own run on the same "
            "cases/scorer as laya and jevmlx and should be preferred for comparison.",
            "",
            f"TypeSafe leaderboard citation retrieved {official_retrieved}; its cited row "
            "does not report a sample size. The reference labels here are consensus labels; "
            "independent ground truth is not available.",
            "",
            f"The Laya checkpoint has a {model_max_len:,}-token model input limit. "
            "laya-mlx truncates state tokens to fit after the question and option prefix, "
            "keeping the FRONT of the document and dropping the tail (default "
            "``truncate_left=False``, not overridden by this adapter). Verified mechanism "
            "(2026-09-28): on invoice_processing's longest case (34,166 chars / 10,358 "
            "tokens), only the first ~9% of the document (906 of 1,024 available tokens) "
            "reaches the model — enough to see the invoice's own line-item list, but not "
            "the underlying PO/contract terms further into the packet that the `scope` and "
            "`kind` questions need to judge against. This is a plausible, evidence-backed "
            "explanation for why those specific fields score zero across every line index "
            "(0-4) regardless of context, while header-level fields in the same workflow "
            "(`unusual_urgency`, `tax_two_rates`, `different_entity`) score well. It does "
            "NOT explain the worst-performing fields overall: `intent`, `churn_risk` "
            "(customer_service) and `attribution`, `first_bad_step` "
            "(agent_trace_observability) come from contexts of 406-1,381 chars — far under "
            "the token budget, never truncated — and still show the same constant-wrong-"
            "answer pattern. For those, the checkpoint is not truncation-starved; it simply "
            "defaults to one answer for that question type regardless of context. Treat "
            "these as two distinct, separately-diagnosed limitations, not one \"truncation\" "
            "story.",
            "",
            "The runtime warns that choice:11+ confidence calibration is clamped; "
            "confidence values are not evaluated in this report.",
            "",
            "By workflow (Laya agreement with consensus):",
        ]
    )
    for workflow, rate in sorted(result["by_workflow"].items()):
        counts = result["by_workflow_counts"][workflow]
        extra = []
        jevmlx_wf = (jevmlx_agreement or {}).get("by_workflow", {}).get(workflow)
        if jevmlx_wf is not None:
            extra.append(f"jevmlx {jevmlx_wf:.3f}")
        hosted_wf = (hosted_jev_agreement or {}).get("by_workflow", {}).get(workflow)
        if hosted_wf is not None:
            extra.append(f"hosted-jev {hosted_wf:.3f}")
        baseline_wf = baseline.get("by_workflow", {}).get(workflow)
        if baseline_wf is not None:
            extra.append(f"baseline {baseline_wf:.3f}")
        suffix = f" [{', '.join(extra)}]" if extra else ""
        lines.append(
            f"- {workflow}: {rate:.3f} "
            f"({counts['n_cases']} cases, {counts['n_fields']} fields){suffix}"
        )
    lines.extend(["", "By workflow and field:"])
    for workflow, fields in sorted(result["by_workflow_field"].items()):
        for field, stats in sorted(fields.items()):
            lines.append(
                f"- {workflow} / {field}: {stats['agreement']:.3f} "
                f"({stats['n_cases']} cases, {stats['n_fields']} fields)"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    ensure_project_root_on_path()
    from adapters.laya_adapter import LayaAdapter
    from scoring.agreement import majority_baseline, score_agreement

    cases = [
        json.loads(line)
        for line in CACHE.read_text(encoding="utf-8").splitlines()
        if line
    ]
    current_sha = _lock_file_sha256()
    jevmlx_manifest = json.loads(JEVMLX_MANIFEST.read_text(encoding="utf-8")) if JEVMLX_MANIFEST.exists() else None
    hosted_jev_sha = HOSTED_JEV_LOCK_SHA.read_text(encoding="utf-8").strip() if HOSTED_JEV_LOCK_SHA.exists() else None
    if HOSTED_JEV_PREDICTIONS.exists() and hosted_jev_sha is None:
        sys.exit("results/hosted_jev: missing dataset lock digest; rerun hosted Jev")
    assert_dataset_identity(jevmlx_manifest, hosted_jev_sha, current_sha)

    adapter = LayaAdapter()
    predictions = [adapter.predict_case(case) for case in cases]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    predictions_path = RESULTS_DIR / "predictions.jsonl"
    with predictions_path.open("w", encoding="utf-8") as handle:
        for prediction in predictions:
            handle.write(json.dumps(prediction, ensure_ascii=False) + "\n")

    result = score_agreement(cases, predictions)
    result.update(sample_counts(cases, predictions))
    result["n_input_cases"] = len(cases)
    jevmlx_report = json.loads(JEVMLX_REPORT.read_text(encoding="utf-8"))
    jevmlx_agreement = jevmlx_report.get("metrics", {}).get("agreement", {})
    hosted_jev_agreement = None
    if HOSTED_JEV_PREDICTIONS.exists():
        hosted_predictions = [
            json.loads(line)
            for line in HOSTED_JEV_PREDICTIONS.read_text(encoding="utf-8").splitlines()
            if line
        ]
        hosted_jev_agreement = score_agreement(cases, hosted_predictions)
    baseline = majority_baseline(cases)
    official = json.loads(OFFICIAL.read_text(encoding="utf-8"))
    jev_row = next(
        (model for model in official.get("models", []) if model.get("name") == "Jev"),
        {},
    )

    report = format_report(
        result=result,
        total_unmapped=sum(len(prediction["unmapped"]) for prediction in predictions),
        hosted_jev_agreement=hosted_jev_agreement,
        baseline=baseline,
        jevmlx_agreement=jevmlx_agreement,
        jev_row=jev_row,
        model_max_len=adapter.max_input_tokens,
        official_retrieved=official.get("retrieved", "unknown date"),
    )
    report_path = RESULTS_DIR / "report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"wrote {predictions_path}")
    print(f"wrote {report_path}")


if __name__ == "__main__":
    main()
