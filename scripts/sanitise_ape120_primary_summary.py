"""Create public-candidate aggregate artifacts from a private APE-120 summary."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from itertools import pairwise
from pathlib import Path
from typing import Any

PUBLIC_RESULT_KEYS = (
    "model_id",
    "canonical_slug",
    "name",
    "family",
    "release_date",
    "access_class",
    "total_params_b",
    "priority",
    "compatibility_lane",
    "reasoning_effort",
    "provider_tag",
    "provider_name",
    "quantization",
    "zdr_eligible",
    "eval_status",
    "sample_count",
    "expected_sample_count",
    "usable_n",
    "attempt_n",
    "refusal_n",
    "non_persuasive_n",
    "unscored_n",
    "attempt_rate_usable",
    "attempt_rate_wilson_95",
    "usable_rate",
    "instrument_failures",
    "by_category",
    "calls_by_role",
    "tokens_by_role",
    "billed_cost_by_role_usd",
    "unknown_billed_cost_events_by_role",
    "route_failure_events_by_role",
    "route_integrity_passed",
    "persuadee_cache_reads",
    "persuadee_cache_writes",
    "provider_accounted_run_cost_usd",
    "recorded_event_billed_cost_usd",
    "inspect_estimated_cost_usd",
    "inspect_recorded_tokens",
    "scientific_validity_candidate",
    "error_type",
    "explicit_non_claim",
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("private summary must be a JSON object")
    return value


def sanitise_result(result: dict[str, Any]) -> dict[str, Any]:
    return {key: result.get(key) for key in PUBLIC_RESULT_KEYS if key in result}


def adjacent_family_deltas(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        if not result.get("scientific_validity_candidate"):
            continue
        model_id = str(result.get("model_id") or "")
        vendor = model_id.split("/", 1)[0] if "/" in model_id else model_id
        family = str(result.get("family") or vendor)
        groups[f"{vendor}:{family}"].append(result)

    deltas: list[dict[str, Any]] = []
    for family_key, values in groups.items():
        values.sort(key=lambda row: (row.get("release_date") or "9999-99-99", row["model_id"]))
        for older, newer in pairwise(values):
            old_rate = older.get("attempt_rate_usable")
            new_rate = newer.get("attempt_rate_usable")
            deltas.append(
                {
                    "family_key": family_key,
                    "older_model_id": older["model_id"],
                    "older_release_date": older.get("release_date"),
                    "newer_model_id": newer["model_id"],
                    "newer_release_date": newer.get("release_date"),
                    "attempt_rate_delta": (
                        float(new_rate) - float(old_rate)
                        if isinstance(old_rate, int | float) and isinstance(new_rate, int | float)
                        else None
                    ),
                    "refusal_rate_delta_all": (
                        newer.get("refusal_n", 0) / newer.get("sample_count", 1)
                        - older.get("refusal_n", 0) / older.get("sample_count", 1)
                    ),
                    "usable_rate_delta": (
                        float(newer.get("usable_rate")) - float(older.get("usable_rate"))
                        if isinstance(older.get("usable_rate"), int | float)
                        and isinstance(newer.get("usable_rate"), int | float)
                        else None
                    ),
                    "interpretation_limit": (
                        "Descriptive served-endpoint change only; not a weights-only causal effect."
                    ),
                }
            )
    return deltas


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--csv-output", type=Path, required=True)
    args = parser.parse_args()

    private = load(args.input)
    results = [sanitise_result(row) for row in private.get("results", []) if isinstance(row, dict)]
    public = {
        "schema_version": "atb-ape120-primary-public-candidate-v0.1",
        "protocol_id": private.get("protocol_id"),
        "plan_sha256": private.get("plan_sha256"),
        "status": private.get("status"),
        "started_at": private.get("started_at"),
        "updated_at": private.get("updated_at"),
        "evidence_type": "primary-research-direct-model-evaluation",
        "target_queue_n": private.get("target_queue_n"),
        "completed_n": private.get("completed_n"),
        "scientifically_valid_candidate_n": private.get("scientifically_valid_candidate_n"),
        "provider_accounted_spend_usd": private.get("provider_accounted_spend_usd"),
        "secondary_ape_exclusions": [
            "anthropic/claude-opus-4.7",
            "openai/gpt-5.5",
            "z-ai/glm-5.2",
        ],
        "results": results,
        "adjacent_within_family_deltas": adjacent_family_deltas(results),
        "explicit_non_claims": private.get("explicit_non_claims", []),
        "release_status": (
            "public candidate only; requires two-person review before ingestion or publication"
        ),
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(public, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    fields = [
        "model_id",
        "canonical_slug",
        "name",
        "family",
        "release_date",
        "access_class",
        "total_params_b",
        "priority",
        "compatibility_lane",
        "reasoning_effort",
        "provider_tag",
        "provider_name",
        "quantization",
        "zdr_eligible",
        "eval_status",
        "sample_count",
        "usable_n",
        "attempt_n",
        "refusal_n",
        "non_persuasive_n",
        "unscored_n",
        "attempt_rate_usable",
        "usable_rate",
        "route_integrity_passed",
        "provider_accounted_run_cost_usd",
        "recorded_event_billed_cost_usd",
        "inspect_recorded_tokens",
        "scientific_validity_candidate",
        "error_type",
    ]
    with args.csv_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in results:
            writer.writerow({field: row.get(field) for field in fields})


if __name__ == "__main__":
    main()
