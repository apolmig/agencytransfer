from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from urllib.request import Request

import atb_eval.runner as runner
import pytest
from atb_eval.manifest import load_manifest_with_hash
from atb_eval.paid_execution import (
    OPENROUTER_KEY_STATUS_URL,
    OPENROUTER_MANAGEMENT_KEYS_URL,
    FreshRouteCapture,
    PaidExecutionPermit,
    fetch_openrouter_key_status,
    load_paid_execution_permit,
    persist_fresh_openrouter_route_capture,
    verify_fresh_openrouter_route_capture,
    verify_not_openrouter_management_key,
    verify_openrouter_key_budget,
    verify_paid_execution_authorization,
    verify_paid_execution_permit,
)
from atb_eval.runner import parse_args

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "evals/manifests/diselect-route-preflight-v0.2.json"
COMMIT = "a" * 40
NOW = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)


class FakeResponse:
    def __init__(self, payload: object, status: int = 200) -> None:
        self.status = status
        self.raw = json.dumps(payload).encode()

    def read(self, amount: int = -1) -> bytes:
        return self.raw[:amount] if amount >= 0 else self.raw

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def manifest_and_hash():
    return load_manifest_with_hash(MANIFEST_PATH)


def permit_payload(manifest_hash: str, **overrides: object) -> dict[str, object]:
    manifest, _ = manifest_and_hash()
    payload: dict[str, object] = {
        "schema_version": "atb-paid-execution-permit-v0.1",
        "protocol_id": manifest.protocol_id,
        "manifest_sha256": manifest_hash,
        "code_commit": COMMIT,
        "acknowledged_by": "research-operator",
        "acknowledged_at": "2026-08-12T11:55:00Z",
        "expires_at": "2026-08-12T12:30:00Z",
        "maximum_cost_usd": 0.04,
    }
    payload.update(overrides)
    return payload


def write_permit(path: Path, manifest_hash: str, **overrides: object) -> Path:
    path.write_text(json.dumps(permit_payload(manifest_hash, **overrides)), encoding="utf-8")
    path.chmod(0o600)
    return path


def key_opener(payload: object, *, management_status: int = 403):
    def open_url(request: Request, *, timeout: float) -> FakeResponse:
        assert request.method == "GET"
        assert request.get_header("Authorization") == "Bearer inference-secret"
        assert timeout == 10
        if request.full_url == OPENROUTER_KEY_STATUS_URL:
            return FakeResponse(payload)
        assert request.full_url == OPENROUTER_MANAGEMENT_KEYS_URL
        return FakeResponse({"error": {"code": management_status}}, status=management_status)

    return open_url


def valid_key_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "limit": 30.0,
        "limit_remaining": 30.0,
        "limit_reset": None,
        "include_byok_in_limit": True,
        "expires_at": None,
    }
    data.update(overrides)
    return data


def test_cli_accepts_external_paid_permit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "atb-eval",
            "--manifest",
            "manifest.json",
            "--log-dir",
            "/controlled/logs",
            "--execute",
            "--allow-paid",
            "--paid-permit",
            "/controlled/permit.json",
        ],
    )
    args = parse_args()
    assert args.paid_permit == Path("/controlled/permit.json")


def test_permit_must_be_external_owner_only_regular_json(tmp_path: Path) -> None:
    _, manifest_hash = manifest_and_hash()
    external = write_permit(tmp_path / "permit.json", manifest_hash)
    permit = load_paid_execution_permit(external, REPO_ROOT)
    assert permit.manifest_sha256 == manifest_hash

    external.chmod(0o640)
    with pytest.raises(ValueError, match="mode 0600"):
        load_paid_execution_permit(external, REPO_ROOT)

    fake_repo = tmp_path / "repo"
    fake_repo.mkdir()
    internal = write_permit(fake_repo / "permit.json", manifest_hash)
    with pytest.raises(ValueError, match="outside the public repository"):
        load_paid_execution_permit(internal, fake_repo)


def test_permit_rejects_symlinks(tmp_path: Path) -> None:
    _, manifest_hash = manifest_and_hash()
    target = write_permit(tmp_path / "target.json", manifest_hash)
    link = tmp_path / "permit-link.json"
    link.symlink_to(target)
    with pytest.raises(ValueError, match="cannot be a symlink"):
        load_paid_execution_permit(link, REPO_ROOT)


def test_permit_rejects_hardlinks_and_duplicate_json_keys(tmp_path: Path) -> None:
    _, manifest_hash = manifest_and_hash()
    target = write_permit(tmp_path / "target.json", manifest_hash)
    hardlink = tmp_path / "permit-hardlink.json"
    hardlink.hardlink_to(target)
    with pytest.raises(ValueError, match="hard links"):
        load_paid_execution_permit(hardlink, REPO_ROOT)

    duplicate = tmp_path / "duplicate.json"
    payload = json.dumps(permit_payload(manifest_hash))
    duplicate.write_text(
        payload[:-1] + ',"maximum_cost_usd":0.04}',
        encoding="utf-8",
    )
    duplicate.chmod(0o600)
    with pytest.raises(ValueError, match="invalid"):
        load_paid_execution_permit(duplicate, REPO_ROOT)


@pytest.mark.parametrize(
    ("override", "provenance", "now", "message"),
    [
        ({"manifest_sha256": "b" * 64}, None, NOW, "manifest hash"),
        ({"protocol_id": "another-protocol"}, None, NOW, "protocol"),
        ({"code_commit": "b" * 40}, None, NOW, "commit"),
        ({}, {"code_commit": COMMIT, "code_dirty": True}, NOW, "clean repository"),
        ({"acknowledged_at": "2026-08-12T12:05:00Z"}, None, NOW, "in the future"),
        ({"expires_at": "2026-08-12T12:00:00Z"}, None, NOW, "expired"),
        ({"expires_at": "2026-08-14T12:00:00Z"}, None, NOW, "24 hours"),
        ({"maximum_cost_usd": 0.03}, None, NOW, "exactly match"),
        ({"maximum_cost_usd": 0.05}, None, NOW, "exactly match"),
        ({"maximum_cost_usd": 30.01}, None, NOW, "exactly match"),
    ],
)
def test_permit_is_bound_to_exact_execution_state(
    override: dict[str, object],
    provenance: dict[str, str | bool] | None,
    now: datetime,
    message: str,
) -> None:
    manifest, manifest_hash = manifest_and_hash()
    permit = PaidExecutionPermit.model_validate(permit_payload(manifest_hash, **override))
    with pytest.raises(ValueError, match=message):
        verify_paid_execution_permit(
            permit,
            manifest,
            manifest_hash,
            provenance or {"code_commit": COMMIT, "code_dirty": False},
            now=now,
        )


def test_permit_accepts_matching_clean_unexpired_state() -> None:
    manifest, manifest_hash = manifest_and_hash()
    permit = PaidExecutionPermit.model_validate(permit_payload(manifest_hash))
    verify_paid_execution_permit(
        permit,
        manifest,
        manifest_hash,
        {"code_commit": COMMIT, "code_dirty": False},
        now=NOW,
    )


def test_openrouter_key_status_request_does_not_expose_key_in_result() -> None:
    data = fetch_openrouter_key_status(
        "inference-secret",
        opener=key_opener({"data": valid_key_data()}),
    )
    assert data["limit"] == 30.0
    assert "inference-secret" not in repr(data)


def test_openrouter_transport_error_does_not_echo_the_key() -> None:
    def failing_opener(*args: object, **kwargs: object) -> FakeResponse:
        raise ValueError("transport saw inference-secret")

    with pytest.raises(ValueError, match="could not verify") as failure:
        fetch_openrouter_key_status("inference-secret", opener=failing_opener)
    assert "inference-secret" not in str(failure.value)


def test_openrouter_key_status_rejects_duplicate_json_keys() -> None:
    class DuplicateResponse(FakeResponse):
        def __init__(self) -> None:
            self.status = 200
            self.raw = b'{"data":{"limit":0.1,"limit":null}}'

    def duplicate_opener(*args: object, **kwargs: object) -> DuplicateResponse:
        return DuplicateResponse()

    with pytest.raises(ValueError, match="not valid JSON"):
        fetch_openrouter_key_status("inference-secret", opener=duplicate_opener)


def test_openrouter_key_must_have_lifetime_cap_and_sufficient_balance() -> None:
    manifest, _ = manifest_and_hash()
    budget = verify_openrouter_key_budget(
        manifest,
        environment={"OPENROUTER_API_KEY": "inference-secret"},
        opener=key_opener({"data": valid_key_data()}),
    )
    assert budget.limit_usd == 30.0
    assert budget.remaining_usd == 30.0


@pytest.mark.parametrize("denial_status", [401, 403])
def test_inference_key_is_denied_by_management_api(denial_status: int) -> None:
    verify_not_openrouter_management_key(
        "inference-secret",
        opener=key_opener({"data": valid_key_data()}, management_status=denial_status),
    )


@pytest.mark.parametrize("unexpected_status", [200, 400, 429, 500])
def test_management_key_probe_fails_closed(unexpected_status: int) -> None:
    message = "management API key" if unexpected_status == 200 else "did not fail"
    with pytest.raises(ValueError, match=message):
        verify_not_openrouter_management_key(
            "inference-secret",
            opener=key_opener({"data": valid_key_data()}, management_status=unexpected_status),
        )


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (valid_key_data(limit=None, limit_remaining=None), "finite number"),
        (valid_key_data(limit=30.01), "exceeds"),
        (valid_key_data(limit_remaining=0.03), "below"),
        (valid_key_data(limit_reset="daily"), "lifetime"),
        (valid_key_data(include_byok_in_limit=False), "include BYOK"),
        (valid_key_data(include_byok_in_limit=None), "include BYOK"),
        (
            valid_key_data(is_management_key=True),
            "inference-only",
        ),
        (
            valid_key_data(is_provisioning_key=True),
            "inference-only",
        ),
        (
            valid_key_data(expires_at="2026-08-12T11:59:00Z"),
            "expired",
        ),
        (valid_key_data(limit_remaining=30.01), "exceeds its limit"),
        (valid_key_data(limit=True), "finite number"),
    ],
)
def test_openrouter_key_budget_fails_closed(data: dict[str, object], message: str) -> None:
    manifest, _ = manifest_and_hash()
    with pytest.raises(ValueError, match=message):
        verify_openrouter_key_budget(
            manifest,
            environment={"OPENROUTER_API_KEY": "inference-secret"},
            opener=key_opener({"data": data}),
            now=NOW,
        )


def test_management_key_presence_fails_before_network() -> None:
    manifest, _ = manifest_and_hash()

    def forbidden_opener(*args: object, **kwargs: object) -> FakeResponse:
        raise AssertionError("network must not be reached")

    with pytest.raises(ValueError, match="OPENROUTER_MANAGEMENT_KEY"):
        verify_openrouter_key_budget(
            manifest,
            environment={
                "OPENROUTER_API_KEY": "inference-secret",
                "OPENROUTER_MANAGEMENT_KEY": "",
            },
            opener=forbidden_opener,
        )


def test_combined_authorization_checks_permit_and_provider_budget(tmp_path: Path) -> None:
    manifest, manifest_hash = manifest_and_hash()
    permit_path = write_permit(tmp_path / "permit.json", manifest_hash)
    budget = verify_paid_execution_authorization(
        manifest,
        manifest_hash,
        {"code_commit": COMMIT, "code_dirty": False},
        permit_path,
        REPO_ROOT,
        environment={"OPENROUTER_API_KEY": "inference-secret"},
        opener=key_opener({"data": valid_key_data()}),
        now=NOW,
    )
    assert budget.limit_usd == 30.0
    assert budget.remaining_usd == 30.0


def test_manifest_lifetime_cap_is_independent_of_the_per_run_permit() -> None:
    manifest, _ = manifest_and_hash()
    budget = verify_openrouter_key_budget(
        manifest,
        environment={"OPENROUTER_API_KEY": "inference-secret"},
        opener=key_opener({"data": valid_key_data()}),
        now=NOW,
    )
    assert manifest.run.planned_run_cost_envelope_usd == 0.04
    assert budget.limit_usd == manifest.run.provider_key_limit_usd == 30.0


def write_fresh_capture(
    output_dir: Path,
    manifest: object,
    observed_at: str,
    *,
    canonical_drift: bool = False,
) -> None:
    output_dir.mkdir(parents=True)
    raw = b'{"data":[]}'
    raw_hash = sha256(raw).hexdigest()
    raw_dir = output_dir / "provider-responses"
    raw_dir.mkdir()
    (raw_dir / f"{raw_hash}.json").write_bytes(raw)
    for condition in [*manifest.models, *manifest.model_roles.values()]:
        revision = condition.revision
        assert revision is not None and condition.pricing is not None
        payload = {
            "schema_version": "atb-model-revision-evidence-v0.1",
            "requested_model": condition.model.removeprefix("openrouter/"),
            "resolved_model": revision.resolved_model,
            "canonical_slug": (
                "changed/canonical-20990101" if canonical_drift else revision.canonical_slug
            ),
            "inventory_model_id": revision.inventory_model_id,
            "endpoint_model_id": revision.endpoint_model_id,
            "endpoint_name": revision.endpoint_name,
            "provider_name": revision.provider_name,
            "provider_tag": revision.provider_tag,
            "quantization": revision.quantization,
            "supported_parameters": revision.supported_parameters,
            "supported_reasoning_efforts": revision.supported_reasoning_efforts,
            "max_completion_tokens": revision.max_completion_tokens,
            "request_price_usd": revision.request_price_usd,
            "internal_reasoning_price_usd_per_million": (
                revision.internal_reasoning_price_usd_per_million
            ),
            "observed_at": observed_at,
            "source_url": revision.source_url,
            "model_source_url": revision.model_source_url,
            "models_source_url": revision.models_source_url,
            "zdr_source_url": revision.zdr_source_url,
            "model_response_sha256": raw_hash,
            "models_response_sha256": raw_hash,
            "endpoint_response_sha256": raw_hash,
            "zdr_response_sha256": raw_hash,
            "zdr_eligible": True,
            "pricing_usd_per_million": condition.pricing.model_dump(),
        }
        (output_dir / Path(revision.evidence_path).name).write_text(
            json.dumps(payload), encoding="utf-8"
        )


def test_fresh_route_capture_must_match_frozen_projection(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    manifest, _ = manifest_and_hash()

    def fake_run(command: list[str], **kwargs: object) -> object:
        output_dir = Path(command[command.index("--output-dir") + 1])
        observed_at = command[command.index("--observed-at") + 1]
        write_fresh_capture(output_dir, manifest, observed_at)
        return object()

    monkeypatch.setattr("atb_eval.paid_execution.subprocess.run", fake_run)
    capture = verify_fresh_openrouter_route_capture(
        manifest,
        REPO_ROOT,
        observed_at="2026-08-12T12:00:00Z",
        manifest_sha256="a" * 64,
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir(mode=0o700)
    digest = persist_fresh_openrouter_route_capture(capture, run_dir)
    receipt = run_dir / "openrouter-route-capture/receipt.json"
    assert digest == sha256(receipt.read_bytes()).hexdigest()
    assert json.loads(receipt.read_text())["manifest_sha256"] == "a" * 64


def test_fresh_route_capture_fails_closed_on_canonical_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, _ = manifest_and_hash()

    def fake_run(command: list[str], **kwargs: object) -> object:
        output_dir = Path(command[command.index("--output-dir") + 1])
        observed_at = command[command.index("--observed-at") + 1]
        write_fresh_capture(output_dir, manifest, observed_at, canonical_drift=True)
        return object()

    monkeypatch.setattr("atb_eval.paid_execution.subprocess.run", fake_run)
    with pytest.raises(ValueError, match="no longer matches"):
        verify_fresh_openrouter_route_capture(
            manifest,
            REPO_ROOT,
            observed_at="2026-08-12T12:00:00Z",
            manifest_sha256="a" * 64,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("request_price_usd", 0.01),
        ("supported_reasoning_efforts", ["high"]),
        ("max_completion_tokens", 1),
        ("internal_reasoning_price_usd_per_million", 0.01),
    ],
)
def test_fresh_route_capture_fails_closed_on_protocol_drift(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
) -> None:
    manifest, manifest_hash = manifest_and_hash()

    def fake_run(command: list[str], **kwargs: object) -> object:
        output_dir = Path(command[command.index("--output-dir") + 1])
        observed_at = command[command.index("--observed-at") + 1]
        write_fresh_capture(output_dir, manifest, observed_at)
        revision = manifest.models[0].revision
        assert revision is not None
        path = output_dir / Path(revision.evidence_path).name
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload[field] = value
        path.write_text(json.dumps(payload), encoding="utf-8")
        return object()

    monkeypatch.setattr("atb_eval.paid_execution.subprocess.run", fake_run)
    with pytest.raises(ValueError, match="no longer matches"):
        verify_fresh_openrouter_route_capture(
            manifest,
            REPO_ROOT,
            observed_at="2026-08-12T12:00:00Z",
            manifest_sha256=manifest_hash,
        )


def test_key_must_remain_valid_for_the_execution_permit(tmp_path: Path) -> None:
    manifest, manifest_hash = manifest_and_hash()
    permit_path = write_permit(tmp_path / "permit.json", manifest_hash)
    with pytest.raises(ValueError, match="expires before"):
        verify_paid_execution_authorization(
            manifest,
            manifest_hash,
            {"code_commit": COMMIT, "code_dirty": False},
            permit_path,
            REPO_ROOT,
            environment={"OPENROUTER_API_KEY": "inference-secret"},
            opener=key_opener({"data": valid_key_data(expires_at="2026-08-12T12:15:00Z")}),
            now=NOW,
        )


def test_runner_gate_failure_prevents_eval_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, manifest_hash = manifest_and_hash()
    args = SimpleNamespace(
        manifest=MANIFEST_PATH,
        log_dir=tmp_path / "logs",
        source_dir=tmp_path / "source",
        execute=True,
        allow_paid=True,
        paid_permit=tmp_path / "permit.json",
    )
    provenance = {
        "code_commit": COMMIT,
        "code_dirty": False,
        "environment_lock_sha256": "b" * 64,
    }
    monkeypatch.setattr(runner, "parse_args", lambda: args)
    monkeypatch.setattr(runner, "repository_root", lambda: REPO_ROOT)
    monkeypatch.setattr(
        runner,
        "preflight",
        lambda *call_args: (manifest, tmp_path / "logs", manifest_hash),
    )
    monkeypatch.setattr(
        runner,
        "build_task",
        lambda *call_args: SimpleNamespace(dataset=object()),
    )
    monkeypatch.setattr(runner, "verify_task_identity", lambda *call_args: None)
    monkeypatch.setattr(
        runner,
        "dataset_inventory_sha256",
        lambda *call_args: manifest.dataset.selected_inventory_sha256,
    )
    monkeypatch.setattr(runner, "execution_envelope", lambda *call_args: {})
    monkeypatch.setattr(runner, "repository_provenance", lambda *call_args: provenance)
    monkeypatch.setattr(runner, "verify_committed_file", lambda *call_args: None)
    monkeypatch.setattr(runner, "verify_model_revision_evidence", lambda *call_args: None)
    monkeypatch.setattr(
        runner, "verify_fresh_openrouter_route_capture", lambda *call_args, **kwargs: None
    )
    monkeypatch.setattr(runner, "missing_credentials", lambda *call_args: [])
    monkeypatch.setattr(runner, "forbidden_runtime_overrides", lambda: [])
    monkeypatch.setattr(
        runner,
        "verify_paid_execution_authorization",
        lambda *call_args: (_ for _ in ()).throw(ValueError("permit rejected")),
    )

    def forbidden_execute(*call_args: object, **call_kwargs: object) -> bool:
        raise AssertionError("evaluation must not run after a gate failure")

    monkeypatch.setattr(runner, "execute", forbidden_execute)
    with pytest.raises(SystemExit, match="permit rejected"):
        runner.main()
    assert not (tmp_path / "logs").exists()


def test_dry_run_never_checks_paid_authorization_or_executes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, manifest_hash = load_manifest_with_hash(
        REPO_ROOT / "evals/manifests/inspect-canary-v0.1.json"
    )
    args = SimpleNamespace(
        manifest=REPO_ROOT / "evals/manifests/inspect-canary-v0.1.json",
        log_dir=tmp_path / "logs",
        source_dir=None,
        execute=False,
        allow_paid=False,
        paid_permit=None,
    )
    monkeypatch.setattr(runner, "parse_args", lambda: args)
    monkeypatch.setattr(runner, "repository_root", lambda: REPO_ROOT)
    monkeypatch.setattr(
        runner,
        "preflight",
        lambda *call_args: (manifest, tmp_path / "logs", manifest_hash),
    )
    monkeypatch.setattr(
        runner,
        "build_task",
        lambda *call_args: SimpleNamespace(dataset=object()),
    )
    monkeypatch.setattr(runner, "verify_task_identity", lambda *call_args: None)
    monkeypatch.setattr(
        runner,
        "dataset_inventory_sha256",
        lambda *call_args: manifest.dataset.selected_inventory_sha256,
    )
    monkeypatch.setattr(runner, "execution_envelope", lambda *call_args: {})
    monkeypatch.setattr(
        runner,
        "repository_provenance",
        lambda *call_args: {
            "code_commit": COMMIT,
            "code_dirty": False,
            "environment_lock_sha256": "b" * 64,
        },
    )
    monkeypatch.setattr(
        runner,
        "verify_paid_execution_authorization",
        lambda *call_args: (_ for _ in ()).throw(
            AssertionError("dry-run must not check the paid gate")
        ),
    )
    monkeypatch.setattr(
        runner,
        "execute",
        lambda *call_args: (_ for _ in ()).throw(AssertionError("dry-run must not execute")),
    )
    runner.main()
    assert not (tmp_path / "logs").exists()


def test_valid_paid_gate_rechecks_before_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, manifest_hash = manifest_and_hash()
    args = SimpleNamespace(
        manifest=MANIFEST_PATH,
        log_dir=tmp_path / "logs",
        source_dir=tmp_path / "source",
        execute=True,
        allow_paid=True,
        paid_permit=tmp_path / "permit.json",
    )
    provenance = {
        "code_commit": COMMIT,
        "code_dirty": False,
        "environment_lock_sha256": "b" * 64,
    }
    monkeypatch.setattr(runner, "parse_args", lambda: args)
    monkeypatch.setattr(runner, "repository_root", lambda: REPO_ROOT)
    monkeypatch.setattr(
        runner,
        "preflight",
        lambda *call_args: (manifest, tmp_path / "logs", manifest_hash),
    )
    monkeypatch.setattr(
        runner,
        "build_task",
        lambda *call_args: SimpleNamespace(dataset=object()),
    )
    monkeypatch.setattr(runner, "verify_task_identity", lambda *call_args: None)
    monkeypatch.setattr(
        runner,
        "dataset_inventory_sha256",
        lambda *call_args: manifest.dataset.selected_inventory_sha256,
    )
    monkeypatch.setattr(runner, "execution_envelope", lambda *call_args: {})
    monkeypatch.setattr(runner, "repository_provenance", lambda *call_args: provenance)
    monkeypatch.setattr(runner, "verify_committed_file", lambda *call_args: None)
    monkeypatch.setattr(runner, "verify_model_revision_evidence", lambda *call_args: None)
    monkeypatch.setattr(runner, "missing_credentials", lambda *call_args: [])
    monkeypatch.setattr(runner, "forbidden_runtime_overrides", lambda: [])
    events: list[str] = []
    monkeypatch.setattr(
        runner,
        "verify_paid_execution_authorization",
        lambda *call_args: events.append("gate"),
    )
    monkeypatch.setattr(
        runner,
        "verify_fresh_openrouter_route_capture",
        lambda *call_args, **call_kwargs: (
            events.append("route")
            or FreshRouteCapture(
                receipt_bytes=b"{}\n",
                receipt_sha256=sha256(b"{}\n").hexdigest(),
                artifacts=(),
            )
        ),
    )
    monkeypatch.setattr(
        runner,
        "persist_fresh_openrouter_route_capture",
        lambda *call_args, **call_kwargs: events.append("persist") or sha256(b"{}\n").hexdigest(),
    )
    monkeypatch.setattr(
        runner,
        "verify_paid_execution_permit_current",
        lambda *call_args, **call_kwargs: events.append("permit-current"),
    )

    def successful_execute(*call_args: object, **call_kwargs: object) -> bool:
        events.append("execute")
        return True

    monkeypatch.setattr(runner, "execute", successful_execute)
    runner.main()
    assert events == ["gate", "route", "gate", "persist", "permit-current", "execute"]


def test_expired_permit_after_receipt_persistence_prevents_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, manifest_hash = manifest_and_hash()
    args = SimpleNamespace(
        manifest=MANIFEST_PATH,
        log_dir=tmp_path / "logs",
        source_dir=tmp_path / "source",
        execute=True,
        allow_paid=True,
        paid_permit=tmp_path / "permit.json",
    )
    provenance = {
        "code_commit": COMMIT,
        "code_dirty": False,
        "environment_lock_sha256": "b" * 64,
    }
    monkeypatch.setattr(runner, "parse_args", lambda: args)
    monkeypatch.setattr(runner, "repository_root", lambda: REPO_ROOT)
    monkeypatch.setattr(
        runner,
        "preflight",
        lambda *call_args: (manifest, tmp_path / "logs", manifest_hash),
    )
    monkeypatch.setattr(runner, "build_task", lambda *call_args: SimpleNamespace(dataset=object()))
    monkeypatch.setattr(runner, "verify_task_identity", lambda *call_args: None)
    monkeypatch.setattr(
        runner,
        "dataset_inventory_sha256",
        lambda *call_args: manifest.dataset.selected_inventory_sha256,
    )
    monkeypatch.setattr(runner, "execution_envelope", lambda *call_args: {})
    monkeypatch.setattr(runner, "repository_provenance", lambda *call_args: provenance)
    monkeypatch.setattr(runner, "verify_committed_file", lambda *call_args: None)
    monkeypatch.setattr(runner, "verify_model_revision_evidence", lambda *call_args: None)
    monkeypatch.setattr(runner, "missing_credentials", lambda *call_args: [])
    monkeypatch.setattr(runner, "forbidden_runtime_overrides", lambda: [])
    monkeypatch.setattr(runner, "verify_paid_execution_authorization", lambda *call_args: None)
    capture = FreshRouteCapture(
        receipt_bytes=b"{}\n",
        receipt_sha256=sha256(b"{}\n").hexdigest(),
        artifacts=(),
    )
    monkeypatch.setattr(
        runner,
        "verify_fresh_openrouter_route_capture",
        lambda *call_args, **call_kwargs: capture,
    )
    monkeypatch.setattr(
        runner,
        "persist_fresh_openrouter_route_capture",
        lambda *call_args: capture.receipt_sha256,
    )
    monkeypatch.setattr(
        runner,
        "verify_paid_execution_permit_current",
        lambda *call_args: (_ for _ in ()).throw(ValueError("paid execution permit has expired")),
    )
    monkeypatch.setattr(
        runner,
        "execute",
        lambda *call_args: (_ for _ in ()).throw(
            AssertionError("expired permit must prevent model calls")
        ),
    )
    with pytest.raises(SystemExit, match="permit has expired"):
        runner.main()
