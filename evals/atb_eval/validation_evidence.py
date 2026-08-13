"""Combine two completed blind review packets into release-gate evidence."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from atb_eval import runner
from atb_eval.release_gate import (
    IndependentHumanLabel,
    ValidationEvidence,
    ValidationEvidenceRow,
)
from atb_eval.validation_packet import (
    BLINDED_FIELDS,
    NATIVE_CLASSES,
    PrivateMap,
    ReviewPacket,
    _key_confirmation_hmac,
    _read_owner_only_file,
    _require_owner_only_directory,
    _response_hmac,
    _write_private_file,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class AdjudicationItem(StrictModel):
    review_item_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_hmac: str = Field(pattern=r"^[a-f0-9]{64}$")
    native_class: Literal["comply", "soft_refuse", "refuse", "incoherent"]


class Adjudications(StrictModel):
    schema_version: Literal["atb-validation-adjudications-v0.1"]
    packet_set_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    adjudicator_pseudonym: str = Field(min_length=1, max_length=64)
    independent_read_attested: Literal[True]
    item_count: int = Field(ge=1)
    items: list[AdjudicationItem] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_adjudications(self) -> Adjudications:
        if self.item_count != len(self.items):
            raise ValueError("adjudication item_count does not match items")
        ids = [item.review_item_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("adjudications contain duplicate items")
        pseudonym = self.adjudicator_pseudonym.strip()
        if not pseudonym or pseudonym != self.adjudicator_pseudonym:
            raise ValueError("adjudicator pseudonym is invalid")
        return self


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("private JSON contains duplicate keys")
        result[key] = value
    return result


def _reject_constant(unused: str) -> Any:
    raise ValueError("private JSON contains a non-finite number")


def _load_private_model(path: Path, label: str, model_type: type[BaseModel]) -> BaseModel:
    raw = _read_owner_only_file(path, label)
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
        return model_type.model_validate(value)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"{label} is invalid") from exc


def _packet_items(packet: ReviewPacket) -> dict[str, Any]:
    return {item.review_item_id: item for item in packet.items}


def build_validation_evidence(
    *,
    reviewer_packet_paths: tuple[Path, Path],
    private_map_path: Path,
    key_file: Path,
    output_file: Path,
    adjudications_path: Path | None = None,
) -> ValidationEvidence:
    """Verify every blind-review binding and write exclusive owner-only evidence."""

    all_inputs = [*reviewer_packet_paths, private_map_path, key_file]
    if adjudications_path is not None:
        all_inputs.append(adjudications_path)
    resolved_inputs = [path.resolve(strict=False) for path in all_inputs]
    if len(resolved_inputs) != len(set(resolved_inputs)):
        raise ValueError("validation evidence inputs must be distinct files")

    repo_root = runner.repository_root().resolve()
    resolved_output = output_file.resolve(strict=False)
    if resolved_output == repo_root or repo_root in resolved_output.parents:
        raise ValueError("validation evidence must remain outside the public repository")
    if output_file.exists() or output_file.is_symlink():
        raise ValueError("validation evidence output already exists")
    _require_owner_only_directory(output_file.parent, "validation evidence parent")

    key = _read_owner_only_file(
        key_file, "validation HMAC key", minimum_bytes=32, maximum_bytes=4096
    )
    private_map = _load_private_model(private_map_path, "private validation map", PrivateMap)
    if not isinstance(private_map, PrivateMap):
        raise ValueError("private validation map has an invalid type")
    if not hmac.compare_digest(
        private_map.key_confirmation_hmac,
        _key_confirmation_hmac(key, private_map.packet_set_id),
    ):
        raise ValueError("validation HMAC key does not match the private map")

    loaded_packets = [
        _load_private_model(path, "completed reviewer packet", ReviewPacket)
        for path in reviewer_packet_paths
    ]
    if not all(isinstance(packet, ReviewPacket) for packet in loaded_packets):
        raise ValueError("completed reviewer packet has an invalid type")
    packets = [packet for packet in loaded_packets if isinstance(packet, ReviewPacket)]
    reviewers = [packet.reviewer_pseudonym for packet in packets]
    if len(set(reviewers)) != 2 or set(reviewers) != set(private_map.reviewer_pseudonyms):
        raise ValueError("completed packets do not match the two frozen reviewers")

    map_items = {item.review_item_id: item for item in private_map.items}
    packet_items = [_packet_items(packet) for packet in packets]
    expected_ids = set(map_items)
    for packet, items in zip(packets, packet_items, strict=True):
        if (
            packet.packet_set_id != private_map.packet_set_id
            or packet.protocol_id != private_map.protocol_id
            or packet.codebook_version != private_map.codebook_version
            or tuple(packet.blinded_fields) != BLINDED_FIELDS
            or packet.independent_read_attested is not True
            or set(items) != expected_ids
        ):
            raise ValueError("completed reviewer packet does not match the private map")
        if any(item.native_class is None for item in packet.items):
            raise ValueError("completed reviewer packet contains an unlabeled item")

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
                or item.response_hmac != private_item.response_hmac
                or not hmac.compare_digest(item.response_hmac, expected_hmac)
            ):
                raise ValueError("completed reviewer packet failed its content binding")
        if first.request != second.request or first.response != second.response:
            raise ValueError("reviewers did not receive identical blinded material")

    disagreements = {
        review_item_id
        for review_item_id in expected_ids
        if packet_items[0][review_item_id].native_class
        != packet_items[1][review_item_id].native_class
    }
    adjudications: Adjudications | None = None
    if disagreements:
        if adjudications_path is None:
            raise ValueError("reviewer disagreements require independent adjudication")
        loaded = _load_private_model(adjudications_path, "completed adjudications", Adjudications)
        if not isinstance(loaded, Adjudications):
            raise ValueError("completed adjudications have an invalid type")
        adjudications = loaded
        adjudication_items = {item.review_item_id: item for item in adjudications.items}
        if (
            adjudications.packet_set_id != private_map.packet_set_id
            or adjudications.adjudicator_pseudonym in set(reviewers)
            or set(adjudication_items) != disagreements
        ):
            raise ValueError("completed adjudications do not match reviewer disagreements")
        for review_item_id, item in adjudication_items.items():
            if not hmac.compare_digest(item.response_hmac, map_items[review_item_id].response_hmac):
                raise ValueError("adjudication response binding does not match")
    elif adjudications_path is not None:
        raise ValueError("adjudications were supplied without reviewer disagreement")

    adjudication_by_id = (
        {item.review_item_id: item for item in adjudications.items}
        if adjudications is not None
        else {}
    )
    rows: list[ValidationEvidenceRow] = []
    for private_item in private_map.items:
        review_item_id = private_item.review_item_id
        first_label = packet_items[0][review_item_id].native_class
        second_label = packet_items[1][review_item_id].native_class
        if first_label is None or second_label is None:
            raise ValueError("completed reviewer packet contains an unlabeled item")
        independent_labels = [
            IndependentHumanLabel(
                reviewer_pseudonym=packets[0].reviewer_pseudonym,
                native_class=first_label,
            ),
            IndependentHumanLabel(
                reviewer_pseudonym=packets[1].reviewer_pseudonym,
                native_class=second_label,
            ),
        ]
        if first_label == second_label:
            if first_label == "unscorable" or first_label not in NATIVE_CLASSES:
                raise ValueError("agreed unscorable material cannot become validation evidence")
            rows.append(
                ValidationEvidenceRow(
                    condition_id=private_item.condition_id,
                    sample_id=private_item.sample_id,
                    epoch=private_item.epoch,
                    sampling_frame="probability_validation",
                    inclusion_probability=private_item.inclusion_probability,
                    response_sha256=private_item.response_sha256,
                    oracle_class=first_label,
                    independent_labels=independent_labels,
                    adjudication_status="agreement",
                    adjudicator_pseudonym=None,
                    adjudicator_label=None,
                )
            )
        else:
            adjudicated = adjudication_by_id[review_item_id]
            rows.append(
                ValidationEvidenceRow(
                    condition_id=private_item.condition_id,
                    sample_id=private_item.sample_id,
                    epoch=private_item.epoch,
                    sampling_frame="probability_validation",
                    inclusion_probability=private_item.inclusion_probability,
                    response_sha256=private_item.response_sha256,
                    oracle_class=adjudicated.native_class,
                    independent_labels=independent_labels,
                    adjudication_status="adjudicated",
                    adjudicator_pseudonym=adjudications.adjudicator_pseudonym,
                    adjudicator_label=adjudicated.native_class,
                )
            )

    evidence = ValidationEvidence(
        schema_version="atb-validation-evidence-v0.1",
        protocol_id=private_map.protocol_id,
        codebook_version=private_map.codebook_version,
        blinded_fields=list(BLINDED_FIELDS),
        rows=rows,
    )
    content = (
        json.dumps(evidence.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    ).encode()
    _write_private_file(output_file, content)
    return evidence


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build adjudicated ATB validation evidence")
    parser.add_argument("--reviewer-packet", type=Path, action="append", required=True)
    parser.add_argument("--private-map", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--adjudications", type=Path)
    parser.add_argument("--output-file", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        if len(args.reviewer_packet) != 2:
            raise ValueError("exactly two reviewer packets are required")
        evidence = build_validation_evidence(
            reviewer_packet_paths=(args.reviewer_packet[0], args.reviewer_packet[1]),
            private_map_path=args.private_map,
            key_file=args.key_file,
            output_file=args.output_file,
            adjudications_path=args.adjudications,
        )
    except Exception:
        print("validation evidence generation failed safely", file=sys.stderr)
        return 1
    print(json.dumps({"row_count": len(evidence.rows), "status": "created"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
