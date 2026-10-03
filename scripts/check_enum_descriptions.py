"""Count enum fields in the cached TypeSafe cases and look for per-option text.

Per-option text would show up as a non-string choice or an enum spec key
beyond type/description/choices/ordered. Run: python scripts/check_enum_descriptions.py
"""

import json
import os
from collections import Counter

CASES = os.path.expanduser("~/.cache/jevmlx/typesafe/cases.jsonl")
KNOWN = {"type", "description", "choices", "ordered"}

rows = [json.loads(line) for line in open(CASES) if line.strip()]
with_schema = [r for r in rows if r.get("schema")]
enums = [f for r in with_schema for f in r["schema"].values() if f.get("type") == "enum"]
extra_keys = Counter(k for f in enums for k in f if k not in KNOWN)
non_str = sum(not isinstance(c, str) for f in enums for c in f["choices"])

print(f"cases: {len(rows)} ({len(with_schema)} with schema)")
print(f"enum fields: {len(enums)} ({sum(bool(f.get('ordered')) for f in enums)} ordered)")
print(f"non-string choices: {non_str}")
print(f"extra enum spec keys: {dict(extra_keys) or 'none'}")
