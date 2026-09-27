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
    cases = [
        _case(
            "c1",
            "wf_a",
            {"urgent": True, "category": "billing"},
            ambiguous=["category"],
        )
    ]
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


def test_by_workflow_and_field_breakdown_has_field_and_case_denominators():
    cases = [
        _case("c1", "wf_a", {"x": True, "y": "a"}),
        _case("c2", "wf_a", {"x": False}),
        _case("c3", "wf_b", {"x": True}),
    ]
    predictions = [
        {"id": "c1", "predictions": {"x": True, "y": "b"}},
        {"id": "c2", "predictions": {"x": False}},
        {"id": "c3", "predictions": {"x": False}},
    ]

    result = score_agreement(cases, predictions)

    assert result["by_workflow_field"] == {
        "wf_a": {
            "x": {"agreement": 1.0, "n_cases": 2, "n_fields": 2},
            "y": {"agreement": 0.0, "n_cases": 1, "n_fields": 1},
        },
        "wf_b": {"x": {"agreement": 0.0, "n_cases": 1, "n_fields": 1}},
    }
