from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

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
    verify_committed_file,
)
from atb_eval.runner import (
    build_model,
    build_task,
    condition_map,
    effective_event_generate_config,
    ensure_private_permissions,
    execution_envelope,
    expected_runtime_packages,
    repository_root,
    request_parameters_match,
    run_fingerprint,
    runtime_package_versions,
    sample_model_inputs_match,
    sample_routes_match,
    sample_target_output_matches,
    verify_task_identity,
)
from inspect_ai.model import GenerateConfig
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
                "route": RouteSpec(provider_only=["Pinned Provider"]).model_dump(),
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
            "route": RouteSpec(provider_only=["Pinned Provider"]).model_dump(),
            "model_args": {},
            "generate_config": {},
        }
    )
    event = type("ModelEvent", (), {})()
    event.model = condition.model
    event.role = None
    event.output = SimpleNamespace(model="vendor/model-2025-01-01", fallback=None)
    event.call = SimpleNamespace(response={"provider": "Pinned Provider"})
    sample = SimpleNamespace(events=[event])
    assert condition.inspect_model_args()["provider"]["only"] == ["Pinned Provider"]
    assert "order" not in condition.inspect_model_args()["provider"]
    assert sample_routes_match(sample, condition)
    event.call.response["provider"] = "Unexpected Provider"
    assert not sample_routes_match(sample, condition)


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
            "route": RouteSpec(provider_only=["OpenAI"]).model_dump(),
            "model_args": {},
            "generate_config": {"reasoning_effort": "max", "seed": 42},
        }
    )
    expected = {"reasoning_effort": "max", "seed": 42}
    request = {
        "model": "openai/gpt-5-2025-08-07",
        "messages": [],
        "extra_headers": {"x-irid": "request-id"},
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
            "route": RouteSpec(provider_only=["Pinned Provider"]).model_dump(),
            "model_args": {},
            "generate_config": {"reasoning_tokens": 1234, "seed": 42},
        }
    )
    expected = {"reasoning_tokens": 1234, "seed": 42}
    assert request_parameters_match(
        {
            "model": "vendor/model-2025-01-01",
            "messages": [],
            "extra_headers": {"x-irid": "request-id"},
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
            "extra_headers": {"x-irid": "request-id"},
            "seed": 42,
            "extra_body": {"provider": condition.inspect_model_args()["provider"]},
        },
        condition,
        expected,
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
    for path in (REPO_ROOT / "evals/manifests").glob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        text = json.dumps(payload).lower()
        assert 'api_key"' not in text
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
            "resolved_model": "openai/gpt-test-2025-01-01",
            "observed_at": "2026-08-12T00:00:00Z",
            "source_url": "https://api.openai.com/v1/models",
            "evidence_path": "evals/model-revisions/test-fixture.json",
            "evidence_sha256": "a" * 64,
        },
        "model_args": {},
        "generate_config": {"seed": 42},
    }
    if max_tokens is not None:
        condition["generate_config"]["max_tokens"] = max_tokens
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
    target["revision"]["resolved_model"] = target["model"]
    payload["models"] = [target]
    with pytest.raises(ValidationError, match="removes their temperature request"):
        ProtocolManifest.model_validate(payload)
