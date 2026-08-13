from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import atb_eval.manifest as manifest_module
import httpx
import pytest
from atb_eval.manifest import (
    ModelCondition,
    ProtocolManifest,
    ProtocolStatus,
    RouteSpec,
    forbidden_runtime_overrides,
    load_manifest,
    require_controlled_log_dir,
    require_path_outside_repo,
    sha256_file,
    verify_committed_file,
    verify_model_revision_evidence,
)
from atb_eval.runner import (
    build_model,
    build_task,
    condition_map,
    diselect_score_contract_matches,
    effective_event_generate_config,
    ensure_private_permissions,
    execution_envelope,
    expected_runtime_packages,
    model_cost_config,
    openrouter_route_metadata_matches,
    read_postflight_log,
    recorded_execution_usage_within_envelope,
    recorded_openrouter_billed_costs,
    repository_root,
    request_parameters_match,
    run_fingerprint,
    runtime_package_versions,
    sample_model_inputs_match,
    sample_routes_match,
    sample_target_output_matches,
    verify_task_identity,
)
from inspect_ai.event import ModelEvent
from inspect_ai.log import EvalConfig, EvalDataset, EvalLog, EvalSample, EvalSpec, write_eval_log
from inspect_ai.model import (
    ChatCompletionChoice,
    ChatMessageAssistant,
    ChatMessageUser,
    ContentReasoning,
    ContentText,
    GenerateConfig,
    ModelOutput,
    get_model,
)
from inspect_ai.scorer import Score
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_frozen_canary_manifest_is_valid() -> None:
    manifest = load_manifest(REPO_ROOT / "evals/manifests/inspect-canary-v0.1.json")
    assert manifest.status is ProtocolStatus.FROZEN
    assert manifest.models[0].model == "mockllm/model"
    assert not manifest.is_paid
    task = build_task(manifest, None)
    verify_task_identity(manifest, task)
    assert execution_envelope(manifest, task) == {
        "samples_per_model": 3,
        "maximum_sample_attempts": 6,
        "maximum_cost_usd": 0,
        "maximum_tokens": 6000,
    }
    runtime = expected_runtime_packages(manifest)
    assert runtime_package_versions(manifest) == runtime
    assert {"openai", "mistralai", "anthropic", "google-genai"}.issubset(runtime)


def test_draft_protocols_are_schema_valid() -> None:
    for name in ("diselect-wave1a-v0.1.json", "ape-turn1-template-v0.1.json"):
        manifest = load_manifest(REPO_ROOT / "evals/manifests" / name)
        assert manifest.status is ProtocolStatus.DRAFT
        assert manifest.models == []


def test_frozen_wave1a_manifest_is_bounded_and_nonpublic() -> None:
    manifest = load_manifest(REPO_ROOT / "evals/manifests/diselect-wave1a-v0.2.json")
    assert manifest.status is ProtocolStatus.FROZEN
    assert manifest.protocol_id == "atb-diselect-wave1a-v0.2"
    assert manifest.task.args == {
        "selection_seed": "atb-diselect-wave1a-v0.1",
        "harmful_per_stratum": 5,
        "benign_count": 10,
        "include_actionability": False,
        "temperature": 1.0,
        "max_tokens": 700,
    }
    assert manifest.dataset.selected_inventory_sha256 == (
        "2e6b2fe804453a62b1295a9ab920bc28ea97c18837bc65afa41491c9fd8427e6"
    )
    assert len(manifest.models) == 2
    assert all(condition.generate_config["top_k"] == 40 for condition in manifest.models)
    assert all(condition.generate_config["top_p"] == 0.95 for condition in manifest.models)
    assert manifest.run.expected_samples_per_model == 50
    assert manifest.run.max_retries == manifest.run.retry_on_error == 0
    assert manifest.run.retry_attempts == 0
    assert manifest.run.sample_cost_limit_usd == 0.01
    assert manifest.run.planned_run_cost_envelope_usd == 1.0
    assert manifest.run.sample_token_limit == 5000
    assert manifest.run.planned_run_token_envelope == 500000
    assert manifest.run.provider_key_limit_usd == 30.0
    assert manifest.validation.double_coded_n == 30
    assert manifest.validation.probability_strata == ["condition_id", "use_case"]
    assert manifest.release.public_aggregate_candidate is False
    assert manifest.release.requires_two_person_review is True


@pytest.mark.parametrize(
    (
        "manifest_name",
        "provider_key_limit_usd",
        "target_max_tokens",
        "sample_token_limit",
        "run_token_envelope",
    ),
    [
        ("diselect-route-preflight-v0.1.json", 0.04, 250, 2000, 4000),
        ("diselect-route-preflight-v0.2.json", 30.0, 250, 2000, 4000),
        ("diselect-route-preflight-v0.3.json", 30.0, 700, 3000, 6000),
    ],
)
def test_diselect_route_preflight_is_bounded_and_nonpublic(
    manifest_name: str,
    provider_key_limit_usd: float,
    target_max_tokens: int,
    sample_token_limit: int,
    run_token_envelope: int,
) -> None:
    manifest = load_manifest(REPO_ROOT / "evals/manifests" / manifest_name)
    assert manifest.status is ProtocolStatus.FROZEN
    assert manifest.task.kind == "diselect"
    assert manifest.task.args["harmful_per_stratum"] == 0
    assert manifest.task.args["benign_count"] == 1
    assert manifest.run.expected_samples_per_model == 1
    assert manifest.run.epochs == 1
    assert manifest.run.max_connections == 1
    assert manifest.run.max_retries == 0
    assert manifest.run.planned_run_cost_envelope_usd == 0.04
    assert manifest.run.provider_key_limit_usd == provider_key_limit_usd
    assert manifest.task.args["max_tokens"] == target_max_tokens
    assert manifest.run.sample_cost_limit_usd == 0.02
    assert manifest.run.sample_token_limit == sample_token_limit
    assert manifest.run.planned_run_token_envelope == run_token_envelope
    assert target_max_tokens < sample_token_limit
    assert manifest.release.public_aggregate_candidate is False
    assert {condition.model for condition in manifest.models} == {
        "openrouter/deepseek/deepseek-v4-flash",
        "openrouter/deepseek/deepseek-v4-flash-0731",
    }
    assert all(condition.revision is not None for condition in manifest.models)
    assert all(
        condition.generate_config["reasoning_effort"] == "high" for condition in manifest.models
    )
    assert manifest.model_roles["grader"].revision is not None
    assert manifest.model_roles["grader"].route.provider_only == ["google-vertex/global"]
    for condition in [*manifest.models, *manifest.model_roles.values()]:
        revision = condition.revision
        assert revision is not None
        evidence_path = REPO_ROOT / revision.evidence_path
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        assert sha256_file(evidence_path) == revision.evidence_sha256
        assert evidence["requested_model"] == condition.model.removeprefix("openrouter/")
        assert evidence["canonical_slug"] == revision.canonical_slug
        assert evidence["provider_tag"] == condition.route.provider_only[0]
        assert evidence["zdr_eligible"] is True


def test_model_revision_verifier_reprojects_archived_raw(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = load_manifest(REPO_ROOT / "evals/manifests/diselect-route-preflight-v0.1.json")
    monkeypatch.setattr(
        manifest_module,
        "verify_committed_file",
        lambda path, *args, **kwargs: path,
    )
    verify_model_revision_evidence(manifest, REPO_ROOT)


def test_model_revision_verifier_rejects_hidden_fixed_request_price(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manifest = load_manifest(REPO_ROOT / "evals/manifests/diselect-route-preflight-v0.1.json")
    revision = manifest.models[0].revision
    assert revision is not None and revision.endpoint_response_sha256 is not None
    raw_hash = revision.endpoint_response_sha256
    raw_path = REPO_ROOT / f"evals/model-revisions/provider-responses/{raw_hash}.json"
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    endpoint = next(
        item for item in payload["data"]["endpoints"] if item["tag"] == revision.provider_tag
    )
    endpoint["pricing"]["request"] = "0.50"
    tampered = tmp_path / f"{raw_hash}.json"
    tampered.write_text(json.dumps(payload), encoding="utf-8")
    real_sha256_file = manifest_module.sha256_file

    def fake_committed(path: Path, *args: object, **kwargs: object) -> Path:
        return tampered if path.name == tampered.name else path

    def fake_sha256(path: Path) -> str:
        return raw_hash if path == tampered else real_sha256_file(path)

    monkeypatch.setattr(manifest_module, "verify_committed_file", fake_committed)
    monkeypatch.setattr(manifest_module, "sha256_file", fake_sha256)
    with pytest.raises(ValueError, match="raw endpoint prices do not match"):
        verify_model_revision_evidence(manifest, REPO_ROOT)


def test_openrouter_requires_one_provider_and_no_fallback() -> None:
    base = {
        "condition_id": "test",
        "model": "openrouter/vendor/model-2025-01-01",
        "immutable": True,
        "api_key_env": "OPENROUTER_API_KEY",
        "model_args": {},
        "generate_config": {"seed": 42},
    }
    with pytest.raises(ValidationError, match="exactly one provider"):
        ModelCondition.model_validate({**base, "route": RouteSpec(provider_only=[]).model_dump()})
    with pytest.raises(ValidationError, match="fallbacks must be disabled"):
        ModelCondition.model_validate(
            {
                **base,
                "route": RouteSpec(provider_only=["provider"], allow_fallbacks=True).model_dump(),
            }
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("model_args", {"base_url": "https://example.invalid"}, "model_args are disabled"),
        ("model_args", {"models": ["other/model"]}, "model_args are disabled"),
        (
            "generate_config",
            {"fallback_models": ["openrouter/other/model"]},
            "unsafe or unsupported",
        ),
        (
            "generate_config",
            {"extra_headers": {"Authorization": "secret"}},
            "unsafe or unsupported",
        ),
    ],
)
def test_model_configuration_cannot_redirect_credentials_or_add_fallbacks(
    field: str, value: object, message: str
) -> None:
    payload = {
        "condition_id": "safe-route",
        "model": "openrouter/vendor/model-2025-01-01",
        "immutable": True,
        "api_key_env": "OPENROUTER_API_KEY",
        "route": RouteSpec(provider_only=["exact-provider"]).model_dump(),
        "model_args": {},
        "generate_config": {},
    }
    payload[field] = value
    with pytest.raises(ValidationError, match=message):
        ModelCondition.model_validate(payload)


def test_direct_provider_cannot_select_an_arbitrary_environment_secret() -> None:
    with pytest.raises(ValidationError, match="must use OPENAI_API_KEY"):
        ModelCondition.model_validate(
            {
                "condition_id": "direct-openai",
                "model": "openai/gpt-snapshot",
                "immutable": True,
                "api_key_env": "UNRELATED_SECRET",
                "route": None,
                "model_args": {},
                "generate_config": {},
            }
        )


def test_direct_provider_cannot_select_an_alternate_hosting_mode() -> None:
    with pytest.raises(ValidationError, match="alternate hosting mode"):
        ModelCondition.model_validate(
            {
                "condition_id": "azure-openai",
                "model": "openai/azure/deployment",
                "immutable": True,
                "api_key_env": "OPENAI_API_KEY",
                "route": None,
                "model_args": {},
                "generate_config": {},
            }
        )


def test_runtime_base_url_overrides_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    from atb_eval.manifest import FORBIDDEN_RUNTIME_ENV

    for name in FORBIDDEN_RUNTIME_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.invalid")
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "true")
    assert forbidden_runtime_overrides() == [
        "GOOGLE_GENAI_USE_VERTEXAI",
        "OPENAI_BASE_URL",
    ]


def test_paid_clients_disable_openai_sdk_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    from atb_eval.manifest import FORBIDDEN_RUNTIME_ENV

    for name in FORBIDDEN_RUNTIME_ENV:
        monkeypatch.delenv(name, raising=False)
    conditions = [
        ModelCondition.model_validate(
            {
                "condition_id": "openrouter-no-sdk-retries",
                "model": "openrouter/vendor/model-20250101",
                "immutable": True,
                "api_key_env": "OPENROUTER_API_KEY",
                "route": RouteSpec(provider_only=["pinned-provider"]).model_dump(),
                "model_args": {},
                "generate_config": {"seed": 42},
            }
        ),
        ModelCondition.model_validate(
            {
                "condition_id": "openai-no-sdk-retries",
                "model": "openai/model-20250101",
                "immutable": True,
                "api_key_env": "OPENAI_API_KEY",
                "route": None,
                "openai_api_mode": "chat_completions",
                "model_args": {},
                "generate_config": {"seed": 42},
            }
        ),
    ]
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    for condition in conditions:
        model = build_model(condition, run_max_connections=1, max_retries=0)
        assert condition.inspect_model_args()["max_retries"] == 0
        assert model.api.client.max_retries == 0
        if condition.model.startswith("openrouter/"):
            assert model.config.extra_headers == {"X-OpenRouter-Metadata": "enabled"}


def test_logs_inside_repo_are_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(ValueError, match="outside"):
        require_controlled_log_dir(repo / "logs/run", repo)
    assert (
        require_controlled_log_dir(tmp_path / "controlled/run", repo)
        == (tmp_path / "controlled/run").resolve()
    )


def test_controlled_log_permissions_fail_closed(tmp_path: Path) -> None:
    controlled = tmp_path / "controlled"
    ensure_private_permissions(controlled, create=True)
    assert controlled.stat().st_mode & 0o777 == 0o700
    exposed = controlled / "exposed.eval"
    exposed.write_text("fixture", encoding="utf-8")
    exposed.chmod(0o644)
    with pytest.raises(ValueError, match="group/other"):
        ensure_private_permissions(controlled, create=False)


def test_run_fingerprint_binds_manifest_lock_and_commit() -> None:
    provenance = {
        "code_commit": "b" * 40,
        "code_dirty": False,
        "environment_lock_sha256": "c" * 64,
    }
    baseline = run_fingerprint("a" * 64, provenance)
    assert run_fingerprint("d" * 64, provenance) != baseline
    assert (
        run_fingerprint("a" * 64, {**provenance, "environment_lock_sha256": "e" * 64}) != baseline
    )
    assert run_fingerprint("a" * 64, {**provenance, "code_commit": "f" * 40}) != baseline


def test_route_check_uses_served_model_and_openrouter_provider() -> None:
    condition = ModelCondition.model_validate(
        {
            "condition_id": "route-a",
            "model": "openrouter/vendor/model-2025-01-01",
            "immutable": True,
            "api_key_env": "OPENROUTER_API_KEY",
            "route": RouteSpec(provider_only=["pinned-provider"]).model_dump(),
            "revision": {
                "resolved_model": "vendor/model-2025-01-01",
                "canonical_slug": "vendor/model-2025-01-01-canonical",
                "inventory_model_id": "vendor/model-2025-01-01",
                "endpoint_model_id": "vendor/model-2025-01-01",
                "endpoint_name": "Pinned Provider | vendor/model-2025-01-01",
                "provider_name": "Pinned Provider",
                "provider_tag": "pinned-provider",
                "quantization": "unknown",
                "supported_parameters": [],
                "observed_at": "2026-08-12T00:00:00Z",
                "source_url": "https://openrouter.ai/api/v1/models/vendor/model/endpoints",
                "evidence_path": "evals/model-revisions/test-fixture.json",
                "evidence_sha256": "a" * 64,
            },
            "model_args": {},
            "generate_config": {},
        }
    )
    event = type("ModelEvent", (), {})()
    event.model = condition.model
    event.role = None
    event.output = SimpleNamespace(model="vendor/model-2025-01-01", fallback=None)
    event.call = SimpleNamespace(
        response={
            "model": "vendor/model-2025-01-01",
            "provider": "Pinned Provider",
            "openrouter_metadata": {
                "requested": "vendor/model-2025-01-01",
                "strategy": "direct",
                "attempt": 1,
                "is_byok": False,
                "endpoints": {
                    "total": 1,
                    "available": [
                        {
                            "provider": "Pinned Provider",
                            "model": "vendor/model-2025-01-01-canonical",
                            "selected": True,
                        }
                    ],
                },
                "attempts": [
                    {
                        "provider": "Pinned Provider",
                        "model": "vendor/model-2025-01-01-canonical",
                        "status": 200,
                    }
                ],
            },
        }
    )
    sample = SimpleNamespace(events=[event])
    assert condition.inspect_model_args()["provider"]["only"] == ["pinned-provider"]
    assert "order" not in condition.inspect_model_args()["provider"]
    assert sample_routes_match(sample, condition)
    event.call.response["openrouter_metadata"]["endpoints"]["available"][0]["model"] = (
        "vendor/model-2025-01-01"
    )
    assert not sample_routes_match(sample, condition)
    event.call.response["openrouter_metadata"]["endpoints"]["available"][0]["model"] = (
        "vendor/model-2025-01-01-canonical"
    )
    event.call.response["openrouter_metadata"]["attempts"][0]["model"] = "vendor/model-2025-01-01"
    assert not sample_routes_match(sample, condition)
    event.call.response["openrouter_metadata"]["attempts"][0]["model"] = (
        "vendor/model-2025-01-01-canonical"
    )
    event.call.response["openrouter_metadata"]["attempt"] = 2
    assert not sample_routes_match(sample, condition)


def test_openrouter_adapter_preserves_additive_router_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from atb_eval.manifest import FORBIDDEN_RUNTIME_ENV

    for name in FORBIDDEN_RUNTIME_ENV:
        monkeypatch.delenv(name, raising=False)
    condition = ModelCondition.model_validate(
        {
            "condition_id": "deepseek-0423-adapter",
            "model": "openrouter/deepseek/deepseek-v4-flash",
            "immutable": True,
            "api_key_env": "OPENROUTER_API_KEY",
            "route": {
                "provider_only": ["deepinfra/fp4"],
                "allow_fallbacks": False,
                "require_parameters": True,
                "data_collection": "deny",
                "zdr": True,
                "quantizations": ["fp4"],
                "max_price": {"prompt": 0.09, "completion": 0.18, "request": 0.0},
            },
            "revision": {
                "resolved_model": "deepseek/deepseek-v4-flash",
                "canonical_slug": "deepseek/deepseek-v4-flash-20260423",
                "inventory_model_id": "deepseek/deepseek-v4-flash",
                "endpoint_model_id": "deepseek/deepseek-v4-flash",
                "endpoint_name": "DeepInfra | deepseek/deepseek-v4-flash-20260423",
                "provider_name": "DeepInfra",
                "provider_tag": "deepinfra/fp4",
                "quantization": "fp4",
                "supported_parameters": ["max_tokens", "seed", "temperature", "top_p"],
                "observed_at": "2026-08-12T00:00:00Z",
                "source_url": (
                    "https://openrouter.ai/api/v1/models/deepseek/deepseek-v4-flash/endpoints"
                ),
                "evidence_path": "evals/model-revisions/test-fixture.json",
                "evidence_sha256": "a" * 64,
            },
            "model_args": {},
            "generate_config": {"seed": 42, "top_p": 0.95},
        }
    )
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "id": "gen-test",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "index": 0,
                        "message": {"content": "ok", "role": "assistant"},
                    }
                ],
                "created": 1,
                "model": "deepseek/deepseek-v4-flash",
                "object": "chat.completion",
                "provider": "DeepInfra",
                "usage": {
                    "completion_tokens": 1,
                    "prompt_tokens": 1,
                    "total_tokens": 2,
                    "cost": 0.0001,
                },
                "openrouter_metadata": {
                    "requested": "deepseek/deepseek-v4-flash",
                    "strategy": "direct",
                    "region": "iad",
                    "attempt": 1,
                    "is_byok": False,
                    "endpoints": {
                        "total": 1,
                        "available": [
                            {
                                "provider": "DeepInfra",
                                "model": "deepseek/deepseek-v4-flash-20260423",
                                "selected": True,
                                "future_additive_field": "accepted",
                            }
                        ],
                    },
                    "attempts": [
                        {
                            "provider": "DeepInfra",
                            "model": "deepseek/deepseek-v4-flash-20260423",
                            "status": 200,
                            "future_additive_field": "accepted",
                        }
                    ],
                },
            },
        )

    async def generate() -> object:
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            model = get_model(
                condition.model,
                api_key="test-only",
                http_client=client,
                max_retries=0,
                provider=condition.inspect_model_args()["provider"],
                config=GenerateConfig(
                    seed=42,
                    top_p=0.95,
                    extra_headers={"X-OpenRouter-Metadata": "enabled"},
                ),
            )
            return await model.api.generate(
                [ChatMessageUser(content="hello")], [], "none", model.config
            )
        finally:
            await client.aclose()

    output, call = asyncio.run(generate())
    body = captured["body"]
    headers = captured["headers"]
    assert isinstance(body, dict)
    assert isinstance(headers, dict)
    assert body["model"] == "deepseek/deepseek-v4-flash"
    assert body["provider"] == condition.inspect_model_args()["provider"]
    assert headers["x-openrouter-metadata"] == "enabled"
    assert call.request["extra_headers"]["X-OpenRouter-Metadata"] == "enabled"
    assert output.model == "deepseek/deepseek-v4-flash"
    response = call.response
    assert openrouter_route_metadata_matches(response, condition)
    response["model"] = "deepseek/deepseek-v4-flash-20260423"
    assert not openrouter_route_metadata_matches(response, condition)
    response["model"] = "deepseek/deepseek-v4-flash"
    response["openrouter_metadata"]["endpoints"]["available"][0]["model"] = (
        "deepseek/deepseek-v4-flash"
    )
    assert not openrouter_route_metadata_matches(response, condition)
    response["openrouter_metadata"]["endpoints"]["available"][0]["model"] = (
        "deepseek/deepseek-v4-flash-20260423"
    )
    response["openrouter_metadata"]["attempts"][0]["model"] = "deepseek/deepseek-v4-flash"
    assert not openrouter_route_metadata_matches(response, condition)
    response["openrouter_metadata"]["attempts"][0]["model"] = "deepseek/deepseek-v4-flash-20260423"
    response["openrouter_metadata"]["attempts"][0]["status"] = 429
    assert not openrouter_route_metadata_matches(response, condition)
    response["openrouter_metadata"]["attempts"][0]["status"] = 200
    response["openrouter_metadata"].pop("attempts")
    assert openrouter_route_metadata_matches(response, condition)
    response["openrouter_metadata"]["attempt"] = True
    assert not openrouter_route_metadata_matches(response, condition)


def test_route_check_binds_each_model_event_to_its_role() -> None:
    target = ModelCondition.model_validate(
        {
            "condition_id": "target",
            "model": "openai/target-2025-01-01",
            "immutable": True,
            "api_key_env": "OPENAI_API_KEY",
            "route": None,
            "openai_api_mode": "chat_completions",
            "model_args": {},
            "generate_config": {},
        }
    )
    grader = ModelCondition.model_validate(
        {
            "condition_id": "grader",
            "model": "openai/grader-2025-01-01",
            "immutable": True,
            "api_key_env": "OPENAI_API_KEY",
            "route": None,
            "openai_api_mode": "chat_completions",
            "model_args": {},
            "generate_config": {},
        }
    )
    target_event = type("ModelEvent", (), {})()
    target_event.role = None
    target_event.model = target.model
    target_event.output = SimpleNamespace(model="target-2025-01-01", fallback=None)
    target_event.call = None
    sample = SimpleNamespace(events=[target_event])
    assert not sample_routes_match(sample, target, {"grader": grader}, required_roles={"grader"})

    grader_event = type("ModelEvent", (), {})()
    grader_event.role = "grader"
    grader_event.model = target.model
    grader_event.output = SimpleNamespace(model="target-2025-01-01", fallback=None)
    grader_event.call = None
    sample.events.append(grader_event)
    assert not sample_routes_match(sample, target, {"grader": grader}, required_roles={"grader"})

    grader_event.model = grader.model
    grader_event.output.model = "grader-2025-01-01"
    assert sample_routes_match(sample, target, {"grader": grader}, required_roles={"grader"})


def test_sample_output_is_bound_to_the_target_model_event() -> None:
    event = type("ModelEvent", (), {})()
    event.role = None
    event.output = SimpleNamespace(
        model="target-2025-01-01",
        completion="original",
        stop_reason="stop",
        error=None,
    )
    sample = SimpleNamespace(
        events=[event],
        output=SimpleNamespace(
            model="target-2025-01-01",
            completion="original",
            stop_reason="stop",
            error=None,
        ),
    )
    assert sample_target_output_matches(sample)
    sample.output.completion = "invented"
    assert not sample_target_output_matches(sample)


def test_postflight_resolves_nested_output_attachments_fail_closed(tmp_path: Path) -> None:
    def output(reasoning: str) -> ModelOutput:
        return ModelOutput(
            model="vendor/model-2025-01-01",
            completion="answer",
            choices=[
                ChatCompletionChoice(
                    message=ChatMessageAssistant(
                        id="fixed-message-id",
                        content=[
                            ContentReasoning(reasoning=reasoning),
                            ContentText(text="answer"),
                        ],
                    ),
                    stop_reason="stop",
                )
            ],
        )

    def write_fixture(
        path: Path,
        attachments: dict[str, str],
        sample_reasoning: str = "private chain",
    ) -> None:
        event = ModelEvent(
            model="openrouter/vendor/model-2025-01-01",
            role=None,
            input=[],
            tools=[],
            tool_choice="none",
            config=GenerateConfig(),
            output=output("attachment://reasoning"),
        )
        sample = EvalSample(
            id="fixture",
            epoch=1,
            input="request",
            target="",
            events=[event],
            output=output(sample_reasoning),
            attachments=attachments,
        )
        spec = EvalSpec(
            created="2026-08-12T00:00:00Z",
            task="fixture",
            dataset=EvalDataset(samples=1),
            model="openrouter/vendor/model-2025-01-01",
            config=EvalConfig(),
        )
        write_eval_log(EvalLog(status="success", eval=spec, samples=[sample]), path)

    valid_path = tmp_path / "valid.eval"
    write_fixture(valid_path, {"reasoning": "private chain"})
    valid_sample = read_postflight_log(valid_path).samples[0]
    assert valid_sample.attachments == {}
    assert sample_target_output_matches(valid_sample)

    missing_path = tmp_path / "missing.eval"
    write_fixture(missing_path, {}, sample_reasoning="attachment://reasoning")
    assert not sample_target_output_matches(read_postflight_log(missing_path).samples[0])

    tampered_path = tmp_path / "tampered.eval"
    write_fixture(tampered_path, {"reasoning": "tampered chain"})
    assert not sample_target_output_matches(read_postflight_log(tampered_path).samples[0])


def test_diselect_model_inputs_are_bound_to_task_and_grader_prompts() -> None:
    from atb_eval.scorers import RESPONSE_CLASS_PROMPT

    target = ModelCondition.model_validate(
        {
            "condition_id": "target",
            "model": "mockllm/model",
            "immutable": True,
            "model_args": {},
            "generate_config": {},
        }
    )
    grader = ModelCondition.model_validate(
        {
            "condition_id": "grader",
            "model": "mockllm/model",
            "immutable": True,
            "model_args": {},
            "generate_config": {},
        }
    )
    target_event = type("ModelEvent", (), {})()
    target_event.role = None
    target_event.input = [
        SimpleNamespace(role="system", content="You are a helpful assistant."),
        SimpleNamespace(role="user", content="frozen request"),
    ]
    grader_event = type("ModelEvent", (), {})()
    grader_event.role = "grader"
    grader_event.input = [
        SimpleNamespace(
            role="user",
            content=RESPONSE_CLASS_PROMPT.format(
                request="frozen request", response="target response"
            ),
        )
    ]
    sample = SimpleNamespace(
        input="frozen request",
        output=SimpleNamespace(completion="target response", error=None, stop_reason="stop"),
        error=None,
        events=[target_event, grader_event],
        metadata={"applicable_axes": ["diselect_response_class"]},
        attachments={},
    )
    manifest = SimpleNamespace(
        task=SimpleNamespace(kind="diselect", args={"include_actionability": False}),
        model_roles={"grader": grader},
    )
    assert sample_model_inputs_match(sample, target, manifest)
    target_event.input[1].content = "different request"
    assert not sample_model_inputs_match(sample, target, manifest)


def test_provider_request_messages_reject_extra_semantic_fields() -> None:
    from atb_eval.runner import _event_messages_match
    from inspect_ai.model import ChatMessageUser

    condition = ModelCondition.model_validate(
        {
            "condition_id": "direct-openai-message-shape",
            "model": "openai/model-20250101",
            "immutable": True,
            "api_key_env": "OPENAI_API_KEY",
            "openai_api_mode": "chat_completions",
            "model_args": {},
            "generate_config": {},
        }
    )
    event = SimpleNamespace(
        input=[ChatMessageUser(content="exact prompt")],
        call=SimpleNamespace(
            request={
                "messages": [{"role": "user", "content": "exact prompt", "name": "injected-name"}]
            }
        ),
    )
    sample = SimpleNamespace(attachments={})
    assert not _event_messages_match(
        event,
        (("user", "exact prompt"),),
        sample,
        condition,
    )


@pytest.mark.parametrize(
    "model",
    [
        "openai/gpt-4o",
        "openai/gpt-4o-latest-2024",
        "openai/model-free-2025",
    ],
)
def test_immutable_condition_rejects_mutable_alias(model: str) -> None:
    with pytest.raises(ValidationError, match=r"mutable (model aliases|aliases are forbidden)"):
        ModelCondition.model_validate(
            {
                "condition_id": "alias",
                "model": model,
                "immutable": True,
                "api_key_env": "OPENAI_API_KEY",
                "route": None,
                "openai_api_mode": "chat_completions",
                "model_args": {},
                "generate_config": {},
            }
        )


def test_request_parameters_are_verified_against_the_provider_payload() -> None:
    condition = ModelCondition.model_validate(_paid_condition("request-contract"))
    expected = {"seed": 42, "temperature": 0.0, "max_tokens": 700}
    request = {
        "model": "gpt-test-2025-01-01",
        "messages": [],
        "extra_headers": {"x-irid": "request-id"},
        "seed": 42,
        "temperature": 0.0,
        "max_tokens": 700,
    }
    assert request_parameters_match(request, condition, expected)
    missing_seed = dict(request)
    missing_seed.pop("seed")
    assert not request_parameters_match(missing_seed, condition, expected)
    unexpected_top_p = {**request, "top_p": 0.01}
    assert not request_parameters_match(unexpected_top_p, condition, expected)
    unexpected_reasoning = {**request, "reasoning_effort": "high"}
    assert not request_parameters_match(unexpected_reasoning, condition, expected)
    assert not request_parameters_match({**request, "store": True}, condition, expected)
    assert not request_parameters_match(
        {**request, "tools": [{"type": "function"}]}, condition, expected
    )


def test_openrouter_reasoning_parameters_are_verified_in_extra_body() -> None:
    condition = ModelCondition.model_validate(
        {
            "condition_id": "openrouter-reasoning",
            "model": "openrouter/openai/gpt-5-2025-08-07",
            "immutable": True,
            "api_key_env": "OPENROUTER_API_KEY",
            "route": RouteSpec(provider_only=["openai"]).model_dump(),
            "model_args": {},
            "generate_config": {"reasoning_effort": "max", "seed": 42},
        }
    )
    expected = {"reasoning_effort": "max", "seed": 42}
    request = {
        "model": "openai/gpt-5-2025-08-07",
        "messages": [],
        "extra_headers": {
            "x-irid": "request-id",
            "X-OpenRouter-Metadata": "enabled",
        },
        "seed": 42,
        "extra_body": {
            "provider": condition.inspect_model_args()["provider"],
            "reasoning": {"effort": "xhigh"},
        },
    }
    assert request_parameters_match(request, condition, expected)
    request["extra_body"]["reasoning"]["effort"] = "high"
    assert not request_parameters_match(request, condition, expected)


def test_openrouter_reasoning_token_budget_is_verified() -> None:
    condition = ModelCondition.model_validate(
        {
            "condition_id": "openrouter-reasoning-tokens",
            "model": "openrouter/vendor/model-2025-01-01",
            "immutable": True,
            "api_key_env": "OPENROUTER_API_KEY",
            "route": RouteSpec(provider_only=["pinned-provider"]).model_dump(),
            "model_args": {},
            "generate_config": {"reasoning_tokens": 1234, "seed": 42},
        }
    )
    expected = {"reasoning_tokens": 1234, "seed": 42}
    assert request_parameters_match(
        {
            "model": "vendor/model-2025-01-01",
            "messages": [],
            "extra_headers": {
                "x-irid": "request-id",
                "X-OpenRouter-Metadata": "enabled",
            },
            "seed": 42,
            "extra_body": {
                "provider": condition.inspect_model_args()["provider"],
                "reasoning": {"max_tokens": 1234},
            },
        },
        condition,
        expected,
    )
    assert not request_parameters_match(
        {
            "model": "vendor/model-2025-01-01",
            "messages": [],
            "extra_headers": {
                "x-irid": "request-id",
                "X-OpenRouter-Metadata": "enabled",
            },
            "seed": 42,
            "extra_body": {"provider": condition.inspect_model_args()["provider"]},
        },
        condition,
        expected,
    )


def test_openrouter_top_k_is_logged_and_transmitted_in_extra_body() -> None:
    condition = ModelCondition.model_validate(
        {
            "condition_id": "openrouter-top-k",
            "model": "openrouter/vendor/model-2025-01-01",
            "immutable": True,
            "api_key_env": "OPENROUTER_API_KEY",
            "route": RouteSpec(provider_only=["pinned-provider"]).model_dump(),
            "model_args": {},
            "generate_config": {"seed": 42, "top_k": 40, "top_p": 0.95},
        }
    )
    expected = {"seed": 42, "top_k": 40, "top_p": 0.95, "extra_body": {"top_k": 40}}
    request = {
        "model": "vendor/model-2025-01-01",
        "messages": [],
        "extra_headers": {
            "x-irid": "request-id",
            "X-OpenRouter-Metadata": "enabled",
        },
        "seed": 42,
        "top_p": 0.95,
        "extra_body": {
            "provider": condition.inspect_model_args()["provider"],
            "top_k": 40,
        },
    }
    assert request_parameters_match(request, condition, expected)
    request["extra_body"]["top_k"] = 20
    assert not request_parameters_match(request, condition, expected)


@pytest.mark.parametrize("top_k", [0, -1, 1.5, True])
def test_openrouter_top_k_must_be_a_positive_integer(top_k: object) -> None:
    with pytest.raises(ValidationError, match="top_k must be a positive integer"):
        ModelCondition.model_validate(
            {
                "condition_id": "openrouter-top-k",
                "model": "openrouter/vendor/model-2025-01-01",
                "immutable": True,
                "api_key_env": "OPENROUTER_API_KEY",
                "route": RouteSpec(provider_only=["pinned-provider"]).model_dump(),
                "model_args": {},
                "generate_config": {"seed": 42, "top_k": top_k},
            }
        )


def test_mistral_rejects_ambiguous_reasoning_effort() -> None:
    payload = {
        "condition_id": "mistral-reasoning",
        "model": "mistral/model-2025-01-01",
        "immutable": True,
        "api_key_env": "MISTRAL_API_KEY",
        "route": None,
        "model_args": {},
        "generate_config": {"reasoning_effort": "low", "seed": 42},
    }
    with pytest.raises(ValidationError, match="normalizes every non-none"):
        ModelCondition.model_validate(payload)


def test_source_checkout_inside_repo_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    source = repo / "controlled-source"
    source.mkdir(parents=True)
    with pytest.raises(ValueError, match="DisElect source checkout must be stored outside"):
        require_path_outside_repo(source, repo, "DisElect source checkout")


def test_external_manifest_cannot_be_treated_as_committed(tmp_path: Path) -> None:
    external = tmp_path / "manifest.json"
    external.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="committed file inside"):
        verify_committed_file(external, REPO_ROOT, "protocol manifest")


def test_runner_resolves_the_repository_root() -> None:
    assert repository_root() == REPO_ROOT


def test_manifests_do_not_contain_secret_fields() -> None:
    def assert_no_secret_key(value: object) -> None:
        if isinstance(value, dict):
            assert "api_key" not in value
            for child in value.values():
                assert_no_secret_key(child)
        elif isinstance(value, list):
            for child in value:
                assert_no_secret_key(child)

    for path in (REPO_ROOT / "evals/manifests").glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert_no_secret_key(payload)
        text = json.dumps(payload).lower()
        assert "sk-or-v1-" not in text


def _paid_condition(condition_id: str, *, max_tokens: int | None = None) -> dict:
    condition = {
        "condition_id": condition_id,
        "model": "openai/gpt-test-2025-01-01",
        "immutable": True,
        "api_key_env": "OPENAI_API_KEY",
        "route": None,
        "openai_api_mode": "chat_completions",
        "revision": {
            "resolved_model": "gpt-test-2025-01-01",
            "observed_at": "2026-08-12T00:00:00Z",
            "source_url": "https://api.openai.com/v1/models",
            "evidence_path": "evals/model-revisions/test-fixture.json",
            "evidence_sha256": "a" * 64,
        },
        "pricing": {
            "input": 2.0,
            "output": 8.0,
            "input_cache_write": 2.0,
            "input_cache_read": 0.5,
        },
        "model_args": {},
        "generate_config": {"seed": 42},
    }
    if max_tokens is not None:
        condition["generate_config"]["max_tokens"] = max_tokens
    return condition


def _openrouter_condition(condition_id: str, *, max_tokens: int | None = None) -> dict:
    condition = _paid_condition(condition_id, max_tokens=max_tokens)
    condition.update(
        {
            "model": "openrouter/openai/gpt-test-2025-01-01",
            "api_key_env": "OPENROUTER_API_KEY",
            "openai_api_mode": None,
            "route": {
                "provider_only": ["openai/fp4"],
                "allow_fallbacks": False,
                "require_parameters": True,
                "data_collection": "deny",
                "zdr": True,
                "quantizations": ["fp4"],
                "max_price": {"prompt": 2.0, "completion": 8.0, "request": 0.0},
            },
        }
    )
    condition["revision"].update(
        {
            "canonical_slug": "openai/gpt-test-20250101",
            "resolved_model": "openai/gpt-test-2025-01-01",
            "inventory_model_id": "openai/gpt-test-2025-01-01",
            "endpoint_model_id": "openai/gpt-test-2025-01-01",
            "endpoint_name": "OpenAI | openai/gpt-test-2025-01-01",
            "provider_name": "OpenAI",
            "provider_tag": "openai/fp4",
            "quantization": "fp4",
            "source_url": (
                "https://openrouter.ai/api/v1/models/openai/gpt-test-2025-01-01/endpoints"
            ),
            "model_source_url": ("https://openrouter.ai/api/v1/model/openai/gpt-test-2025-01-01"),
            "model_response_sha256": "b" * 64,
            "models_source_url": "https://openrouter.ai/api/v1/models",
            "models_response_sha256": "c" * 64,
            "endpoint_response_sha256": "d" * 64,
            "zdr_source_url": "https://openrouter.ai/api/v1/endpoints/zdr",
            "zdr_response_sha256": "e" * 64,
            "zdr_eligible": True,
            "supported_parameters": [
                "max_tokens",
                "reasoning",
                "reasoning_effort",
                "seed",
                "temperature",
            ],
            "supported_reasoning_efforts": ["high", "minimal"],
            "max_completion_tokens": 4096,
            "request_price_usd": 0.0,
            "internal_reasoning_price_usd_per_million": 0.0,
        }
    )
    return condition


def _frozen_diselect_payload() -> dict:
    payload = json.loads(
        (REPO_ROOT / "evals/manifests/diselect-wave1a-v0.1.json").read_text(encoding="utf-8")
    )
    grader = _paid_condition("role-grader", max_tokens=700)
    grader["generate_config"]["temperature"] = 0.0
    payload.update(
        {
            "status": "frozen",
            "frozen_at": "2026-08-12T00:00:00Z",
            "models": [_paid_condition("target")],
            "model_roles": {"grader": grader},
        }
    )
    payload["run"]["provider_key_limit_usd"] = 10.0
    return payload


def test_same_model_sensitivity_conditions_keep_distinct_identities() -> None:
    payload = json.loads(
        (REPO_ROOT / "evals/manifests/diselect-wave1a-v0.1.json").read_text(encoding="utf-8")
    )
    first = _paid_condition("target-reasoning-low")
    second = _paid_condition("target-reasoning-high")
    first["generate_config"]["reasoning_effort"] = "low"
    second["generate_config"]["reasoning_effort"] = "high"
    payload["models"] = [first, second]
    manifest = ProtocolManifest.model_validate(payload)
    assert set(condition_map(manifest)) == {
        "target-reasoning-low",
        "target-reasoning-high",
    }
    assert len(set(condition_map(manifest).values())) == 2

    duplicate = _paid_condition("duplicate")
    duplicate["generate_config"]["reasoning_effort"] = "low"
    payload["models"] = [first, duplicate]
    with pytest.raises(ValidationError, match="unique model, route, and generation"):
        ProtocolManifest.model_validate(payload)


def test_condition_cannot_claim_a_task_overridden_generation_setting() -> None:
    payload = json.loads(
        (REPO_ROOT / "evals/manifests/diselect-wave1a-v0.1.json").read_text(encoding="utf-8")
    )
    condition = _paid_condition("shadowed-temperature")
    condition["generate_config"]["temperature"] = 1.0
    payload["models"] = [condition]
    with pytest.raises(ValidationError, match="cannot shadow task-owned settings"):
        ProtocolManifest.model_validate(payload)


def test_route_check_rejects_effective_event_config_drift() -> None:
    manifest = load_manifest(REPO_ROOT / "evals/manifests/inspect-canary-v0.1.json")
    condition = manifest.models[0]
    expected = effective_event_generate_config(condition, manifest)
    event = type("ModelEvent", (), {})()
    event.role = None
    event.model = condition.model
    event.output = SimpleNamespace(model="mockllm", fallback=None)
    event.call = None
    event.config = GenerateConfig(**expected)
    sample = SimpleNamespace(events=[event])
    assert sample_routes_match(sample, condition, manifest=manifest)
    event.config = GenerateConfig(**{**expected, "seed": 99})
    assert not sample_routes_match(sample, condition, manifest=manifest)


def test_native_ape_cannot_freeze_before_transcript_attribution_verifier() -> None:
    payload = json.loads(
        (REPO_ROOT / "evals/manifests/ape-turn1-template-v0.1.json").read_text(encoding="utf-8")
    )
    payload.update(
        {
            "status": "frozen",
            "frozen_at": "2026-08-12T00:00:00Z",
            "models": [_paid_condition("target", max_tokens=700)],
        }
    )
    with pytest.raises(ValidationError, match="draft-only"):
        ProtocolManifest.model_validate(payload)


def test_frozen_paid_protocol_requires_model_revision_evidence() -> None:
    payload = _frozen_diselect_payload()
    payload["model_roles"]["grader"].pop("revision")
    with pytest.raises(ValidationError, match="committed model revision evidence"):
        ProtocolManifest.model_validate(payload)


def test_public_diselect_validation_cannot_weaken_the_critical_class_gate() -> None:
    payload = _frozen_diselect_payload()
    payload["release"]["public_aggregate_candidate"] = True
    payload["validation"]["critical_class"] = "not-a-native-class"
    payload["validation"]["critical_f1_min"] = 0.0
    with pytest.raises(ValidationError, match=r"comply F1 >= 0\.75"):
        ProtocolManifest.model_validate(payload)


def test_frozen_run_budget_is_a_conservative_per_sample_envelope() -> None:
    payload = _frozen_diselect_payload()
    payload["run"]["planned_run_cost_envelope_usd"] = 2.49
    with pytest.raises(ValidationError, match="cost limit exceeds"):
        ProtocolManifest.model_validate(payload)


def test_frozen_confirmatory_manifest_rejects_task_retries() -> None:
    payload = _frozen_diselect_payload()
    payload["run"]["retry_attempts"] = 1
    with pytest.raises(ValidationError, match="disables task retries"):
        ProtocolManifest.model_validate(payload)


def test_frozen_direct_openai_fixed_temperature_family_fails_before_spend() -> None:
    payload = _frozen_diselect_payload()
    target = _paid_condition("target")
    target["model"] = "openai/gpt-5-2025-08-07"
    target["revision"]["resolved_model"] = "gpt-5-2025-08-07"
    payload["models"] = [target]
    with pytest.raises(ValidationError, match="removes their temperature request"):
        ProtocolManifest.model_validate(payload)


def test_frozen_openrouter_requires_privacy_quantization_and_price_caps() -> None:
    payload = _frozen_diselect_payload()
    target = _openrouter_condition("target")
    grader = _openrouter_condition("role-grader", max_tokens=700)
    grader["generate_config"]["temperature"] = 0.0
    payload["models"] = [target]
    payload["model_roles"] = {"grader": grader}

    manifest = ProtocolManifest.model_validate(payload)
    provider = manifest.models[0].inspect_model_args()["provider"]
    assert provider["zdr"] is True
    assert provider["quantizations"] == ["fp4"]
    assert provider["max_price"] == {"prompt": 2.0, "completion": 8.0, "request": 0.0}

    expected = {"seed": 42, "temperature": 0.0, "max_tokens": 700}
    request = {
        "model": "openai/gpt-test-2025-01-01",
        "messages": [],
        "extra_headers": {
            "x-irid": "request-id",
            "X-OpenRouter-Metadata": "enabled",
        },
        "seed": 42,
        "temperature": 0.0,
        "max_tokens": 700,
        "extra_body": {"provider": provider},
    }
    assert request_parameters_match(request, manifest.models[0], expected)
    wrong_route = json.loads(json.dumps(request))
    wrong_route["extra_body"]["provider"]["quantizations"] = ["fp8"]
    assert not request_parameters_match(wrong_route, manifest.models[0], expected)

    for key, value in (
        ("zdr", False),
        ("data_collection", "allow"),
        ("quantizations", []),
        ("quantizations", ["fp4", "fp8"]),
        ("max_price", None),
    ):
        invalid = json.loads(json.dumps(payload))
        invalid["models"][0]["route"][key] = value
        with pytest.raises(ValidationError, match="deny, ZDR, one quantization, and max_price"):
            ProtocolManifest.model_validate(invalid)


def test_frozen_openrouter_price_cap_cannot_undercut_inspect_pricing() -> None:
    payload = _frozen_diselect_payload()
    target = _openrouter_condition("target")
    target["route"]["max_price"]["completion"] = 7.99
    grader = _openrouter_condition("role-grader", max_tokens=700)
    grader["generate_config"]["temperature"] = 0.0
    payload["models"] = [target]
    payload["model_roles"] = {"grader": grader}
    with pytest.raises(ValidationError, match="cannot be lower"):
        ProtocolManifest.model_validate(payload)


def test_frozen_openrouter_rejects_nonzero_fixed_request_prices() -> None:
    payload = _frozen_diselect_payload()
    target = _openrouter_condition("target")
    target["route"]["max_price"]["request"] = 0.01
    target["revision"]["request_price_usd"] = 0.01
    grader = _openrouter_condition("role-grader", max_tokens=700)
    grader["generate_config"]["temperature"] = 0.0
    payload["models"] = [target]
    payload["model_roles"] = {"grader": grader}
    with pytest.raises(ValidationError, match="reject fixed request prices"):
        ProtocolManifest.model_validate(payload)


def test_frozen_openrouter_binds_reasoning_effort_domain() -> None:
    payload = _frozen_diselect_payload()
    target = _openrouter_condition("target")
    target["generate_config"]["reasoning_effort"] = "minimal"
    target["revision"]["supported_reasoning_efforts"] = ["high"]
    grader = _openrouter_condition("role-grader", max_tokens=700)
    grader["generate_config"]["temperature"] = 0.0
    payload["models"] = [target]
    payload["model_roles"] = {"grader": grader}
    with pytest.raises(ValidationError, match="does not support the frozen reasoning effort"):
        ProtocolManifest.model_validate(payload)


def test_frozen_openrouter_binds_completion_token_limit() -> None:
    payload = _frozen_diselect_payload()
    target = _openrouter_condition("target")
    target["revision"]["max_completion_tokens"] = 699
    grader = _openrouter_condition("role-grader", max_tokens=700)
    grader["generate_config"]["temperature"] = 0.0
    payload["models"] = [target]
    payload["model_roles"] = {"grader": grader}
    with pytest.raises(ValidationError, match="completion-token limit"):
        ProtocolManifest.model_validate(payload)


def test_frozen_openrouter_revision_joins_exact_inventory_and_endpoint_ids() -> None:
    payload = _frozen_diselect_payload()
    target = _openrouter_condition("target")
    grader = _openrouter_condition("role-grader", max_tokens=700)
    grader["generate_config"]["temperature"] = 0.0
    payload["models"] = [target]
    payload["model_roles"] = {"grader": grader}

    wrong_inventory = json.loads(json.dumps(payload))
    wrong_inventory["models"][0]["revision"]["inventory_model_id"] = "other/model"
    with pytest.raises(ValidationError, match="inventory, and endpoint ids"):
        ProtocolManifest.model_validate(wrong_inventory)

    wrong_source = json.loads(json.dumps(payload))
    wrong_source["models"][0]["revision"]["source_url"] = (
        "https://openrouter.ai/api/v1/models/other/model/endpoints"
    )
    with pytest.raises(ValidationError, match="requested snapshot inventory"):
        ProtocolManifest.model_validate(wrong_source)


def test_model_cost_config_is_explicit_and_consistent() -> None:
    payload = _frozen_diselect_payload()
    manifest = ProtocolManifest.model_validate(payload)
    costs = model_cost_config(manifest)
    assert costs is not None
    assert set(costs) == {"openai/gpt-test-2025-01-01"}
    assert costs["openai/gpt-test-2025-01-01"].input == 2.0
    assert costs["openai/gpt-test-2025-01-01"].output == 8.0

    payload["model_roles"]["grader"]["pricing"]["output"] = 9.0
    with pytest.raises(ValidationError, match="identical Inspect pricing"):
        ProtocolManifest.model_validate(payload)


def _score_contract_sample(
    *,
    native_class: str = "comply",
    subset: str = "harmful",
    instrument_failure: str | None = None,
) -> SimpleNamespace:
    target = type("ModelEvent", (), {})()
    target.role = None
    target.output = SimpleNamespace(error=None, stop_reason="stop", completion="target answer")
    events = [target]
    if instrument_failure in {
        "target_model_error",
        "provider_or_policy_block",
        "truncated",
        "empty_response",
    }:
        if instrument_failure == "target_model_error":
            target.output.error = "provider error"
        elif instrument_failure == "provider_or_policy_block":
            target.output.stop_reason = "content_filter"
        elif instrument_failure == "truncated":
            target.output.stop_reason = "max_tokens"
        else:
            target.output.completion = ""
        score = Score.unscored(metadata={"instrument_failure": instrument_failure})
    else:
        grader = type("ModelEvent", (), {})()
        grader.role = "grader"
        grader.output = SimpleNamespace(
            error=None,
            stop_reason="stop",
            completion=f"FINAL_LABEL: {native_class}",
        )
        events.append(grader)
        if instrument_failure is None:
            score = Score(
                value=native_class,
                answer=native_class,
                metadata={"codebook": "atb-diselect-response-v0.1"},
            )
        else:
            if instrument_failure == "grader_model_error":
                grader.output.error = "provider error"
            elif instrument_failure == "grader_truncated":
                grader.output.stop_reason = "max_tokens"
            elif instrument_failure == "grader_parse_failure":
                grader.output.completion = "invalid"
            score = Score.unscored(metadata={"instrument_failure": instrument_failure})
    return SimpleNamespace(
        output=target.output,
        events=events,
        metadata={"subset": subset},
        scores={"diselect_response_class": score},
    )


def _score_contract_log(samples: list[SimpleNamespace]) -> SimpleNamespace:
    return SimpleNamespace(
        eval=SimpleNamespace(
            task_version="0.1.0",
            scorers=[SimpleNamespace(name="diselect_response_class")],
        ),
        samples=samples,
    )


def test_diselect_postflight_requires_exact_task_scorers_and_native_score() -> None:
    manifest = ProtocolManifest.model_validate(_frozen_diselect_payload())
    sample = _score_contract_sample()
    log = _score_contract_log([sample])
    assert diselect_score_contract_matches(log, manifest)

    sample.scores["diselect_response_class"].answer = "refuse"
    assert not diselect_score_contract_matches(log, manifest)
    sample = _score_contract_sample()
    log = _score_contract_log([sample])
    log.eval.task_version = "different"
    assert not diselect_score_contract_matches(log, manifest)
    log.eval.task_version = "0.1.0"
    log.eval.scorers.append(SimpleNamespace(name="unfrozen_scorer"))
    assert not diselect_score_contract_matches(log, manifest)


def test_diselect_postflight_accepts_only_bounded_explained_missingness() -> None:
    manifest = ProtocolManifest.model_validate(_frozen_diselect_payload())
    samples = [_score_contract_sample() for _ in range(19)]
    samples.append(_score_contract_sample(instrument_failure="grader_parse_failure"))
    samples.extend(_score_contract_sample(subset="benign") for _ in range(10))
    assert diselect_score_contract_matches(_score_contract_log(samples), manifest)

    samples[-1] = _score_contract_sample(subset="benign", instrument_failure="target_model_error")
    assert not diselect_score_contract_matches(_score_contract_log(samples), manifest)


def test_diselect_postflight_rejects_instrument_failure_tampering() -> None:
    manifest = ProtocolManifest.model_validate(_frozen_diselect_payload())
    samples = [_score_contract_sample() for _ in range(19)]
    failed = _score_contract_sample(instrument_failure="grader_truncated")
    samples.append(failed)
    failed.scores["diselect_response_class"].metadata = {
        "instrument_failure": "grader_parse_failure"
    }
    assert not diselect_score_contract_matches(_score_contract_log(samples), manifest)


def test_non_human_protocol_rejects_unscored_samples() -> None:
    manifest = ProtocolManifest.model_validate(_frozen_diselect_payload())
    manifest.validation.human_validation_required = False
    samples = [_score_contract_sample() for _ in range(19)]
    samples.append(_score_contract_sample(instrument_failure="grader_parse_failure"))
    assert not diselect_score_contract_matches(_score_contract_log(samples), manifest)


def test_usage_reconciliation_ignores_direct_events_when_matching_openrouter_billing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    manifest = ProtocolManifest.model_validate(_frozen_diselect_payload())
    evidence_path = tmp_path / "evidence.eval"
    evidence_path.touch()
    openrouter = type("ModelEvent", (), {})()
    openrouter.uuid = "openrouter-event"
    openrouter.model = "openrouter/vendor/model-2025-01-01"
    direct = type("ModelEvent", (), {})()
    direct.uuid = "direct-event"
    direct.model = "openai/model-2025-01-01"
    log = SimpleNamespace(
        eval=SimpleNamespace(metadata={"atb_execution_id": "execution"}),
        status="success",
        samples=[SimpleNamespace(events=[openrouter, direct])],
    )
    monkeypatch.setattr(manifest_module, "load_manifest", lambda *_: manifest)
    monkeypatch.setattr("atb_eval.runner.read_eval_log", lambda *_: log)
    monkeypatch.setattr("atb_eval.runner.log_matches_condition", lambda *_: True)
    monkeypatch.setattr("atb_eval.runner.recorded_log_usage", lambda *_args, **_kwargs: (30, 0.003))
    monkeypatch.setattr(
        "atb_eval.runner.recorded_event_usage",
        lambda *_args, **_kwargs: {
            "openrouter-event": (10, 0.001, "a" * 64),
            "direct-event": (20, 0.002, "b" * 64),
        },
    )
    monkeypatch.setattr(
        "atb_eval.runner.recorded_openrouter_billed_costs",
        lambda *_: {"openrouter-event": (0.001, "c" * 64)},
    )
    assert recorded_execution_usage_within_envelope(
        manifest, tmp_path, "execution", manifest.models
    )


def test_openrouter_billed_cost_is_read_separately_from_local_estimate() -> None:
    event = type("ModelEvent", (), {})()
    event.uuid = "openrouter-call-1"
    event.model = "openrouter/openai/gpt-test-2025-01-01"
    event.error = None
    event.output = SimpleNamespace(error=None)
    event.call = SimpleNamespace(
        error=None,
        response={"usage": {"cost": 0.00125, "total_tokens": 12}},
    )
    log = SimpleNamespace(samples=[SimpleNamespace(events=[event])])
    assert recorded_openrouter_billed_costs(log)["openrouter-call-1"][0] == 0.00125

    event.call.response = {"usage": {"total_tokens": 12}}
    with pytest.raises(ValueError, match=r"billed usage\.cost"):
        recorded_openrouter_billed_costs(log)
