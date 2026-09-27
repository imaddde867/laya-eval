"""One-off: capture laya-typed-decisions-mlx's real predict() output shape.

Run once; the printed/saved JSON becomes tests/fixtures/laya_raw_response.json,
which adapters/laya_adapter.py's parser is written and tested against.
"""

import json
from pathlib import Path

import laya_mlx as laya

agent = laya.load("aac6fef/laya-typed-decisions-mlx", dtype="float16")

state = "Customer was charged twice and wants the duplicate refunded."
questions = {
    "department": {
        "type": "choice",
        "instructions": "Which team should handle this?",
        "criteria": {
            "billing": "invoices, payments, refunds",
            "technical": "bugs and outages",
            "sales": "new purchases",
        },
    },
    "urgency": {
        "type": "score",
        "instructions": "How urgent is this request?",
        "criteria": ["not urgent", "soon", "critical"],
    },
    "refund": {
        "type": "noul",
        "instructions": "Does the customer ask for money back?",
    },
}

result = agent.predict(state, questions)
print(json.dumps(result, indent=2, default=str))

out_path = Path(__file__).parent.parent / "tests" / "fixtures" / "laya_raw_response.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
print(f"wrote {out_path}")
