"""Adapter from fetched jevmlx cases to Laya's typed question API."""

from __future__ import annotations


def parse_laya_result(raw: dict) -> dict[str, object]:
    """Convert Laya's response into field labels comparable with case labels."""
    predictions: dict[str, object] = {}
    for name, answer in raw["answers"].items():
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
            raise ValueError(f"unsupported Laya answer type for {name!r}: {answer_type!r}")
    return predictions


class LayaAdapter:
    """Wrap laya-typed-decisions-mlx with one model load per adapter."""

    def __init__(self, model_id: str = "aac6fef/laya-typed-decisions-mlx"):
        import laya_mlx as laya

        self._agent = laya.load(model_id, dtype="float16")

    def predict_case(self, case: dict) -> dict:
        from mapping.map_schema import map_schema

        questions, unmapped = map_schema(case["schema"])
        predictions: dict = {}
        if questions:
            raw = self._agent.predict(case["context"], questions)
            predictions = parse_laya_result(raw)
        return {
            "id": case["id"],
            "workflow": case.get("workflow"),
            "predictions": predictions,
            "unmapped": unmapped,
        }
