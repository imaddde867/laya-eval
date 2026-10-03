import pathlib

import pytest

from scripts import run_position_laya as rp


class FakeAgent:
    """Mimics laya's predict(): returns the same shape as tests/fixtures/laya_raw_response.json."""

    def __init__(self, picker):
        self.picker = picker

    def predict(self, context, questions):
        criteria = list(questions["risk_tier"]["criteria"])
        chosen = self.picker(context, criteria)
        probs = {k: (0.8 if k == chosen else 0.1) for k in criteria}
        return {
            "answers": {
                "risk_tier": {"type": "choice", "choice": chosen, "probabilities": probs},
                "is_risky": {"type": "noul", "noul": 0.5},
            },
            "usage": {"input_tokens": 10},
        }


def by_content(context, criteria):
    return "high" if "URGENT" in context else "low"


def by_second_slot(context, criteria):
    return criteria[1]


def test_content_driven_agent_is_order_invariant():
    summary = rp.summarize(rp.run_experiment(FakeAgent(by_content)))
    assert summary["cases_flipped"] == 0
    assert summary["cases_complete"] == 6
    assert summary["control_choice_changes"] == 0
    assert summary["control_max_prob_diff"] == 0


def test_position_driven_agent_flips_and_follows_second_slot():
    summary = rp.summarize(rp.run_experiment(FakeAgent(by_second_slot)))
    assert summary["cases_flipped"] == 6  # second slot is medium, medium, high across the 3 orders
    assert summary["slot_counts"][1] == 18
    assert summary["slot_counts"][0] == 0 and summary["slot_counts"][2] == 0


def test_constant_answer_is_flagged():
    summary = rp.summarize(rp.run_experiment(FakeAgent(lambda c, k: "medium")))
    assert summary["cases_flipped"] == 0
    assert summary["constant_answer"] is True
    assert "constant answer" in rp.format_table(summary)


def test_failing_call_is_recorded_not_fatal():
    class EmptyFails(FakeAgent):
        def predict(self, context, questions):
            if context == "":
                raise ValueError("empty context")
            return super().predict(context, questions)

    records = rp.run_experiment(EmptyFails(by_content))
    summary = rp.summarize(records)
    assert summary["cases_total"] == 6
    assert summary["cases_complete"] == 5
    assert summary["per_case"]["empty_string"]["errors"]
    assert summary["per_case"]["empty_string"]["flipped"] is False


def test_build_questions_changes_only_order():
    a = rp.build_questions(["low", "medium", "high"])
    b = rp.build_questions(["high", "medium", "low"])
    assert list(a["risk_tier"]["criteria"]) != list(b["risk_tier"]["criteria"])
    assert a["risk_tier"]["criteria"] == b["risk_tier"]["criteria"]  # same content (dict equality ignores order)
    assert a["is_risky"] == b["is_risky"]
    blank = rp.build_questions(["low", "medium", "high"], keep_descriptions=False)
    assert set(blank["risk_tier"]["criteria"].values()) == {""}


REFERENCE = rp.DEFAULT_REFERENCE


@pytest.mark.skipif(not REFERENCE.exists(), reason="sibling jev-position-test not present")
def test_inputs_match_reference_script():
    rp.check_against_reference(REFERENCE)


@pytest.mark.skipif(not REFERENCE.exists(), reason="sibling jev-position-test not present")
def test_reference_drift_is_caught(monkeypatch):
    changed = dict(rp.CASES, benign_smalltalk="changed")
    monkeypatch.setattr(rp, "CASES", changed)
    with pytest.raises(SystemExit):
        rp.check_against_reference(REFERENCE)
