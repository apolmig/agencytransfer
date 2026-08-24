"""Build a live, sanitised APE-120 candidate inventory from OpenRouter.

This script performs no model inference and uses no credentials. It records the
models and fixed ZDR provider routes that are currently eligible for the
longitudinal APE-120 wave, together with explicit exclusions and conservative
cost projections.
"""

from __future__ import annotations

import csv
import json
import math
import re
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

BASE_URL = "https://openrouter.ai/api/v1"
REGISTRY_PATH = Path("data/models/frontier-models.csv")
REPORT_JSON = Path("evals/research-notes/ape120-live-inventory-20260825.json")
REPORT_CSV = Path("evals/research-notes/ape120-live-inventory-20260825.csv")
MAX_RESPONSE_BYTES = 64 * 1024 * 1024
TARGET_EXPECTED_INPUT_TOKENS = 1_000
TARGET_EXPECTED_OUTPUT_TOKENS = 450
TARGET_MAX_INPUT_TOKENS = 2_000
TARGET_MAX_OUTPUT_TOKENS = 1_024
TARGET_BUDGET_USD = 25.0
TOTAL_EXECUTION_BUDGET_USD = 29.5
MUTABLE_TOKENS = {"latest", "auto", "preview", "beta", "experimental", "free"}
EXCLUDED_TOKENS = {
    "embedding",
    "moderation",
    "rerank",
    "transcribe",
    "tts",
    "audio",
    "image",
    "video",
    "realtime",
    "search",
    "computer-use",
    "computer_use",
}
SMALL_TOKENS = {
    "mini",
    "nano",
    "haiku",
    "flash-lite",
    "flash_lite",
    "small",
    "tiny",
}
QUANTIZATION_ORDER = {
    "bf16": 0,
    "fp16": 1,
    "fp8": 2,
    "int8": 3,
    "unknown": 4,
    "fp4": 5,
    "int4": 6,
}


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


def fetch_json(path: str) -> tuple[bytes, dict[str, Any]]:
    request = urllib.request.Request(
        f"{BASE_URL}/{path}",
        headers={
            "Accept": "application/json",
            "User-Agent": "agencytransfer-ape120-inventory/0.1",
        },
    )
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        NoRedirect(),
    )
    try:
        with opener.open(request, timeout=60) as response:
            if response.status != 200:
                raise RuntimeError(f"OpenRouter returned {response.status} for {path}")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, TimeoutError, urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise RuntimeError(f"OpenRouter capture failed for {path}: {exc}") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise RuntimeError(f"OpenRouter response is unexpectedly large for {path}")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise RuntimeError(f"OpenRouter response lacks a JSON object for {path}")
    return raw, payload


def finite_nonnegative(value: Any, *, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        raise ValueError("boolean is not a price")
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError("price must be finite and non-negative")
    return result


def price_per_million(pricing: dict[str, Any], field: str) -> float:
    return finite_nonnegative(pricing.get(field)) * 1_000_000


def tokenise(value: str) -> set[str]:
    return {part for part in re.split(r"[^a-z0-9_]+", value.lower()) if part}


def parse_total_params_b(
    model: dict[str, Any], registry_row: dict[str, str] | None
) -> tuple[float | None, str | None]:
    if registry_row and registry_row.get("totalParamsB"):
        return float(registry_row["totalParamsB"]), "registry"

    text = " ".join(str(model.get(key) or "") for key in ("name", "description"))
    patterns = (
        (r"out of\s+([\d,.]+)\s*T(?:rillion)?\b", 1_000.0),
        (r"out of\s+([\d,.]+)\s*B(?:illion)?\b", 1.0),
        (r"([\d,.]+)\s*T(?:rillion)?\s+(?:total\s+)?parameters?\b", 1_000.0),
        (r"([\d,.]+)\s*B(?:illion)?\s+(?:total\s+)?parameters?\b", 1.0),
        (r"([\d,.]+)\s*T\s+total\b", 1_000.0),
        (r"([\d,.]+)\s*B\s+total\b", 1.0),
        (r"([\d,.]+)\s+trillion[- ]parameter", 1_000.0),
        (r"([\d,.]+)\s+billion[- ]parameter", 1.0),
    )
    values: list[float] = []
    for pattern, multiplier in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            values.append(float(match.group(1).replace(",", "")) * multiplier)
    return (max(values), "description") if values else (None, None)


def hosted_scope(model_id: str, name: str) -> tuple[bool, str]:
    combined = f"{model_id} {name}".lower()
    tokens = tokenise(combined)
    if ":" in model_id or model_id.startswith("~") or any(
        marker in combined for marker in (":free", ":batch", "-fast")
    ):
        return False, "duplicate_discount_or_mutable_alias"
    if MUTABLE_TOKENS & tokens:
        return False, "mutable_or_preview_identity"
    if EXCLUDED_TOKENS & tokens:
        return False, "specialised_non_general_endpoint"

    if model_id.startswith("openai/"):
        if not ("/gpt-" in model_id or re.search(r"/o[1-9](?:$|[-.])", model_id)):
            return False, "not_gpt_or_frontier_o_series"
        if SMALL_TOKENS & tokens or "codex" in tokens:
            return False, "small_or_specialised_openai_tier"
        return True, "hosted_frontier_or_quasi_frontier_openai"

    if model_id.startswith("anthropic/"):
        if "claude" not in model_id:
            return False, "not_claude"
        if "haiku" in tokens:
            return False, "small_claude_tier"
        return True, "hosted_frontier_or_quasi_frontier_claude"

    if model_id.startswith("google/"):
        if "gemini" not in model_id:
            return False, "not_gemini"
        if {"flash-lite", "flash_lite", "nano"} & tokens:
            return False, "small_gemini_tier"
        return True, "hosted_frontier_or_quasi_frontier_gemini"

    if model_id.startswith("x-ai/"):
        if "grok" not in model_id:
            return False, "not_grok"
        if SMALL_TOKENS & tokens or "code" in tokens:
            return False, "small_or_specialised_grok_tier"
        return True, "hosted_frontier_or_quasi_frontier_grok"

    return False, "not_target_hosted_vendor"


def choose_endpoint(
    model_id: str,
    endpoint_inventory: dict[str, Any],
    zdr_pairs: set[tuple[str, str]],
) -> dict[str, Any] | None:
    candidates: list[tuple[int, float, str, dict[str, Any]]] = []
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
        if (model_id, tag) not in zdr_pairs:
            continue
        if not {"max_tokens", "temperature"}.issubset(supported):
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
        if pricing.get("overrides") not in (None, []):
            continue
        input_price = price_per_million(pricing, "prompt")
        output_price = price_per_million(pricing, "completion")
        if input_price <= 0 or output_price <= 0:
            continue
        expected = 120 * (
            TARGET_EXPECTED_INPUT_TOKENS * input_price
            + TARGET_EXPECTED_OUTPUT_TOKENS * output_price
        ) / 1_000_000
        candidates.append(
            (
                QUANTIZATION_ORDER.get(quantization, QUANTIZATION_ORDER["unknown"]),
                expected,
                tag,
                endpoint,
            )
        )
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    _, expected, tag, endpoint = candidates[0]
    pricing = endpoint.get("pricing") or {}
    input_price = price_per_million(pricing, "prompt")
    output_price = price_per_million(pricing, "completion")
    return {
        "provider_tag": tag,
        "provider_name": endpoint.get("provider_name"),
        "endpoint_name": endpoint.get("name"),
        "quantization": str(endpoint.get("quantization") or "unknown").lower(),
        "supported_parameters": sorted(set(endpoint.get("supported_parameters") or [])),
        "max_completion_tokens": endpoint.get("max_completion_tokens"),
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


def release_date(model: dict[str, Any], registry_row: dict[str, str] | None) -> str | None:
    if registry_row and registry_row.get("releaseDate"):
        return registry_row["releaseDate"]
    created = model.get("created")
    if isinstance(created, (int, float)) and not isinstance(created, bool):
        return datetime.fromtimestamp(created, UTC).date().isoformat()
    return None


def family_key(model_id: str, registry_row: dict[str, str] | None) -> str:
    if registry_row and registry_row.get("family"):
        return registry_row["family"]
    return model_id.split("/", 1)[0]


def budget_select(candidates: list[dict[str, Any]]) -> None:
    """Select the broadest useful longitudinal set inside the target allowance."""

    for row in candidates:
        row["selected_for_budget"] = False
        row["budget_priority"] = None

    by_vendor: dict[str, list[dict[str, Any]]] = {
        "openai": [],
        "anthropic": [],
        "google": [],
        "x-ai": [],
    }
    open_weight: list[dict[str, Any]] = []
    remaining_hosted: list[dict[str, Any]] = []

    for row in candidates:
        vendor = row["model_id"].split("/", 1)[0]
        if row["selection_basis"].startswith("hosted_") and vendor in by_vendor:
            by_vendor[vendor].append(row)
        elif row["selection_basis"] == "open_weight_total_params_ge_100b":
            open_weight.append(row)
        else:
            remaining_hosted.append(row)

    for values in by_vendor.values():
        values.sort(key=lambda row: (row["release_date"] or "9999-99-99", row["model_id"]))
    open_weight.sort(
        key=lambda row: (row["release_date"] or "9999-99-99", row["model_id"])
    )

    priority: list[dict[str, Any]] = []
    for vendor in ("openai", "anthropic", "google", "x-ai"):
        values = by_vendor[vendor]
        if values:
            priority.append(values[0])
            if values[-1] is not values[0]:
                priority.append(values[-1])
    priority.extend(open_weight)
    already = {id(row) for row in priority}
    middle = [
        row
        for vendor in ("openai", "anthropic", "google", "x-ai")
        for row in by_vendor[vendor]
        if id(row) not in already
    ]
    middle.extend(remaining_hosted)
    middle.sort(key=lambda row: (row["release_date"] or "9999-99-99", row["model_id"]))
    priority.extend(middle)

    spent = 0.0
    selected_ids: set[str] = set()
    for index, row in enumerate(priority, start=1):
        if row["model_id"] in selected_ids:
            continue
        projected = float(row["expected_target_cost_usd_120"]) * 1.35
        if spent + projected > TARGET_BUDGET_USD:
            continue
        row["selected_for_budget"] = True
        row["budget_priority"] = index
        selected_ids.add(row["model_id"])
        spent += projected


def main() -> None:
    _, models_payload = fetch_json("models")
    _, zdr_payload = fetch_json("endpoints/zdr")
    models = models_payload.get("data") or []
    zdr_records = zdr_payload.get("data") or []
    if not isinstance(models, list) or not isinstance(zdr_records, list):
        raise RuntimeError("OpenRouter inventory shape changed")
    zdr_pairs = {
        (item.get("model_id"), item.get("tag"))
        for item in zdr_records
        if isinstance(item, dict) and item.get("status") == 0
    }

    registry_rows: dict[str, dict[str, str]] = {}
    with REGISTRY_PATH.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            openrouter_id = row.get("openRouterId")
            if openrouter_id:
                registry_rows[openrouter_id] = row

    rows: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for model in models:
        if not isinstance(model, dict):
            continue
        model_id = str(model.get("id") or "")
        if not model_id or ":" in model_id or model_id.startswith("~"):
            continue
        architecture = model.get("architecture") or {}
        if not isinstance(architecture, dict):
            architecture = {}
        if "text" not in (architecture.get("input_modalities") or []):
            continue
        if "text" not in (architecture.get("output_modalities") or []):
            continue

        registry_row = registry_rows.get(model_id)
        total_b, parameter_source = parse_total_params_b(model, registry_row)
        hosted, hosted_reason = hosted_scope(model_id, str(model.get("name") or ""))
        open_weight = bool(model.get("hugging_face_id"))
        open_weight_eligible = bool(
            open_weight and total_b is not None and total_b >= 100
        )
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

        canonical_slug = str(model.get("canonical_slug") or "")
        canonical_mutable = bool(MUTABLE_TOKENS & tokenise(canonical_slug))
        if candidate and canonical_mutable:
            candidate = False
            selection_basis = "mutable_canonical_identity"

        endpoint = None
        endpoint_error = None
        if candidate:
            try:
                _, endpoint_payload = fetch_json(f"models/{model_id}/endpoints")
                endpoint_data = endpoint_payload.get("data") or {}
                if not isinstance(endpoint_data, dict):
                    raise RuntimeError("endpoint response lacks data object")
                endpoint = choose_endpoint(model_id, endpoint_data, zdr_pairs)
                if endpoint is None:
                    endpoint_error = (
                        "no_operational_zdr_route_with_temperature_and_1024_tokens"
                    )
                    candidate = False
                    selection_basis = endpoint_error
            except Exception as exc:
                endpoint_error = f"endpoint_capture_error:{type(exc).__name__}"
                candidate = False
                selection_basis = endpoint_error

        row: dict[str, Any] = {
            "candidate": candidate,
            "selection_basis": selection_basis,
            "model_id": model_id,
            "canonical_slug": canonical_slug,
            "name": model.get("name"),
            "release_date": release_date(model, registry_row),
            "family": family_key(model_id, registry_row),
            "registry_id": (registry_row or {}).get("id"),
            "hugging_face_id": model.get("hugging_face_id"),
            "total_params_b": total_b,
            "parameter_source": parameter_source,
            "endpoint_error": endpoint_error,
            "provider_tag": None,
            "provider_name": None,
            "endpoint_name": None,
            "quantization": None,
            "seed_supported": False,
            "reasoning_effort_supported": False,
            "input_usd_per_million": None,
            "output_usd_per_million": None,
            "expected_target_cost_usd_120": None,
            "maximum_target_cost_usd_120": None,
        }
        if endpoint is not None:
            supported = set(endpoint["supported_parameters"])
            row.update(endpoint)
            row["seed_supported"] = "seed" in supported
            row["reasoning_effort_supported"] = "reasoning_effort" in supported
        rows.append(row)
        if candidate:
            candidates.append(row)

    candidates.sort(
        key=lambda row: (row["release_date"] or "9999-99-99", row["model_id"])
    )
    budget_select(candidates)
    rows.sort(
        key=lambda row: (
            0 if row.get("selected_for_budget") else 1,
            row["release_date"] or "9999-99-99",
            row["model_id"],
        )
    )

    selected = [row for row in candidates if row["selected_for_budget"]]
    expected_target = sum(
        float(row["expected_target_cost_usd_120"]) for row in selected
    )
    maximum_target = sum(
        float(row["maximum_target_cost_usd_120"]) for row in selected
    )
    summary = {
        "schema_version": "atb-ape120-live-inventory-v0.2",
        "observed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "models_source_url": f"{BASE_URL}/models",
        "zdr_source_url": f"{BASE_URL}/endpoints/zdr",
        "selection_rule": {
            "hosted": "stable general GPT/o-series, Claude except Haiku/Fast, Gemini except Lite/Nano, and Grok except small/code tiers",
            "open_weight": "live OpenRouter text model with Hugging Face identity and documented total parameters >=100B",
            "route": "one operational ZDR endpoint, no fallback, request price zero, no conditional overrides, temperature and >=1024 output tokens",
            "budget": "longest hosted-family span first, then open-weight anchors oldest first, then intermediate hosted checkpoints",
        },
        "total_execution_budget_usd": TOTAL_EXECUTION_BUDGET_USD,
        "target_selection_budget_usd": TARGET_BUDGET_USD,
        "candidate_count": len(candidates),
        "selected_count": len(selected),
        "expected_selected_target_cost_usd": expected_target,
        "maximum_selected_target_cost_usd": maximum_target,
        "selected_model_ids": [row["model_id"] for row in selected],
        "rows": rows,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    fieldnames = [
        "selected_for_budget",
        "budget_priority",
        "candidate",
        "selection_basis",
        "model_id",
        "canonical_slug",
        "name",
        "release_date",
        "family",
        "registry_id",
        "hugging_face_id",
        "total_params_b",
        "parameter_source",
        "provider_tag",
        "provider_name",
        "endpoint_name",
        "quantization",
        "seed_supported",
        "reasoning_effort_supported",
        "input_usd_per_million",
        "output_usd_per_million",
        "expected_target_cost_usd_120",
        "maximum_target_cost_usd_120",
        "endpoint_error",
    ]
    with REPORT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})

    print(
        json.dumps(
            {key: value for key, value in summary.items() if key != "rows"},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
