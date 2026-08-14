"""Create a blind third-reviewer packet for disputed APE v0.2 labels."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from atb_eval import runner
from atb_eval.ape_validation_evidence import _load_private_model
from atb_eval.ape_validation_packet import (
    _PSEUDONYM,
    APE_CODEBOOK_VERSION,
    APE_LABEL_SET_ID,
    APE_VALIDATION_PROJECTION,
    APEPrivateMap,
    APEReviewClass,
    APEReviewPacket,
    _ape_packet_set_id,
    _require_clean_validation_checkout,
)
from atb_eval.validation_packet import (
    BLINDED_FIELDS,
    _domain_hmac,
    _json_document,
    _key_confirmation_hmac,
    _read_owner_only_file,
    _require_owner_only_directory,
    _response_hmac,
    _write_private_file,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class APEAdjudicationReviewItem(StrictModel):
    review_item_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_hmac: str = Field(pattern=r"^[a-f0-9]{64}$")
    request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    request: str = Field(min_length=1)
    response: str = Field(min_length=1)
    human_label: APEReviewClass | None = None

    @model_validator(mode="after")
    def content_matches_digests(self) -> APEAdjudicationReviewItem:
        if (
            hashlib.sha256(self.request.encode()).hexdigest() != self.request_sha256
            or hashlib.sha256(self.response.encode()).hexdigest() != self.response_sha256
        ):
            raise ValueError("APE adjudication review material does not match its digests")
        return self


class APEAdjudicationReviewPacket(StrictModel):
    schema_version: Literal["atb-ape-validation-adjudication-review-packet-v0.2"]
    task_kind: Literal["ape"]
    label_set_id: Literal["atb-ape-attempt-labels-v0.1"]
    validation_projection: Literal["attempt_vs_rest"]
    packet_set_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    protocol_id: str = Field(min_length=1)
    codebook_version: Literal["atb-ape-attempt-v0.1"]
    codebook_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    adjudicator_pseudonym: str = Field(min_length=1, max_length=64)
    independent_read_attested: bool
    blinded_fields: list[
        Literal["model", "provider", "organisation", "release_date", "automated_score"]
    ]
    item_count: int = Field(ge=1)
    items: list[APEAdjudicationReviewItem] = Field(min_length=1)

    @field_validator("adjudicator_pseudonym")
    @classmethod
    def valid_adjudicator(cls, value: str) -> str:
        if _PSEUDONYM.fullmatch(value) is None or value in {"private-map", "codebook"}:
            raise ValueError("APE adjudicator pseudonym is not safe")
        return value

    @model_validator(mode="after")
    def coherent_packet(self) -> APEAdjudicationReviewPacket:
        if self.item_count != len(self.items):
            raise ValueError("APE adjudication review packet item_count does not match items")
        if tuple(self.blinded_fields) != BLINDED_FIELDS:
            raise ValueError("APE adjudication review packet does not preserve blinding")
        ids = [item.review_item_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("APE adjudication review packet contains duplicate items")
        return self

def _packet_items(packet: APEReviewPacket) -> dict[str, Any]:
    return {item.review_item_id: item for item in packet.items}


def _load_bound_review_material(
    *,
    reviewer_packet_paths: tuple[Path, Path],
    private_map_path: Path,
    key_file: Path,
) -> tuple[bytes, APEPrivateMap, list[APEReviewPacket], list[dict[str, Any]]]:
    """Load two complete reviews and verify their full APE v0.2 bindings."""

    key = _read_owner_only_file(
        key_file, "APE validation HMAC key", minimum_bytes=32, maximum_bytes=4096
    )
    loaded_map = _load_private_model(private_map_path, "APE private map", APEPrivateMap)
    if not isinstance(loaded_map, APEPrivateMap):
        raise ValueError("APE private map has an invalid type")
    private_map = loaded_map
    codebook_bytes = _read_owner_only_file(
        private_map_path.parent / "codebook.md",
        "APE validation codebook copy",
        minimum_bytes=1,
        maximum_bytes=1_000_000,
    )
    if not hmac.compare_digest(
        hashlib.sha256(codebook_bytes).hexdigest(), private_map.codebook_sha256
    ):
        raise ValueError("APE validation codebook copy does not match the private map")
    expected_packet_set_id = _ape_packet_set_id(
        key,
        protocol_id=private_map.protocol_id,
        manifest_sha256=private_map.manifest_sha256,
        execution_id=private_map.execution_id,
        code_commit=private_map.code_commit,
        evidence_inventory_sha256=private_map.evidence_inventory_sha256,
        codebook_sha256=private_map.codebook_sha256,
        reviewer_pseudonyms=private_map.reviewer_pseudonyms,
        macro_f1_min=private_map.macro_f1_min,
        critical_f1_min=private_map.critical_f1_min,
        minimum_joint_usable_rate=private_map.minimum_joint_usable_rate,
        sample_descriptors=[
            {
                "condition_id": item.condition_id,
                "category": item.category,
                "sample_id": item.sample_id,
                "epoch": item.epoch,
                "inclusion_probability": item.inclusion_probability,
                "request_sha256": item.request_sha256,
                "response_sha256": item.response_sha256,
                "automated_class": item.automated_class,
            }
            for item in private_map.items
        ],
    )
    if not hmac.compare_digest(private_map.packet_set_id, expected_packet_set_id):
        raise ValueError("APE private-map header failed its packet-set binding")
    if not hmac.compare_digest(
        private_map.key_confirmation_hmac,
        _key_confirmation_hmac(key, private_map.packet_set_id),
    ):
        raise ValueError("APE validation HMAC key does not match the private map")

    loaded_packets = [
        _load_private_model(path, "completed APE reviewer packet", APEReviewPacket)
        for path in reviewer_packet_paths
    ]
    if not all(isinstance(value, APEReviewPacket) for value in loaded_packets):
        raise ValueError("completed APE reviewer packet has an invalid type")
    packets = [value for value in loaded_packets if isinstance(value, APEReviewPacket)]
    reviewers = [value.reviewer_pseudonym for value in packets]
    if len(set(reviewers)) != 2 or set(reviewers) != set(private_map.reviewer_pseudonyms):
        raise ValueError("completed APE packets do not match the frozen reviewers")

    map_items = {item.review_item_id: item for item in private_map.items}
    packet_items = [_packet_items(value) for value in packets]
    expected_ids = set(map_items)
    for review_packet, items in zip(packets, packet_items, strict=True):
        if (
            review_packet.task_kind != private_map.task_kind
            or review_packet.label_set_id != private_map.label_set_id
            or review_packet.validation_projection != private_map.validation_projection
            or review_packet.packet_set_id != private_map.packet_set_id
            or review_packet.protocol_id != private_map.protocol_id
            or review_packet.codebook_version != private_map.codebook_version
            or review_packet.codebook_sha256 != private_map.codebook_sha256
            or tuple(review_packet.blinded_fields) != BLINDED_FIELDS
            or review_packet.independent_read_attested is not True
            or set(items) != expected_ids
        ):
            raise ValueError("completed APE reviewer packet does not match the private map")
        if any(item.human_label is None for item in review_packet.items):
            raise ValueError("completed APE reviewer packet contains an unlabeled item")

    for review_item_id, private_item in map_items.items():
        first = packet_items[0][review_item_id]
        second = packet_items[1][review_item_id]
        for item in (first, second):
            request_sha256 = hashlib.sha256(item.request.encode()).hexdigest()
            response_sha256 = hashlib.sha256(item.response.encode()).hexdigest()
            expected_hmac = _response_hmac(
                key,
                packet_set_id=private_map.packet_set_id,
                review_item_id=review_item_id,
                condition_id=private_item.condition_id,
                sample_id=private_item.sample_id,
                epoch=private_item.epoch,
                inclusion_probability=private_item.inclusion_probability,
                request_sha256=request_sha256,
                response_sha256=response_sha256,
            )
            if (
                item.inclusion_probability != private_item.inclusion_probability
                or item.request_sha256 != request_sha256
                or item.response_sha256 != response_sha256
                or item.request_sha256 != private_item.request_sha256
                or item.response_sha256 != private_item.response_sha256
                or not hmac.compare_digest(item.response_hmac, private_item.response_hmac)
                or not hmac.compare_digest(item.response_hmac, expected_hmac)
            ):
                raise ValueError("completed APE reviewer packet failed its content binding")
        if first.request != second.request or first.response != second.response:
            raise ValueError("APE reviewers did not receive identical blinded material")
    return key, private_map, packets, packet_items


def create_ape_adjudication_packet(
    *,
    reviewer_packet_paths: tuple[Path, Path],
    private_map_path: Path,
    key_file: Path,
    output_file: Path,
    adjudicator_pseudonym: str,
) -> APEAdjudicationReviewPacket:
    """Write an owner-only blind packet containing exactly reviewer disagreements."""

    if len(reviewer_packet_paths) != 2:
        raise ValueError("exactly two completed APE reviewer packets are required")
    all_paths = [*reviewer_packet_paths, private_map_path, key_file, output_file]
    resolved_paths = [path.resolve(strict=False) for path in all_paths]
    if len(resolved_paths) != len(set(resolved_paths)):
        raise ValueError("APE adjudication packet paths must be distinct")
    repo_root = runner.repository_root().resolve()
    resolved_output = output_file.resolve(strict=False)
    if resolved_output == repo_root or repo_root in resolved_output.parents:
        raise ValueError("APE adjudication packet must remain outside the public repository")
    if output_file.exists() or output_file.is_symlink():
        raise ValueError("APE adjudication packet output already exists")
    _require_owner_only_directory(output_file.parent, "APE adjudication packet parent")

    key, private_map, _packets, packet_items = _load_bound_review_material(
        reviewer_packet_paths=reviewer_packet_paths,
        private_map_path=private_map_path,
        key_file=key_file,
    )
    _require_clean_validation_checkout(private_map.code_commit)
    if (
        _PSEUDONYM.fullmatch(adjudicator_pseudonym) is None
        or adjudicator_pseudonym in {"private-map", "codebook"}
        or adjudicator_pseudonym in set(private_map.reviewer_pseudonyms)
    ):
        raise ValueError("a distinct safe APE adjudicator pseudonym is required")

    disputed_ids = {
        review_item_id
        for review_item_id in packet_items[0]
        if packet_items[0][review_item_id].human_label
        != packet_items[1][review_item_id].human_label
    }
    if not disputed_ids:
        raise ValueError("completed APE reviewer packets contain no disagreements")
    ordered_ids = sorted(
        disputed_ids,
        key=lambda review_item_id: _domain_hmac(
            key,
            "atb-ape-validation-adjudication-review-order-v0.2",
            [private_map.packet_set_id, adjudicator_pseudonym, review_item_id],
        ),
    )
    first_items = packet_items[0]
    output_items = [
        APEAdjudicationReviewItem(
            review_item_id=review_item_id,
            response_hmac=first_items[review_item_id].response_hmac,
            request_sha256=first_items[review_item_id].request_sha256,
            response_sha256=first_items[review_item_id].response_sha256,
            request=first_items[review_item_id].request,
            response=first_items[review_item_id].response,
            human_label=None,
        )
        for review_item_id in ordered_ids
    ]
    result = APEAdjudicationReviewPacket(
        schema_version="atb-ape-validation-adjudication-review-packet-v0.2",
        task_kind="ape",
        label_set_id=APE_LABEL_SET_ID,
        validation_projection=APE_VALIDATION_PROJECTION,
        packet_set_id=private_map.packet_set_id,
        protocol_id=private_map.protocol_id,
        codebook_version=APE_CODEBOOK_VERSION,
        codebook_sha256=private_map.codebook_sha256,
        adjudicator_pseudonym=adjudicator_pseudonym,
        independent_read_attested=False,
        blinded_fields=list(BLINDED_FIELDS),
        item_count=len(output_items),
        items=output_items,
    )
    _write_private_file(output_file, _json_document(result))
    return result


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a blind APE adjudication packet")
    parser.add_argument("--reviewer-packet", type=Path, action="append", required=True)
    parser.add_argument("--private-map", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--output-file", type=Path, required=True)
    parser.add_argument("--adjudicator", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        if len(args.reviewer_packet) != 2:
            raise ValueError("exactly two completed APE reviewer packets are required")
        result = create_ape_adjudication_packet(
            reviewer_packet_paths=(args.reviewer_packet[0], args.reviewer_packet[1]),
            private_map_path=args.private_map,
            key_file=args.key_file,
            output_file=args.output_file,
            adjudicator_pseudonym=args.adjudicator,
        )
    except Exception:
        print("APE adjudication packet generation failed safely", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "adjudication_item_count": result.item_count,
                "packet_set_id": result.packet_set_id,
                "status": "created",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
