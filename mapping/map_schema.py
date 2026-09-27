"""jevmlx schema field -> laya question mapping (see schema_mapping.md).

boolean -> noul; enum -> choice; enum with ordered=True -> score. Anything
else (multi-select, constraint-bearing fields) is unmapped and returned by
name, never silently dropped or approximated.
"""

from __future__ import annotations


def map_schema(schema: dict) -> tuple[dict, list[str]]:
    """Map one case's jevmlx schema to laya questions.

    Returns (laya_questions, unmapped_field_names).
    """
    questions: dict = {}
    unmapped: list[str] = []
    for name, field in schema.items():
        ftype = field.get("type")
        if ftype == "boolean":
            questions[name] = {"type": "noul", "instructions": field["description"]}
        elif ftype == "enum" and field.get("ordered"):
            questions[name] = {
                "type": "score",
                "instructions": field["description"],
                "criteria": list(field["choices"]),
            }
        elif ftype == "enum":
            questions[name] = {
                "type": "choice",
                "instructions": field["description"],
                "criteria": dict.fromkeys(field["choices"], ""),
            }
        else:
            unmapped.append(name)
    return questions, unmapped
