"""Fail-closed authorization and provider-budget checks for paid executions."""

from __future__ import annotations

import json
import math
import os
import stat
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from pydantic import BaseModel, ConfigDict, Field, field_validator

from atb_eval.manifest import ProtocolManifest

OPENROUTER_KEY_STATUS_URL = "https://openrouter.ai/api/v1/key"
OPENROUTER_MANAGEMENT_KEYS_URL = "https://openrouter.ai/api/v1/keys"
MAX_PERMIT_BYTES = 64 * 1024
MAX_PERMIT_LIFETIME = timedelta(hours=24)
MAX_ROUTE_CAPTURE_BYTES = 64 * 1024 * 1024
MAX_ROUTE_CAPTURE_FILES = 64


class PaidExecutionPermit(BaseModel):
    """A short-lived operator acknowledgement for one frozen protocol state.

    This local file records deliberate execution intent. It is not a signature
    and does not prove approval by an independent reviewer.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal["atb-paid-execution-permit-v0.1"]
    protocol_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,127}$")
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    code_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    acknowledged_by: str = Field(min_length=1, max_length=200)
    acknowledged_at: str = Field(pattern=r"^20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
    expires_at: str = Field(pattern=r"^20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
    maximum_cost_usd: float = Field(gt=0)

    @field_validator("acknowledged_by")
    @classmethod
    def nonblank_operator(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("paid execution operator cannot be blank")
        return value

    @field_validator("maximum_cost_usd")
    @classmethod
    def finite_maximum_cost(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("paid execution maximum cost must be finite")
        return value


class UrlResponse(Protocol):
    status: int

    def read(self, amount: int = -1) -> bytes: ...

    def __enter__(self) -> UrlResponse: ...

    def __exit__(self, *args: object) -> None: ...


UrlOpener = Callable[..., UrlResponse]


class ProviderKeyBudget(BaseModel):
    """Sanitised result of checking the inference key's lifetime cap."""

    model_config = ConfigDict(extra="forbid", strict=True)

    limit_usd: float
    remaining_usd: float


@dataclass(frozen=True)
class FreshRouteCapture:
    """Verified public route snapshot retained beside the paid Inspect logs."""

    receipt_bytes: bytes
    receipt_sha256: str
    artifacts: tuple[tuple[str, bytes], ...]


def _utc_timestamp(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise ValueError(f"paid execution permit has an invalid {label}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError(f"paid execution permit {label} must be UTC")
    return parsed


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON object contains a duplicate key")
        result[key] = value
    return result


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def _direct_urlopen(request: Request, *, timeout: float) -> UrlResponse:
    """Open the fixed provider URL without environment proxies or redirects."""

    return build_opener(ProxyHandler({}), _NoRedirectHandler()).open(request, timeout=timeout)


def _outside_repository(path: Path, repo_root: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_symlink():
        raise ValueError("paid execution permit cannot be a symlink")
    try:
        resolved = expanded.resolve(strict=True)
    except OSError as exc:
        raise ValueError("paid execution permit does not exist") from exc
    resolved_repo = repo_root.resolve()
    if resolved == resolved_repo or resolved_repo in resolved.parents:
        raise ValueError("paid execution permit must remain outside the public repository")
    return resolved


def load_paid_execution_permit(path: Path, repo_root: Path) -> PaidExecutionPermit:
    """Load an owner-only regular JSON file that lives outside the public repository."""

    resolved = _outside_repository(path, repo_root)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(resolved, flags)
    except OSError as exc:
        raise ValueError("cannot open paid execution permit safely") from exc
    try:
        details = os.fstat(descriptor)
        if not stat.S_ISREG(details.st_mode):
            raise ValueError("paid execution permit must be a regular file")
        if details.st_nlink != 1:
            raise ValueError("paid execution permit cannot have hard links")
        if details.st_uid != os.getuid():
            raise ValueError("paid execution permit has an unexpected owner")
        if stat.S_IMODE(details.st_mode) != 0o600:
            raise ValueError("paid execution permit must have mode 0600")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            raw = handle.read(MAX_PERMIT_BYTES + 1)
    finally:
        os.close(descriptor)
    if len(raw) > MAX_PERMIT_BYTES:
        raise ValueError("paid execution permit is unexpectedly large")
    try:
        payload = json.loads(raw, object_pairs_hook=_unique_json_object)
        return PaidExecutionPermit.model_validate(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("paid execution permit is invalid") from exc


def verify_paid_execution_permit(
    permit: PaidExecutionPermit,
    manifest: ProtocolManifest,
    manifest_sha256: str,
    code_provenance: Mapping[str, str | bool],
    *,
    now: datetime | None = None,
) -> None:
    """Bind approval to the exact manifest, clean commit, lifetime, and cost envelope."""

    if permit.protocol_id != manifest.protocol_id:
        raise ValueError("paid execution permit protocol does not match the manifest")
    if permit.manifest_sha256 != manifest_sha256:
        raise ValueError("paid execution permit manifest hash does not match")
    code_commit = code_provenance.get("code_commit")
    if code_provenance.get("code_dirty") is not False:
        raise ValueError("paid execution permit requires a clean repository checkout")
    if permit.code_commit != code_commit:
        raise ValueError("paid execution permit commit does not match the clean checkout")

    acknowledged_at = _utc_timestamp(permit.acknowledged_at, "acknowledged_at")
    expires_at = _utc_timestamp(permit.expires_at, "expires_at")
    current_time = now or datetime.now(UTC)
    if current_time.tzinfo is None:
        raise ValueError("paid execution verification time must be timezone-aware")
    current_time = current_time.astimezone(UTC)
    if acknowledged_at > current_time:
        raise ValueError("paid execution acknowledgement time is in the future")
    if expires_at <= acknowledged_at:
        raise ValueError("paid execution permit must expire after acknowledgement")
    if expires_at - acknowledged_at > MAX_PERMIT_LIFETIME:
        raise ValueError("paid execution permit lifetime cannot exceed 24 hours")
    if current_time >= expires_at:
        raise ValueError("paid execution permit has expired")

    provider_cap = manifest.run.provider_key_limit_usd
    if provider_cap is None or not math.isfinite(provider_cap):
        raise ValueError("paid execution manifest lacks a provider key hard cap")
    if not math.isfinite(manifest.run.planned_run_cost_envelope_usd):
        raise ValueError("paid execution planned run envelope must be finite")
    if not math.isfinite(manifest.run.sample_cost_limit_usd):
        raise ValueError("paid execution sample cost limit must be finite")
    if not math.isclose(
        permit.maximum_cost_usd,
        manifest.run.planned_run_cost_envelope_usd,
        rel_tol=0,
        abs_tol=1e-9,
    ):
        raise ValueError("paid execution permit must exactly match the planned run envelope")
    if permit.maximum_cost_usd > provider_cap + 1e-9:
        raise ValueError("paid execution permit exceeds the manifest provider key hard cap")


def _finite_nonnegative_number(value: Any, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"OpenRouter inference key {label} is not a finite number")
    result = float(value)
    if not math.isfinite(result) or result < 0 or (positive and result <= 0):
        raise ValueError(f"OpenRouter inference key {label} is not a valid finite amount")
    return result


def fetch_openrouter_key_status(
    api_key: str,
    *,
    opener: UrlOpener | None = None,
    timeout_seconds: float = 10,
) -> Mapping[str, Any]:
    """Fetch key metadata without returning or logging reusable credentials."""

    request = Request(
        OPENROUTER_KEY_STATUS_URL,
        headers={"Accept": "application/json", "Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    open_url = opener or _direct_urlopen
    try:
        with open_url(request, timeout=timeout_seconds) as response:
            if response.status != 200:
                raise ValueError("OpenRouter key-status endpoint returned a non-success status")
            raw = response.read(MAX_PERMIT_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        raise ValueError("could not verify the OpenRouter inference-key budget") from exc
    if len(raw) > MAX_PERMIT_BYTES:
        raise ValueError("OpenRouter key-status response is unexpectedly large")
    try:
        payload = json.loads(raw, object_pairs_hook=_unique_json_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("OpenRouter key-status response is not valid JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), dict):
        raise ValueError("OpenRouter key-status response lacks a data object")
    return payload["data"]


def verify_not_openrouter_management_key(
    api_key: str,
    *,
    opener: UrlOpener | None = None,
    timeout_seconds: float = 10,
) -> None:
    """Require the valid key to be denied by the management-only key-list API."""

    request = Request(
        OPENROUTER_MANAGEMENT_KEYS_URL,
        headers={"Accept": "application/json", "Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    open_url = opener or _direct_urlopen
    try:
        with open_url(request, timeout=timeout_seconds) as response:
            status = response.status
    except HTTPError as exc:
        status = exc.code
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise ValueError("could not verify that the OpenRouter key is inference-only") from exc
    if status == 200:
        raise ValueError("OpenRouter credential is a management API key")
    if status not in {401, 403}:
        raise ValueError("OpenRouter management-key probe did not fail by authorization")


def verify_openrouter_key_budget(
    manifest: ProtocolManifest,
    *,
    environment: Mapping[str, str] | None = None,
    opener: UrlOpener | None = None,
    now: datetime | None = None,
    valid_until: datetime | None = None,
) -> ProviderKeyBudget:
    """Require an inference key within the manifest's lifetime exposure cap."""

    env = os.environ if environment is None else environment
    if "OPENROUTER_MANAGEMENT_KEY" in env:
        raise ValueError("OPENROUTER_MANAGEMENT_KEY must not be present during paid execution")
    api_key = env.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is required for paid OpenRouter execution")
    provider_cap = manifest.run.provider_key_limit_usd
    if provider_cap is None or not math.isfinite(provider_cap):
        raise ValueError("paid execution manifest lacks a provider key hard cap")
    paid_conditions = [*manifest.models, *manifest.model_roles.values()]
    if any(not condition.model.startswith("openrouter/") for condition in paid_conditions):
        raise ValueError("paid execution key gate currently supports OpenRouter conditions only")

    data = fetch_openrouter_key_status(api_key, opener=opener)
    # The documented GET /api/v1/key response does not promise key-type flags.
    # Reject them if the API supplies a positive signal, while treating a
    # successful response from this inference-key endpoint as the base proof.
    if data.get("is_management_key") is True or data.get("is_provisioning_key") is True:
        raise ValueError("OpenRouter credential is not an inference-only API key")
    verify_not_openrouter_management_key(api_key, opener=opener)
    key_expiry = data.get("expires_at")
    if key_expiry is not None:
        if not isinstance(key_expiry, str):
            raise ValueError("OpenRouter inference-key expiry is invalid")
        try:
            expires_at = _utc_timestamp(key_expiry, "inference-key expires_at")
        except ValueError as exc:
            raise ValueError("OpenRouter inference-key expiry is invalid") from exc
        current_time = now or datetime.now(UTC)
        if current_time.tzinfo is None:
            raise ValueError("OpenRouter key verification time must be timezone-aware")
        if current_time.astimezone(UTC) >= expires_at:
            raise ValueError("OpenRouter inference key has expired")
        if valid_until is not None:
            if valid_until.tzinfo is None:
                raise ValueError("OpenRouter required key-validity time must be timezone-aware")
            if expires_at < valid_until.astimezone(UTC):
                raise ValueError("OpenRouter inference key expires before the execution permit")
    if "limit_reset" not in data or data["limit_reset"] is not None:
        raise ValueError("OpenRouter inference key must use a lifetime, non-resetting limit")
    if data.get("include_byok_in_limit") is not True:
        raise ValueError("OpenRouter inference-key limit must include BYOK usage")
    limit = _finite_nonnegative_number(data.get("limit"), "limit", positive=True)
    remaining = _finite_nonnegative_number(data.get("limit_remaining"), "remaining balance")
    if limit > provider_cap + 1e-9:
        raise ValueError("OpenRouter inference-key limit exceeds the manifest lifetime cap")
    if remaining > limit + 1e-9:
        raise ValueError("OpenRouter inference-key remaining balance exceeds its limit")
    if remaining + 1e-9 < manifest.run.planned_run_cost_envelope_usd:
        raise ValueError("OpenRouter inference-key balance is below the planned run envelope")
    return ProviderKeyBudget(limit_usd=limit, remaining_usd=remaining)


def verify_paid_execution_authorization(
    manifest: ProtocolManifest,
    manifest_sha256: str,
    code_provenance: Mapping[str, str | bool],
    permit_path: Path,
    repo_root: Path,
    *,
    environment: Mapping[str, str] | None = None,
    opener: UrlOpener | None = None,
    now: datetime | None = None,
) -> ProviderKeyBudget:
    """Verify operator acknowledgement and provider key before any paid model call."""

    permit = load_paid_execution_permit(permit_path, repo_root)
    verify_paid_execution_permit(
        permit,
        manifest,
        manifest_sha256,
        code_provenance,
        now=now,
    )
    return verify_openrouter_key_budget(
        manifest,
        environment=environment,
        opener=opener,
        now=now,
        valid_until=_utc_timestamp(permit.expires_at, "expires_at"),
    )


def verify_paid_execution_permit_current(
    manifest: ProtocolManifest,
    manifest_sha256: str,
    code_provenance: Mapping[str, str | bool],
    permit_path: Path,
    repo_root: Path,
    *,
    now: datetime | None = None,
) -> None:
    """Recheck the local operator acknowledgement immediately before model calls."""

    verify_paid_execution_permit(
        load_paid_execution_permit(permit_path, repo_root),
        manifest,
        manifest_sha256,
        code_provenance,
        now=now,
    )


def verify_fresh_openrouter_route_capture(
    manifest: ProtocolManifest,
    repo_root: Path,
    *,
    observed_at: str,
    manifest_sha256: str,
) -> FreshRouteCapture:
    """Require a fresh public recapture to match every frozen route before spending."""

    script = repo_root / "scripts/capture_openrouter_routes.py"
    with TemporaryDirectory(prefix="atb-openrouter-preflight-") as temp_dir:
        output_dir = Path(temp_dir) / "capture"
        try:
            subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--output-dir",
                    str(output_dir),
                    "--observed-at",
                    observed_at,
                ],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise ValueError("could not refresh OpenRouter route evidence before spending") from exc

        condition_receipts: list[dict[str, Any]] = []
        for condition in [*manifest.models, *manifest.model_roles.values()]:
            if not condition.model.startswith("openrouter/") or condition.revision is None:
                continue
            expected_name = Path(condition.revision.evidence_path).name
            path = output_dir / expected_name
            try:
                evidence = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(
                    f"fresh OpenRouter route evidence is missing for {condition.condition_id}"
                ) from exc
            expected = {
                "schema_version": "atb-model-revision-evidence-v0.1",
                "requested_model": condition.model.removeprefix("openrouter/"),
                "resolved_model": condition.revision.resolved_model,
                "canonical_slug": condition.revision.canonical_slug,
                "inventory_model_id": condition.revision.inventory_model_id,
                "endpoint_model_id": condition.revision.endpoint_model_id,
                "endpoint_name": condition.revision.endpoint_name,
                "provider_name": condition.revision.provider_name,
                "provider_tag": condition.revision.provider_tag,
                "quantization": condition.revision.quantization,
                "supported_parameters": condition.revision.supported_parameters,
                "supported_reasoning_efforts": (condition.revision.supported_reasoning_efforts),
                "max_completion_tokens": condition.revision.max_completion_tokens,
                "request_price_usd": condition.revision.request_price_usd,
                "internal_reasoning_price_usd_per_million": (
                    condition.revision.internal_reasoning_price_usd_per_million
                ),
                "observed_at": observed_at,
                "source_url": condition.revision.source_url,
                "model_source_url": condition.revision.model_source_url,
                "models_source_url": condition.revision.models_source_url,
                "zdr_source_url": condition.revision.zdr_source_url,
                "zdr_eligible": True,
                "pricing_usd_per_million": (
                    condition.pricing.model_dump() if condition.pricing is not None else None
                ),
            }
            if any(evidence.get(key) != value for key, value in expected.items()):
                raise ValueError(
                    f"fresh OpenRouter route no longer matches {condition.condition_id}"
                )

            raw_hashes: dict[str, str] = {}
            for field in (
                "model_response_sha256",
                "models_response_sha256",
                "endpoint_response_sha256",
                "zdr_response_sha256",
            ):
                raw_hash = evidence.get(field)
                if (
                    not isinstance(raw_hash, str)
                    or len(raw_hash) != 64
                    or any(char not in "0123456789abcdef" for char in raw_hash)
                ):
                    raise ValueError(
                        f"fresh OpenRouter route lacks raw evidence for {condition.condition_id}"
                    )
                raw_path = output_dir / "provider-responses" / f"{raw_hash}.json"
                try:
                    raw = raw_path.read_bytes()
                except OSError as exc:
                    raise ValueError(
                        f"fresh OpenRouter route lacks raw evidence for {condition.condition_id}"
                    ) from exc
                if sha256(raw).hexdigest() != raw_hash:
                    raise ValueError(
                        f"fresh OpenRouter raw evidence is corrupt for {condition.condition_id}"
                    )
                raw_hashes[field] = raw_hash
            evidence_bytes = path.read_bytes()
            condition_receipts.append(
                {
                    "condition_id": condition.condition_id,
                    "evidence_path": expected_name,
                    "evidence_sha256": sha256(evidence_bytes).hexdigest(),
                    "raw_response_sha256": raw_hashes,
                }
            )

        artifact_paths = sorted(path for path in output_dir.rglob("*") if path.is_file())
        if not artifact_paths or len(artifact_paths) > MAX_ROUTE_CAPTURE_FILES:
            raise ValueError("fresh OpenRouter route capture has an invalid artifact count")
        artifacts: list[tuple[str, bytes]] = []
        artifact_receipts: list[dict[str, Any]] = []
        total_bytes = 0
        for path in artifact_paths:
            if path.is_symlink():
                raise ValueError("fresh OpenRouter route capture contains a symlink")
            relative = path.relative_to(output_dir).as_posix()
            raw = path.read_bytes()
            total_bytes += len(raw)
            if total_bytes > MAX_ROUTE_CAPTURE_BYTES:
                raise ValueError("fresh OpenRouter route capture is unexpectedly large")
            digest = sha256(raw).hexdigest()
            if relative.startswith("provider-responses/") and Path(relative).stem != digest:
                raise ValueError("fresh OpenRouter raw evidence is not content-addressed")
            artifacts.append((relative, raw))
            artifact_receipts.append({"path": relative, "sha256": digest, "size_bytes": len(raw)})

        receipt = {
            "schema_version": "atb-openrouter-route-receipt-v0.1",
            "protocol_id": manifest.protocol_id,
            "manifest_sha256": manifest_sha256,
            "observed_at": observed_at,
            "conditions": sorted(condition_receipts, key=lambda item: item["condition_id"]),
            "artifacts": artifact_receipts,
        }
        receipt_bytes = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
        return FreshRouteCapture(
            receipt_bytes=receipt_bytes,
            receipt_sha256=sha256(receipt_bytes).hexdigest(),
            artifacts=tuple(artifacts),
        )


def persist_fresh_openrouter_route_capture(
    capture: FreshRouteCapture,
    run_log_dir: Path,
) -> str:
    """Write the verified public snapshot once with owner-only permissions."""

    capture_dir = run_log_dir / "openrouter-route-capture"
    try:
        capture_dir.mkdir(mode=0o700)
    except OSError as exc:
        raise ValueError("cannot create the OpenRouter route-receipt directory") from exc

    def write_new(path: Path, raw: bytes) -> None:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(path, flags, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(raw)
        except OSError as exc:
            raise ValueError("cannot persist the OpenRouter route receipt safely") from exc

    for relative, raw in capture.artifacts:
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError("OpenRouter route receipt contains an unsafe artifact path")
        write_new(capture_dir / relative_path, raw)
    write_new(capture_dir / "receipt.json", capture.receipt_bytes)
    if sha256((capture_dir / "receipt.json").read_bytes()).hexdigest() != capture.receipt_sha256:
        raise ValueError("persisted OpenRouter route receipt hash does not match")
    return capture.receipt_sha256
