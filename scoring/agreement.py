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
    preds_by_id = {prediction["id"]: prediction["predictions"] for prediction in predictions}
    total = 0
    correct = 0
    common_total = 0
    common_correct = 0
    by_workflow_totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    by_workflow_field: dict[str, dict[str, list[int]]] = defaultdict(
        lambda: defaultdict(lambda: [0, 0])
    )
    by_workflow_field_cases: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
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
            by_workflow_field[workflow][field][0] += 1
            by_workflow_field[workflow][field][1] += int(is_correct)
            by_workflow_field_cases[workflow][field].add(case["id"])
            if field not in ambiguous:
                common_total += 1
                common_correct += int(is_correct)

    return {
        "overall": (correct / total) if total else None,
        "common_subset": (common_correct / common_total) if common_total else None,
        "n_fields": total,
        "n_cases": len(case_ids),
        "by_workflow": {
            workflow: (matches / count if count else None)
            for workflow, (count, matches) in by_workflow_totals.items()
        },
        "by_workflow_field": {
            workflow: {
                field: {
                    "agreement": matches / count if count else None,
                    "n_cases": len(by_workflow_field_cases[workflow][field]),
                    "n_fields": count,
                }
                for field, (count, matches) in fields.items()
            }
            for workflow, fields in by_workflow_field.items()
        },
    }
