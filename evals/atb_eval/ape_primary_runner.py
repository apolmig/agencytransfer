"""Budget-bound primary APE-120 longitudinal runner.

This module executes the pinned one-turn APE adaptation against an ordered set
of OpenRouter checkpoints. It keeps model outputs and judge traces in a private
log directory and emits only count, route, missingness, usage, and cost fields
into the sanitised checkpoint summary.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
import secrets
import shutil
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from inspect_ai import eval_set
from inspect_ai.model import ModelCost

from atb_eval.manifest import ModelCondition, ModelCostSpec, RouteMaxPriceSpec, RouteSpec
from atb_eval.paid_execution import (
    fetch_openrouter_key_status,
    verify_not_openrouter_management_key,
)
from atb_eval.runner import (
    build_model,
    dataset_inventory_sha256,
    register_missing_inspect_model_costs,
)
from atb_eval.tasks.ape import APE_INTERLOCUTOR_CACHE_SCOPE_ENV, ape_turn1

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MAX_PUBLIC_RESPONSE_BYTES = 64 * 1024 * 1024
SUMMARY_SCHEMA = "atb-ape120-primary-summary-v0.1"
ROUTE_RECEIPT_SCHEMA = "atb-ape120-route-receipt-v0.1"
ALLOWED_LABELS = ("attempt", "refusal", "non_persuasive", "unscored")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def write_private_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)


def load_unique_json(path: Path) -> dict[str, Any]:
    def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key in {path}: {key}")
            result[key] = value
        return result

    payload = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON file must contain an object: {path}")
    return payload


def direct_public_json(path: str) -> tuple[bytes, dict[str, Any]]:
    request = urllib.request.Request(
        f"{OPENROUTER_BASE_URL}/{path}",
        headers={
            "Accept": "application/json",
            "User-Agent": "agencytransfer-ape120-primary/0.1",
        },
    )
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        NoRedirect(),
    )
    try:
        with opener.open(request, timeout=60) as response:
            if response.status != 200:
                raise ValueError(f"OpenRouter returned {response.status} for {path}")
            raw = response.read(MAX_PUBLIC_RESPONSE_BYTES + 1)
    except (OSError, TimeoutError, urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise ValueError(f"OpenRouter public route capture failed for {path}") from exc
    if len(raw) > MAX_PUBLIC_RESPONSE_BYTES:
        raise ValueError(f"OpenRouter public response too large for {path}")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError(f"OpenRouter public response is not a JSON object for {path}")
    return raw, payload


def finite_nonnegative(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{label} is not numeric")
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{label} is not finite and non-negative")
    return result


def key_budget(api_key: str, *, cap_usd: float) -> dict[str, float]:
    data = fetch_openrouter_key_status(api_key)
    verify_not_openrouter_management_key(api_key)
    if data.get("limit_reset") is not None:
        raise ValueError("OpenRouter key must use a non-resetting lifetime limit")
    if data.get("include_byok_in_limit") is not True:
        raise ValueError("OpenRouter key limit must include BYOK usage")
    limit = finite_nonnegative(data.get("limit"), "OpenRouter key limit")
    remaining = finite_nonnegative(data.get("limit_remaining"), "OpenRouter key remaining balance")
    usage = finite_nonnegative(data.get("usage", limit - remaining), "OpenRouter key usage")
    if limit <= 0 or limit > cap_usd + 1e-9:
        raise ValueError(
            "OpenRouter key lifetime limit is "
            f"{limit:.6f}; expected a positive cap <= {cap_usd:.2f}"
        )
    if remaining > limit + 1e-9 or usage > limit + 1e-9:
        raise ValueError("OpenRouter key accounting is internally inconsistent")
    return {"limit_usd": limit, "remaining_usd": remaining, "usage_usd": usage}


def pricing_per_million(pricing: Mapping[str, Any], field: str) -> float:
    raw = pricing.get(field)
    if raw in (None, ""):
        return 0.0
    value = float(raw) * 1_000_000
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"invalid endpoint price: {field}")
    return value


def _endpoint_for_tag(payload: dict[str, Any], provider_tag: str) -> dict[str, Any]:
    data = payload.get("data")
    endpoints = data.get("endpoints") if isinstance(data, dict) else None
    if not isinstance(endpoints, list):
        raise ValueError("OpenRouter endpoint response lacks data.endpoints")
    matches = [
        item
        for item in endpoints
        if isinstance(item, dict) and item.get("tag") == provider_tag and item.get("status") == 0
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one operational endpoint for provider tag {provider_tag}")
    return matches[0]


def _model_record(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("OpenRouter model response lacks data object")
    return data


def _overrides_safe(
    overrides: Any,
    *,
    sample_token_limit: int,
    base_input: float,
    base_output: float,
) -> bool:
    if overrides in (None, []):
        return True
    if not isinstance(overrides, list):
        return False
    for override in overrides:
        if not isinstance(override, dict):
            return False
        threshold = override.get("min_prompt_tokens")
        if isinstance(threshold, bool) or not isinstance(threshold, int):
            return False
        if threshold <= sample_token_limit:
            prompt = pricing_per_million(override, "prompt")
            completion = pricing_per_million(override, "completion")
            if prompt > base_input + 1e-9 or completion > base_output + 1e-9:
                return False
    return True


def capture_route(
    target: dict[str, Any],
    *,
    route_dir: Path,
    sample_token_limit: int,
) -> dict[str, Any]:
    model_id = target["model_id"]
    provider_tag = target["route"]["provider_tag"]
    model_raw, model_payload = direct_public_json(f"model/{model_id}")
    endpoint_raw, endpoint_payload = direct_public_json(f"models/{model_id}/endpoints")
    model_record = _model_record(model_payload)
    endpoint = _endpoint_for_tag(endpoint_payload, provider_tag)

    canonical_slug = str(model_record.get("canonical_slug") or "")
    if canonical_slug != target["canonical_slug"]:
        raise ValueError(f"canonical model identity drift for {model_id}: {canonical_slug!r}")
    if endpoint.get("name") != target["route"]["endpoint_name"]:
        raise ValueError(f"endpoint identity drift for {model_id}")
    if endpoint.get("provider_name") != target["route"]["provider_name"]:
        raise ValueError(f"provider identity drift for {model_id}")
    quantization = str(endpoint.get("quantization") or "unknown").lower()
    if quantization != str(target["route"]["quantization"] or "unknown").lower():
        raise ValueError(f"quantization drift for {model_id}")

    supported = set(endpoint.get("supported_parameters") or [])
    if not {"max_tokens", "temperature"}.issubset(supported):
        raise ValueError(f"endpoint no longer supports APE generation parameters: {model_id}")
    generation = target["generation"]
    if generation.get("seed") is not None and "seed" not in supported:
        raise ValueError(f"endpoint lost seed support: {model_id}")
    if generation.get("top_p") is not None and "top_p" not in supported:
        raise ValueError(f"endpoint lost top_p support: {model_id}")
    if generation.get("reasoning_effort") is not None and not (
        {"reasoning_effort", "reasoning"} & supported
    ):
        raise ValueError(f"endpoint lost reasoning configuration support: {model_id}")
    max_completion = endpoint.get("max_completion_tokens")
    if (
        isinstance(max_completion, bool)
        or not isinstance(max_completion, int)
        or max_completion < int(generation["max_tokens"])
    ):
        raise ValueError(f"endpoint completion ceiling is too low: {model_id}")

    pricing = endpoint.get("pricing")
    if not isinstance(pricing, dict):
        raise ValueError(f"endpoint pricing is unavailable: {model_id}")
    if pricing.get("request") not in (None, "", "0", "0.0", 0, 0.0):
        raise ValueError(f"fixed request pricing is unsupported: {model_id}")
    base_input = pricing_per_million(pricing, "prompt")
    base_output = pricing_per_million(pricing, "completion")
    expected_pricing = target["pricing_usd_per_million"]
    if not math.isclose(base_input, float(expected_pricing["input"]), abs_tol=1e-9):
        raise ValueError(f"input price drift for {model_id}")
    if not math.isclose(base_output, float(expected_pricing["output"]), abs_tol=1e-9):
        raise ValueError(f"output price drift for {model_id}")
    if not _overrides_safe(
        pricing.get("overrides"),
        sample_token_limit=sample_token_limit,
        base_input=base_input,
        base_output=base_output,
    ):
        raise ValueError(f"conditional endpoint pricing can affect APE samples: {model_id}")

    stem = hashlib.sha256(f"{model_id}|{provider_tag}".encode()).hexdigest()[:20]
    model_path = route_dir / f"{stem}-model.json"
    endpoint_path = route_dir / f"{stem}-endpoints.json"
    model_path.write_bytes(model_raw)
    endpoint_path.write_bytes(endpoint_raw)
    model_path.chmod(0o600)
    endpoint_path.chmod(0o600)
    receipt = {
        "schema_version": ROUTE_RECEIPT_SCHEMA,
        "observed_at": utc_now(),
        "model_id": model_id,
        "canonical_slug": canonical_slug,
        "provider_tag": provider_tag,
        "provider_name": endpoint.get("provider_name"),
        "endpoint_name": endpoint.get("name"),
        "quantization": quantization,
        "zdr_declared_in_plan": bool(target["route"].get("zdr_eligible")),
        "supported_parameters": sorted(supported),
        "max_completion_tokens": max_completion,
        "pricing_usd_per_million": {
            "input": base_input,
            "output": base_output,
            "input_cache_read": pricing_per_million(pricing, "input_cache_read"),
            "input_cache_write": pricing_per_million(pricing, "input_cache_write"),
        },
        "model_response_sha256": sha256_bytes(model_raw),
        "endpoint_response_sha256": sha256_bytes(endpoint_raw),
    }
    write_private_json(route_dir / f"{stem}-receipt.json", receipt)
    return receipt


def condition_from_plan(target: dict[str, Any]) -> ModelCondition:
    route = target["route"]
    generation = {
        key: value
        for key, value in target["generation"].items()
        if key in {"max_tokens", "top_p", "seed", "reasoning_effort"} and value is not None
    }
    quantization = str(route.get("quantization") or "unknown").lower()
    price = target["pricing_usd_per_million"]
    return ModelCondition(
        condition_id="ape120-" + hashlib.sha256(target["model_id"].encode()).hexdigest()[:16],
        model=f"openrouter/{target['model_id']}",
        immutable=False,
        api_key_env="OPENROUTER_API_KEY",
        route=RouteSpec(
            provider_only=[route["provider_tag"]],
            allow_fallbacks=False,
            require_parameters=True,
            data_collection="deny",
            zdr=bool(route.get("zdr_eligible")),
            quantizations=[] if quantization == "unknown" else [quantization],
            max_price=RouteMaxPriceSpec(
                prompt=float(price["input"]),
                completion=float(price["output"]),
                request=0.0,
            ),
        ),
        revision=None,
        pricing=ModelCostSpec(
            input=float(price["input"]),
            output=float(price["output"]),
            input_cache_read=float(price.get("input_cache_read") or 0.0),
            input_cache_write=float(price.get("input_cache_write") or 0.0),
        ),
        generate_config=generation,
    )


def role_target(role: str, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "model_id": config["model_id"],
        "canonical_slug": config["canonical_slug"],
        "name": f"APE {role}",
        "release_date": None,
        "family": "APE helper",
        "registry_id": None,
        "access_class": "helper",
        "total_params_b": None,
        "hugging_face_id": None,
        "inclusion_basis": f"frozen-{role}-instrument",
        "route": {
            "provider_tag": config["provider_tag"],
            "provider_name": config["provider_name"],
            "endpoint_name": f"{config['provider_name']} | {config['canonical_slug']}",
            "quantization": config["quantization"],
            "zdr_eligible": True,
            "temperature_supported": True,
            "seed_supported": True,
            "reasoning_effort_supported": False,
            "supported_reasoning_efforts": [],
            "pricing_overrides": [],
            "max_completion_tokens": config["max_tokens"],
        },
        "pricing_usd_per_million": {
            "input": config["input_usd_per_million"],
            "output": config["output_usd_per_million"],
            "input_cache_read": config["input_cache_read_usd_per_million"],
            "input_cache_write": config["input_cache_write_usd_per_million"],
        },
        "generation": {
            "temperature": 0.5,
            "max_tokens": config["max_tokens"],
            "top_p": config.get("top_p"),
            "seed": config.get("seed"),
            "reasoning_effort": None,
            "compatibility_lane": "seeded",
        },
        "expected_target_cost_usd_120": 0.0,
        "maximum_target_cost_usd_120": 0.0,
    }


def model_cost_config(conditions: Iterable[ModelCondition]) -> dict[str, ModelCost]:
    costs: dict[str, ModelCost] = {}
    for condition in conditions:
        if condition.pricing is None:
            raise ValueError(f"missing model pricing: {condition.condition_id}")
        cost = ModelCost(**condition.pricing.model_dump())
        previous = costs.setdefault(condition.model, cost)
        if previous != cost:
            raise ValueError(f"conflicting pricing for {condition.model}")
    register_missing_inspect_model_costs(costs)
    return costs


def wilson_interval(successes: int, total: int, z: float = 1.96) -> list[float | None]:
    if total <= 0:
        return [None, None]
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    margin = (
        z * math.sqrt((proportion * (1 - proportion) + z * z / (4 * total)) / total) / denominator
    )
    return [max(0.0, centre - margin), min(1.0, centre + margin)]


def _iter_model_events(log: Any) -> Iterable[Any]:
    for sample in log.samples or []:
        for event in sample.events or []:
            if type(event).__name__ == "ModelEvent":
                yield event


def _event_role(event: Any) -> str:
    role = getattr(event, "role", None)
    return "target" if role in (None, "persuader") else str(role)


def _event_billed_cost(event: Any) -> float | None:
    if getattr(event, "cache", None) == "read" and getattr(event, "call", None) is None:
        return 0.0
    call = getattr(event, "call", None)
    response = getattr(call, "response", None) if call is not None else None
    usage = response.get("usage") if isinstance(response, dict) else None
    cost = usage.get("cost") if isinstance(usage, dict) else None
    if cost is None:
        return None
    if isinstance(cost, bool) or not isinstance(cost, int | float) or not math.isfinite(cost):
        return None
    return float(cost)


def _event_tokens(event: Any) -> int:
    output = getattr(event, "output", None)
    usage = getattr(output, "usage", None)
    value = getattr(usage, "total_tokens", None)
    return int(value) if isinstance(value, int) and value >= 0 else 0


def _route_event_matches(event: Any, expected: dict[str, Any]) -> bool:
    if getattr(event, "cache", None) == "read" and getattr(event, "call", None) is None:
        return True
    call = getattr(event, "call", None)
    response = getattr(call, "response", None) if call is not None else None
    if not isinstance(response, dict):
        # Failed provider requests are missingness, not a positive route assertion.
        return bool(getattr(event, "error", None) or getattr(call, "error", None))
    if response.get("model") != expected["model_id"]:
        return False
    if response.get("provider") not in (None, expected["route"]["provider_name"]):
        return False
    metadata = response.get("openrouter_metadata")
    if not isinstance(metadata, dict):
        return False
    if metadata.get("requested") != expected["model_id"]:
        return False
    available = (metadata.get("endpoints") or {}).get("available")
    if not isinstance(available, list):
        return False
    selected = [
        item for item in available if isinstance(item, dict) and item.get("selected") is True
    ]
    return (
        len(selected) == 1
        and selected[0].get("provider") == expected["route"]["provider_name"]
        and selected[0].get("model") == expected["canonical_slug"]
    )


def aggregate_log(
    log: Any,
    *,
    target: dict[str, Any],
    role_targets: dict[str, dict[str, Any]],
    key_before: dict[str, float],
    key_after: dict[str, float],
    started_at: str,
    completed_at: str,
) -> dict[str, Any]:
    overall = Counter()
    by_category: dict[str, Counter[str]] = defaultdict(Counter)
    failures = Counter()
    sample_count = 0
    for sample in log.samples or []:
        sample_count += 1
        scores = sample.scores or {}
        score = scores.get("ape_turn1_scorer")
        if score is None and len(scores) == 1:
            score = next(iter(scores.values()))
        label = str(getattr(score, "answer", "unscored") or "unscored")
        if label not in ALLOWED_LABELS:
            label = "unscored"
        metadata = getattr(score, "metadata", None) or {}
        category = str(metadata.get("category") or (sample.metadata or {}).get("category") or "")
        overall[label] += 1
        by_category[category][label] += 1
        failure = metadata.get("instrument_failure")
        if isinstance(failure, str) and failure:
            failures[failure] += 1

    calls_by_role = Counter()
    tokens_by_role = Counter()
    billed_cost_by_role: dict[str, float] = defaultdict(float)
    unknown_cost_events = Counter()
    route_failures = Counter()
    cache_reads = 0
    cache_writes = 0
    for event in _iter_model_events(log):
        role = _event_role(event)
        if getattr(event, "cache", None) == "read":
            cache_reads += 1
        elif getattr(event, "cache", None) == "write":
            cache_writes += 1
        else:
            calls_by_role[role] += 1
        tokens_by_role[role] += _event_tokens(event)
        cost = _event_billed_cost(event)
        if cost is None:
            unknown_cost_events[role] += 1
        else:
            billed_cost_by_role[role] += cost
        expected = target if role == "target" else role_targets.get(role)
        if expected is None or not _route_event_matches(event, expected):
            route_failures[role] += 1

    usable = overall["attempt"] + overall["refusal"] + overall["non_persuasive"]
    by_category_rows: dict[str, Any] = {}
    for category, counts in sorted(by_category.items()):
        category_usable = counts["attempt"] + counts["refusal"] + counts["non_persuasive"]
        interval = wilson_interval(counts["attempt"], category_usable)
        by_category_rows[category] = {
            "n": sum(counts.values()),
            "usable_n": category_usable,
            "attempt_n": counts["attempt"],
            "refusal_n": counts["refusal"],
            "non_persuasive_n": counts["non_persuasive"],
            "unscored_n": counts["unscored"],
            "attempt_rate_usable": (
                counts["attempt"] / category_usable if category_usable else None
            ),
            "attempt_rate_wilson_95": interval,
        }

    estimated_log_cost = 0.0
    estimated_tokens = 0
    for usage in (log.stats.model_usage or {}).values():
        if isinstance(usage.total_cost, int | float) and math.isfinite(usage.total_cost):
            estimated_log_cost += float(usage.total_cost)
        if isinstance(usage.total_tokens, int) and usage.total_tokens >= 0:
            estimated_tokens += usage.total_tokens

    actual_cost = key_before["remaining_usd"] - key_after["remaining_usd"]
    return {
        "schema_version": SUMMARY_SCHEMA,
        "model_id": target["model_id"],
        "canonical_slug": target["canonical_slug"],
        "name": target["name"],
        "family": target["family"],
        "release_date": target["release_date"],
        "access_class": target["access_class"],
        "total_params_b": target.get("total_params_b"),
        "priority": target["priority"],
        "compatibility_lane": target["generation"]["compatibility_lane"],
        "reasoning_effort": target["generation"].get("reasoning_effort"),
        "provider_tag": target["route"]["provider_tag"],
        "provider_name": target["route"]["provider_name"],
        "quantization": target["route"]["quantization"],
        "zdr_eligible": target["route"]["zdr_eligible"],
        "started_at": started_at,
        "completed_at": completed_at,
        "eval_status": str(log.status),
        "sample_count": sample_count,
        "expected_sample_count": 120,
        "usable_n": usable,
        "attempt_n": overall["attempt"],
        "refusal_n": overall["refusal"],
        "non_persuasive_n": overall["non_persuasive"],
        "unscored_n": overall["unscored"],
        "attempt_rate_usable": overall["attempt"] / usable if usable else None,
        "attempt_rate_wilson_95": wilson_interval(overall["attempt"], usable),
        "usable_rate": usable / sample_count if sample_count else 0.0,
        "instrument_failures": dict(sorted(failures.items())),
        "by_category": by_category_rows,
        "calls_by_role": dict(sorted(calls_by_role.items())),
        "tokens_by_role": dict(sorted(tokens_by_role.items())),
        "billed_cost_by_role_usd": {
            role: round(value, 12) for role, value in sorted(billed_cost_by_role.items())
        },
        "unknown_billed_cost_events_by_role": dict(sorted(unknown_cost_events.items())),
        "route_failure_events_by_role": dict(sorted(route_failures.items())),
        "route_integrity_passed": not route_failures,
        "persuadee_cache_reads": cache_reads,
        "persuadee_cache_writes": cache_writes,
        "provider_key_before": key_before,
        "provider_key_after": key_after,
        "provider_accounted_run_cost_usd": round(max(0.0, actual_cost), 12),
        "recorded_event_billed_cost_usd": round(sum(billed_cost_by_role.values()), 12),
        "inspect_estimated_cost_usd": round(estimated_log_cost, 12),
        "inspect_recorded_tokens": estimated_tokens,
        "scientific_validity_candidate": bool(
            sample_count == 120
            and usable >= 114
            and not route_failures
            and not unknown_cost_events
            and str(log.status) == "success"
        ),
        "explicit_non_claim": (
            "APE turn 1 measures attempted persuasion in simulation, not persuasion success, "
            "belief change, manipulation efficacy, agency transfer, or electoral effect."
        ),
    }


def safe_slug(model_id: str) -> str:
    return model_id.replace("/", "--").replace(":", "-")


def verify_plan(plan: dict[str, Any], plan_path: Path, source_dir: Path) -> None:
    if plan.get("schema_version") != "atb-ape120-primary-plan-v0.1":
        raise ValueError("unsupported APE primary plan schema")
    if plan.get("status") != "frozen":
        raise ValueError("APE primary plan must be frozen")
    if plan.get("evidence_type") != "primary-research-direct-model-evaluation":
        raise ValueError("APE primary plan has the wrong evidence type")
    repo_root = plan_path.resolve().parents[2]
    inventory = repo_root / plan["inventory"]["path"]
    exclusions = repo_root / plan["secondary_exclusion_ledger"]["path"]
    if sha256_file(inventory) != plan["inventory"]["sha256"]:
        raise ValueError("APE live inventory hash does not match the frozen plan")
    if sha256_file(exclusions) != plan["secondary_exclusion_ledger"]["sha256"]:
        raise ValueError("APE secondary exclusion ledger hash does not match the plan")
    excluded = set(plan["secondary_exclusion_ledger"]["excluded_model_ids"])
    target_ids = [item["model_id"] for item in plan["targets"]]
    if len(target_ids) != len(set(target_ids)):
        raise ValueError("APE primary target queue contains duplicates")
    if excluded & set(target_ids):
        raise ValueError("secondary APE release appears in the primary target queue")
    if [item["priority"] for item in plan["targets"]] != list(range(1, len(target_ids) + 1)):
        raise ValueError("APE primary target priorities are not contiguous")
    topic_path = source_dir / plan["dataset"]["topic_file"]
    if sha256_file(topic_path) != plan["dataset"]["topic_file_sha256"]:
        raise ValueError("pinned APE topic source hash does not match")


def resume_records(summary_path: Path, plan: dict[str, Any]) -> list[dict[str, Any]]:
    if not summary_path.exists():
        return []
    payload = load_unique_json(summary_path)
    if payload.get("protocol_id") != plan["protocol_id"]:
        raise ValueError("existing checkpoint summary belongs to another protocol")
    records = payload.get("results")
    if not isinstance(records, list):
        raise ValueError("existing checkpoint summary lacks results")
    return records


def checkpoint_summary(
    path: Path,
    *,
    plan: dict[str, Any],
    plan_sha256: str,
    run_id: str,
    started_at: str,
    initial_budget: dict[str, float],
    current_budget: dict[str, float],
    results: list[dict[str, Any]],
    skips: list[dict[str, Any]],
    status: str,
) -> None:
    completed_ids = {item["model_id"] for item in results}
    write_private_json(
        path,
        {
            "schema_version": SUMMARY_SCHEMA,
            "protocol_id": plan["protocol_id"],
            "plan_sha256": plan_sha256,
            "run_id": run_id,
            "status": status,
            "started_at": started_at,
            "updated_at": utc_now(),
            "initial_provider_key_budget": initial_budget,
            "current_provider_key_budget": current_budget,
            "provider_accounted_spend_usd": round(
                initial_budget["remaining_usd"] - current_budget["remaining_usd"], 12
            ),
            "target_queue_n": len(plan["targets"]),
            "completed_n": len(results),
            "scientifically_valid_candidate_n": sum(
                bool(item.get("scientific_validity_candidate")) for item in results
            ),
            "completed_model_ids": sorted(completed_ids),
            "skips": skips,
            "results": results,
            "explicit_non_claims": plan["explicit_non_claims"],
        },
    )


def run(args: argparse.Namespace) -> None:
    plan_path = args.plan.resolve()
    source_dir = args.source_dir.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir.exists() and output_dir.is_symlink():
        raise ValueError("controlled output directory cannot be a symlink")
    output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    output_dir.chmod(0o700)
    plan = load_unique_json(plan_path)
    verify_plan(plan, plan_path, source_dir)
    plan_sha256 = sha256_file(plan_path)

    task = ape_turn1(
        source_dir=str(source_dir),
        categories=plan["dataset"]["categories"],
        persuader_prompt_type=plan["dataset"]["persuader_prompt_type"],
        seed=plan["dataset"]["belief_seed"],
        belief_range=tuple(plan["dataset"]["belief_range"]),
        temperature=plan["execution"]["target_temperature"],
        samples_per_category=plan["dataset"]["samples_per_category"],
        selection_seed=plan["dataset"]["selection_seed"],
        paired_interlocutor_cache=True,
    )
    if dataset_inventory_sha256(task.dataset) != plan["dataset"]["selected_inventory_sha256"]:
        raise ValueError("constructed APE-120 inventory does not match the frozen plan")

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is required")
    execution = plan["execution"]
    initial_budget = key_budget(
        api_key,
        cap_usd=float(execution["openrouter_key_lifetime_cap_usd"]),
    )
    if initial_budget["limit_usd"] + 1e-9 < float(execution["planned_execution_envelope_usd"]):
        raise ValueError(
            "OpenRouter key lifetime cap is below the frozen USD 29.50 execution envelope"
        )
    if initial_budget["remaining_usd"] <= float(execution["minimum_stop_reserve_usd"]):
        raise ValueError("OpenRouter key has no usable balance after the stop reserve")

    run_id = args.run_id or secrets.token_hex(16)
    if len(run_id) != 32 or any(char not in "0123456789abcdef" for char in run_id):
        raise ValueError("run_id must be 32 lowercase hexadecimal characters")
    started_at = utc_now()
    cache_dir = output_dir / "ape-interlocutor-cache"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    cache_dir.mkdir(mode=0o700)
    route_dir = output_dir / "route-captures"
    route_dir.mkdir(mode=0o700)
    log_root = output_dir / "logs"
    log_root.mkdir(mode=0o700)
    summary_path = output_dir / "sanitised-summary.json"

    previous_cache_dir = os.environ.get("INSPECT_CACHE_DIR")
    previous_scope = os.environ.get(APE_INTERLOCUTOR_CACHE_SCOPE_ENV)
    os.environ["INSPECT_CACHE_DIR"] = str(cache_dir)
    os.environ[APE_INTERLOCUTOR_CACHE_SCOPE_ENV] = run_id

    results = resume_records(summary_path, plan) if args.resume else []
    completed = {item["model_id"] for item in results}
    skips: list[dict[str, Any]] = []
    current_budget = key_budget(
        api_key,
        cap_usd=float(execution["openrouter_key_lifetime_cap_usd"]),
    )

    try:
        role_targets = {
            role: role_target(role, config) for role, config in plan["model_roles"].items()
        }
        role_conditions: dict[str, ModelCondition] = {}
        for role, target in role_targets.items():
            capture_route(
                target,
                route_dir=route_dir,
                sample_token_limit=int(execution["sample_token_limit"]),
            )
            role_conditions[role] = condition_from_plan(target)
        role_models = {
            role: build_model(
                condition,
                int(execution["max_connections"]),
                int(execution["max_retries"]),
            )
            for role, condition in role_conditions.items()
        }

        for target in plan["targets"]:
            model_id = target["model_id"]
            if model_id in completed:
                continue
            current_budget = key_budget(
                api_key,
                cap_usd=float(execution["openrouter_key_lifetime_cap_usd"]),
            )
            expected_cost = float(target["expected_target_cost_usd_120"]) + float(
                execution.get("expected_auxiliary_cost_usd_per_target", 0.0)
            )
            forecast = expected_cost * float(execution["maximum_model_forecast_multiplier"])
            reserve = float(execution["minimum_stop_reserve_usd"])
            if current_budget["remaining_usd"] <= reserve:
                skips.append(
                    {
                        "model_id": model_id,
                        "priority": target["priority"],
                        "reason": "budget-reserve-reached",
                        "remaining_usd": current_budget["remaining_usd"],
                    }
                )
                break
            # Do not start a 120-topic checkpoint when its preregistered target-plus-
            # auxiliary forecast cannot fit inside the remaining lifetime key budget.
            # The provider's USD 30 lifetime cap is still the final hard stop.
            if current_budget["remaining_usd"] < forecast + reserve:
                skips.append(
                    {
                        "model_id": model_id,
                        "priority": target["priority"],
                        "reason": "insufficient-balance-for-conservative-model-forecast",
                        "forecast_usd": forecast,
                        "remaining_usd": current_budget["remaining_usd"],
                    }
                )
                continue

            target_started = utc_now()
            try:
                capture_route(
                    target,
                    route_dir=route_dir,
                    sample_token_limit=int(execution["sample_token_limit"]),
                )
                target_condition = condition_from_plan(target)
                target_model = build_model(
                    target_condition,
                    int(execution["max_connections"]),
                    int(execution["max_retries"]),
                )
                costs = model_cost_config([target_condition, *role_conditions.values()])
                target_log_dir = log_root / f"{target['priority']:03d}-{safe_slug(model_id)}"
                target_log_dir.mkdir(mode=0o700)
                metadata = {
                    "atb_protocol_id": plan["protocol_id"],
                    "atb_plan_sha256": plan_sha256,
                    "atb_primary_research": True,
                    "atb_run_id": run_id,
                    "atb_target_model_id": model_id,
                    "atb_target_priority": target["priority"],
                    "atb_secondary_ape_exclusions": plan["secondary_exclusion_ledger"][
                        "excluded_model_ids"
                    ],
                    "release_tier": "controlled",
                }
                success, logs = eval_set(
                    tasks=[task],
                    model=[target_model],
                    model_roles=role_models,
                    log_dir=str(target_log_dir),
                    log_format="eval",
                    log_samples=True,
                    log_model_api=True,
                    log_refusals=True,
                    retry_attempts=int(execution["retry_attempts"]),
                    retry_cleanup=False,
                    retry_immediate=False,
                    retry_on_error=int(execution["retry_on_error"]),
                    epochs=1,
                    sample_shuffle=42,
                    fail_on_error=execution["fail_on_error"],
                    token_limit=int(execution["sample_token_limit"]),
                    cost_limit=float(execution["sample_cost_limit_usd"]),
                    model_cost_config=costs,
                    max_samples=int(execution["max_samples"]),
                    max_tasks=1,
                    max_connections=int(execution["max_connections"]),
                    max_retries=int(execution["max_retries"]),
                    eval_set_id=f"{plan['protocol_id']}-{run_id}-{target['priority']:03d}",
                    metadata=metadata,
                    display=execution["run_display"],
                    trace=False,
                )
                if len(logs) != 1:
                    raise RuntimeError(f"Inspect returned {len(logs)} logs for one target")
                key_after = key_budget(
                    api_key,
                    cap_usd=float(execution["openrouter_key_lifetime_cap_usd"]),
                )
                aggregate = aggregate_log(
                    logs[0],
                    target=target,
                    role_targets=role_targets,
                    key_before=current_budget,
                    key_after=key_after,
                    started_at=target_started,
                    completed_at=utc_now(),
                )
                aggregate["eval_set_success"] = bool(success)
                results.append(aggregate)
                completed.add(model_id)
                current_budget = key_after
            except Exception as exc:
                current_budget = key_budget(
                    api_key,
                    cap_usd=float(execution["openrouter_key_lifetime_cap_usd"]),
                )
                results.append(
                    {
                        "schema_version": SUMMARY_SCHEMA,
                        "model_id": model_id,
                        "canonical_slug": target["canonical_slug"],
                        "name": target["name"],
                        "family": target["family"],
                        "release_date": target["release_date"],
                        "access_class": target["access_class"],
                        "priority": target["priority"],
                        "started_at": target_started,
                        "completed_at": utc_now(),
                        "eval_status": "runner-error",
                        "error_type": type(exc).__name__,
                        "error_message": str(exc)[:500],
                        "scientific_validity_candidate": False,
                        "provider_key_before": current_budget,
                        "provider_key_after": current_budget,
                        "explicit_non_claim": (
                            "A failed execution is instrumentation evidence only and cannot "
                            "support "
                            "a model capability claim."
                        ),
                    }
                )
                completed.add(model_id)

            checkpoint_summary(
                summary_path,
                plan=plan,
                plan_sha256=plan_sha256,
                run_id=run_id,
                started_at=started_at,
                initial_budget=initial_budget,
                current_budget=current_budget,
                results=results,
                skips=skips,
                status="running",
            )
            print(
                json.dumps(
                    {
                        "priority": target["priority"],
                        "model_id": model_id,
                        "completed_n": len(results),
                        "valid_candidate_n": sum(
                            bool(item.get("scientific_validity_candidate")) for item in results
                        ),
                        "remaining_usd": current_budget["remaining_usd"],
                    },
                    separators=(",", ":"),
                ),
                flush=True,
            )

        checkpoint_summary(
            summary_path,
            plan=plan,
            plan_sha256=plan_sha256,
            run_id=run_id,
            started_at=started_at,
            initial_budget=initial_budget,
            current_budget=current_budget,
            results=results,
            skips=skips,
            status="completed",
        )
    finally:
        if previous_cache_dir is None:
            os.environ.pop("INSPECT_CACHE_DIR", None)
        else:
            os.environ["INSPECT_CACHE_DIR"] = previous_cache_dir
        if previous_scope is None:
            os.environ.pop(APE_INTERLOCUTOR_CACHE_SCOPE_ENV, None)
        else:
            os.environ[APE_INTERLOCUTOR_CACHE_SCOPE_ENV] = previous_scope
        with contextlib.suppress(OSError):
            shutil.rmtree(cache_dir)
        for path in output_dir.rglob("*"):
            try:
                if path.is_file():
                    path.chmod(0o600)
                elif path.is_dir():
                    path.chmod(0o700)
            except OSError:
                continue


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    try:
        run(parse_args())
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(f"APE-120 primary execution failed: {exc}") from exc


if __name__ == "__main__":
    main()
