import json
import hashlib

from scripts.write_repro_receipt import build_receipt


def test_build_receipt_records_matching_artifact_identity(tmp_path):
    lock_path = tmp_path / "dataset.lock.json"
    lock_path.write_bytes(b"cache lock")
    lock_sha = hashlib.sha256(b"cache lock").hexdigest()
    baseline = tmp_path / "results" / "jevmlx_baseline"
    hosted = tmp_path / "results" / "hosted_jev"
    laya = tmp_path / "results" / "laya_phase1"
    baseline.mkdir(parents=True)
    hosted.mkdir(parents=True)
    laya.mkdir(parents=True)
    (baseline / "manifest.json").write_text(json.dumps({"dataset_lock_sha256": lock_sha, "model_id": "fast"}))
    (hosted / "dataset_lock_sha256.txt").write_text(lock_sha)
    (hosted / "predictions.jsonl").write_text("{\"id\": \"c1\"}\n")
    (laya / "report.md").write_text("# report")

    receipt = build_receipt(tmp_path, lock_path)

    assert receipt["jevmlx_dataset_lock_sha256"] == lock_sha
    assert receipt["hosted_jev_dataset_lock_sha256"] == lock_sha
    assert receipt["current_dataset_lock_sha256"] == lock_sha
    assert receipt["hosted_jev_predictions_sha256"] == hashlib.sha256(b'{"id": "c1"}\n').hexdigest()
    assert receipt["laya_phase1_report_sha256"] == hashlib.sha256(b"# report").hexdigest()
    assert receipt["dataset_identity_matches"] is True
    assert receipt["jevmlx_model_id"] == "fast"
    assert receipt["laya_phase1_report_present"] is True
    assert "generated_at" in receipt


def test_build_receipt_flags_different_dataset_locks(tmp_path):
    lock_path = tmp_path / "dataset.lock.json"
    lock_path.write_bytes(b"cache lock")
    baseline = tmp_path / "results" / "jevmlx_baseline"
    hosted = tmp_path / "results" / "hosted_jev"
    baseline.mkdir(parents=True)
    hosted.mkdir(parents=True)
    (baseline / "manifest.json").write_text(json.dumps({"dataset_lock_sha256": "abc"}))
    (hosted / "dataset_lock_sha256.txt").write_text("different")

    assert build_receipt(tmp_path, lock_path)["dataset_identity_matches"] is False


def test_build_receipt_rejects_artifacts_matching_each_other_but_not_cache(tmp_path):
    lock_path = tmp_path / "dataset.lock.json"
    lock_path.write_bytes(b"current lock")
    baseline = tmp_path / "results" / "jevmlx_baseline"
    hosted = tmp_path / "results" / "hosted_jev"
    baseline.mkdir(parents=True)
    hosted.mkdir(parents=True)
    (baseline / "manifest.json").write_text(json.dumps({"dataset_lock_sha256": "stale"}))
    (hosted / "dataset_lock_sha256.txt").write_text("stale")

    assert build_receipt(tmp_path, lock_path)["dataset_identity_matches"] is False
