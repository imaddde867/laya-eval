"""Run Laya over the TypeSafe public eval and report agreement with consensus."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

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

    jev_value = jev_row.get("accuracy")
    cited_value = f"{jev_value:.3f}" if isinstance(jev_value, (int, float)) else "not available"
    lines.extend(
        [
            f"- TypeSafe cited hosted Jev (private eval; n not reported): {cited_value}",
            "",
            f"TypeSafe leaderboard citation retrieved {official_retrieved}; its cited row "
            "does not report a sample size. The reference labels here are consensus labels; "
            "independent ground truth is not available.",
            "",
            f"The Laya checkpoint has a {model_max_len:,}-token model input limit. "
            "laya-mlx truncates state tokens to fit after the question and option prefix; "
            "the results reflect that default behavior.",
            "",
            "The runtime warns that choice:11+ confidence calibration is clamped; "
            "confidence values are not evaluated in this report.",
            "",
            "By workflow (Laya agreement with consensus):",
        ]
    )
    for workflow, rate in sorted(result["by_workflow"].items()):
        counts = result["by_workflow_counts"][workflow]
        lines.append(
            f"- {workflow}: {rate:.3f} "
            f"({counts['n_cases']} cases, {counts['n_fields']} fields)"
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
    from scoring.agreement import score_agreement

    cases = [
        json.loads(line)
        for line in CACHE.read_text(encoding="utf-8").splitlines()
        if line
    ]

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
    official = json.loads(OFFICIAL.read_text(encoding="utf-8"))
    jev_row = next(
        (model for model in official.get("models", []) if model.get("name") == "Jev"),
        {},
    )

    report = format_report(
        result=result,
        total_unmapped=sum(len(prediction["unmapped"]) for prediction in predictions),
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
