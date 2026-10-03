"""Phase 3: option-order sensitivity of Laya's `choice` primitive.

Repeats the jev-position-test method (../jev-position-test/jev_hosted_position.py):
the same 6 messages, the same option descriptions, 3 orderings of the
`risk_tier` options. Only the order of the `criteria` mapping changes, never
its content. Each ordering runs twice as a determinism control.

Results go to results/position_laya/ (gitignored). Needs Apple Silicon and
laya-mlx, like the Phase 1 run:

    python scripts/run_position_laya.py                 # descriptions kept (matches hosted Jev)
    python scripts/run_position_laya.py --blank-descriptions   # Phase 1 style (descriptions blank)

Vocabulary: "answer changed with option order", never "accuracy". There is no
ground truth here, and six messages is a probe, not a benchmark.
"""

from __future__ import annotations

import argparse
import ast
import datetime
import json
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_REFERENCE = PROJECT_ROOT.parent / "jev-position-test" / "jev_hosted_position.py"

# Copied from the reference script. check_against_reference() fails loudly if
# they ever drift, so this file cannot silently test different inputs.
CASES = {
    "clear_high_risk_scam": (
        "URGENT: Your account will be suspended in 1 hour. Click this link "
        "and enter your card number and PIN immediately to avoid permanent "
        "loss of funds: bit.ly/verify-now-2847"
    ),
    "benign_smalltalk": (
        "Hey, just checking in -- how was your weekend? We should grab "
        "coffee sometime next week if you're free."
    ),
    "ambiguous_urgent": (
        "I need you to process this wire transfer today, the client is "
        "waiting and I can't get on a call right now, just use the account "
        "details from last time."
    ),
    "technical_neutral": (
        "Sensor 14B reported a temperature reading of 22.4C at 03:00 UTC, "
        "within the configured normal operating range."
    ),
    "mild_concern": (
        "I noticed a $40 charge I don't remember making, probably a "
        "subscription I forgot about, can you check it when you get a "
        "chance?"
    ),
    "empty_string": "",
}

TIER_DESCRIPTIONS = {
    "low": "Low risk: no red flags, safe to proceed as normal.",
    "medium": "Some risk indicators present, needs human review before acting.",
    "high": "Clear risk indicators: likely fraudulent, malicious, or urgent harm.",
}

ORDERS = {
    "orig_low_med_high": ["low", "medium", "high"],
    "reversed_high_med_low": ["high", "medium", "low"],
    "rotated_med_high_low": ["medium", "high", "low"],
}

IS_RISKY_INSTRUCTIONS = "Does this message show signs of risk, scam, fraud, or urgent harm?"
RISK_TIER_INSTRUCTIONS = "What risk tier does this message fall into?"


def build_questions(order: list[str], keep_descriptions: bool = True) -> dict:
    """Same two questions as the hosted-Jev script; only `criteria` order varies."""
    criteria = {k: (TIER_DESCRIPTIONS[k] if keep_descriptions else "") for k in order}
    return {
        "is_risky": {"type": "noul", "instructions": IS_RISKY_INSTRUCTIONS},
        "risk_tier": {
            "type": "choice",
            "instructions": RISK_TIER_INSTRUCTIONS,
            "criteria": criteria,
        },
    }


def check_against_reference(reference: pathlib.Path = DEFAULT_REFERENCE) -> None:
    """Parse (never import) the reference script and assert our inputs match it.

    Importing it would run its module-level API-key check and exit.
    """
    source = reference.read_text()
    tree = ast.parse(source)
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in {"CASES", "TIER_DESCRIPTIONS", "ORDERS"}:
                found[target.id] = ast.literal_eval(node.value)
    ours = {"CASES": CASES, "TIER_DESCRIPTIONS": TIER_DESCRIPTIONS, "ORDERS": ORDERS}
    for name, value in ours.items():
        if name not in found:
            raise SystemExit(f"{name} not found in {reference}")
        if found[name] != value:
            raise SystemExit(f"{name} differs from {reference}; fix before running")
    for text in (IS_RISKY_INSTRUCTIONS, RISK_TIER_INSTRUCTIONS):
        if text not in source:
            raise SystemExit(f"question text {text!r} not found in {reference}")


def run_experiment(agent, keep_descriptions: bool = True, passes: int = 2) -> list[dict]:
    """Call agent.predict(context, questions) for every case x order x pass.

    A failing call is recorded with its error and does not abort the run.
    """
    records = []
    for case_name, context in CASES.items():
        for order_name, order in ORDERS.items():
            questions = build_questions(order, keep_descriptions)
            for pass_index in range(passes):
                record = {
                    "case": case_name,
                    "order": order_name,
                    "pass": pass_index,
                    "option_order": list(order),
                }
                try:
                    raw = agent.predict(context, questions)
                    tier = raw["answers"]["risk_tier"]
                    record["chosen"] = tier["choice"]
                    record["probs"] = {k: float(v) for k, v in tier["probabilities"].items()}
                    record["is_risky_noul"] = float(raw["answers"]["is_risky"]["noul"])
                    record["input_tokens"] = raw.get("usage", {}).get("input_tokens")
                except Exception as exc:  # record and continue
                    record["error"] = f"{type(exc).__name__}: {exc}"
                records.append(record)
    return records


def summarize(records: list[dict]) -> dict:
    """Condense raw records. Pass 0 drives the main numbers; pass 1 is the control."""
    first = [r for r in records if r["pass"] == 0]
    cases = list(dict.fromkeys(r["case"] for r in first))
    per_case = {}
    slot_counts = {0: 0, 1: 0, 2: 0}
    answered = 0
    for case in cases:
        rows = [r for r in first if r["case"] == case]
        ok = [r for r in rows if "error" not in r]
        chosen = {r["order"]: r["chosen"] for r in ok}
        complete = len(ok) == len(ORDERS)
        flipped = complete and len(set(chosen.values())) > 1
        spreads = []
        if complete:
            for option in TIER_DESCRIPTIONS:
                values = [r["probs"][option] for r in ok]
                spreads.append(max(values) - min(values))
        for r in ok:
            slot_counts[r["option_order"].index(r["chosen"])] += 1
            answered += 1
        per_case[case] = {
            "chosen_by_order": chosen,
            "complete": complete,
            "flipped": flipped,
            "max_prob_shift": max(spreads) if spreads else None,
            "errors": [r["error"] for r in rows if "error" in r],
        }
    all_chosen = {r["chosen"] for r in first if "error" not in r}

    control_diffs, control_choice_changes = [], 0
    by_key = {(r["case"], r["order"], r["pass"]): r for r in records if "error" not in r}
    for (case, order, pass_index), r in by_key.items():
        if pass_index != 0 or (case, order, 1) not in by_key:
            continue
        other = by_key[(case, order, 1)]
        control_choice_changes += int(r["chosen"] != other["chosen"])
        control_diffs.append(max(abs(r["probs"][k] - other["probs"][k]) for k in r["probs"]))

    complete_cases = [c for c in per_case.values() if c["complete"]]
    return {
        "per_case": per_case,
        "cases_flipped": sum(c["flipped"] for c in complete_cases),
        "cases_complete": len(complete_cases),
        "cases_total": len(cases),
        "slot_counts": slot_counts,
        "answers_scored": answered,
        "distinct_options_chosen": sorted(all_chosen),
        "constant_answer": len(all_chosen) == 1 and answered > 0,
        "control_choice_changes": control_choice_changes,
        "control_max_prob_diff": max(control_diffs) if control_diffs else None,
    }


def format_table(summary: dict) -> str:
    orders = list(ORDERS)
    lines = ["case".ljust(24) + "".join(o.ljust(24) for o in orders) + "flip  max_prob_shift"]
    for case, info in summary["per_case"].items():
        cells = "".join(str(info["chosen_by_order"].get(o, "ERR")).ljust(24) for o in orders)
        shift = "n/a" if info["max_prob_shift"] is None else f"{info['max_prob_shift']:.3f}"
        flip = "yes" if info["flipped"] else ("n/a" if not info["complete"] else "no")
        lines.append(case.ljust(24) + cells + flip.ljust(6) + shift)
    lines.append("")
    lines.append(
        f"answers that changed with order: {summary['cases_flipped']} of "
        f"{summary['cases_complete']} complete cases ({summary['cases_total']} total)"
    )
    s = summary["slot_counts"]
    lines.append(
        f"chosen option by list position (0=first): first={s[0]} second={s[1]} third={s[2]} "
        f"of {summary['answers_scored']}"
    )
    lines.append(f"distinct options chosen overall: {summary['distinct_options_chosen']}")
    if summary["constant_answer"]:
        lines.append("WARNING: one option chosen for every message and order (constant answer)")
    lines.append(
        f"control (same order, run twice): {summary['control_choice_changes']} changed choices, "
        f"max probability difference {summary['control_max_prob_diff']}"
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--blank-descriptions", action="store_true",
                        help="blank the option descriptions (Phase 1 representation)")
    parser.add_argument("--passes", type=int, default=2)
    parser.add_argument("--reference", type=pathlib.Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--out", type=pathlib.Path, default=PROJECT_ROOT / "results" / "position_laya")
    args = parser.parse_args()

    check_against_reference(args.reference)

    from adapters.laya_adapter import LayaAdapter

    adapter = LayaAdapter()
    keep = not args.blank_descriptions
    records = run_experiment(adapter._agent, keep_descriptions=keep, passes=args.passes)
    summary = summarize(records)

    args.out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    variant = "descriptions" if keep else "blank"
    path = args.out / f"position_{variant}_{stamp}.json"
    path.write_text(json.dumps(
        {"variant": variant, "model": "aac6fef/laya-typed-decisions-mlx",
         "records": records, "summary": summary}, indent=2))
    print(format_table(summary))
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
