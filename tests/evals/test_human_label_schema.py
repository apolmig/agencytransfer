from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (REPO_ROOT / "evals/schemas/human-label-v0.1.schema.json").read_text(encoding="utf-8")
)
VALIDATOR = Draft202012Validator(SCHEMA)


def _label() -> dict:
    return {
        "sample_id": "opaque-sample-001",
        "response_hmac": "a" * 64,
        "codebook_version": "atb-human-codebook-v0.1",
        "reviewer_pseudonym": "reviewer-01",
        "sampling_frame": "probability_validation",
        "inclusion_probability": 0.2,
        "blinded_fields": [
            "model",
            "provider",
            "organisation",
            "release_date",
            "automated_score",
        ],
        "native_class": "refuse",
        "axis_applicability": {
            "deception_or_concealment_assistance": False,
            "exploitative_personalization_assistance": False,
            "persistence_or_pressure_assistance": False,
            "operational_actionability": True,
            "reference_factuality": False,
        },
        "deception_or_concealment_assistance": "not_applicable",
        "exploitative_personalization_assistance": "not_applicable",
        "persistence_or_pressure_assistance": "not_applicable",
        "operational_actionability": "none",
        "reference_factuality": "not_applicable",
        "private_evidence_offsets": [],
        "uncertainty": "low",
        "skip_reason": None,
        "adjudication_status": "independent",
    }


def test_human_label_schema_accepts_a_coherent_blind_annotation() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    VALIDATOR.validate(_label())


def test_all_committed_json_schemas_are_valid() -> None:
    for path in (REPO_ROOT / "evals/schemas").glob("*.schema.json"):
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))


def test_not_applicable_axis_rejects_a_behaviour_label() -> None:
    label = deepcopy(_label())
    label["deception_or_concealment_assistance"] = "present"
    with pytest.raises(ValidationError):
        VALIDATOR.validate(label)


def test_probability_sample_requires_inclusion_probability() -> None:
    label = deepcopy(_label())
    label["inclusion_probability"] = None
    with pytest.raises(ValidationError):
        VALIDATOR.validate(label)


def test_unscorable_response_requires_a_skip_reason() -> None:
    label = deepcopy(_label())
    label["native_class"] = "unscorable"
    with pytest.raises(ValidationError):
        VALIDATOR.validate(label)
