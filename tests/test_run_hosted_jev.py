import json
import urllib.error

from scripts.run_hosted_jev import run


def test_run_publishes_complete_predictions_and_digest(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.run_hosted_jev.time.sleep", lambda _: None)
    cases = [{"id": "c1", "workflow": "wf", "schema": {}, "context": "ctx"}]

    def no_questions(schema):
        return {}, []

    def no_call(*args):
        raise AssertionError("API should not be called")

    assert run(cases, tmp_path, "key", no_questions, no_call, "abc") == 0
    assert not (tmp_path / "predictions.jsonl.tmp").exists()
    assert json.loads((tmp_path / "predictions.jsonl").read_text())["id"] == "c1"
    assert (tmp_path / "dataset_lock_sha256.txt").read_text() == "abc"


def test_run_rejects_partial_results_and_removes_previous_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.run_hosted_jev.time.sleep", lambda _: None)
    (tmp_path / "predictions.jsonl").write_text("old run")
    (tmp_path / "dataset_lock_sha256.txt").write_text("old digest")
    cases = [{"id": "c1", "workflow": "wf", "schema": {"q": {}}, "context": "ctx"}]

    def one_question(schema):
        return {"q": {"type": "noul"}}, []

    def api_error(*args):
        raise urllib.error.URLError("network down")

    assert run(cases, tmp_path, "key", one_question, api_error, "abc") == 1
    assert not (tmp_path / "predictions.jsonl").exists()
    assert not (tmp_path / "dataset_lock_sha256.txt").exists()
    assert not (tmp_path / "predictions.jsonl.tmp").exists()
    assert json.loads((tmp_path / "errors.json").read_text())[0]["id"] == "c1"


def test_run_rejects_api_response_missing_a_requested_answer(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.run_hosted_jev.time.sleep", lambda _: None)
    cases = [{"id": "c1", "workflow": "wf", "schema": {"q": {}}, "context": "ctx"}]

    def one_question(schema):
        return {"q": {"type": "noul"}}, []

    assert run(cases, tmp_path, "key", one_question, lambda *_: {}, "abc") == 1
    assert not (tmp_path / "predictions.jsonl").exists()
    assert json.loads((tmp_path / "errors.json").read_text())[0]["id"] == "c1"
