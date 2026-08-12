"""Capture sanitised, hash-bound OpenRouter route evidence without credentials.

The public APIs are mutable. This script validates the invocable model ID,
permanent canonical slug, selected provider endpoint, prices, parameters, and
ZDR eligibility in one capture. It writes no prompts, outputs, or secrets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

BASE_URL = "https://openrouter.ai/api/v1"
RAW_DIR_NAME = "provider-responses"
MAX_RESPONSE_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class RouteRequest:
    model_id: str
    canonical_slug: str
    provider_tag: str
    required_parameters: frozenset[str]
    required_reasoning_effort: str
    required_max_completion_tokens: int
    output_name: str


ROUTES = (
    RouteRequest(
        model_id="deepseek/deepseek-v4-flash",
        canonical_slug="deepseek/deepseek-v4-flash-20260423",
        provider_tag="deepinfra/fp4",
        required_parameters=frozenset(
            {"max_tokens", "reasoning", "reasoning_effort", "seed", "temperature", "top_p"}
        ),
        required_reasoning_effort="high",
        required_max_completion_tokens=250,
        output_name="openrouter-deepseek-v4-flash-deepinfra-fp4.json",
    ),
    RouteRequest(
        model_id="deepseek/deepseek-v4-flash-0731",
        canonical_slug="deepseek/deepseek-v4-flash-20260731",
        provider_tag="deepinfra/fp4",
        required_parameters=frozenset(
            {"max_tokens", "reasoning", "reasoning_effort", "seed", "temperature", "top_p"}
        ),
        required_reasoning_effort="high",
        required_max_completion_tokens=250,
        output_name="openrouter-deepseek-v4-flash-0731-deepinfra-fp4.json",
    ),
    RouteRequest(
        model_id="google/gemini-3.6-flash",
        canonical_slug="google/gemini-3.6-flash-20260721",
        provider_tag="google-vertex/global",
        required_parameters=frozenset({"max_tokens", "reasoning", "reasoning_effort", "seed"}),
        required_reasoning_effort="minimal",
        required_max_completion_tokens=256,
        output_name="openrouter-gemini-3.6-flash-google-vertex-global.json",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--observed-at",
        help="UTC ISO-8601 timestamp; defaults to the capture time.",
    )
    return parser.parse_args()


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
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


def _direct_urlopen(request: urllib.request.Request, *, timeout: float) -> Any:
    """Open the fixed public endpoint without environment proxies or redirects."""

    return urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        _NoRedirectHandler(),
    ).open(request, timeout=timeout)


def _fetch(path: str) -> tuple[bytes, Any]:
    request = urllib.request.Request(
        f"{BASE_URL}/{path}",
        headers={"Accept": "application/json", "User-Agent": "agencytransfer-route-freeze/0.1"},
    )
    try:
        with _direct_urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise RuntimeError("OpenRouter capture returned a non-success status")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, TimeoutError, urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise RuntimeError(f"OpenRouter capture failed for {path}: {exc}") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise RuntimeError(f"OpenRouter capture response is unexpectedly large for {path}")
    try:
        return raw, json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"OpenRouter returned invalid JSON for {path}") from exc


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _price(pricing: dict[str, Any], field: str) -> float:
    value = pricing.get(field)
    if value is None:
        return 0.0
    if isinstance(value, bool):
        raise ValueError(f"endpoint price {field} is not a finite non-negative number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"endpoint price {field} is not a finite non-negative number") from exc
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"endpoint price {field} is not a finite non-negative number")
    return result


def _per_million(pricing: dict[str, Any], field: str) -> float:
    return _price(pricing, field) * 1_000_000


def _write_content_addressed(raw_dir: Path, raw: bytes) -> str:
    digest = _sha256(raw)
    path = raw_dir / f"{digest}.json"
    if path.exists() and path.read_bytes() != raw:
        raise ValueError(f"content-addressed raw capture collision for {digest}")
    path.write_bytes(raw)
    return path.name


def _one(items: list[dict[str, Any]], description: str) -> dict[str, Any]:
    if len(items) != 1:
        raise ValueError(f"expected exactly one {description}; found {len(items)}")
    return items[0]


def build_evidence(
    route: RouteRequest,
    *,
    observed_at: str,
    models_raw: bytes,
    models: dict[str, Any],
    model_raw: bytes,
    model: dict[str, Any],
    endpoints_raw: bytes,
    endpoints: dict[str, Any],
    zdr_raw: bytes,
    zdr: dict[str, Any],
) -> dict[str, Any]:
    model_list_record = _one(
        [item for item in models.get("data", []) if item.get("id") == route.model_id],
        f"models record for {route.model_id}",
    )
    model_record = model.get("data")
    endpoint_inventory = endpoints.get("data")
    if not isinstance(model_record, dict) or not isinstance(endpoint_inventory, dict):
        raise ValueError("model or endpoint response lacks a data object")
    for record in (model_list_record, model_record):
        if record.get("id") != route.model_id:
            raise ValueError(f"model id mismatch for {route.model_id}")
        if record.get("canonical_slug") != route.canonical_slug:
            raise ValueError(f"canonical slug mismatch for {route.model_id}")
    if endpoint_inventory.get("id") != route.model_id:
        raise ValueError(f"endpoint inventory id mismatch for {route.model_id}")

    endpoint = _one(
        [
            item
            for item in endpoint_inventory.get("endpoints", [])
            if item.get("tag") == route.provider_tag
        ],
        f"endpoint {route.provider_tag} for {route.model_id}",
    )
    zdr_endpoint = _one(
        [
            item
            for item in zdr.get("data", [])
            if item.get("model_id") == route.model_id and item.get("tag") == route.provider_tag
        ],
        f"ZDR endpoint {route.provider_tag} for {route.model_id}",
    )
    identity_fields = ("name", "model_id", "provider_name", "tag", "quantization")
    if any(endpoint.get(field) != zdr_endpoint.get(field) for field in identity_fields):
        raise ValueError(f"endpoint and ZDR inventories disagree for {route.model_id}")
    if endpoint.get("status") != 0 or zdr_endpoint.get("status") != 0:
        raise ValueError(f"selected endpoint is not operational for {route.model_id}")
    supported = sorted(set(endpoint.get("supported_parameters", [])))
    missing = sorted(route.required_parameters.difference(supported))
    if missing:
        raise ValueError(f"selected endpoint lacks required parameters: {', '.join(missing)}")
    reasoning = model_record.get("reasoning")
    supported_efforts = (
        reasoning.get("supported_efforts", []) if isinstance(reasoning, dict) else []
    )
    if not isinstance(supported_efforts, list) or any(
        not isinstance(effort, str) for effort in supported_efforts
    ):
        raise ValueError(f"model has an invalid reasoning-effort inventory for {route.model_id}")
    if route.required_reasoning_effort not in supported_efforts:
        raise ValueError(
            f"model does not support frozen reasoning effort {route.required_reasoning_effort}"
        )
    max_completion_tokens = endpoint.get("max_completion_tokens")
    if (
        isinstance(max_completion_tokens, bool)
        or not isinstance(max_completion_tokens, int)
        or max_completion_tokens < route.required_max_completion_tokens
    ):
        raise ValueError("selected endpoint cannot satisfy the frozen completion-token limit")

    pricing = endpoint.get("pricing") or {}
    if not isinstance(pricing, dict):
        raise ValueError(f"selected endpoint lacks a pricing object for {route.model_id}")
    if pricing.get("overrides") not in (None, []):
        raise ValueError("selected endpoint has unsupported conditional pricing overrides")
    output_price = _per_million(pricing, "completion")
    internal_reasoning_price = _per_million(pricing, "internal_reasoning")
    if internal_reasoning_price > output_price:
        raise ValueError("endpoint internal-reasoning price exceeds the frozen output price")
    price_snapshot = {
        "input": _per_million(pricing, "prompt"),
        "output": output_price,
        "input_cache_write": _per_million(pricing, "input_cache_write"),
        "input_cache_read": _per_million(pricing, "input_cache_read"),
    }
    request_price_usd = _price(pricing, "request")
    return {
        "schema_version": "atb-model-revision-evidence-v0.1",
        "requested_model": route.model_id,
        "resolved_model": route.model_id,
        "canonical_slug": route.canonical_slug,
        "inventory_model_id": endpoint_inventory["id"],
        "endpoint_model_id": endpoint["model_id"],
        "endpoint_name": endpoint["name"],
        "provider_name": endpoint["provider_name"],
        "provider_tag": endpoint["tag"],
        "quantization": endpoint["quantization"],
        "supported_parameters": supported,
        "supported_reasoning_efforts": supported_efforts,
        "max_completion_tokens": max_completion_tokens,
        "request_price_usd": request_price_usd,
        "internal_reasoning_price_usd_per_million": internal_reasoning_price,
        "observed_at": observed_at,
        "source_url": f"{BASE_URL}/models/{route.model_id}/endpoints",
        "model_source_url": f"{BASE_URL}/model/{route.model_id}",
        "model_response_sha256": _sha256(model_raw),
        "models_source_url": f"{BASE_URL}/models",
        "models_response_sha256": _sha256(models_raw),
        "endpoint_response_sha256": _sha256(endpoints_raw),
        "zdr_source_url": f"{BASE_URL}/endpoints/zdr",
        "zdr_response_sha256": _sha256(zdr_raw),
        "zdr_eligible": True,
        "pricing_usd_per_million": price_snapshot,
        "model_observation": {
            "created": model_record.get("created"),
            "expiration_date": model_record.get("expiration_date"),
            "hugging_face_id": model_record.get("hugging_face_id"),
            "reasoning": reasoning,
        },
        "endpoint_observation": {
            "context_length": endpoint.get("context_length"),
            "max_completion_tokens": endpoint.get("max_completion_tokens"),
            "max_prompt_tokens": endpoint.get("max_prompt_tokens"),
            "status": endpoint.get("status"),
            "supports_implicit_caching": endpoint.get("supports_implicit_caching"),
        },
        "scope": "Sanitised public route record; no credential or request content",
    }


def main() -> None:
    args = parse_args()
    observed_at = args.observed_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    if not observed_at.endswith("Z"):
        raise SystemExit("--observed-at must be an ISO-8601 UTC timestamp ending in Z")
    models_raw, models = _fetch("models")
    zdr_raw, zdr = _fetch("endpoints/zdr")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    raw_dir = args.output_dir / RAW_DIR_NAME
    raw_dir.mkdir(mode=0o755)
    _write_content_addressed(raw_dir, models_raw)
    _write_content_addressed(raw_dir, zdr_raw)
    for route in ROUTES:
        model_raw, model = _fetch(f"model/{route.model_id}")
        endpoints_raw, endpoints = _fetch(f"models/{route.model_id}/endpoints")
        _write_content_addressed(raw_dir, model_raw)
        _write_content_addressed(raw_dir, endpoints_raw)
        evidence = build_evidence(
            route,
            observed_at=observed_at,
            models_raw=models_raw,
            models=models,
            model_raw=model_raw,
            model=model,
            endpoints_raw=endpoints_raw,
            endpoints=endpoints,
            zdr_raw=zdr_raw,
            zdr=zdr,
        )
        raw_hashes = (
            evidence["model_response_sha256"],
            evidence["models_response_sha256"],
            evidence["endpoint_response_sha256"],
            evidence["zdr_response_sha256"],
        )
        if any(not (raw_dir / f"{digest}.json").is_file() for digest in raw_hashes):
            raise ValueError(f"raw response archive is incomplete for {route.model_id}")
        path = args.output_dir / route.output_name
        path.write_text(json.dumps(evidence, indent=2, sort_keys=False) + "\n", encoding="utf-8")
        print(f"{path} {_sha256(path.read_bytes())}")


if __name__ == "__main__":
    main()
