import sys
from pathlib import Path

from scripts.run_phase1 import ensure_project_root_on_path, format_report, sample_counts


def test_direct_script_bootstrap_adds_project_root(monkeypatch):
    project_root = Path(__file__).parent.parent.resolve()
    monkeypatch.setattr(sys, "path", [str(project_root / "scripts")])

    ensure_project_root_on_path()

    assert sys.path[0] == str(project_root)


def test_sample_counts_use_scored_fields_and_exclude_ambiguous_from_common_subset():
    cases = [
        {
            "id": "c1",
            "workflow": "wf_a",
            "labels": {"urgent": True, "category": "billing"},
            "meta": {"ambiguous": ["category"]},
        },
        {
            "id": "c2",
            "workflow": "wf_b",
            "labels": {"urgent": False},
            "meta": {"ambiguous": []},
        },
    ]
    predictions = [
        {"id": "c1", "predictions": {"urgent": True, "category": "billing"}},
        {"id": "c2", "predictions": {"urgent": True}},
    ]

    assert sample_counts(cases, predictions) == {
        "n_common_cases": 2,
        "n_common_fields": 2,
        "by_workflow_counts": {
            "wf_a": {"n_cases": 1, "n_fields": 2},
            "wf_b": {"n_cases": 1, "n_fields": 1},
        },
    }


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
        jev_row={"accuracy": 0.678},
        model_max_len=1024,
        official_retrieved="2026-09-17",
    )

    assert "2 fetched cases; 2 had fields scored; 0 had no comparable fields." in report
    assert "Overall agreement with consensus: 0.667 (2 cases, 3 fields)" in report
    assert "Non-ambiguous agreement with consensus: 1.000 (2 cases, 2 fields)" in report
    assert "jevmlx local agreement on the fetched dataset: 0.750 (2 cases, 4 fields)" in report
    assert "TypeSafe cited hosted Jev (private eval; n not reported): 0.678" in report
    assert "wf_a: 0.667 (2 cases, 3 fields)" in report
    assert "wf_a / urgent: 1.000 (2 cases, 2 fields)" in report
    assert "1,024-token model input limit." in report
    assert "laya-mlx truncates state tokens" in report
    assert "confidence values are not evaluated" in report
