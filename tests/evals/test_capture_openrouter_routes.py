from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parents[2] / "scripts/capture_openrouter_routes.py"
SPEC = spec_from_file_location("capture_openrouter_routes", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
capture_openrouter_routes = module_from_spec(SPEC)
sys.modules[SPEC.name] = capture_openrouter_routes
SPEC.loader.exec_module(capture_openrouter_routes)
RouteRequest = capture_openrouter_routes.RouteRequest
build_evidence = capture_openrouter_routes.build_evidence
fetch = capture_openrouter_routes._fetch
write_content_addressed = capture_openrouter_routes._write_content_addressed

ROUTE = RouteRequest(
    model_id="vendor/model",
    canonical_slug="vendor/model-20260812",
    provider_tag="provider/fp4",
    required_parameters=frozenset({"max_tokens", "seed"}),
    required_reasoning_effort="minimal",
    required_max_completion_tokens=256,
    output_name="evidence.json",
)


def test_wave1_capture_routes_match_current_serving_conditions() -> None:
    routes = {route.model_id: route for route in capture_openrouter_routes.ROUTES}
    assert routes["deepseek/deepseek-v4-flash"].provider_tag == "deepinfra/fp8"
    assert routes["deepseek/deepseek-v4-flash-0731"].provider_tag == "deepinfra/fp8"
    assert routes["google/gemini-3.6-flash"].provider_tag == "google-vertex/global"
    assert {route.output_name for route in routes.values()} == {
        "openrouter-deepseek-v4-flash-deepinfra-fp8.json",
        "openrouter-deepseek-v4-flash-0731-deepinfra-fp8.json",
        "openrouter-gemini-3.6-flash-google-vertex-global.json",
    }


def capture_payloads() -> dict[str, object]:
    model = {
        "id": ROUTE.model_id,
        "canonical_slug": ROUTE.canonical_slug,
        "created": 1,
        "expiration_date": None,
        "hugging_face_id": "vendor/model",
        "reasoning": {
            "supported_efforts": ["high", "minimal"],
            "default_effort": "minimal",
        },
    }
    endpoint = {
        "name": "Provider | vendor/model-20260812",
        "model_id": ROUTE.model_id,
        "provider_name": "Provider",
        "tag": ROUTE.provider_tag,
        "quantization": "fp4",
        "status": 0,
        "supported_parameters": ["seed", "max_tokens"],
        "pricing": {
            "prompt": "0.000001",
            "completion": "0.000002",
            "input_cache_read": "0.0000001",
        },
        "context_length": 8192,
        "max_completion_tokens": 1024,
        "max_prompt_tokens": 7168,
        "supports_implicit_caching": False,
    }
    return {
        "models": {"data": [model]},
        "model": {"data": model},
        "endpoints": {"data": {"id": ROUTE.model_id, "endpoints": [endpoint]}},
        "zdr": {"data": [endpoint]},
    }


def build_from(payloads: dict[str, object]) -> dict[str, object]:
    return build_evidence(
        ROUTE,
        observed_at="2026-08-12T12:00:00Z",
        models_raw=b"models",
        models=payloads["models"],
        model_raw=b"model",
        model=payloads["model"],
        endpoints_raw=b"endpoints",
        endpoints=payloads["endpoints"],
        zdr_raw=b"zdr",
        zdr=payloads["zdr"],
    )


def test_capture_binds_invocable_canonical_endpoint_and_zdr_records() -> None:
    evidence = build_from(capture_payloads())
    assert evidence["requested_model"] == ROUTE.model_id
    assert evidence["resolved_model"] == ROUTE.model_id
    assert evidence["canonical_slug"] == ROUTE.canonical_slug
    assert evidence["provider_tag"] == ROUTE.provider_tag
    assert evidence["supported_parameters"] == ["max_tokens", "seed"]
    assert evidence["supported_reasoning_efforts"] == ["high", "minimal"]
    assert evidence["max_completion_tokens"] == 1024
    assert evidence["request_price_usd"] == 0.0
    assert evidence["internal_reasoning_price_usd_per_million"] == 0.0
    assert evidence["zdr_eligible"] is True
    assert evidence["models_source_url"] == "https://openrouter.ai/api/v1/models"
    assert evidence["pricing_usd_per_million"] == pytest.approx(
        {
            "input": 1.0,
            "output": 2.0,
            "input_cache_write": 0.0,
            "input_cache_read": 0.1,
        }
    )


def test_capture_rejects_non_zdr_selected_endpoint() -> None:
    payloads = capture_payloads()
    payloads["zdr"] = {"data": []}
    with pytest.raises(ValueError, match="exactly one ZDR endpoint"):
        build_from(payloads)


def test_capture_rejects_endpoint_missing_a_frozen_parameter() -> None:
    payloads = capture_payloads()
    endpoint = payloads["endpoints"]["data"]["endpoints"][0]
    endpoint["supported_parameters"] = ["max_tokens"]
    with pytest.raises(ValueError, match="lacks required parameters: seed"):
        build_from(payloads)


def test_capture_rejects_disagreement_between_endpoint_inventories() -> None:
    payloads = capture_payloads()
    payloads["zdr"]["data"][0] = dict(payloads["zdr"]["data"][0])
    payloads["zdr"]["data"][0]["provider_name"] = "Different Provider"
    with pytest.raises(ValueError, match="inventories disagree"):
        build_from(payloads)


@pytest.mark.parametrize("price", ["Infinity", "NaN", "-0.000001", True, "invalid"])
def test_capture_rejects_invalid_endpoint_prices(price: object) -> None:
    payloads = capture_payloads()
    payloads["endpoints"]["data"]["endpoints"][0]["pricing"]["prompt"] = price
    with pytest.raises(ValueError, match="finite non-negative"):
        build_from(payloads)


def test_capture_rejects_conditional_price_overrides() -> None:
    payloads = capture_payloads()
    payloads["endpoints"]["data"]["endpoints"][0]["pricing"]["overrides"] = [
        {"min_prompt_tokens": 10, "prompt": "0.1"}
    ]
    with pytest.raises(ValueError, match="conditional pricing overrides"):
        build_from(payloads)


def test_capture_rejects_more_expensive_internal_reasoning() -> None:
    payloads = capture_payloads()
    payloads["endpoints"]["data"]["endpoints"][0]["pricing"]["internal_reasoning"] = "0.000003"
    with pytest.raises(ValueError, match="internal-reasoning price"):
        build_from(payloads)


def test_capture_preserves_internal_reasoning_price() -> None:
    payloads = capture_payloads()
    payloads["endpoints"]["data"]["endpoints"][0]["pricing"]["internal_reasoning"] = "0.0000015"
    evidence = build_from(payloads)
    assert evidence["internal_reasoning_price_usd_per_million"] == 1.5


def test_capture_preserves_fixed_request_price() -> None:
    payloads = capture_payloads()
    payloads["endpoints"]["data"]["endpoints"][0]["pricing"]["request"] = "0.05"
    evidence = build_from(payloads)
    assert evidence["request_price_usd"] == 0.05


def test_capture_rejects_reasoning_effort_domain_drift() -> None:
    payloads = capture_payloads()
    payloads["model"]["data"]["reasoning"]["supported_efforts"] = ["high", "low"]
    with pytest.raises(ValueError, match="does not support frozen reasoning effort minimal"):
        build_from(payloads)


def test_capture_rejects_insufficient_completion_limit() -> None:
    payloads = capture_payloads()
    payloads["endpoints"]["data"]["endpoints"][0]["max_completion_tokens"] = 255
    with pytest.raises(ValueError, match="completion-token limit"):
        build_from(payloads)


def test_raw_responses_are_archived_by_content_hash(tmp_path: Path) -> None:
    name = write_content_addressed(tmp_path, b'{"data": []}')
    assert (tmp_path / name).read_bytes() == b'{"data": []}'
    assert name.endswith(".json")


def test_fetch_is_bounded_and_rejects_non_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def __init__(self, status: int, raw: bytes) -> None:
            self.status = status
            self.raw = raw

        def read(self, amount: int = -1) -> bytes:
            return self.raw[:amount] if amount >= 0 else self.raw

        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    monkeypatch.setattr(
        capture_openrouter_routes,
        "_direct_urlopen",
        lambda *args, **kwargs: FakeResponse(302, b"{}"),
    )
    with pytest.raises(RuntimeError, match="non-success"):
        fetch("models")

    oversized = b"x" * (capture_openrouter_routes.MAX_RESPONSE_BYTES + 1)
    monkeypatch.setattr(
        capture_openrouter_routes,
        "_direct_urlopen",
        lambda *args, **kwargs: FakeResponse(200, oversized),
    )
    with pytest.raises(RuntimeError, match="unexpectedly large"):
        fetch("models")
