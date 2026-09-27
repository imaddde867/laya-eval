import json
from pathlib import Path

from adapters.laya_adapter import parse_laya_result

FIXTURE = Path(__file__).parent / "fixtures" / "laya_raw_response.json"


def test_parse_laya_result_matches_captured_fixture():
    raw = json.loads(FIXTURE.read_text())
    parsed = parse_laya_result(raw)
    assert parsed == {
        "department": "billing",
        "urgency": "critical",
        "refund": True,
    }
