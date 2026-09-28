"""Run TypeSafe's hosted Jev over the same Phase 1 cases laya and jevmlx used.

Replaces the cited leaderboard number (private eval, n not reported) with a
number we produced ourselves: same 44-45 cases, same consensus labels, same
scorer as laya and jevmlx. Uses the same ``mapping/map_schema`` output as the
laya adapter, since the hosted ``/v1/systemone`` API speaks the same typed
question vocabulary (choice/score/noul) laya does.

Reads TYPESAFE_API_KEY from a local .env (gitignored) or the environment.
Never prints the key. Costs real API calls against your TypeSafe account.
"""

from __future__ import annotations

import json
import hashlib
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path.home() / ".cache" / "jevmlx" / "typesafe" / "cases.jsonl"
RESULTS_DIR = ROOT / "results" / "hosted_jev"
ENDPOINT = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"


def load_api_key() -> str:
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("TYPESAFE_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    import os

    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        sys.exit("TYPESAFE_API_KEY not set in .env or environment.")
    return key


def call_jev(api_key: str, state: str, questions: dict, retries: int = 4) -> dict:
    body = json.dumps({"state": state, "model": MODEL, "questions": questions}).encode("utf-8")
    delay = 1.0
    for attempt in range(retries):
        request = urllib.request.Request(
            ENDPOINT,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 529) and attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            raise
    raise RuntimeError("unreachable")


def parse_jev_result(raw: dict) -> dict[str, object]:
    """Same answer shape as laya's ``parse_laya_result`` (both speak choice/score/noul)."""
    predictions: dict[str, object] = {}
    for name, answer in raw.get("answers", {}).items():
        answer_type = answer["type"]
        if answer_type == "choice":
            predictions[name] = answer["choice"]
        elif answer_type == "score":
            probabilities = answer["probabilities"]
            winning_level = max(probabilities, key=probabilities.get)
            predictions[name] = answer["legend"][winning_level]
        elif answer_type == "noul":
            predictions[name] = answer["noul"] >= 0.5
        else:
            raise ValueError(f"unsupported hosted-Jev answer type for {name!r}: {answer_type!r}")
    return predictions


def main() -> None:
    sys.path.insert(0, str(ROOT))
    from mapping.map_schema import map_schema

    api_key = load_api_key()
    cases = [json.loads(line) for line in CACHE.read_text(encoding="utf-8").splitlines() if line]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    predictions_path = RESULTS_DIR / "predictions.jsonl"
    errors = []
    with predictions_path.open("w", encoding="utf-8") as handle:
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
        (RESULTS_DIR / "errors.json").write_text(json.dumps(errors, indent=2), encoding="utf-8")
        print(f"{len(errors)} case(s) failed; see {RESULTS_DIR / 'errors.json'}", file=sys.stderr)
    else:
        lock_path = Path.home() / ".cache" / "jevmlx" / "typesafe" / "dataset.lock.json"
        (RESULTS_DIR / "dataset_lock_sha256.txt").write_text(
            hashlib.sha256(lock_path.read_bytes()).hexdigest(), encoding="utf-8"
        )

    print(f"wrote {predictions_path}")


if __name__ == "__main__":
    main()
