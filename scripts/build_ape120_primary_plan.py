"""Build the frozen primary APE-120 longitudinal execution plan.

The builder consumes the same-day OpenRouter endpoint inventory, removes exact
releases already covered by secondary APE research, and orders every remaining
eligible checkpoint by scientific value. The execution runner uses real key
balance after every model and stops before the USD 30 lifetime cap.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

INVENTORY_PATH = Path("evals/research-notes/ape120-live-inventory-20260825.json")
EXCLUSIONS_PATH = Path("evals/research-notes/ape120-secondary-exclusions-v0.1.json")
OUTPUT_PATH = Path("evals/config/ape120-primary-v0.1.json")

HOSTED_ALLOWLIST: dict[str, list[str]] = {
    "openai": [
        "openai/gpt-3.5-turbo",
        "openai/gpt-4",
        "openai/gpt-4-turbo",
        "openai/gpt-4o-2024-05-13",
        "openai/gpt-4o-2024-08-06",
        "openai/gpt-4o-2024-11-20",
        "openai/o1",
        "openai/gpt-4.1",
        "openai/o3",
        "openai/gpt-5",
        "openai/gpt-5.1",
        "openai/gpt-5.2",
        "openai/gpt-5.4",
        "openai/gpt-5.6-luna",
        "openai/gpt-5.6-terra",
        "openai/gpt-5.6-sol",
    ],
    "anthropic": [
        "anthropic/claude-opus-4",
        "anthropic/claude-sonnet-4",
        "anthropic/claude-opus-4.1",
        "anthropic/claude-sonnet-4.5",
        "anthropic/claude-opus-4.5",
        "anthropic/claude-opus-4.6",
        "anthropic/claude-sonnet-4.6",
        "anthropic/claude-opus-4.7",
        "anthropic/claude-opus-4.8",
        "anthropic/claude-fable-5",
        "anthropic/claude-sonnet-5",
        "anthropic/claude-opus-5",
    ],
    "google": [
        "google/gemini-2.5-pro-preview-05-06",
        "google/gemini-2.5-pro",
        "google/gemini-2.5-flash",
        "google/gemini-3-flash-preview",
        "google/gemini-3.1-pro-preview",
        "google/gemini-3.5-flash",
        "google/gemini-3.6-flash",
        "google/gemini-3.7-flash",
    ],
    "x-ai": [
        "x-ai/grok-4.20",
        "x-ai/grok-4.3",
        "x-ai/grok-4.5",
        "x-ai/grok-4.6",
    ],
}

OPEN_WEIGHT_EXCLUSIONS: dict[str, str] = {
    "nousresearch/hermes-3-llama-3.1-405b": (
        "third-party fine-tune rather than an original frontier-family release"
    ),
    "nousresearch/hermes-4-405b": (
        "third-party fine-tune rather than an original frontier-family release"
    ),
    "poolside/laguna-s-2.1": (
        "specialised coding model; not a general frontier or quasi-frontier release"
    ),
}

HOSTED_NON_SELECTION_REASONS: dict[str, str] = {
    "openai/gpt-3.5-turbo-16k": "context-window variant, not a distinct capability checkpoint",
    "openai/gpt-3.5-turbo-instruct": (
        "instruction-completion endpoint, not chat-protocol comparable"
    ),
    "openai/gpt-4-turbo-preview": "mutable preview duplicate of the stable GPT-4 Turbo checkpoint",
    "openai/gpt-4o": "mutable alias; dated GPT-4o checkpoints are used instead",
    "openai/o1-pro": "cost-dominant service tier, not a distinct base checkpoint",
    "openai/o3-pro": "cost-dominant service tier, not a distinct base checkpoint",
    "openai/gpt-5-pro": "cost-dominant service tier, not a distinct base checkpoint",
    "openai/gpt-5.2-pro": "cost-dominant service tier, not a distinct base checkpoint",
    "openai/gpt-5.4-pro": "cost-dominant service tier, not a distinct base checkpoint",
    "openai/gpt-5.5-pro": "cost-dominant service tier; base GPT-5.5 is excluded as secondary APE",
    "openai/gpt-5.6-luna-pro": "service-tier duplicate of GPT-5.6 Luna",
    "openai/gpt-5.6-sol-pro": "service-tier duplicate of GPT-5.6 Sol",
    "openai/gpt-5.6-terra-pro": "service-tier duplicate of GPT-5.6 Terra",
    "google/gemini-2.5-pro-preview": "later preview duplicate; earliest dated preview retained",
    "google/gemini-3.1-pro-preview-customtools": "tool-specialised endpoint",
    "x-ai/grok-4.20-multi-agent": (
        "multi-agent service mode, not single-model checkpoint comparable"
    ),
    "x-ai/grok-build-0.1": "build-specialised endpoint, not general Grok checkpoint",
}

ROLE_MODELS = {
    "persuadee": {
        "model_id": "qwen/qwen3-235b-a22b-2507",
        "canonical_slug": "qwen/qwen3-235b-a22b-07-25",
        "provider_tag": "novita/fp8",
        "provider_name": "Novita",
        "quantization": "fp8",
        "max_tokens": 512,
        "input_usd_per_million": 0.09,
        "output_usd_per_million": 0.58,
        "input_cache_read_usd_per_million": 0.0,
        "input_cache_write_usd_per_million": 0.0,
        "seed": 42,
        "top_p": 1.0,
    },
    "evaluator": {
        "model_id": "qwen/qwen3-235b-a22b-2507",
        "canonical_slug": "qwen/qwen3-235b-a22b-07-25",
        "provider_tag": "novita/fp8",
        "provider_name": "Novita",
        "quantization": "fp8",
        "max_tokens": 256,
        "input_usd_per_million": 0.09,
        "output_usd_per_million": 0.58,
        "input_cache_read_usd_per_million": 0.0,
        "input_cache_write_usd_per_million": 0.0,
        "seed": 42,
        "top_p": 1.0,
    },
    "refusal_judge": {
        "model_id": "qwen/qwen3-30b-a3b-instruct-2507",
        "canonical_slug": "qwen/qwen3-30b-a3b-instruct-2507",
        "provider_tag": "coreweave/bf16",
        "provider_name": "CoreWeave",
        "quantization": "bf16",
        "max_tokens": 1024,
        "input_usd_per_million": 0.10,
        "output_usd_per_million": 0.30,
        "input_cache_read_usd_per_million": 0.10,
        "input_cache_write_usd_per_million": 0.0,
        "seed": 42,
        "top_p": 1.0,
    },
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalise_reasoning(row: dict[str, Any]) -> str | None:
    supported = row.get("supported_reasoning_efforts") or []
    for effort in ("max", "xhigh", "high", "medium", "low"):
        if effort in supported:
            return effort
    return None


def original_lab_release(row: dict[str, Any]) -> bool:
    model_id = row["model_id"]
    hf = str(row.get("hugging_face_id") or "").lower()
    vendor = model_id.split("/", 1)[0].lower()
    aliases = {
        "meta-llama": {"meta-llama", "meta"},
        "z-ai": {"zai-org", "z-ai"},
        "moonshotai": {"moonshotai"},
        "deepseek": {"deepseek-ai"},
        "qwen": {"qwen"},
        "mistralai": {"mistralai"},
        "minimax": {"minimaxai"},
        "openai": {"openai"},
        "cohere": {"cohereforai"},
        "baidu": {"baidu"},
        "stepfun": {"stepfun-ai"},
        "nvidia": {"nvidia"},
        "nex-agi": {"nex-agi"},
        "thinkingmachines": {"thinkingmachines"},
        "meituan": {"meituan-longcat"},
    }
    return any(hf.startswith(prefix + "/") for prefix in aliases.get(vendor, {vendor}))


def target_record(row: dict[str, Any], *, inclusion_basis: str) -> dict[str, Any]:
    supported = set(row.get("supported_parameters") or [])
    reasoning_effort = normalise_reasoning(row)
    return {
        "model_id": row["model_id"],
        "canonical_slug": row["canonical_slug"],
        "name": row["name"],
        "release_date": row["release_date"],
        "family": row["family"],
        "registry_id": row.get("registry_id"),
        "access_class": (
            "open-weight"
            if row["selection_basis"] == "open_weight_total_params_ge_100b"
            else "hosted"
        ),
        "total_params_b": row.get("total_params_b"),
        "hugging_face_id": row.get("hugging_face_id"),
        "inclusion_basis": inclusion_basis,
        "route": {
            "provider_tag": row["provider_tag"],
            "provider_name": row["provider_name"],
            "endpoint_name": row["endpoint_name"],
            "quantization": row["quantization"],
            "zdr_eligible": bool(row.get("zdr_eligible")),
            "temperature_supported": bool(row.get("temperature_supported")),
            "seed_supported": bool(row.get("seed_supported")),
            "reasoning_effort_supported": bool(row.get("reasoning_effort_supported")),
            "supported_reasoning_efforts": row.get("supported_reasoning_efforts") or [],
            "pricing_overrides": row.get("pricing_overrides") or [],
            "max_completion_tokens": row.get("max_completion_tokens"),
        },
        "pricing_usd_per_million": {
            "input": row["input_usd_per_million"],
            "output": row["output_usd_per_million"],
            "input_cache_read": row.get("input_cache_read_usd_per_million") or 0.0,
            "input_cache_write": row.get("input_cache_write_usd_per_million") or 0.0,
        },
        "generation": {
            "temperature": 0.5,
            "max_tokens": 1024,
            "top_p": 1.0 if "top_p" in supported else None,
            "seed": 42 if row.get("seed_supported") else None,
            "reasoning_effort": reasoning_effort,
            "compatibility_lane": ("seeded" if row.get("seed_supported") else "provider-unseeded"),
        },
        "expected_target_cost_usd_120": row["expected_target_cost_usd_120"],
        "maximum_target_cost_usd_120": row["maximum_target_cost_usd_120"],
    }


def round_robin_by_family(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        family = str(record["family"] or record["model_id"].split("/", 1)[0])
        groups[family].append(record)
    for values in groups.values():
        values.sort(key=lambda item: (item["release_date"] or "9999-99-99", item["model_id"]))
    ordered: list[dict[str, Any]] = []
    round_index = 0
    while True:
        added = False
        for family in sorted(groups):
            values = groups[family]
            if round_index < len(values):
                ordered.append(values[round_index])
                added = True
        if not added:
            return ordered
        round_index += 1


def build_plan(inventory: dict[str, Any], exclusions: dict[str, Any]) -> dict[str, Any]:
    exact_excluded = {item["model_id"] for item in exclusions["exclusions"]}
    excluded_canonical = {
        canonical
        for item in exclusions["exclusions"]
        for canonical in item.get("canonical_ids", [])
    }
    rows = {row["model_id"]: row for row in inventory["rows"]}

    selected: list[dict[str, Any]] = []
    decision_ledger: list[dict[str, Any]] = []

    for vendor, model_ids in HOSTED_ALLOWLIST.items():
        for model_id in model_ids:
            row = rows.get(model_id)
            if row is None or not row.get("candidate"):
                decision_ledger.append(
                    {
                        "model_id": model_id,
                        "decision": "not-runnable",
                        "reason": (
                            "not present as a live eligible OpenRouter endpoint at inventory freeze"
                        ),
                    }
                )
                continue
            if model_id in exact_excluded or row.get("canonical_slug") in excluded_canonical:
                decision_ledger.append(
                    {
                        "model_id": model_id,
                        "decision": "excluded-secondary-ape",
                        "reason": "exact served release already has secondary APE evidence",
                    }
                )
                continue
            selected.append(target_record(row, inclusion_basis=f"hosted-{vendor}-frontier-release"))

    hosted_allow = {model_id for values in HOSTED_ALLOWLIST.values() for model_id in values}
    for model_id, reason in HOSTED_NON_SELECTION_REASONS.items():
        if model_id in rows:
            decision_ledger.append(
                {"model_id": model_id, "decision": "not-selected", "reason": reason}
            )
    for row in inventory["rows"]:
        model_id = row["model_id"]
        if (
            row.get("selection_basis", "").startswith("hosted_")
            and model_id not in hosted_allow
            and model_id not in HOSTED_NON_SELECTION_REASONS
        ):
            decision_ledger.append(
                {
                    "model_id": model_id,
                    "decision": "not-selected",
                    "reason": (
                        "not a distinct general hosted-family checkpoint in the "
                        "longitudinal envelope"
                    ),
                }
            )

    for row in inventory["rows"]:
        if not row.get("candidate"):
            continue
        if row["selection_basis"] != "open_weight_total_params_ge_100b":
            continue
        model_id = row["model_id"]
        if model_id in exact_excluded or row.get("canonical_slug") in excluded_canonical:
            decision_ledger.append(
                {
                    "model_id": model_id,
                    "decision": "excluded-secondary-ape",
                    "reason": "exact served release already has secondary APE evidence",
                }
            )
            continue
        if model_id in OPEN_WEIGHT_EXCLUSIONS:
            decision_ledger.append(
                {
                    "model_id": model_id,
                    "decision": "not-selected",
                    "reason": OPEN_WEIGHT_EXCLUSIONS[model_id],
                }
            )
            continue
        if not original_lab_release(row):
            decision_ledger.append(
                {
                    "model_id": model_id,
                    "decision": "not-selected",
                    "reason": "model identity could not be bound to an original-lab release",
                }
            )
            continue
        selected.append(
            target_record(
                row,
                inclusion_basis="open-weight-original-lab-total-parameters-ge-100b",
            )
        )

    if len({item["model_id"] for item in selected}) != len(selected):
        raise ValueError("selected targets are not unique")
    if exact_excluded & {item["model_id"] for item in selected}:
        raise ValueError("secondary APE exclusion leaked into primary plan")

    hosted = [item for item in selected if item["access_class"] == "hosted"]
    open_weight = [item for item in selected if item["access_class"] == "open-weight"]

    # Old checkpoints are the core scientific objective. Sort both access classes
    # chronologically and interleave them so an expensive hosted family cannot
    # crowd every open-weight anchor out of the fixed budget. Same-day ties favour
    # the cheaper route, preserving more longitudinal points.
    hosted_order = sorted(
        hosted,
        key=lambda item: (
            item["release_date"] or "9999-99-99",
            float(item["expected_target_cost_usd_120"]),
            item["model_id"],
        ),
    )
    open_order = sorted(
        open_weight,
        key=lambda item: (
            item["release_date"] or "9999-99-99",
            float(item["expected_target_cost_usd_120"]),
            item["model_id"],
        ),
    )
    queue: list[dict[str, Any]] = []
    while hosted_order or open_order:
        if hosted_order:
            queue.append(hosted_order.pop(0))
        if open_order:
            queue.append(open_order.pop(0))
    for priority, item in enumerate(queue, start=1):
        item["priority"] = priority

    expected_target_cost = sum(float(item["expected_target_cost_usd_120"]) for item in queue)
    maximum_target_cost = sum(float(item["maximum_target_cost_usd_120"]) for item in queue)
    return {
        "schema_version": "atb-ape120-primary-plan-v0.1",
        "protocol_id": "atb-ape120-primary-20260825-v0.1",
        "status": "frozen",
        "frozen_at": inventory["observed_at"],
        "construct_definition": (
            "Propensity to attempt persuasion in a one-turn simulated dialogue under "
            "a pinned 120-topic APE adaptation"
        ),
        "explicit_non_claims": [
            "persuasion success",
            "belief or behaviour change",
            "manipulation efficacy",
            "agency transfer",
            "electoral effect",
            "weights-only causal effect",
            "cross-provider equivalence",
        ],
        "evidence_type": "primary-research-direct-model-evaluation",
        "dataset": {
            "source_url": "https://github.com/AlignmentResearch/AttemptPersuadeEval",
            "source_revision": "d77a4b14d5d3353ea4ac73fb22df239e36606c1d",
            "topic_file": "src/topics/diverse_topics.jsonl",
            "topic_file_sha256": "c1de93f13220c32b806e1fa83cf51e82153b3a80a2a33fce6ee782991e5d3796",
            "categories": [
                "Conspiracy",
                "BenignOpinion",
                "BenignFactual",
                "Controversial",
                "NoncontroversiallyHarmful",
                "UnderminingControl",
            ],
            "samples_per_category": 20,
            "expected_samples_per_model": 120,
            "selection_seed": "atb-ape-stage2a-v0.1",
            "selected_inventory_sha256": (
                "2f0a27b2874acb9f982c9557934cb6ba6a8e5da8ae1606cf5e5b0dfb21ebcd6a"
            ),
            "belief_seed": 42,
            "belief_range": [0, 20],
            "persuader_prompt_type": "persuade",
        },
        "secondary_exclusion_ledger": {
            "path": str(EXCLUSIONS_PATH),
            "sha256": sha256_file(EXCLUSIONS_PATH),
            "excluded_model_ids": sorted(exact_excluded),
        },
        "inventory": {
            "path": str(INVENTORY_PATH),
            "sha256": sha256_file(INVENTORY_PATH),
            "observed_at": inventory["observed_at"],
            "models_source_url": inventory["models_source_url"],
            "zdr_source_url": inventory["zdr_source_url"],
        },
        "execution": {
            "openrouter_key_lifetime_cap_usd": 30.0,
            "planned_execution_envelope_usd": 29.5,
            "minimum_stop_reserve_usd": 0.25,
            "maximum_model_forecast_multiplier": 1.25,
            "max_samples": 4,
            "max_connections": 4,
            "max_retries": 0,
            "retry_on_error": 0,
            "retry_attempts": 0,
            "fail_on_error": 0.05,
            "sample_token_limit": 24000,
            "sample_cost_limit_usd": 0.25,
            "target_temperature": 0.5,
            "target_max_tokens": 1024,
            "target_top_p": 1.0,
            "paired_interlocutor_cache": True,
            "run_display": "none",
            "budget_policy": (
                "fresh key-status check before and after every target; stop rather "
                "than exceed the provider lifetime cap"
            ),
        },
        "model_roles": ROLE_MODELS,
        "target_count": len(queue),
        "hosted_target_count": len(hosted),
        "open_weight_target_count": len(open_weight),
        "expected_all_target_cost_usd": expected_target_cost,
        "maximum_all_target_cost_usd": maximum_target_cost,
        "targets": queue,
        "decision_ledger": sorted(
            decision_ledger,
            key=lambda item: (item["decision"], item["model_id"]),
        ),
        "release": {
            "raw_logs": "private-controlled",
            "target_outputs": "private-controlled",
            "judge_traces": "private-controlled",
            "route_receipts": "private-controlled",
            "sanitised_aggregates": "public-candidate-after-review",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, default=INVENTORY_PATH)
    parser.add_argument("--exclusions", type=Path, default=EXCLUSIONS_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    exclusions = json.loads(args.exclusions.read_text(encoding="utf-8"))
    plan = build_plan(inventory, exclusions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "protocol_id": plan["protocol_id"],
                "target_count": plan["target_count"],
                "hosted_target_count": plan["hosted_target_count"],
                "open_weight_target_count": plan["open_weight_target_count"],
                "expected_all_target_cost_usd": plan["expected_all_target_cost_usd"],
                "secondary_exclusions": plan["secondary_exclusion_ledger"]["excluded_model_ids"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
