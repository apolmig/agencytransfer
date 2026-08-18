"""Create blind, content-bound human-validation packets from controlled logs."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import stat
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from atb_eval import runner
from atb_eval.manifest import (
    ProtocolManifest,
    ProtocolStatus,
    load_manifest_with_hash,
    verify_committed_file,
)
from atb_eval.offline_revalidation import execution_context_from_logs
from atb_eval.paid_execution import verify_persisted_openrouter_route_capture
from atb_eval.release_gate import LoggedResponse, _stratified_probability_sample

BLINDED_FIELDS = ("model", "provider", "organisation", "release_date", "automated_score")
NATIVE_CLASSES = ("comply", "soft_refuse", "refuse", "incoherent")
ALL_REVIEW_CLASSES = (*NATIVE_CLASSES, "unscorable")
MAX_PRIVATE_JSON_BYTES = 32 * 1024 * 1024
MINIMUM_VALIDATION_FRAME = 30
_PSEUDONYM = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ReviewPacketItem(StrictModel):
    review_item_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_hmac: str = Field(pattern=r"^[a-f0-9]{64}$")
    request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    inclusion_probability: float = Field(gt=0, le=1)
    request: str = Field(min_length=1)
    response: str = Field(min_length=1)
    native_class: Literal["comply", "soft_refuse", "refuse", "incoherent", "unscorable"] | None = (
        None
    )


class ReviewPacket(StrictModel):
    schema_version: Literal["atb-validation-review-packet-v0.1"]
    packet_set_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    protocol_id: str = Field(min_length=1)
    codebook_version: str = Field(min_length=1)
    reviewer_pseudonym: str = Field(min_length=1)
    independent_read_attested: bool
    blinded_fields: list[
        Literal["model", "provider", "organisation", "release_date", "automated_score"]
    ]
    item_count: int = Field(ge=1)
    items: list[ReviewPacketItem] = Field(min_length=1)

    @field_validator("reviewer_pseudonym")
    @classmethod
    def valid_reviewer(cls, value: str) -> str:
        if _PSEUDONYM.fullmatch(value) is None or value in {"private-map", "codebook"}:
            raise ValueError("reviewer pseudonym is not safe")
        return value

    @model_validator(mode="after")
    def coherent_packet(self) -> ReviewPacket:
        if self.item_count != len(self.items):
            raise ValueError("review packet item_count does not match items")
        if tuple(self.blinded_fields) != BLINDED_FIELDS:
            raise ValueError("review packet does not preserve the frozen blinding contract")
        ids = [item.review_item_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("review packet contains duplicate items")
        return self


class PrivateMapItem(StrictModel):
    review_item_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_hmac: str = Field(pattern=r"^[a-f0-9]{64}$")
    condition_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    epoch: int = Field(ge=1)
    inclusion_probability: float = Field(gt=0, le=1)
    request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class PrivateMap(StrictModel):
    schema_version: Literal["atb-validation-private-map-v0.1"]
    packet_set_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    protocol_id: str = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    execution_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    code_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    evidence_inventory_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    codebook_version: str = Field(min_length=1)
    reviewer_pseudonyms: list[str] = Field(min_length=2, max_length=2)
    key_confirmation_hmac: str = Field(pattern=r"^[a-f0-9]{64}$")
    item_count: int = Field(ge=1)
    items: list[PrivateMapItem] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_map(self) -> PrivateMap:
        if self.item_count != len(self.items):
            raise ValueError("private map item_count does not match items")
        if len(set(self.reviewer_pseudonyms)) != 2 or any(
            _PSEUDONYM.fullmatch(value) is None for value in self.reviewer_pseudonyms
        ):
            raise ValueError("private map requires two distinct safe reviewer pseudonyms")
        ids = [item.review_item_id for item in self.items]
        keys = [(item.condition_id, item.sample_id, item.epoch) for item in self.items]
        if len(ids) != len(set(ids)) or len(keys) != len(set(keys)):
            raise ValueError("private map contains duplicate response identities")
        return self


@dataclass(frozen=True)
class FrameItem:
    condition_id: str
    sample_id: str
    epoch: int
    stratum: tuple[str, ...]
    request: str
    response: str


@dataclass(frozen=True)
class ExecutionFrame:
    manifest: ProtocolManifest
    manifest_sha256: str
    execution_id: str
    code_commit: str
    evidence_inventory_sha256: str
    items: tuple[FrameItem, ...]


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def _domain_hmac(key: bytes, domain: str, value: Any) -> str:
    return hmac.new(
        key,
        domain.encode("ascii") + b"\x00" + _canonical_json_bytes(value),
        hashlib.sha256,
    ).hexdigest()


def _key_confirmation_hmac(key: bytes, packet_set_id: str) -> str:
    return _domain_hmac(key, "atb-validation-key-confirmation-v0.1", packet_set_id)


def _response_hmac(
    key: bytes,
    *,
    packet_set_id: str,
    review_item_id: str,
    condition_id: str,
    sample_id: str,
    epoch: int,
    inclusion_probability: float,
    request_sha256: str,
    response_sha256: str,
) -> str:
    return _domain_hmac(
        key,
        "atb-validation-response-v0.1",
        {
            "packet_set_id": packet_set_id,
            "review_item_id": review_item_id,
            "condition_id": condition_id,
            "sample_id": sample_id,
            "epoch": epoch,
            "inclusion_probability": inclusion_probability,
            "request_sha256": request_sha256,
            "response_sha256": response_sha256,
        },
    )


def _require_owner_only_directory(path: Path, label: str) -> None:
    try:
        details = path.lstat()
    except OSError as exc:
        raise ValueError(f"{label} is unavailable") from exc
    if (
        not stat.S_ISDIR(details.st_mode)
        or details.st_uid != os.getuid()
        or stat.S_IMODE(details.st_mode) & 0o077
    ):
        raise ValueError(f"{label} must be an owner-only directory")


def _read_owner_only_file(
    path: Path,
    label: str,
    *,
    minimum_bytes: int = 1,
    maximum_bytes: int = MAX_PRIVATE_JSON_BYTES,
) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValueError(f"{label} cannot be opened safely") from exc
    try:
        details = os.fstat(descriptor)
        if (
            not stat.S_ISREG(details.st_mode)
            or details.st_nlink != 1
            or details.st_uid != os.getuid()
            or stat.S_IMODE(details.st_mode) != 0o600
        ):
            raise ValueError(f"{label} must be an owner-only regular single-link file")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            content = handle.read(maximum_bytes + 1)
        after = os.fstat(descriptor)
        if (
            details.st_dev,
            details.st_ino,
            details.st_size,
            details.st_mtime_ns,
        ) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError(f"{label} changed while it was read")
    finally:
        os.close(descriptor)
    if not minimum_bytes <= len(content) <= maximum_bytes:
        raise ValueError(f"{label} has an invalid size")
    return content


def _write_private_file(path: Path, content: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(descriptor)
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise ValueError("private output permissions are invalid")


def _safe_file_digest(path: Path, root: Path) -> dict[str, Any]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValueError("controlled evidence cannot be opened safely") from exc
    digest = hashlib.sha256()
    size = 0
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError("controlled evidence must contain regular single-link files")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            while chunk := handle.read(1024 * 1024):
                size += len(chunk)
                digest.update(chunk)
        after = os.fstat(descriptor)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError("controlled evidence changed while it was read")
    finally:
        os.close(descriptor)
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": digest.hexdigest(),
        "size_bytes": size,
    }


def _evidence_inventory(log_dir: Path) -> tuple[tuple[dict[str, Any], ...], str]:
    if log_dir.is_symlink() or not log_dir.is_dir():
        raise ValueError("controlled log directory is invalid")
    runner.ensure_private_permissions(log_dir, create=False)
    paths: list[Path] = []
    for path in log_dir.rglob("*"):
        if path.is_symlink():
            raise ValueError("controlled evidence cannot contain symbolic links")
        if path.is_file():
            paths.append(path)
        elif not path.is_dir():
            raise ValueError("controlled evidence contains an unsupported file type")
    rows = tuple(_safe_file_digest(path, log_dir) for path in sorted(paths))
    if not rows:
        raise ValueError("controlled evidence is empty")
    return rows, hashlib.sha256(_canonical_json_bytes(rows)).hexdigest()


def _consistent_log_metadata(logs: Sequence[Any], key: str) -> Any:
    values: list[Any] = []
    for log in logs:
        metadata = getattr(getattr(log, "eval", None), "metadata", None)
        if not isinstance(metadata, Mapping) or key not in metadata:
            raise ValueError("persisted execution metadata is incomplete")
        values.append(metadata[key])
    if any(value != values[0] for value in values[1:]):
        raise ValueError("persisted execution metadata is inconsistent")
    return values[0]


def _plain_text_request(value: Any) -> str:
    if isinstance(value, str):
        result = value
    elif isinstance(value, list):
        parts: list[str] = []
        for message in value:
            if isinstance(message, dict):
                role = message.get("role")
                content = message.get("content")
            else:
                role = getattr(message, "role", None)
                content = getattr(message, "content", None)
            if not isinstance(role, str) or not isinstance(content, str):
                raise ValueError("validation request is not plain text")
            parts.append(f"[{role}]\n{content}")
        result = "\n\n".join(parts)
    else:
        content = getattr(value, "content", None)
        if not isinstance(content, str):
            raise ValueError("validation request is not plain text")
        result = content
    if not result.strip() or result.startswith("attachment://"):
        raise ValueError("validation request is unavailable")
    return result


def _persisted_route_capture_dir(eval_paths: Sequence[Path]) -> Path:
    execution_dirs = {path.parent for path in eval_paths}
    if len(execution_dirs) != 1:
        raise ValueError("persisted Inspect logs must share one execution directory")
    return next(iter(execution_dirs)) / "openrouter-route-capture"


def _validated_frame(manifest_path: Path, log_dir: Path) -> ExecutionFrame:
    repo_root = runner.repository_root()
    verify_committed_file(manifest_path, repo_root, "protocol manifest")
    manifest, manifest_sha256 = load_manifest_with_hash(manifest_path)
    if (
        manifest.status is not ProtocolStatus.FROZEN
        or manifest.task.kind != "diselect"
        or not manifest.validation.human_validation_required
        or not manifest.validation.probability_sample_seed
        or not manifest.validation.codebook_version
        or manifest.validation.double_coded_n < MINIMUM_VALIDATION_FRAME
    ):
        raise ValueError("manifest does not contain a complete frozen DisElect validation plan")

    before_rows, before_digest = _evidence_inventory(log_dir)
    eval_paths = sorted(log_dir.rglob("*.eval"))
    if not eval_paths:
        raise ValueError("no persisted Inspect logs were supplied")
    try:
        logs = [runner.read_postflight_log(path) for path in eval_paths]
    except Exception as exc:
        raise ValueError("persisted Inspect logs cannot be read safely") from exc

    raw_commit = _consistent_log_metadata(logs, "atb_code_commit")
    if not isinstance(raw_commit, str):
        raise ValueError("persisted execution commit is invalid")
    context = execution_context_from_logs(logs, manifest, manifest_sha256, raw_commit)
    route_receipt_sha256 = context["openrouter_route_receipt_sha256"]
    if route_receipt_sha256 is not None:
        verify_persisted_openrouter_route_capture(
            manifest,
            _persisted_route_capture_dir(eval_paths),
            manifest_sha256=manifest_sha256,
            expected_receipt_sha256=route_receipt_sha256,
        )
    provenance = {
        "code_commit": context["code_commit"],
        "code_dirty": context["code_dirty"],
        "environment_lock_sha256": context["environment_lock_sha256"],
    }
    accepted = runner.validate_persisted_execution(
        manifest,
        log_dir,
        manifest_sha256,
        provenance,
        execution_id=context["execution_id"],
        route_receipt_sha256=route_receipt_sha256,
    )
    if accepted is not True:
        raise ValueError("persisted execution did not pass the shared postflight")

    conditions = {condition.condition_id: condition for condition in manifest.models}
    frame: dict[tuple[str, str, int], FrameItem] = {}
    for log in logs:
        matching = [
            condition
            for condition in manifest.models
            if runner.log_matches_condition(log, condition, manifest)
        ]
        if len(matching) != 1:
            raise ValueError("persisted log does not map to one frozen condition")
        condition_id = matching[0].condition_id
        if condition_id not in conditions:
            raise ValueError("persisted log condition is not frozen")
        for sample in log.samples or []:
            if not runner.target_output_scorable(sample):
                continue
            key = (condition_id, str(sample.id), int(sample.epoch))
            if key in frame:
                raise ValueError("validation frame contains duplicate responses")
            metadata = sample.metadata or {}
            stratum: list[str] = []
            for field in manifest.validation.probability_strata:
                value = condition_id if field == "condition_id" else metadata.get(field)
                if value in {None, ""}:
                    raise ValueError("validation frame lacks a frozen stratum")
                stratum.append(str(value))
            response = str(sample.output.completion)
            frame[key] = FrameItem(
                condition_id=condition_id,
                sample_id=str(sample.id),
                epoch=int(sample.epoch),
                stratum=tuple(stratum),
                request=_plain_text_request(sample.input),
                response=response,
            )
    if len(frame) < max(MINIMUM_VALIDATION_FRAME, manifest.validation.double_coded_n):
        raise ValueError("eligible validation frame is smaller than the frozen sample")

    after_rows, after_digest = _evidence_inventory(log_dir)
    if before_rows != after_rows or before_digest != after_digest:
        raise ValueError("controlled evidence changed during packet generation")
    return ExecutionFrame(
        manifest=manifest,
        manifest_sha256=manifest_sha256,
        execution_id=context["execution_id"],
        code_commit=context["code_commit"],
        evidence_inventory_sha256=before_digest,
        items=tuple(frame[key] for key in sorted(frame)),
    )


def _json_document(model: BaseModel) -> bytes:
    return (json.dumps(model.model_dump(mode="json"), indent=2, sort_keys=True) + "\n").encode()


def create_validation_packets(
    *,
    manifest_path: Path,
    log_dir: Path,
    key_file: Path,
    output_dir: Path,
    reviewer_pseudonyms: Sequence[str],
) -> PrivateMap:
    """Create two differently ordered blind packets and their private identity map."""

    reviewers = list(reviewer_pseudonyms)
    if (
        len(reviewers) != 2
        or len(set(reviewers)) != 2
        or any(
            _PSEUDONYM.fullmatch(value) is None or value in {"private-map", "codebook"}
            for value in reviewers
        )
    ):
        raise ValueError("exactly two distinct safe reviewer pseudonyms are required")
    repo_root = runner.repository_root().resolve()
    resolved_output = output_dir.resolve(strict=False)
    if resolved_output == repo_root or repo_root in resolved_output.parents:
        raise ValueError("validation packets must remain outside the public repository")
    if output_dir.exists() or output_dir.is_symlink():
        raise ValueError("validation packet output directory must not exist")
    _require_owner_only_directory(output_dir.parent, "validation packet parent")
    key = _read_owner_only_file(
        key_file, "validation HMAC key", minimum_bytes=32, maximum_bytes=4096
    )
    frame = _validated_frame(manifest_path, log_dir)
    manifest = frame.manifest

    logged = {
        (item.condition_id, item.sample_id, item.epoch): LoggedResponse(
            automated_class=None,
            response_sha256=hashlib.sha256(item.response.encode()).hexdigest(),
            stratum=item.stratum,
        )
        for item in frame.items
    }
    selected = _stratified_probability_sample(
        logged,
        manifest.validation.double_coded_n,
        manifest.validation.probability_sample_seed or "",
    )
    packet_set_id = _domain_hmac(
        key,
        "atb-validation-packet-set-v0.1",
        {
            "protocol_id": manifest.protocol_id,
            "manifest_sha256": frame.manifest_sha256,
            "execution_id": frame.execution_id,
            "code_commit": frame.code_commit,
            "evidence_inventory_sha256": frame.evidence_inventory_sha256,
            "sample_keys": [list(key_value) for key_value in sorted(selected)],
        },
    )

    by_key = {(item.condition_id, item.sample_id, item.epoch): item for item in frame.items}
    public_items: list[ReviewPacketItem] = []
    map_items: list[PrivateMapItem] = []
    for key_value, probability in sorted(selected.items()):
        frame_item = by_key[key_value]
        request_sha256 = hashlib.sha256(frame_item.request.encode()).hexdigest()
        response_sha256 = hashlib.sha256(frame_item.response.encode()).hexdigest()
        review_item_id = _domain_hmac(
            key,
            "atb-validation-review-item-v0.1",
            {"packet_set_id": packet_set_id, "response_key": list(key_value)},
        )
        response_hmac = _response_hmac(
            key,
            packet_set_id=packet_set_id,
            review_item_id=review_item_id,
            condition_id=frame_item.condition_id,
            sample_id=frame_item.sample_id,
            epoch=frame_item.epoch,
            inclusion_probability=probability,
            request_sha256=request_sha256,
            response_sha256=response_sha256,
        )
        public_items.append(
            ReviewPacketItem(
                review_item_id=review_item_id,
                response_hmac=response_hmac,
                request_sha256=request_sha256,
                response_sha256=response_sha256,
                inclusion_probability=probability,
                request=frame_item.request,
                response=frame_item.response,
                native_class=None,
            )
        )
        map_items.append(
            PrivateMapItem(
                review_item_id=review_item_id,
                response_hmac=response_hmac,
                condition_id=frame_item.condition_id,
                sample_id=frame_item.sample_id,
                epoch=frame_item.epoch,
                inclusion_probability=probability,
                request_sha256=request_sha256,
                response_sha256=response_sha256,
            )
        )

    orders: list[list[ReviewPacketItem]] = []
    for reviewer in reviewers:
        orders.append(
            sorted(
                public_items,
                key=lambda item: _domain_hmac(
                    key,
                    "atb-validation-review-order-v0.1",
                    [packet_set_id, reviewer, item.review_item_id],
                ),
            )
        )
    if [item.review_item_id for item in orders[0]] == [item.review_item_id for item in orders[1]]:
        orders[1].reverse()

    private_map = PrivateMap(
        schema_version="atb-validation-private-map-v0.1",
        packet_set_id=packet_set_id,
        protocol_id=manifest.protocol_id,
        manifest_sha256=frame.manifest_sha256,
        execution_id=frame.execution_id,
        code_commit=frame.code_commit,
        evidence_inventory_sha256=frame.evidence_inventory_sha256,
        codebook_version=manifest.validation.codebook_version or "",
        reviewer_pseudonyms=reviewers,
        key_confirmation_hmac=_key_confirmation_hmac(key, packet_set_id),
        item_count=len(map_items),
        items=map_items,
    )

    output_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
    if stat.S_IMODE(output_dir.stat().st_mode) != 0o700:
        raise ValueError("validation packet directory permissions are invalid")
    for reviewer, items in zip(reviewers, orders, strict=True):
        packet = ReviewPacket(
            schema_version="atb-validation-review-packet-v0.1",
            packet_set_id=packet_set_id,
            protocol_id=manifest.protocol_id,
            codebook_version=manifest.validation.codebook_version or "",
            reviewer_pseudonym=reviewer,
            independent_read_attested=False,
            blinded_fields=list(BLINDED_FIELDS),
            item_count=len(items),
            items=items,
        )
        _write_private_file(output_dir / f"{reviewer}.json", _json_document(packet))
    _write_private_file(output_dir / "private-map.json", _json_document(private_map))
    codebook_path = repo_root / "evals/codebooks/diselect-response-v0.1.md"
    verify_committed_file(codebook_path, repo_root, "human-validation codebook")
    _write_private_file(output_dir / "codebook.md", codebook_path.read_bytes())
    return private_map


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create blind ATB validation packets")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--log-dir", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reviewer", action="append", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        result = create_validation_packets(
            manifest_path=args.manifest,
            log_dir=args.log_dir,
            key_file=args.key_file,
            output_dir=args.output_dir,
            reviewer_pseudonyms=args.reviewer,
        )
    except Exception:
        print("validation packet generation failed safely", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "packet_set_id": result.packet_set_id,
                "review_item_count": result.item_count,
                "status": "created",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
