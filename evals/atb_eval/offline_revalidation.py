"""Fail-closed offline revalidation of persisted paid-evaluation evidence.

The generated receipt contains hashes, provenance, usage, and acceptance state.
It deliberately excludes prompts, responses, request payloads, and provider
response bodies. The complete persisted-execution postflight is delegated to the same
``validate_persisted_execution`` helper used by the online runner.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import os
import re
import stat
import sys
import tempfile
import zipfile
from collections.abc import Mapping, Sequence
from contextlib import suppress
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any

from atb_eval import artifact_scan, runner
from atb_eval.execution_receipt import controlled_usage_summary
from atb_eval.manifest import ProtocolManifest, load_manifest_with_hash
from atb_eval.paid_execution import verify_persisted_openrouter_route_capture

_COMMIT_PATTERN = re.compile(r"^[a-f0-9]{40}$")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_EXECUTION_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")
_REVALIDATION_RECEIPT_SCHEMA = "atb-offline-postflight-revalidation-receipt-v0.1"
_HISTORICAL_RECEIPT_SCHEMA = "atb-controlled-canary-receipt-v0.1"
_MAX_ARCHIVE_MEMBERS = 10_000
_MAX_ARCHIVE_BYTES = 128 * 1024 * 1024
_MAX_ARCHIVE_UNCOMPRESSED_BYTES = 512 * 1024 * 1024
_MAX_ARCHIVE_MEMBER_BYTES = 128 * 1024 * 1024
_MAX_COMPRESSION_RATIO = 200
_CHECKSUM_LINE = re.compile(r"^([a-f0-9]{64})  \./(.+)$")
_HISTORICAL_RECEIPT_KEYS = {
    "schema_version",
    "protocol_id",
    "manifest_sha256",
    "public_commit",
    "source_commit",
    "workflow_actor",
    "workflow_run_id",
    "paid_step_outcome",
    "planned_run_cost_envelope_usd",
    "provider_key_lifetime_cap_usd",
    "recorded_at",
}


def _require_match(value: str, pattern: re.Pattern[str], label: str) -> str:
    if pattern.fullmatch(value) is None:
        raise ValueError(f"{label} has an invalid format")
    return value


def _require_regular_single_link(path: Path, label: str) -> os.stat_result:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ValueError(f"{label} is unavailable") from exc
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise ValueError(f"{label} must be a regular single-link file")
    return metadata


def _verified_archive_bytes(path: Path, expected_sha256: str) -> tuple[bytes, str]:
    _require_match(expected_sha256, _SHA256_PATTERN, "artifact SHA-256")
    before = _require_regular_single_link(path, "artifact archive")
    if before.st_size > _MAX_ARCHIVE_BYTES:
        raise ValueError("artifact archive is too large")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    digest = sha256()
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as handle:
            opened = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_nlink != 1
                or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)
            ):
                raise ValueError("artifact archive changed before verification")
            content = handle.read(_MAX_ARCHIVE_BYTES + 1)
            if len(content) > _MAX_ARCHIVE_BYTES:
                raise ValueError("artifact archive is too large")
            digest.update(content)
            after = os.fstat(handle.fileno())
            if (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns) != (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
            ):
                raise ValueError("artifact archive changed during verification")
            actual = digest.hexdigest()
            if actual != expected_sha256:
                raise ValueError("artifact archive SHA-256 does not match")
            return content, actual
    except OSError as exc:
        raise ValueError("artifact archive cannot be hashed safely") from exc


def _safe_archive_name(name: str) -> PurePosixPath:
    if not name or not name.isascii() or "\\" in name or "\x00" in name or ":" in name:
        raise ValueError("artifact archive contains an unsafe member path")
    raw_name = name[:-1] if name.endswith("/") else name
    raw_parts = raw_name.split("/")
    path = PurePosixPath(raw_name)
    if (
        path.is_absolute()
        or not path.parts
        or any(part in {"", ".", ".."} for part in raw_parts)
        or path.as_posix() != raw_name
    ):
        raise ValueError("artifact archive contains an unsafe member path")
    return path


def _validated_zip_inventory(
    archive: zipfile.ZipFile,
) -> list[tuple[zipfile.ZipInfo, PurePosixPath]]:
    infos = archive.infolist()
    if not infos or len(infos) > _MAX_ARCHIVE_MEMBERS:
        raise ValueError("artifact archive member count is invalid")
    inventory: list[tuple[zipfile.ZipInfo, PurePosixPath]] = []
    names: set[str] = set()
    folded_names: set[str] = set()
    file_names: set[str] = set()
    total_size = 0
    for info in infos:
        path = _safe_archive_name(info.filename)
        normalized = path.as_posix()
        folded = normalized.casefold()
        if normalized in names or folded in folded_names:
            raise ValueError("artifact archive contains duplicate member paths")
        names.add(normalized)
        folded_names.add(folded)
        unix_type = stat.S_IFMT(info.external_attr >> 16) if info.create_system == 3 else 0
        expected_type = stat.S_IFDIR if info.is_dir() else stat.S_IFREG
        if unix_type not in {0, expected_type}:
            raise ValueError("artifact archive contains a non-regular member")
        if info.flag_bits & 0x1 or info.compress_type not in {
            zipfile.ZIP_STORED,
            zipfile.ZIP_DEFLATED,
        }:
            raise ValueError("artifact archive uses unsupported ZIP features")
        if info.file_size < 0 or info.file_size > _MAX_ARCHIVE_MEMBER_BYTES:
            raise ValueError("artifact archive member is too large")
        total_size += info.file_size
        if total_size > _MAX_ARCHIVE_UNCOMPRESSED_BYTES:
            raise ValueError("artifact archive is too large")
        if info.file_size and info.file_size / max(info.compress_size, 1) > _MAX_COMPRESSION_RATIO:
            raise ValueError("artifact archive compression ratio is unsafe")
        if not info.is_dir():
            file_names.add(folded)
        inventory.append((info, path))
    for _, path in inventory:
        for parent in path.parents:
            if parent != PurePosixPath(".") and parent.as_posix().casefold() in file_names:
                raise ValueError("artifact archive has a file/directory path collision")
    return inventory


def _extract_verified_archive(
    archive_path: Path, expected_sha256: str, root: Path
) -> dict[str, Any]:
    archive_bytes, verified_sha256 = _verified_archive_bytes(archive_path, expected_sha256)
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            inventory = _validated_zip_inventory(archive)
            inventory_rows = sorted(
                (
                    {
                        "path": path.as_posix(),
                        "directory": info.is_dir(),
                        "size_bytes": info.file_size,
                        "compressed_size_bytes": info.compress_size,
                        "crc32": f"{info.CRC:08x}",
                        "compression": info.compress_type,
                    }
                    for info, path in inventory
                ),
                key=lambda row: row["path"],
            )
            root.mkdir(mode=0o700, parents=False, exist_ok=False)
            for info, relative in inventory:
                target = root.joinpath(*relative.parts)
                if info.is_dir():
                    target.mkdir(mode=0o700, parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
                descriptor = os.open(target, flags, 0o600)
                try:
                    with archive.open(info, "r") as source, os.fdopen(descriptor, "wb") as output:
                        descriptor = -1
                        while chunk := source.read(1024 * 1024):
                            output.write(chunk)
                finally:
                    if descriptor >= 0:
                        os.close(descriptor)
                _require_regular_single_link(target, "extracted artifact member")
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        raise ValueError("artifact archive cannot be extracted safely") from exc
    _verify_archive_checksums(root)
    inventory_content = json.dumps(inventory_rows, sort_keys=True, separators=(",", ":")).encode()
    return {
        "sha256": verified_sha256,
        "size_bytes": len(archive_bytes),
        "member_count": len(inventory_rows),
        "uncompressed_bytes": sum(row["size_bytes"] for row in inventory_rows),
        "inventory_sha256": sha256(inventory_content).hexdigest(),
        "checksums_verified": True,
    }


def _verify_archive_checksums(root: Path) -> None:
    checksum_path = root / "checksums.sha256"
    _require_regular_single_link(checksum_path, "artifact checksum manifest")
    try:
        lines = checksum_path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ValueError("artifact checksum manifest cannot be read safely") from exc
    expected: dict[str, str] = {}
    folded: set[str] = set()
    for line in lines:
        match = _CHECKSUM_LINE.fullmatch(line)
        if match is None:
            raise ValueError("artifact checksum manifest is malformed")
        digest, raw_path = match.groups()
        path = _safe_archive_name(raw_path).as_posix()
        if path == "checksums.sha256" or path in expected or path.casefold() in folded:
            raise ValueError("artifact checksum manifest contains a duplicate path")
        expected[path] = digest
        folded.add(path.casefold())
    actual_paths: dict[str, Path] = {}
    for path in root.rglob("*"):
        if path.is_dir():
            if path.is_symlink():
                raise ValueError("artifact extraction contains a symbolic link")
            continue
        _require_regular_single_link(path, "extracted artifact member")
        relative = path.relative_to(root).as_posix()
        if relative != "checksums.sha256":
            actual_paths[relative] = path
    if set(actual_paths) != set(expected):
        raise ValueError("artifact checksum manifest does not match the file inventory")
    for relative, path in actual_paths.items():
        digest, _ = _sha256_path(path)
        if digest != expected[relative]:
            raise ValueError("artifact checksum verification failed")


def _strict_json_object(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("JSON object contains a duplicate key")
            result[key] = value
        return result

    def reject_constant(unused: str) -> Any:
        raise ValueError("non-finite JSON number")

    _require_regular_single_link(path, "historical workflow receipt")
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("historical workflow receipt cannot be read safely") from exc
    if not isinstance(value, dict):
        raise ValueError("historical workflow receipt must be an object")
    return value


def _historical_receipt(
    root: Path, *, expected_workflow_run_id: str, expected_execution_commit: str
) -> dict[str, Any]:
    receipt = _strict_json_object(root / "receipt.json")
    if set(receipt) != _HISTORICAL_RECEIPT_KEYS:
        raise ValueError("historical workflow receipt schema is invalid")
    required_strings = {
        "schema_version",
        "protocol_id",
        "manifest_sha256",
        "public_commit",
        "source_commit",
        "workflow_actor",
        "workflow_run_id",
        "paid_step_outcome",
        "recorded_at",
    }
    if any(type(receipt[key]) is not str for key in required_strings):
        raise ValueError("historical workflow receipt types are invalid")
    if receipt["schema_version"] != _HISTORICAL_RECEIPT_SCHEMA:
        raise ValueError("historical workflow receipt schema is invalid")
    _require_match(receipt["manifest_sha256"], _SHA256_PATTERN, "historical manifest hash")
    _require_match(receipt["public_commit"], _COMMIT_PATTERN, "historical public commit")
    _require_match(receipt["source_commit"], _COMMIT_PATTERN, "historical source commit")
    if (
        not receipt["workflow_run_id"].isascii()
        or not receipt["workflow_run_id"].isdigit()
        or int(receipt["workflow_run_id"]) < 1
        or receipt["workflow_run_id"] != expected_workflow_run_id
    ):
        raise ValueError("historical workflow run id does not match")
    if receipt["public_commit"] != expected_execution_commit:
        raise ValueError("historical public commit does not match")
    if receipt["paid_step_outcome"] not in {"success", "failure", "cancelled", "skipped"}:
        raise ValueError("historical paid step outcome is invalid")
    for key in ("planned_run_cost_envelope_usd", "provider_key_lifetime_cap_usd"):
        if (
            type(receipt[key]) not in {int, float}
            or not math.isfinite(receipt[key])
            or receipt[key] < 0
        ):
            raise ValueError("historical workflow receipt costs are invalid")
    return receipt


def _relative_log_root(root: Path, value: str) -> Path:
    relative = _safe_archive_name(value)
    candidate = root.joinpath(*relative.parts)
    if candidate.is_symlink() or not candidate.is_dir():
        raise ValueError("Inspect log root is not a regular archive directory")
    all_eval_paths = set(root.rglob("*.eval"))
    selected_eval_paths = set(candidate.rglob("*.eval"))
    if all_eval_paths != selected_eval_paths:
        raise ValueError("Inspect eval logs exist outside the selected archive log root")
    return candidate


def _sha256_path(path: Path) -> tuple[str, int]:
    _require_regular_single_link(path, "evidence file")
    digest = sha256()
    size = 0
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                size += len(chunk)
                digest.update(chunk)
    except OSError as exc:
        raise ValueError("evidence file cannot be hashed safely") from exc
    return digest.hexdigest(), size


def _load_evidence_logs(log_root: Path) -> tuple[list[Path], list[Any]]:
    if log_root.is_symlink() or not log_root.is_dir():
        raise ValueError("Inspect log root must be a regular directory")
    paths = sorted(log_root.rglob("*.eval"))
    if not paths:
        raise ValueError("no persisted Inspect eval logs were found")
    for path in paths:
        _require_regular_single_link(path, "persisted Inspect eval log")
    try:
        return paths, [runner.read_postflight_log(path) for path in paths]
    except Exception as exc:
        raise ValueError("persisted Inspect eval logs cannot be read safely") from exc


def _consistent_metadata(logs: Sequence[Any], key: str) -> Any:
    values: list[Any] = []
    for log in logs:
        metadata = getattr(getattr(log, "eval", None), "metadata", None)
        if not isinstance(metadata, Mapping) or key not in metadata:
            raise ValueError("persisted Inspect metadata is incomplete")
        values.append(metadata[key])
    first = values[0]
    if any(value != first for value in values[1:]):
        raise ValueError("persisted Inspect metadata is inconsistent")
    return first


def execution_context_from_logs(
    logs: Sequence[Any],
    manifest: ProtocolManifest,
    manifest_sha256: str,
    execution_commit: str,
) -> dict[str, Any]:
    """Derive safe execution provenance only when every log agrees exactly."""

    if not logs:
        raise ValueError("persisted Inspect evidence is empty")
    _require_match(execution_commit, _COMMIT_PATTERN, "execution commit")
    if _consistent_metadata(logs, "atb_protocol_id") != manifest.protocol_id:
        raise ValueError("persisted protocol id does not match the manifest")
    if _consistent_metadata(logs, "atb_manifest_sha256") != manifest_sha256:
        raise ValueError("persisted manifest hash does not match")
    if _consistent_metadata(logs, "atb_code_commit") != execution_commit:
        raise ValueError("execution commit does not match persisted metadata")
    code_dirty = _consistent_metadata(logs, "atb_code_dirty")
    if code_dirty is not False:
        raise ValueError("offline revalidation requires a clean original execution")
    environment_lock_sha256 = _consistent_metadata(logs, "atb_environment_lock_sha256")
    execution_id = _consistent_metadata(logs, "atb_execution_id")
    if not isinstance(environment_lock_sha256, str):
        raise ValueError("persisted environment lock hash is invalid")
    if not isinstance(execution_id, str):
        raise ValueError("persisted execution id is invalid")
    _require_match(environment_lock_sha256, _SHA256_PATTERN, "execution lock SHA-256")
    _require_match(execution_id, _EXECUTION_ID_PATTERN, "execution id")

    route_conditions = [
        condition
        for condition in [*manifest.models, *manifest.model_roles.values()]
        if condition.model.startswith("openrouter/")
    ]
    route_receipt_sha256: str | None = None
    if route_conditions:
        route_receipt_sha256 = _consistent_metadata(logs, "atb_openrouter_route_receipt_sha256")
        if not isinstance(route_receipt_sha256, str):
            raise ValueError("persisted route receipt hash is invalid")
        _require_match(route_receipt_sha256, _SHA256_PATTERN, "route receipt SHA-256")
    return {
        "code_commit": execution_commit,
        "code_dirty": False,
        "environment_lock_sha256": environment_lock_sha256,
        "execution_id": execution_id,
        "openrouter_route_receipt_sha256": route_receipt_sha256,
    }


def _eval_log_inventory(paths: Sequence[Path], log_root: Path) -> tuple[list[dict[str, Any]], str]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        digest, size = _sha256_path(path)
        rows.append(
            {
                "relative_path": path.relative_to(log_root).as_posix(),
                "sha256": digest,
                "size_bytes": size,
            }
        )
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return rows, sha256(canonical).hexdigest()


def _shared_postflight_acceptance(
    manifest: ProtocolManifest,
    log_root: Path,
    manifest_sha256: str,
    execution_context: Mapping[str, Any],
) -> bool:
    validator = getattr(runner, "validate_persisted_execution", None)
    if not callable(validator):
        raise ValueError("shared persisted-execution validator is unavailable")
    provenance = {
        "code_commit": execution_context["code_commit"],
        "code_dirty": execution_context["code_dirty"],
        "environment_lock_sha256": execution_context["environment_lock_sha256"],
    }
    result = validator(
        manifest,
        log_root,
        manifest_sha256,
        provenance,
        execution_id=execution_context["execution_id"],
        route_receipt_sha256=execution_context["openrouter_route_receipt_sha256"],
    )
    if type(result) is not bool:
        raise ValueError("shared persisted-execution validator returned an invalid result")
    return result


def build_revalidation_receipt(
    *,
    manifest_path: Path,
    artifact_root: Path,
    log_root: Path,
    execution_commit: str,
    validation_commit: str,
    validation_environment_lock_sha256: str,
    artifact_sha256: str,
    artifact_archive_metadata: Mapping[str, Any],
    workflow_run_id: str,
) -> dict[str, Any]:
    """Build a content-bound, content-free postflight revalidation receipt."""

    _require_match(execution_commit, _COMMIT_PATTERN, "execution commit")
    _require_match(validation_commit, _COMMIT_PATTERN, "validation commit")
    _require_match(
        validation_environment_lock_sha256,
        _SHA256_PATTERN,
        "validation lock SHA-256",
    )
    _require_match(artifact_sha256, _SHA256_PATTERN, "artifact SHA-256")
    if not workflow_run_id.isascii() or not workflow_run_id.isdigit() or int(workflow_run_id) < 1:
        raise ValueError("workflow run id must be a positive decimal integer")

    manifest, manifest_sha256 = load_manifest_with_hash(manifest_path)
    historical = _historical_receipt(
        artifact_root,
        expected_workflow_run_id=workflow_run_id,
        expected_execution_commit=execution_commit,
    )
    if (
        historical["protocol_id"] != manifest.protocol_id
        or historical["manifest_sha256"] != manifest_sha256
        or historical["source_commit"] != manifest.dataset.source_revision
        or historical["planned_run_cost_envelope_usd"] != manifest.run.planned_run_cost_envelope_usd
        or historical["provider_key_lifetime_cap_usd"] != manifest.run.provider_key_limit_usd
    ):
        raise ValueError("historical workflow receipt does not match the manifest")
    if artifact_archive_metadata.get("sha256") != artifact_sha256:
        raise ValueError("verified archive metadata is inconsistent")
    required_archive_metadata = {
        "sha256",
        "size_bytes",
        "member_count",
        "uncompressed_bytes",
        "inventory_sha256",
        "checksums_verified",
    }
    if set(artifact_archive_metadata) != required_archive_metadata:
        raise ValueError("verified archive metadata is incomplete")
    if (
        artifact_archive_metadata["checksums_verified"] is not True
        or type(artifact_archive_metadata["size_bytes"]) is not int
        or artifact_archive_metadata["size_bytes"] < 1
        or type(artifact_archive_metadata["member_count"]) is not int
        or artifact_archive_metadata["member_count"] < 1
        or type(artifact_archive_metadata["uncompressed_bytes"]) is not int
        or artifact_archive_metadata["uncompressed_bytes"] < 0
        or not isinstance(artifact_archive_metadata["inventory_sha256"], str)
    ):
        raise ValueError("verified archive metadata is invalid")
    _require_match(
        artifact_archive_metadata["inventory_sha256"],
        _SHA256_PATTERN,
        "archive inventory SHA-256",
    )
    if artifact_scan.scan_artifacts(artifact_root):
        raise ValueError("local artifact scan found unsafe evidence")
    paths, logs = _load_evidence_logs(log_root)
    execution_context = execution_context_from_logs(
        logs, manifest, manifest_sha256, execution_commit
    )
    route_receipt_sha256 = execution_context["openrouter_route_receipt_sha256"]
    route_capture: dict[str, Any] | None = None
    if route_receipt_sha256 is not None:
        capture_paths = sorted(log_root.rglob("openrouter-route-capture/receipt.json"))
        if len(capture_paths) != 1:
            raise ValueError("exactly one OpenRouter route receipt is required")
        route_capture = verify_persisted_openrouter_route_capture(
            manifest,
            capture_paths[0].parent,
            manifest_sha256=manifest_sha256,
            expected_receipt_sha256=route_receipt_sha256,
        )

    usage = controlled_usage_summary(log_root)
    if usage.get("eval_log_count") != len(paths):
        raise ValueError("usage receipt does not cover the exact eval-log inventory")
    acceptance = _shared_postflight_acceptance(
        manifest, log_root, manifest_sha256, execution_context
    )
    eval_logs, eval_inventory_sha256 = _eval_log_inventory(paths, log_root)
    controlled_evidence_accepted = acceptance
    return {
        "schema_version": _REVALIDATION_RECEIPT_SCHEMA,
        "source": "local_revalidation",
        "protocol_id": manifest.protocol_id,
        "manifest_sha256": manifest_sha256,
        "workflow_run_id": workflow_run_id,
        "artifact": {
            **artifact_archive_metadata,
            "sha256_source": "locally_verified_archive",
            "scanner_status": "passed",
            "scanner_status_source": "local_revalidation",
        },
        "original_paid_step_outcome": historical["paid_step_outcome"],
        "corrected_postflight_acceptance": acceptance,
        "controlled_evidence_accepted": controlled_evidence_accepted,
        "evidence_scope": "transport_canary_only",
        "scientific_claim_eligible": False,
        "execution": {
            **execution_context,
            "eval_log_count": len(eval_logs),
            "eval_logs": eval_logs,
            "eval_log_inventory_sha256": eval_inventory_sha256,
        },
        "validation": {
            "code_commit": validation_commit,
            "code_dirty": False,
            "environment_lock_sha256": validation_environment_lock_sha256,
        },
        "usage": usage,
        "openrouter_route_capture": route_capture,
    }


def _write_new(path: Path, content: bytes) -> None:
    if path.is_symlink():
        raise ValueError("receipt output cannot be a symbolic link")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
    except OSError as exc:
        raise ValueError("receipt output cannot be written safely") from exc


def write_content_addressed_receipt(output: Path, receipt: Mapping[str, Any]) -> str:
    """Write a receipt once and an adjacent full-file SHA-256 sidecar."""

    content = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
    digest = sha256(content).hexdigest()
    sidecar = output.with_name(f"{output.name}.sha256")
    _write_new(output, content)
    try:
        _write_new(sidecar, f"{digest}  {output.name}\n".encode())
    except Exception:
        with suppress(OSError):
            output.unlink()
        raise
    return digest


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--artifact-archive", required=True, type=Path)
    parser.add_argument("--log-root", required=True)
    parser.add_argument("--execution-commit", required=True)
    parser.add_argument("--validation-commit", required=True)
    parser.add_argument("--artifact-sha256", required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run revalidation without rendering untrusted paths, content, or exceptions."""

    args = parse_args(argv)
    try:
        output = args.output.resolve(strict=False)
        validation_provenance = runner.repository_provenance(runner.repository_root())
        if (
            validation_provenance.get("code_commit") != args.validation_commit
            or validation_provenance.get("code_dirty") is not False
        ):
            raise ValueError("validation checkout does not match the declared clean commit")
        validation_lock = validation_provenance.get("environment_lock_sha256")
        if not isinstance(validation_lock, str):
            raise ValueError("validation lock provenance is invalid")
        with tempfile.TemporaryDirectory(prefix="atb-offline-revalidation-") as temp:
            artifact_root = Path(temp) / "artifact"
            archive_metadata = _extract_verified_archive(
                args.artifact_archive, args.artifact_sha256, artifact_root
            )
            log_root = _relative_log_root(artifact_root, args.log_root)
            receipt = build_revalidation_receipt(
                manifest_path=args.manifest,
                artifact_root=artifact_root,
                log_root=log_root,
                execution_commit=args.execution_commit,
                validation_commit=args.validation_commit,
                validation_environment_lock_sha256=validation_lock,
                artifact_sha256=args.artifact_sha256,
                artifact_archive_metadata=archive_metadata,
                workflow_run_id=args.workflow_run_id,
            )
        receipt_sha256 = write_content_addressed_receipt(output, receipt)
    except Exception:
        print("offline postflight revalidation failed safely", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "corrected_postflight_acceptance": receipt["corrected_postflight_acceptance"],
                "controlled_evidence_accepted": receipt["controlled_evidence_accepted"],
                "scientific_claim_eligible": receipt["scientific_claim_eligible"],
                "receipt_sha256": receipt_sha256,
            },
            sort_keys=True,
        )
    )
    return 0 if receipt["corrected_postflight_acceptance"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
