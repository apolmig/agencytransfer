"""Create a controlled usage receipt from persisted Inspect evidence."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from inspect_ai.log import read_eval_log

from atb_eval.runner import (
    recorded_event_usage,
    recorded_log_usage,
    recorded_openrouter_billed_costs,
)


def controlled_usage_summary(log_root: Path) -> dict[str, Any]:
    """Return aggregate usage and non-outcome diagnostics without raw content."""

    paths = sorted(log_root.rglob("*.eval"))
    if not paths:
        raise ValueError("no Inspect eval evidence found")
    inspect_tokens = 0
    inspect_cost = 0.0
    event_usage: dict[str, tuple[int, float, str]] = {}
    billed_usage: dict[str, tuple[float, str]] = {}
    conditions: list[dict[str, Any]] = []
    for path in paths:
        log = read_eval_log(path)
        tokens, cost = recorded_log_usage(log, require_cost=True)
        events = recorded_event_usage(log, require_cost=True)
        billed = recorded_openrouter_billed_costs(log)
        inspect_tokens += tokens
        inspect_cost += cost
        for event_id, value in events.items():
            if event_id in event_usage and event_usage[event_id] != value:
                raise ValueError("inconsistent duplicate ModelEvent UUID")
            event_usage[event_id] = value
        for event_id, value in billed.items():
            if event_id in billed_usage and billed_usage[event_id] != value:
                raise ValueError("inconsistent duplicate billed-event UUID")
            billed_usage[event_id] = value
        failures: set[str] = set()
        for sample in log.samples or []:
            for score in (sample.scores or {}).values():
                failure = (score.metadata or {}).get("instrument_failure")
                if failure:
                    failures.add(str(failure))
        conditions.append(
            {
                "target_model": str(log.eval.model),
                "log_status": str(log.status),
                "instrument_failures": sorted(failures),
                "all_roles_inspect_tokens": tokens,
                "all_roles_inspect_estimated_cost_usd": cost,
                "all_roles_openrouter_billed_cost_usd": sum(value[0] for value in billed.values()),
            }
        )
    event_tokens = sum(value[0] for value in event_usage.values())
    event_cost = sum(value[1] for value in event_usage.values())
    billed_cost = sum(value[0] for value in billed_usage.values())
    if (
        inspect_tokens != event_tokens
        or not math.isclose(inspect_cost, event_cost, abs_tol=1e-9)
        or set(billed_usage) != set(event_usage)
        or not math.isclose(inspect_cost, billed_cost, abs_tol=1e-9)
    ):
        raise ValueError("Inspect aggregate usage does not match persisted ModelEvents")
    return {
        "schema_version": "atb-controlled-usage-summary-v0.1",
        "eval_log_count": len(paths),
        "inspect_tokens": inspect_tokens,
        "inspect_estimated_cost_usd": inspect_cost,
        "openrouter_billed_cost_usd": billed_cost,
        "conditions": sorted(conditions, key=lambda item: item["target_model"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        summary = controlled_usage_summary(args.log_root)
        args.output.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except Exception:
        raise SystemExit("controlled usage receipt could not be derived safely") from None


if __name__ == "__main__":
    main()
