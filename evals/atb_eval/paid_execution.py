"""Fail-closed authorization and provider-budget checks for paid executions."""

from __future__ import annotations

import json
import math
import os
import re
import stat
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import Any, Literal, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from pydantic import BaseModel, ConfigDict, Field, field_validator

from atb_eval.manifest import ModelCondition, ProtocolManifest

OPENROUTER_KEY_STATUS_URL = "https://openrouter.ai/api/v1/key"
OPENROUTER_MANAGEMENT_KEYS_URL = "https://openrouter.ai/api/v1/keys"
MAX_PERMIT_BYTES = 64 * 1024
MAX_PERMIT_LIFETIME = timedelta(hours=24)
MAX_ROUTE_CAPTURE_BYTES = 64 * 1024 * 1024
MAX_ROUTE_CAPTURE_FILES = 64
_ROUTE_RECEIPT_SCHEMA = "atb-openrouter-route-receipt-v0.1"
_ROUTE_EVIDENCE_SCHEMA = "atb-model-revision-evidence-v0.1"
_RAW_RESPONSE_HASH_FIELDS = (
    "model_response_sha256",
    "models_response_sha256",
    "endpoint_response_sha256",
    "zdr_response_sha256",
)
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_UTC_TIMESTAMP_PATTERN = re.compile(r"^20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


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


def _valid_route_observed_at(value: Any) -> str:
    if not isinstance(value, str) or _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise ValueError("OpenRouter route receipt observed_at is invalid")
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise ValueError("OpenRouter route receipt observed_at is invalid") from exc
    if parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError("OpenRouter route receipt observed_at must be UTC")
    return value


def _expected_openrouter_route_conditions(
    manifest: ProtocolManifest,
) -> dict[str, ModelCondition]:
    expected: dict[str, ModelCondition] = {}
    for condition in [*manifest.models, *manifest.model_roles.values()]:
        if not condition.model.startswith("openrouter/"):
            continue
        if condition.revision is None:
            raise ValueError("OpenRouter route condition lacks frozen revision evidence")
        if condition.condition_id in expected:
            raise ValueError("OpenRouter route condition ids are not unique")
        expected[condition.condition_id] = condition
    if not expected:
        raise ValueError("OpenRouter route capture has no frozen conditions")
    return expected


def _frozen_route_evidence_projection(
    condition: ModelCondition,
    observed_at: str,
) -> dict[str, Any]:
    revision = condition.revision
    if revision is None:
        raise ValueError("OpenRouter route condition lacks frozen revision evidence")
    return {
        "schema_version": _ROUTE_EVIDENCE_SCHEMA,
        "requested_model": condition.model.removeprefix("openrouter/"),
        "resolved_model": revision.resolved_model,
        "canonical_slug": revision.canonical_slug,
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
        "zdr_eligible": True,
        "pricing_usd_per_million": (
            condition.pricing.model_dump() if condition.pricing is not None else None
        ),
    }


def _safe_route_artifact_path(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("OpenRouter route receipt contains an invalid artifact path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.as_posix() != value
    ):
        raise ValueError("OpenRouter route receipt contains an unsafe artifact path")
    return value


def _read_regular_route_file(path: Path, *, maximum_bytes: int) -> bytes:
    if path.is_symlink():
        raise ValueError("OpenRouter route capture contains a symlink")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValueError("OpenRouter route artifact cannot be opened safely") from exc
    try:
        details = os.fstat(descriptor)
        if not stat.S_ISREG(details.st_mode):
            raise ValueError("OpenRouter route capture contains a non-regular file")
        if details.st_size > maximum_bytes:
            raise ValueError("OpenRouter route capture is unexpectedly large")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            raw = handle.read(maximum_bytes + 1)
    except OSError as exc:
        raise ValueError("OpenRouter route artifact cannot be read safely") from exc
    finally:
        os.close(descriptor)
    if len(raw) > maximum_bytes:
        raise ValueError("OpenRouter route capture is unexpectedly large")
    return raw


def _route_capture_regular_files(capture_dir: Path) -> dict[str, Path]:
    if capture_dir.is_symlink() or not capture_dir.is_dir():
        raise ValueError("OpenRouter route capture directory is missing or unsafe")
    files: dict[str, Path] = {}

    def walk_error(error: OSError) -> None:
        raise ValueError("OpenRouter route capture cannot be traversed safely") from error

    for directory, directory_names, file_names in os.walk(
        capture_dir,
        topdown=True,
        onerror=walk_error,
        followlinks=False,
    ):
        directory_path = Path(directory)
        for name in directory_names:
            child = directory_path / name
            try:
                details = child.lstat()
            except OSError as exc:
                raise ValueError("OpenRouter route capture cannot be traversed safely") from exc
            if stat.S_ISLNK(details.st_mode):
                raise ValueError("OpenRouter route capture contains a symlink")
            if not stat.S_ISDIR(details.st_mode):
                raise ValueError("OpenRouter route capture contains an unsafe path")
        for name in file_names:
            path = directory_path / name
            try:
                details = path.lstat()
            except OSError as exc:
                raise ValueError("OpenRouter route artifact cannot be inspected safely") from exc
            if stat.S_ISLNK(details.st_mode):
                raise ValueError("OpenRouter route capture contains a symlink")
            if not stat.S_ISREG(details.st_mode):
                raise ValueError("OpenRouter route capture contains a non-regular file")
            relative = path.relative_to(capture_dir).as_posix()
            _safe_route_artifact_path(relative)
            if relative in files:
                raise ValueError("OpenRouter route capture contains duplicate paths")
            files[relative] = path
            if len(files) > MAX_ROUTE_CAPTURE_FILES + 1:
                raise ValueError("OpenRouter route capture has too many files")
    return files


def verify_fresh_openrouter_route_capture(
    manifest: ProtocolManifest,
    repo_root: Path,
    *,
    observed_at: str,
    manifest_sha256: str,
) -> FreshRouteCapture:
    """Require a fresh public recapture to match every frozen route before spending."""

    _valid_route_observed_at(observed_at)
    expected_conditions = _expected_openrouter_route_conditions(manifest)
    capture_profiles = {
        "diselect": "diselect-v05",
        "ape": "ape-stage2a-v01",
    }
    try:
        capture_profile = capture_profiles[manifest.task.kind]
    except KeyError as exc:
        raise ValueError("no public OpenRouter route-capture profile exists for this task") from exc
    script = repo_root / "scripts/capture_openrouter_routes.py"
    with TemporaryDirectory(prefix="atb-openrouter-preflight-") as temp_dir:
        output_dir = Path(temp_dir) / "capture"
        try:
            subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--profile",
                    capture_profile,
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
        for condition in expected_conditions.values():
            if condition.revision is None:
                raise ValueError("OpenRouter route condition lacks frozen revision evidence")
            expected_name = Path(condition.revision.evidence_path).name
            path = output_dir / expected_name
            try:
                evidence = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(
                    f"fresh OpenRouter route evidence is missing for {condition.condition_id}"
                ) from exc
            expected = _frozen_route_evidence_projection(condition, observed_at)
            if any(evidence.get(key) != value for key, value in expected.items()):
                raise ValueError(
                    f"fresh OpenRouter route no longer matches {condition.condition_id}"
                )

            raw_hashes: dict[str, str] = {}
            for field in _RAW_RESPONSE_HASH_FIELDS:
                raw_hash = evidence.get(field)
                if not isinstance(raw_hash, str) or _SHA256_PATTERN.fullmatch(raw_hash) is None:
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
            "schema_version": _ROUTE_RECEIPT_SCHEMA,
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


def verify_persisted_openrouter_route_capture(
    manifest: ProtocolManifest,
    capture_dir: Path,
    *,
    manifest_sha256: str,
    expected_receipt_sha256: str,
) -> dict[str, Any]:
    """Offline-verify a persisted route capture and return a redacted summary."""

    if _SHA256_PATTERN.fullmatch(manifest_sha256) is None:
        raise ValueError("OpenRouter route manifest SHA-256 is invalid")
    if _SHA256_PATTERN.fullmatch(expected_receipt_sha256) is None:
        raise ValueError("OpenRouter route receipt SHA-256 is invalid")

    files = _route_capture_regular_files(capture_dir)
    if "receipt.json" not in files:
        raise ValueError("OpenRouter route receipt is missing")
    receipt_bytes = _read_regular_route_file(
        files["receipt.json"], maximum_bytes=MAX_ROUTE_CAPTURE_BYTES
    )
    receipt_sha256 = sha256(receipt_bytes).hexdigest()
    if receipt_sha256 != expected_receipt_sha256:
        raise ValueError("OpenRouter route receipt does not match execution metadata")
    try:
        receipt = json.loads(receipt_bytes, object_pairs_hook=_unique_json_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("OpenRouter route receipt is invalid") from exc
    if not isinstance(receipt, dict) or set(receipt) != {
        "schema_version",
        "protocol_id",
        "manifest_sha256",
        "observed_at",
        "conditions",
        "artifacts",
    }:
        raise ValueError("OpenRouter route receipt has an unexpected schema")
    observed_at = _valid_route_observed_at(receipt.get("observed_at"))
    if (
        receipt.get("schema_version") != _ROUTE_RECEIPT_SCHEMA
        or receipt.get("protocol_id") != manifest.protocol_id
        or receipt.get("manifest_sha256") != manifest_sha256
    ):
        raise ValueError("OpenRouter route receipt does not match the frozen execution")

    artifact_rows = receipt.get("artifacts")
    if (
        not isinstance(artifact_rows, list)
        or not artifact_rows
        or len(artifact_rows) > MAX_ROUTE_CAPTURE_FILES
    ):
        raise ValueError("OpenRouter route receipt has an invalid artifact inventory")
    artifact_inventory: dict[str, dict[str, Any]] = {}
    for row in artifact_rows:
        if not isinstance(row, dict) or set(row) != {"path", "sha256", "size_bytes"}:
            raise ValueError("OpenRouter route artifact receipt is invalid")
        relative = _safe_route_artifact_path(row.get("path"))
        digest = row.get("sha256")
        size = row.get("size_bytes")
        if (
            relative == "receipt.json"
            or relative in artifact_inventory
            or not isinstance(digest, str)
            or _SHA256_PATTERN.fullmatch(digest) is None
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size < 0
        ):
            raise ValueError("OpenRouter route artifact receipt is invalid")
        artifact_inventory[relative] = row
    if [row["path"] for row in artifact_rows] != sorted(artifact_inventory):
        raise ValueError("OpenRouter route artifact inventory is not canonical")
    if set(files) != {"receipt.json", *artifact_inventory}:
        raise ValueError("OpenRouter route artifact inventory is not exact")

    artifact_bytes: dict[str, bytes] = {}
    total_bytes = 0
    for relative, row in artifact_inventory.items():
        remaining = MAX_ROUTE_CAPTURE_BYTES - total_bytes
        if remaining < 0:
            raise ValueError("OpenRouter route capture is unexpectedly large")
        raw = _read_regular_route_file(files[relative], maximum_bytes=remaining)
        total_bytes += len(raw)
        digest = sha256(raw).hexdigest()
        if digest != row["sha256"] or len(raw) != row["size_bytes"]:
            raise ValueError("OpenRouter route artifact does not match its receipt")
        parts = PurePosixPath(relative).parts
        if parts[0] == "provider-responses" and (
            len(parts) != 2
            or not parts[1].endswith(".json")
            or parts[1].removesuffix(".json") != digest
        ):
            raise ValueError("OpenRouter raw evidence is not content-addressed")
        artifact_bytes[relative] = raw

    expected_conditions = _expected_openrouter_route_conditions(manifest)
    condition_rows = receipt.get("conditions")
    if not isinstance(condition_rows, list) or any(
        not isinstance(row, dict) for row in condition_rows
    ):
        raise ValueError("OpenRouter route receipt lacks exact condition evidence")
    if [row.get("condition_id") for row in condition_rows] != sorted(expected_conditions):
        raise ValueError("OpenRouter route receipt condition inventory is not exact")

    seen_conditions: set[str] = set()
    evidence_paths: set[str] = set()
    referenced_raw_paths: set[str] = set()
    for row in condition_rows:
        if set(row) != {
            "condition_id",
            "evidence_path",
            "evidence_sha256",
            "raw_response_sha256",
        }:
            raise ValueError("OpenRouter route condition receipt is invalid")
        condition_id = row.get("condition_id")
        if (
            not isinstance(condition_id, str)
            or condition_id not in expected_conditions
            or condition_id in seen_conditions
        ):
            raise ValueError("OpenRouter route receipt has an unexpected condition")
        seen_conditions.add(condition_id)
        condition = expected_conditions[condition_id]
        revision = condition.revision
        if revision is None:
            raise ValueError("OpenRouter route condition lacks frozen revision evidence")
        evidence_path = _safe_route_artifact_path(row.get("evidence_path"))
        if (
            evidence_path != Path(revision.evidence_path).name
            or evidence_path not in artifact_inventory
            or evidence_path in evidence_paths
        ):
            raise ValueError("OpenRouter route evidence path does not match its condition")
        evidence_paths.add(evidence_path)
        evidence_digest = sha256(artifact_bytes[evidence_path]).hexdigest()
        if (
            row.get("evidence_sha256") != evidence_digest
            or artifact_inventory[evidence_path]["sha256"] != evidence_digest
        ):
            raise ValueError("OpenRouter route condition evidence hash does not match")
        try:
            evidence = json.loads(
                artifact_bytes[evidence_path], object_pairs_hook=_unique_json_object
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError("OpenRouter route condition evidence is invalid") from exc
        if not isinstance(evidence, dict):
            raise ValueError("OpenRouter route condition evidence is invalid")
        expected_projection = _frozen_route_evidence_projection(condition, observed_at)
        if any(evidence.get(key) != value for key, value in expected_projection.items()):
            raise ValueError("OpenRouter route evidence no longer matches its frozen condition")

        raw_hashes = row.get("raw_response_sha256")
        if not isinstance(raw_hashes, dict) or set(raw_hashes) != set(_RAW_RESPONSE_HASH_FIELDS):
            raise ValueError("OpenRouter route condition lacks exact raw evidence hashes")
        for field in _RAW_RESPONSE_HASH_FIELDS:
            raw_digest = raw_hashes[field]
            if (
                not isinstance(raw_digest, str)
                or _SHA256_PATTERN.fullmatch(raw_digest) is None
                or evidence.get(field) != raw_digest
            ):
                raise ValueError("OpenRouter route raw evidence hash does not match")
            raw_path = f"provider-responses/{raw_digest}.json"
            if raw_path not in artifact_inventory:
                raise ValueError("OpenRouter route raw evidence is absent from the inventory")
            referenced_raw_paths.add(raw_path)

    if seen_conditions != set(expected_conditions):
        raise ValueError("OpenRouter route receipt condition inventory is incomplete")
    provider_paths = {
        relative
        for relative in artifact_inventory
        if PurePosixPath(relative).parts[0] == "provider-responses"
    }
    if provider_paths != referenced_raw_paths:
        raise ValueError("OpenRouter raw artifact inventory is not exactly referenced")
    if set(artifact_inventory) - provider_paths != evidence_paths:
        raise ValueError("OpenRouter route evidence inventory has unexpected files")

    canonical_inventory = json.dumps(artifact_rows, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schema_version": _ROUTE_RECEIPT_SCHEMA,
        "receipt_sha256": receipt_sha256,
        "receipt_size_bytes": len(receipt_bytes),
        "observed_at": observed_at,
        "condition_ids": sorted(expected_conditions),
        "artifact_count": len(artifact_inventory),
        "artifact_bytes": total_bytes,
        "artifact_inventory_sha256": sha256(canonical_inventory).hexdigest(),
    }


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
