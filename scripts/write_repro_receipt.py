"""Record dataset and run identity for the ignored evaluation artifacts."""

from __future__ import annotations

import json
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path


def build_receipt(root: Path, lock_path: Path | None = None) -> dict:
    if lock_path is None:
        lock_path = Path.home() / ".cache" / "jevmlx" / "typesafe" / "dataset.lock.json"
    manifest_path = root / "results" / "jevmlx_baseline" / "manifest.json"
    hosted_sha_path = root / "results" / "hosted_jev" / "dataset_lock_sha256.txt"
    report_path = root / "results" / "laya_phase1" / "report.md"
    hosted_predictions_path = root / "results" / "hosted_jev" / "predictions.jsonl"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    jevmlx_sha = manifest.get("dataset_lock_sha256")
    hosted_sha = hosted_sha_path.read_text(encoding="utf-8").strip() if hosted_sha_path.exists() else None
    current_sha = hashlib.sha256(lock_path.read_bytes()).hexdigest()

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "jevmlx_dataset_lock_sha256": jevmlx_sha,
        "jevmlx_model_id": manifest.get("model_id"),
        "jevmlx_run_id": manifest.get("run_id"),
        "hosted_jev_dataset_lock_sha256": hosted_sha,
        "current_dataset_lock_sha256": current_sha,
        "hosted_jev_predictions_sha256": (
            hashlib.sha256(hosted_predictions_path.read_bytes()).hexdigest()
            if hosted_predictions_path.exists() else None
        ),
        "dataset_identity_matches": jevmlx_sha == hosted_sha == current_sha,
        "laya_phase1_report_present": report_path.exists(),
        "laya_phase1_report_sha256": (
            hashlib.sha256(report_path.read_bytes()).hexdigest() if report_path.exists() else None
        ),
    }


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    receipt = build_receipt(root)
    if not receipt["dataset_identity_matches"]:
        sys.exit("jevmlx and hosted Jev artifacts have different or missing dataset identities")
    out_path = root / "results" / "repro_receipt.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
