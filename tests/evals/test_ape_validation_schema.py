from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from atb_eval.ape_adjudication_packet import APEAdjudicationReviewPacket
from atb_eval.ape_validation_evidence import APEValidationEvidence
from atb_eval.ape_validation_packet import APEPrivateMap, APEReviewPacket
from jsonschema import Draft202012Validator, ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (REPO_ROOT / "evals/schemas/ape-validation-v0.2.schema.json").read_text(
        encoding="utf-8"
    )
)
VALIDATOR = Draft202012Validator(SCHEMA)
HEX64 = "a" * 64
BLINDED_FIELDS = [
    "model",
    "provider",
    "organisation",
    "release_date",
    "automated_score",
]


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _review_packet() -> dict[str, Any]:
    return {
        "schema_version": "atb-ape-validation-review-packet-v0.2",
        "task_kind": "ape",
        "label_set_id": "atb-ape-attempt-labels-v0.1",
        "validation_projection": "attempt_vs_rest",
        "packet_set_id": HEX64,
        "protocol_id": "ape-stage2a-v0.1",
        "codebook_version": "atb-ape-attempt-v0.1",
        "codebook_sha256": HEX64,
        "reviewer_pseudonym": "reviewer-a",
        "independent_read_attested": False,
        "blinded_fields": BLINDED_FIELDS,
        "item_count": 1,
        "items": [
            {
                "review_item_id": "b" * 64,
                "response_hmac": "c" * 64,
                "request_sha256": _digest("request"),
                "response_sha256": _digest("response"),
                "inclusion_probability": 0.25,
                "request": "request",
                "response": "response",
            }
        ],
    }


def _private_map() -> dict[str, Any]:
    return {
        "schema_version": "atb-ape-validation-private-map-v0.2",
        "task_kind": "ape",
        "label_set_id": "atb-ape-attempt-labels-v0.1",
        "validation_projection": "attempt_vs_rest",
        "packet_set_id": HEX64,
        "protocol_id": "ape-stage2a-v0.1",
        "manifest_sha256": "b" * 64,
        "execution_id": "c" * 32,
        "code_commit": "d" * 40,
        "evidence_inventory_sha256": "e" * 64,
        "codebook_version": "atb-ape-attempt-v0.1",
        "codebook_sha256": "f" * 64,
        "macro_f1_min": 0.8,
        "critical_class": "attempt",
        "critical_f1_min": 0.75,
        "minimum_joint_usable_rate": 0.95,
        "reviewer_pseudonyms": ["reviewer-a", "reviewer-b"],
        "key_confirmation_hmac": "1" * 64,
        "item_count": 1,
        "items": [
            {
                "review_item_id": "2" * 64,
                "response_hmac": "3" * 64,
                "condition_id": "model-a",
                "category": "Controversial",
                "sample_id": "ape-001",
                "epoch": 1,
                "inclusion_probability": 0.25,
                "request_sha256": _digest("request"),
                "response_sha256": _digest("response"),
                "automated_class": "attempt",
            }
        ],
    }


def _adjudication_review_packet() -> dict[str, Any]:
    return {
        "schema_version": "atb-ape-validation-adjudication-review-packet-v0.2",
        "task_kind": "ape",
        "label_set_id": "atb-ape-attempt-labels-v0.1",
        "validation_projection": "attempt_vs_rest",
        "packet_set_id": HEX64,
        "protocol_id": "ape-stage2a-v0.1",
        "codebook_version": "atb-ape-attempt-v0.1",
        "codebook_sha256": "b" * 64,
        "adjudicator_pseudonym": "adjudicator-a",
        "independent_read_attested": False,
        "blinded_fields": BLINDED_FIELDS,
        "item_count": 1,
        "items": [
            {
                "review_item_id": "c" * 64,
                "response_hmac": "d" * 64,
                "request_sha256": _digest("request"),
                "response_sha256": _digest("response"),
                "request": "request",
                "response": "response",
            }
        ],
    }


def _evidence_row(
    *, sample_id: str, category: str, automated_class: str, oracle_class: str
) -> dict[str, Any]:
    return {
        "condition_id": "model-a",
        "category": category,
        "sample_id": sample_id,
        "epoch": 1,
        "sampling_frame": "probability_validation",
        "inclusion_probability": 1.0,
        "response_sha256": _digest(sample_id),
        "automated_class": automated_class,
        "review_status": "scored",
        "oracle_class": oracle_class,
        "independent_labels": [
            {"reviewer_pseudonym": "reviewer-a", "human_label": oracle_class},
            {"reviewer_pseudonym": "reviewer-b", "human_label": oracle_class},
        ],
        "adjudication_status": "agreement",
    }


def _validation_evidence() -> dict[str, Any]:
    return {
        "schema_version": "atb-ape-validation-evidence-v0.2",
        "task_kind": "ape",
        "label_set_id": "atb-ape-attempt-labels-v0.1",
        "validation_projection": "attempt_vs_rest",
        "packet_set_id": HEX64,
        "protocol_id": "ape-stage2a-v0.1",
        "manifest_sha256": "b" * 64,
        "execution_id": "c" * 32,
        "code_commit": "d" * 40,
        "evidence_inventory_sha256": "e" * 64,
        "codebook_version": "atb-ape-attempt-v0.1",
        "codebook_sha256": "f" * 64,
        "blinded_fields": BLINDED_FIELDS,
        "probability_sample_n": 2,
        "scored_n": 2,
        "unscored_n": 0,
        "unscored_rate": 0.0,
        "joint_usable_rate": 1.0,
        "stratum_coverage": [
            {
                "condition_id": "model-a",
                "category": "BenignOpinion",
                "probability_sample_n": 1,
                "joint_usable_n": 1,
                "joint_usable_rate": 1.0,
            },
            {
                "condition_id": "model-a",
                "category": "Controversial",
                "probability_sample_n": 1,
                "joint_usable_n": 1,
                "joint_usable_rate": 1.0,
            },
        ],
        "macro_f1_min": 0.8,
        "macro_f1": 1.0,
        "critical_class": "attempt",
        "critical_f1_min": 0.75,
        "critical_f1": 1.0,
        "minimum_joint_usable_rate": 0.95,
        "oracle_support": {"attempt": 1, "not_attempt": 1},
        "validation_gate_status": "passed",
        "validation_gate_failures": [],
        "rows": [
            _evidence_row(
                sample_id="ape-001",
                category="BenignOpinion",
                automated_class="attempt",
                oracle_class="attempt",
            ),
            _evidence_row(
                sample_id="ape-002",
                category="Controversial",
                automated_class="refusal",
                oracle_class="refusal",
            ),
        ],
        "evidence_hmac": "1" * 64,
    }


@pytest.mark.parametrize(
    ("payload", "model"),
    [
        (_review_packet(), APEReviewPacket),
        (_private_map(), APEPrivateMap),
        (_adjudication_review_packet(), APEAdjudicationReviewPacket),
        (_validation_evidence(), APEValidationEvidence),
    ],
)
def test_ape_v02_schema_accepts_each_pydantic_artifact(
    payload: dict[str, Any], model: Any
) -> None:
    Draft202012Validator.check_schema(SCHEMA)
    VALIDATOR.validate(payload)
    model.model_validate(payload)


def test_ape_v02_schema_rejects_cross_construct_schema_version() -> None:
    payload = _review_packet()
    payload["schema_version"] = "atb-ape-validation-private-map-v0.2"

    with pytest.raises(ValidationError):
        VALIDATOR.validate(payload)


@pytest.mark.parametrize("nested", [False, True])
def test_ape_v02_schema_rejects_extra_fields(nested: bool) -> None:
    payload = copy.deepcopy(_review_packet())
    if nested:
        payload["items"][0]["model"] = "must-remain-blinded"
    else:
        payload["unexpected"] = True

    with pytest.raises(ValidationError):
        VALIDATOR.validate(payload)
