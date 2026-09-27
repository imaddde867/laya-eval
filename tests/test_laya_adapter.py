import json
from pathlib import Path
from types import SimpleNamespace

from adapters.laya_adapter import LayaAdapter, parse_laya_result

FIXTURE = Path(__file__).parent / "fixtures" / "laya_raw_response.json"


def test_parse_laya_result_matches_captured_fixture():
    raw = json.loads(FIXTURE.read_text())
    parsed = parse_laya_result(raw)
    assert parsed == {
        "department": "billing",
        "urgency": "critical",
        "refund": True,
    }


def test_max_input_tokens_reports_checkpoint_limit():
    adapter = LayaAdapter.__new__(LayaAdapter)
    adapter._agent = SimpleNamespace(cfg={"max_len": 1024})
    assert adapter.max_input_tokens == 1024
