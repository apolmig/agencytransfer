"""One-shot migration from the first live APE-120 inventory rules to v0.3."""

from __future__ import annotations

from pathlib import Path


path = Path("scripts/build_ape120_inventory.py")
text = path.read_text(encoding="utf-8")


def replace(old: str, new: str, count: int = 1) -> None:
    global text
    actual = text.count(old)
    if actual != count:
        raise RuntimeError(
            f"inventory migration anchor count mismatch: expected {count}, got {actual}: {old[:80]!r}"
        )
    text = text.replace(old, new, count)


replace("TARGET_BUDGET_USD = 25.0", "TARGET_BUDGET_USD = 23.5")
replace(
    'MUTABLE_TOKENS = {"latest", "auto", "preview", "beta", "experimental", "free"}',
    'MUTABLE_TOKENS = {"latest", "auto", "beta", "experimental", "free"}',
)
replace(
    '    "computer_use",\n}',
    '    "computer_use",\n    "safeguard",\n    "guard",\n}',
)
replace('    "tiny",\n}', '    "tiny",\n    "lite",\n}')

replace(
    '''    values: list[float] = []
    for pattern, multiplier in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            values.append(float(match.group(1).replace(",", "")) * multiplier)
    return (max(values), "description") if values else (None, None)
''',
    '''    values: list[tuple[float, str]] = []
    for pattern, multiplier in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            values.append(
                (float(match.group(1).replace(",", "")) * multiplier, "description")
            )
    model_id = str(model.get("id") or "")
    for match in re.finditer(
        r"(?:^|[-_/])(\\d+(?:\\.\\d+)?)b(?:$|[-_/])",
        model_id,
        flags=re.IGNORECASE,
    ):
        values.append((float(match.group(1)), "model_id"))
    return max(values, key=lambda item: item[0]) if values else (None, None)
''',
)
replace(
    '''        if {"flash-lite", "flash_lite", "nano"} & tokens:
            return False, "small_gemini_tier"
''',
    '''        if {"lite", "nano"} & tokens:
            return False, "small_gemini_tier"
''',
)

start = text.index("def choose_endpoint(")
end = text.index("\n\ndef release_date", start)
text = (
    text[:start]
    + '''def choose_endpoint(
    model_id: str,
    endpoint_inventory: dict[str, Any],
    zdr_pairs: set[tuple[str, str]],
) -> dict[str, Any] | None:
    candidates: list[tuple[int, int, float, str, dict[str, Any]]] = []
    for endpoint in endpoint_inventory.get("endpoints", []):
        if not isinstance(endpoint, dict):
            continue
        tag = endpoint.get("tag")
        quantization = str(endpoint.get("quantization") or "unknown").lower()
        supported = set(endpoint.get("supported_parameters") or [])
        pricing = endpoint.get("pricing") or {}
        max_completion = endpoint.get("max_completion_tokens")
        if endpoint.get("status") != 0 or not isinstance(tag, str):
            continue
        if "max_tokens" not in supported:
            continue
        if (
            isinstance(max_completion, bool)
            or not isinstance(max_completion, int)
            or max_completion < TARGET_MAX_OUTPUT_TOKENS
        ):
            continue
        if not isinstance(pricing, dict):
            continue
        if finite_nonnegative(pricing.get("request")) != 0:
            continue
        overrides = pricing.get("overrides")
        if overrides not in (None, []) and not (
            isinstance(overrides, list)
            and all(
                isinstance(item, dict)
                and isinstance(item.get("min_prompt_tokens"), int)
                and item["min_prompt_tokens"] > TARGET_MAX_INPUT_TOKENS
                for item in overrides
            )
        ):
            continue
        input_price = price_per_million(pricing, "prompt")
        output_price = price_per_million(pricing, "completion")
        if input_price <= 0 or output_price <= 0:
            continue
        expected = 120 * (
            TARGET_EXPECTED_INPUT_TOKENS * input_price
            + TARGET_EXPECTED_OUTPUT_TOKENS * output_price
        ) / 1_000_000
        zdr_eligible = (model_id, tag) in zdr_pairs
        candidates.append(
            (
                0 if zdr_eligible else 1,
                QUANTIZATION_ORDER.get(quantization, QUANTIZATION_ORDER["unknown"]),
                expected,
                tag,
                endpoint,
            )
        )
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
    zdr_rank, _, expected, tag, endpoint = candidates[0]
    pricing = endpoint.get("pricing") or {}
    input_price = price_per_million(pricing, "prompt")
    output_price = price_per_million(pricing, "completion")
    return {
        "provider_tag": tag,
        "provider_name": endpoint.get("provider_name"),
        "endpoint_name": endpoint.get("name"),
        "quantization": str(endpoint.get("quantization") or "unknown").lower(),
        "zdr_eligible": zdr_rank == 0,
        "supported_parameters": sorted(set(endpoint.get("supported_parameters") or [])),
        "max_completion_tokens": endpoint.get("max_completion_tokens"),
        "pricing_overrides": pricing.get("overrides") or [],
        "input_usd_per_million": input_price,
        "output_usd_per_million": output_price,
        "input_cache_read_usd_per_million": price_per_million(
            pricing, "input_cache_read"
        ),
        "input_cache_write_usd_per_million": price_per_million(
            pricing, "input_cache_write"
        ),
        "expected_target_cost_usd_120": expected,
        "maximum_target_cost_usd_120": 120
        * (
            TARGET_MAX_INPUT_TOKENS * input_price
            + TARGET_MAX_OUTPUT_TOKENS * output_price
        )
        / 1_000_000,
    }
'''
    + text[end:]
)

replace(
    '''        hosted, hosted_reason = hosted_scope(model_id, str(model.get("name") or ""))
        open_weight = bool(model.get("hugging_face_id"))
        open_weight_eligible = bool(open_weight and total_b is not None and total_b >= 100)
        candidate = hosted or open_weight_eligible
        selection_basis = (
            hosted_reason
            if hosted
            else "open_weight_total_params_ge_100b"
            if open_weight_eligible
            else "open_weight_below_or_unknown_100b"
            if open_weight
            else hosted_reason
        )
''',
    '''        hosted, hosted_reason = hosted_scope(model_id, str(model.get("name") or ""))
        open_weight = bool(model.get("hugging_face_id"))
        open_weight_eligible = bool(
            open_weight and total_b is not None and total_b >= 100
        )
        candidate = open_weight_eligible if open_weight else hosted
        selection_basis = (
            "open_weight_total_params_ge_100b"
            if open_weight_eligible
            else "open_weight_below_or_unknown_100b"
            if open_weight
            else hosted_reason
        )
''',
)
text = text.replace(
    "no_operational_zdr_route_with_temperature_and_1024_tokens",
    "no_operational_fixed_route_with_1024_tokens",
)
replace(
    '''            "quantization": None,
            "seed_supported": False,
            "reasoning_effort_supported": False,
''',
    '''            "quantization": None,
            "zdr_eligible": False,
            "temperature_supported": False,
            "seed_supported": False,
            "reasoning_effort_supported": False,
            "supported_reasoning_efforts": [],
            "pricing_overrides": [],
''',
)
replace(
    '''            row["seed_supported"] = "seed" in supported
            row["reasoning_effort_supported"] = "reasoning_effort" in supported
''',
    '''            row["temperature_supported"] = "temperature" in supported
            row["seed_supported"] = "seed" in supported
            row["reasoning_effort_supported"] = "reasoning_effort" in supported
            reasoning = model.get("reasoning") or {}
            if isinstance(reasoning, dict):
                row["supported_reasoning_efforts"] = list(
                    reasoning.get("supported_efforts") or []
                )
''',
)
replace(
    'projected = float(row["expected_target_cost_usd_120"]) * 1.35',
    'projected = float(row["expected_target_cost_usd_120"])',
)
replace(
    "one operational ZDR endpoint, no fallback, request price zero, no conditional overrides, temperature and >=1024 output tokens",
    "one fixed operational endpoint, preferring ZDR, no fallback, request price zero, no relevant conditional override, and >=1024 output tokens",
)
replace(
    '''        "quantization",
        "seed_supported",
        "reasoning_effort_supported",
''',
    '''        "quantization",
        "zdr_eligible",
        "temperature_supported",
        "seed_supported",
        "reasoning_effort_supported",
        "supported_reasoning_efforts",
        "pricing_overrides",
''',
)

path.write_text(text, encoding="utf-8")
