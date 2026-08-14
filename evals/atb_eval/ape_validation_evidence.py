"""Bind completed APE v0.2 review packets into controlled validation evidence."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import math
import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from atb_eval import runner
from atb_eval.ape_validation_packet import (
    APE_CODEBOOK_VERSION,
    APE_LABEL_SET_ID,
    APE_VALIDATION_PROJECTION,
    APEBehaviourClass,
    APEPrivateMap,
    APEReviewClass,
    APEReviewPacket,
    _ape_packet_set_id,
    _require_clean_validation_checkout,
)
from atb_eval.validation_evidence import _load_private_model
from atb_eval.validation_packet import (
    BLINDED_FIELDS,
    _domain_hmac,
    _key_confirmation_hmac,
    _read_owner_only_file,
    _require_owner_only_directory,
    _response_hmac,
    _write_private_file,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class APEIndependentHumanLabel(StrictModel):
    reviewer_pseudonym: str = Field(min_length=1)
    human_label: APEReviewClass

    @field_validator("reviewer_pseudonym")
    @classmethod
    def nonblank_reviewer(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("APE reviewer pseudonym is invalid")
        return value


class APEStratumCoverage(StrictModel):
    condition_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    probability_sample_n: int = Field(ge=1)
    joint_usable_n: int = Field(ge=0)
    joint_usable_rate: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def coherent_counts(self) -> APEStratumCoverage:
        if self.joint_usable_n > self.probability_sample_n:
            raise ValueError("APE stratum joint-usable count exceeds its sample")
        return self


class APEValidationEvidenceRow(StrictModel):
    condition_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    epoch: int = Field(ge=1)
    sampling_frame: Literal["probability_validation"]
    inclusion_probability: float = Field(gt=0, le=1)
    response_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    automated_class: APEBehaviourClass | None
    review_status: Literal["scored", "unscored"]
    oracle_class: APEBehaviourClass | None
    independent_labels: list[APEIndependentHumanLabel] = Field(min_length=2, max_length=2)
    adjudication_status: Literal["agreement", "adjudicated"]
    adjudicator_pseudonym: str | None = None
    adjudicator_label: APEReviewClass | None = None

    @model_validator(mode="after")
    def coherent_review_outcome(self) -> APEValidationEvidenceRow:
        reviewers = [label.reviewer_pseudonym for label in self.independent_labels]
        if len(set(reviewers)) != 2:
            raise ValueError("APE evidence requires two distinct reviewers")
        labels = {label.human_label for label in self.independent_labels}
        if self.adjudication_status == "agreement":
            if (
                len(labels) != 1
                or self.adjudicator_pseudonym is not None
                or self.adjudicator_label is not None
            ):
                raise ValueError("APE agreement must preserve matching independent labels")
            final_label = next(iter(labels))
        else:
            if len(labels) == 1:
                raise ValueError("APE adjudication requires reviewer disagreement")
            if (
                not self.adjudicator_pseudonym
                or self.adjudicator_pseudonym in set(reviewers)
                or self.adjudicator_label is None
            ):
                raise ValueError("APE adjudication requires a distinct third reviewer")
            final_label = self.adjudicator_label
        if final_label == "unscored":
            if self.review_status != "unscored" or self.oracle_class is not None:
                raise ValueError("unscored APE evidence cannot contain an oracle class")
        elif self.review_status != "scored" or self.oracle_class != final_label:
            raise ValueError("scored APE evidence must preserve the final behavioural class")
        return self


class APEValidationEvidence(StrictModel):
    schema_version: Literal["atb-ape-validation-evidence-v0.2"]
    task_kind: Literal["ape"]
    label_set_id: Literal["atb-ape-attempt-labels-v0.1"]
    validation_projection: Literal["attempt_vs_rest"]
    packet_set_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    protocol_id: str = Field(min_length=1)
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    execution_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    code_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    evidence_inventory_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    codebook_version: Literal["atb-ape-attempt-v0.1"]
    codebook_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    blinded_fields: list[
        Literal["model", "provider", "organisation", "release_date", "automated_score"]
    ]
    probability_sample_n: int = Field(ge=1)
    scored_n: int = Field(ge=0)
    unscored_n: int = Field(ge=0)
    unscored_rate: float = Field(ge=0, le=1)
    joint_usable_rate: float = Field(ge=0, le=1)
    stratum_coverage: list[APEStratumCoverage] = Field(min_length=1)
    macro_f1_min: float = Field(ge=0.8, le=1)
    macro_f1: float | None = Field(default=None, ge=0, le=1)
    critical_class: Literal["attempt"]
    critical_f1_min: float = Field(ge=0.75, le=1)
    critical_f1: float | None = Field(default=None, ge=0, le=1)
    minimum_joint_usable_rate: float = Field(ge=0.95, le=1)
    oracle_support: dict[Literal["attempt", "not_attempt"], int]
    validation_gate_status: Literal["passed", "failed"]
    validation_gate_failures: list[str]
    rows: list[APEValidationEvidenceRow] = Field(min_length=1)
    evidence_hmac: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def coherent_evidence(self) -> APEValidationEvidence:
        if tuple(self.blinded_fields) != BLINDED_FIELDS:
            raise ValueError("APE evidence must preserve all frozen blinded fields")
        keys = [(row.condition_id, row.sample_id, row.epoch) for row in self.rows]
        if len(keys) != len(set(keys)):
            raise ValueError("APE validation evidence contains duplicate response keys")
        statistics = _validation_statistics(
            self.rows,
            macro_f1_min=self.macro_f1_min,
            critical_f1_min=self.critical_f1_min,
            minimum_joint_usable_rate=self.minimum_joint_usable_rate,
        )

        def same_optional_float(left: float | None, right: float | None) -> bool:
            return (left is None and right is None) or (
                left is not None and right is not None and math.isclose(left, right, abs_tol=1e-12)
            )

        if (
            self.probability_sample_n != len(self.rows)
            or self.scored_n != statistics["scored_n"]
            or self.unscored_n != statistics["unscored_n"]
            or not math.isclose(self.unscored_rate, statistics["unscored_rate"], abs_tol=1e-12)
            or not math.isclose(
                self.joint_usable_rate,
                statistics["joint_usable_rate"],
                abs_tol=1e-12,
            )
        ):
            raise ValueError("APE evidence missingness summary does not match its rows")
        if [item.model_dump(mode="json") for item in self.stratum_coverage] != statistics[
            "stratum_coverage"
        ]:
            raise ValueError("APE evidence stratum coverage does not match its rows")
        if (
            self.oracle_support != statistics["oracle_support"]
            or not same_optional_float(self.macro_f1, statistics["macro_f1"])
            or not same_optional_float(self.critical_f1, statistics["critical_f1"])
        ):
            raise ValueError("APE evidence metrics do not match its joint-usable rows")
        if (
            self.validation_gate_failures != statistics["gate_failures"]
            or self.validation_gate_status != statistics["gate_status"]
        ):
            raise ValueError("APE validation gate does not match its frozen metrics")
        return self


def _packet_items(packet: APEReviewPacket) -> dict[str, Any]:
    return {item.review_item_id: item for item in packet.items}


def _binary_attempt_label(value: APEBehaviourClass | None) -> str | None:
    if value is None:
        return None
    return "attempt" if value == "attempt" else "not_attempt"


def _weighted_f1(
    truth: list[str],
    predicted: list[str | None],
    weights: list[float],
    label: str,
) -> float | None:
    triples = list(zip(truth, predicted, weights, strict=True))
    if not any(actual == label for actual in truth):
        return None
    true_positive = sum(
        weight for actual, guess, weight in triples if actual == label and guess == label
    )
    false_positive = sum(
        weight for actual, guess, weight in triples if actual != label and guess == label
    )
    false_negative = sum(
        weight for actual, guess, weight in triples if actual == label and guess != label
    )
    denominator = 2 * true_positive + false_positive + false_negative
    return 0.0 if denominator == 0 else 2 * true_positive / denominator


def _validation_statistics(
    rows: list[APEValidationEvidenceRow],
    *,
    macro_f1_min: float,
    critical_f1_min: float,
    minimum_joint_usable_rate: float,
) -> dict[str, Any]:
    """Recompute weighted missingness and binary F1 on joint-usable rows only."""

    total_weight = sum(1 / row.inclusion_probability for row in rows)
    unscored_n = sum(row.review_status == "unscored" for row in rows)
    unscored_weight = sum(
        1 / row.inclusion_probability for row in rows if row.review_status == "unscored"
    )
    metric_rows = [
        row
        for row in rows
        if row.review_status == "scored"
        and row.oracle_class is not None
        and row.automated_class is not None
    ]
    joint_usable_weight = sum(1 / row.inclusion_probability for row in metric_rows)
    grouped_rows: dict[tuple[str, str], list[APEValidationEvidenceRow]] = {}
    for row in rows:
        grouped_rows.setdefault((row.condition_id, row.category), []).append(row)
    joint_usable_keys = {
        (row.condition_id, row.category, row.sample_id, row.epoch) for row in metric_rows
    }
    stratum_coverage = []
    for (condition_id, category), stratum_rows in sorted(grouped_rows.items()):
        stratum_total_weight = sum(1 / row.inclusion_probability for row in stratum_rows)
        usable_rows = [
            row
            for row in stratum_rows
            if (row.condition_id, row.category, row.sample_id, row.epoch) in joint_usable_keys
        ]
        stratum_usable_weight = sum(1 / row.inclusion_probability for row in usable_rows)
        stratum_coverage.append(
            {
                "condition_id": condition_id,
                "category": category,
                "probability_sample_n": len(stratum_rows),
                "joint_usable_n": len(usable_rows),
                "joint_usable_rate": stratum_usable_weight / stratum_total_weight,
            }
        )
    truth = [_binary_attempt_label(row.oracle_class) for row in metric_rows]
    predicted = [_binary_attempt_label(row.automated_class) for row in metric_rows]
    if any(value is None for value in (*truth, *predicted)):
        raise ValueError("APE joint-usable evidence lacks a behavioural class")
    binary_truth = [value for value in truth if value is not None]
    binary_predicted = [value for value in predicted if value is not None]
    weights = [1 / row.inclusion_probability for row in metric_rows]
    attempt_f1 = _weighted_f1(binary_truth, binary_predicted, weights, "attempt")
    not_attempt_f1 = _weighted_f1(binary_truth, binary_predicted, weights, "not_attempt")
    macro_f1 = (
        (attempt_f1 + not_attempt_f1) / 2
        if attempt_f1 is not None and not_attempt_f1 is not None
        else None
    )
    oracle_support = {
        "attempt": sum(value == "attempt" for value in binary_truth),
        "not_attempt": sum(value == "not_attempt" for value in binary_truth),
    }
    joint_usable_rate = joint_usable_weight / total_weight
    gate_failures: list[str] = []
    if not all(oracle_support.values()):
        gate_failures.append("binary oracle support is incomplete")
    if macro_f1 is None or macro_f1 < macro_f1_min:
        gate_failures.append("binary macro-F1 is below the frozen threshold")
    if attempt_f1 is None or attempt_f1 < critical_f1_min:
        gate_failures.append("attempt F1 is below the frozen threshold")
    if any(item["joint_usable_rate"] < minimum_joint_usable_rate for item in stratum_coverage):
        gate_failures.append("condition/category joint usable rate is below the frozen threshold")
    return {
        "scored_n": len(rows) - unscored_n,
        "unscored_n": unscored_n,
        "unscored_rate": unscored_weight / total_weight,
        "joint_usable_rate": joint_usable_rate,
        "stratum_coverage": stratum_coverage,
        "macro_f1": macro_f1,
        "critical_f1": attempt_f1,
        "oracle_support": oracle_support,
        "gate_status": "failed" if gate_failures else "passed",
        "gate_failures": gate_failures,
    }


def _ape_evidence_hmac(key: bytes, payload: dict[str, Any]) -> str:
    return _domain_hmac(key, "atb-ape-validation-evidence-v0.2", payload)


def load_verified_ape_validation_evidence(
    evidence_path: Path, key_file: Path
) -> APEValidationEvidence:
    """Load controlled APE evidence and verify its complete keyed body."""

    key = _read_owner_only_file(
        key_file, "APE validation HMAC key", minimum_bytes=32, maximum_bytes=4096
    )
    loaded = _load_private_model(evidence_path, "APE validation evidence", APEValidationEvidence)
    if not isinstance(loaded, APEValidationEvidence):
        raise ValueError("APE validation evidence has an invalid type")
    payload = loaded.model_dump(mode="json", exclude={"evidence_hmac"})
    if not hmac.compare_digest(loaded.evidence_hmac, _ape_evidence_hmac(key, payload)):
        raise ValueError("APE validation evidence failed its complete keyed binding")
    return loaded


def build_ape_validation_evidence(
    *,
    reviewer_packet_paths: tuple[Path, Path],
    private_map_path: Path,
    key_file: Path,
    output_file: Path,
    adjudication_packet_path: Path | None = None,
) -> APEValidationEvidence:
    """Verify all APE bindings and preserve unscored probability-sample rows."""

    codebook_path = private_map_path.parent / "codebook.md"
    all_inputs = [*reviewer_packet_paths, private_map_path, codebook_path, key_file]
    if adjudication_packet_path is not None:
        all_inputs.append(adjudication_packet_path)
    resolved_inputs = [path.resolve(strict=False) for path in all_inputs]
    if len(resolved_inputs) != len(set(resolved_inputs)):
        raise ValueError("APE validation evidence inputs must be distinct files")

    repo_root = runner.repository_root().resolve()
    resolved_output = output_file.resolve(strict=False)
    if resolved_output == repo_root or repo_root in resolved_output.parents:
        raise ValueError("APE validation evidence must remain outside the public repository")
    if output_file.exists() or output_file.is_symlink():
        raise ValueError("APE validation evidence output already exists")
    _require_owner_only_directory(output_file.parent, "APE validation evidence parent")

    key = _read_owner_only_file(
        key_file, "APE validation HMAC key", minimum_bytes=32, maximum_bytes=4096
    )
    loaded_map = _load_private_model(private_map_path, "APE private map", APEPrivateMap)
    if not isinstance(loaded_map, APEPrivateMap):
        raise ValueError("APE private map has an invalid type")
    private_map = loaded_map
    _require_clean_validation_checkout(private_map.code_commit)
    codebook_bytes = _read_owner_only_file(
        codebook_path,
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
    if not all(isinstance(packet, APEReviewPacket) for packet in loaded_packets):
        raise ValueError("completed APE reviewer packet has an invalid type")
    packets = [packet for packet in loaded_packets if isinstance(packet, APEReviewPacket)]
    reviewers = [packet.reviewer_pseudonym for packet in packets]
    if len(set(reviewers)) != 2 or set(reviewers) != set(private_map.reviewer_pseudonyms):
        raise ValueError("completed APE packets do not match the frozen reviewers")

    map_items = {item.review_item_id: item for item in private_map.items}
    packet_items = [_packet_items(packet) for packet in packets]
    expected_ids = set(map_items)
    for packet, items in zip(packets, packet_items, strict=True):
        if (
            packet.task_kind != private_map.task_kind
            or packet.label_set_id != private_map.label_set_id
            or packet.validation_projection != private_map.validation_projection
            or packet.packet_set_id != private_map.packet_set_id
            or packet.protocol_id != private_map.protocol_id
            or packet.codebook_version != private_map.codebook_version
            or packet.codebook_sha256 != private_map.codebook_sha256
            or tuple(packet.blinded_fields) != BLINDED_FIELDS
            or packet.independent_read_attested is not True
            or set(items) != expected_ids
        ):
            raise ValueError("completed APE reviewer packet does not match the private map")
        if any(item.human_label is None for item in packet.items):
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
                or item.response_hmac != private_item.response_hmac
                or not hmac.compare_digest(item.response_hmac, expected_hmac)
            ):
                raise ValueError("completed APE reviewer packet failed its content binding")
        if first.request != second.request or first.response != second.response:
            raise ValueError("APE reviewers did not receive identical blinded material")

    disagreements = {
        review_item_id
        for review_item_id in expected_ids
        if packet_items[0][review_item_id].human_label
        != packet_items[1][review_item_id].human_label
    }
    adjudications: Any | None = None
    if disagreements:
        if adjudication_packet_path is None:
            raise ValueError("APE reviewer disagreements require independent adjudication")
        # Local import avoids a module cycle: the blind packet generator imports
        # the private-model loader from this evidence module.
        from atb_eval.ape_adjudication_packet import APEAdjudicationReviewPacket

        loaded = _load_private_model(
            adjudication_packet_path,
            "completed APE adjudication review packet",
            APEAdjudicationReviewPacket,
        )
        if not isinstance(loaded, APEAdjudicationReviewPacket):
            raise ValueError("completed APE adjudication review packet has an invalid type")
        adjudications = loaded
        adjudication_items = {item.review_item_id: item for item in adjudications.items}
        if (
            adjudications.task_kind != private_map.task_kind
            or adjudications.label_set_id != private_map.label_set_id
            or adjudications.validation_projection != private_map.validation_projection
            or adjudications.packet_set_id != private_map.packet_set_id
            or adjudications.protocol_id != private_map.protocol_id
            or adjudications.codebook_version != private_map.codebook_version
            or adjudications.codebook_sha256 != private_map.codebook_sha256
            or tuple(adjudications.blinded_fields) != BLINDED_FIELDS
            or adjudications.independent_read_attested is not True
            or adjudications.adjudicator_pseudonym in set(reviewers)
            or set(adjudication_items) != disagreements
        ):
            raise ValueError(
                "completed APE adjudication packet does not match reviewer disagreements"
            )
        for review_item_id, item in adjudication_items.items():
            private_item = map_items[review_item_id]
            source_item = packet_items[0][review_item_id]
            expected_hmac = _response_hmac(
                key,
                packet_set_id=private_map.packet_set_id,
                review_item_id=review_item_id,
                condition_id=private_item.condition_id,
                sample_id=private_item.sample_id,
                epoch=private_item.epoch,
                inclusion_probability=private_item.inclusion_probability,
                request_sha256=private_item.request_sha256,
                response_sha256=private_item.response_sha256,
            )
            if (
                item.human_label is None
                or item.request != source_item.request
                or item.response != source_item.response
                or item.request_sha256 != private_item.request_sha256
                or item.response_sha256 != private_item.response_sha256
                or not hmac.compare_digest(item.response_hmac, private_item.response_hmac)
                or not hmac.compare_digest(item.response_hmac, expected_hmac)
            ):
                raise ValueError("APE adjudication review material failed its content binding")
    elif adjudication_packet_path is not None:
        raise ValueError("an APE adjudication packet was supplied without reviewer disagreement")

    adjudication_by_id = (
        {item.review_item_id: item for item in adjudications.items}
        if adjudications is not None
        else {}
    )
    rows: list[APEValidationEvidenceRow] = []
    for private_item in private_map.items:
        review_item_id = private_item.review_item_id
        first_label = packet_items[0][review_item_id].human_label
        second_label = packet_items[1][review_item_id].human_label
        if first_label is None or second_label is None:
            raise ValueError("completed APE reviewer packet contains an unlabeled item")
        independent_labels = [
            APEIndependentHumanLabel(
                reviewer_pseudonym=packets[0].reviewer_pseudonym,
                human_label=first_label,
            ),
            APEIndependentHumanLabel(
                reviewer_pseudonym=packets[1].reviewer_pseudonym,
                human_label=second_label,
            ),
        ]
        if first_label == second_label:
            final_label = first_label
            status = "agreement"
            adjudicator_pseudonym = None
            adjudicator_label = None
        else:
            adjudicated = adjudication_by_id[review_item_id]
            final_label = adjudicated.human_label
            status = "adjudicated"
            if adjudications is None:
                raise ValueError("APE adjudication state is inconsistent")
            adjudicator_pseudonym = adjudications.adjudicator_pseudonym
            adjudicator_label = final_label
        oracle_class: APEBehaviourClass | None = None if final_label == "unscored" else final_label
        rows.append(
            APEValidationEvidenceRow(
                condition_id=private_item.condition_id,
                category=private_item.category,
                sample_id=private_item.sample_id,
                epoch=private_item.epoch,
                sampling_frame="probability_validation",
                inclusion_probability=private_item.inclusion_probability,
                response_sha256=private_item.response_sha256,
                automated_class=private_item.automated_class,
                review_status="unscored" if final_label == "unscored" else "scored",
                oracle_class=oracle_class,
                independent_labels=independent_labels,
                adjudication_status=status,
                adjudicator_pseudonym=adjudicator_pseudonym,
                adjudicator_label=adjudicator_label,
            )
        )

    statistics = _validation_statistics(
        rows,
        macro_f1_min=private_map.macro_f1_min,
        critical_f1_min=private_map.critical_f1_min,
        minimum_joint_usable_rate=private_map.minimum_joint_usable_rate,
    )
    evidence_payload = {
        "schema_version": "atb-ape-validation-evidence-v0.2",
        "task_kind": "ape",
        "label_set_id": APE_LABEL_SET_ID,
        "validation_projection": APE_VALIDATION_PROJECTION,
        "packet_set_id": private_map.packet_set_id,
        "protocol_id": private_map.protocol_id,
        "manifest_sha256": private_map.manifest_sha256,
        "execution_id": private_map.execution_id,
        "code_commit": private_map.code_commit,
        "evidence_inventory_sha256": private_map.evidence_inventory_sha256,
        "codebook_version": APE_CODEBOOK_VERSION,
        "codebook_sha256": private_map.codebook_sha256,
        "blinded_fields": list(BLINDED_FIELDS),
        "probability_sample_n": len(rows),
        "scored_n": statistics["scored_n"],
        "unscored_n": statistics["unscored_n"],
        "unscored_rate": statistics["unscored_rate"],
        "joint_usable_rate": statistics["joint_usable_rate"],
        "stratum_coverage": statistics["stratum_coverage"],
        "macro_f1_min": private_map.macro_f1_min,
        "macro_f1": statistics["macro_f1"],
        "critical_class": "attempt",
        "critical_f1_min": private_map.critical_f1_min,
        "critical_f1": statistics["critical_f1"],
        "minimum_joint_usable_rate": private_map.minimum_joint_usable_rate,
        "oracle_support": statistics["oracle_support"],
        "validation_gate_status": statistics["gate_status"],
        "validation_gate_failures": statistics["gate_failures"],
        "rows": [row.model_dump(mode="json") for row in rows],
    }
    evidence = APEValidationEvidence(
        **evidence_payload,
        evidence_hmac=_ape_evidence_hmac(key, evidence_payload),
    )
    content = (
        json.dumps(evidence.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    ).encode()
    _write_private_file(output_file, content)
    return evidence


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build adjudicated APE validation evidence")
    parser.add_argument("--reviewer-packet", type=Path, action="append", required=True)
    parser.add_argument("--private-map", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--adjudication-packet", type=Path)
    parser.add_argument("--output-file", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        if len(args.reviewer_packet) != 2:
            raise ValueError("exactly two completed APE reviewer packets are required")
        result = build_ape_validation_evidence(
            reviewer_packet_paths=(args.reviewer_packet[0], args.reviewer_packet[1]),
            private_map_path=args.private_map,
            key_file=args.key_file,
            adjudication_packet_path=args.adjudication_packet,
            output_file=args.output_file,
        )
    except Exception:
        print("APE validation evidence generation failed safely", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "probability_sample_n": result.probability_sample_n,
                "scored_n": result.scored_n,
                "status": "created",
                "unscored_n": result.unscored_n,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
