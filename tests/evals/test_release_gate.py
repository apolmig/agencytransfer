from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
from atb_eval.manifest import load_manifest
from atb_eval.release_gate import (
    LoggedResponse,
    ReleaseCandidate,
    ValidationEvidence,
    _condition_log_configuration_failures,
    _fresh_route_raw_matches,
    _native_class_support_failures,
    _score_integrity,
    _stratified_probability_sample,
    _validation_metrics,
    evaluate_release_candidate,
    verify_release_evidence,
)
from atb_eval.runner import effective_generate_config
from inspect_ai.model import GenerateConfig
from jsonschema import Draft202012Validator
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]


def _candidate() -> dict:
    payload = {
        "schema_version": "atb-release-candidate-v0.1",
        "protocol_id": "atb-diselect-wave1a-v0.1",
        "execution_id": "f" * 32,
        "manifest_sha256": "a" * 64,
        "code_commit": "b" * 40,
        "environment_lock_sha256": "c" * 64,
        "eval_log_set_sha256": "e" * 64,
        "human_validation_evidence_sha256": "d" * 64,
        "route_integrity": {
            "status": "passed",
            "unexpected_models": [],
            "fallback_count": 0,
            "provider_substitution_count": 0,
        },
        "human_validation": {
            "status": "passed",
            "probability_sample_n": 50,
            "double_coded_n": 50,
            "macro_f1": 0.84,
            "critical_class": "comply",
            "critical_class_f1": 0.8,
        },
        "missingness": {
            "attempted_n": 50,
            "usable_n": 49,
            "explained_failure_n": 0,
            "unexplained_failure_n": 1,
            "sample_retry_attempt_n": 0,
            "superseded_eval_attempt_n": 0,
        },
        "recorded_usage": {"total_tokens": 12000, "total_cost_usd": 1.25},
        "dual_use_review": {
            "decision": "release",
            "reviewer_pseudonyms": ["reviewer-a", "reviewer-b"],
        },
        "aggregate_rows": [
            {
                "condition_id": "model-a",
                "subset": "harmful",
                "attempted_n": 50,
                "usable_n": 49,
                "explained_failure_n": 0,
                "unexplained_failure_n": 1,
                "counts": {
                    "comply": 10,
                    "soft_refuse": 5,
                    "refuse": 33,
                    "incoherent": 1,
                },
                "failure_counts": {"unexplained": 1},
            }
        ],
    }
    payload["public_payload"] = {
        "schema_version": "atb-public-aggregate-v0.1",
        "gate_status": "passed",
        "gate_version": "atb-release-gate-v0.1",
        "protocol_id": payload["protocol_id"],
        "execution_id": payload["execution_id"],
        "manifest_sha256": payload["manifest_sha256"],
        "code_commit": payload["code_commit"],
        "environment_lock_sha256": payload["environment_lock_sha256"],
        "eval_log_set_sha256": payload["eval_log_set_sha256"],
        "human_validation_evidence_sha256": payload["human_validation_evidence_sha256"],
        "route_integrity": deepcopy(payload["route_integrity"]),
        "human_validation": deepcopy(payload["human_validation"]),
        "missingness": deepcopy(payload["missingness"]),
        "recorded_usage": deepcopy(payload["recorded_usage"]),
        "dual_use_review": deepcopy(payload["dual_use_review"]),
        "aggregate_rows": deepcopy(payload["aggregate_rows"]),
    }
    return payload


def test_valid_release_candidate_passes() -> None:
    candidate = ReleaseCandidate.model_validate(_candidate())
    assert evaluate_release_candidate(candidate) == []


def test_failed_validation_and_fallback_are_rejected() -> None:
    payload = deepcopy(_candidate())
    payload["human_validation"]["status"] = "pending"
    payload["route_integrity"]["fallback_count"] = 1
    failures = evaluate_release_candidate(ReleaseCandidate.model_validate(payload))
    assert "blind human validation did not pass" in failures
    assert "fallback or provider substitution occurred" in failures


def test_raw_fields_are_rejected_from_public_payload() -> None:
    payload = deepcopy(_candidate())
    payload["public_payload"]["response"] = "raw text"
    try:
        ReleaseCandidate.model_validate(payload)
    except ValueError as exc:
        assert "Extra inputs are not permitted" in str(exc)
    else:
        raise AssertionError("raw public fields must fail the allowlist schema")


def test_public_payload_must_match_gated_aggregates() -> None:
    payload = deepcopy(_candidate())
    payload["public_payload"]["aggregate_rows"][0]["counts"]["comply"] = 11
    payload["public_payload"]["aggregate_rows"][0]["counts"]["refuse"] = 32
    failures = evaluate_release_candidate(ReleaseCandidate.model_validate(payload))
    assert "public payload aggregate_rows does not match gated evidence" in failures


def test_impossible_validation_and_missingness_values_are_rejected() -> None:
    payload = deepcopy(_candidate())
    payload["human_validation"]["macro_f1"] = 1.2
    with pytest.raises(ValidationError):
        ReleaseCandidate.model_validate(payload)

    payload = deepcopy(_candidate())
    payload["missingness"]["unexplained_failure_n"] = 2
    with pytest.raises(ValidationError, match="must sum to attempted_n"):
        ReleaseCandidate.model_validate(payload)


def test_validation_metrics_are_recomputed_over_all_native_classes() -> None:
    oracle = ["comply", "soft_refuse", "refuse", "incoherent"]
    macro_f1, per_class = _validation_metrics(oracle, list(oracle))
    assert macro_f1 == 1
    assert per_class == {label: 1 for label in oracle}


def test_validation_metrics_do_not_score_classes_without_oracle_support() -> None:
    macro_f1, per_class = _validation_metrics(
        ["comply", "refuse"], ["comply", "comply"], [1.0, 3.0]
    )
    assert per_class == {
        "comply": pytest.approx(0.4),
        "soft_refuse": None,
        "refuse": pytest.approx(0.0),
        "incoherent": None,
    }
    assert macro_f1 == pytest.approx(0.2)

    macro_f1, per_class = _validation_metrics(["comply", "refuse"], ["soft_refuse", "refuse"])
    assert per_class["soft_refuse"] == pytest.approx(0.0)
    assert per_class["incoherent"] is None
    assert macro_f1 == pytest.approx(1 / 3)


def test_public_validation_requires_oracle_support_for_every_native_class() -> None:
    assert _native_class_support_failures(["comply", "soft_refuse", "refuse", "incoherent"]) == []
    assert _native_class_support_failures(["comply", "refuse"]) == [
        "public validation sample lacks oracle support for native classes: soft_refuse, incoherent"
    ]


def test_failed_grader_cannot_supply_a_native_score() -> None:
    grader_event = type("ModelEvent", (), {})()
    grader_event.role = "grader"
    grader_event.error = "provider failure"
    grader_event.call = None
    grader_event.output = SimpleNamespace(
        completion="FINAL_LABEL: refuse",
        error=None,
        stop_reason="stop",
    )
    sample = SimpleNamespace(
        error=None,
        output=SimpleNamespace(completion="target", error=None, stop_reason="stop"),
        events=[grader_event],
    )
    score = SimpleNamespace(
        value="refuse",
        metadata={"codebook": "atb-diselect-response-v0.1"},
    )
    failures, cause = _score_integrity(sample, score, "refuse")
    assert "native score exists for a failed or unscorable grader" in failures
    assert cause == "grader_model_error"


def test_release_gate_accepts_effective_openrouter_role_headers(monkeypatch) -> None:
    manifest = load_manifest(REPO_ROOT / "evals/manifests/diselect-route-preflight-v0.1.json")
    condition = manifest.models[0]
    grader = manifest.model_roles["grader"]
    task_args = {**manifest.task.args, "source_revision": manifest.dataset.source_revision}
    eval_config = {
        "sample_shuffle": manifest.run.sample_shuffle,
        "epochs": manifest.run.epochs,
        "fail_on_error": manifest.run.fail_on_error,
        "retry_on_error": manifest.run.retry_on_error,
        "token_limit": manifest.run.sample_token_limit,
        "cost_limit": manifest.run.sample_cost_limit_usd,
        "max_samples": 1,
        "max_tasks": len(manifest.models),
        "log_model_api": manifest.run.log_model_api,
    }
    log = SimpleNamespace(
        eval=SimpleNamespace(
            model=condition.model,
            model_args=condition.inspect_model_args(),
            model_base_url="https://openrouter.ai/api/v1",
            model_generate_config=GenerateConfig(**effective_generate_config(condition, manifest)),
            model_roles={
                "grader": SimpleNamespace(
                    model=grader.model,
                    args=grader.inspect_model_args(),
                    base_url="https://openrouter.ai/api/v1",
                    config=GenerateConfig(**effective_generate_config(grader, manifest)),
                )
            },
            task_args=task_args,
            config=SimpleNamespace(model_dump=lambda: eval_config),
            scorers=[SimpleNamespace(name="diselect_response_class")],
        )
    )
    monkeypatch.setattr("atb_eval.release_gate.logged_packages_match", lambda *_: True)

    assert _condition_log_configuration_failures(log, condition, manifest) == []


def test_validation_metrics_use_inverse_probability_weights() -> None:
    macro_f1, per_class = _validation_metrics(
        ["comply", "refuse"], ["comply", "comply"], [1.0, 3.0]
    )
    assert per_class["comply"] == pytest.approx(0.4)
    assert per_class["soft_refuse"] is None
    assert per_class["incoherent"] is None
    assert macro_f1 == pytest.approx(0.2)


def test_stratified_probability_sample_covers_each_stratum() -> None:
    frame = {
        ("model-a", f"a-{index}", 1): LoggedResponse(
            automated_class="refuse",
            response_sha256="a" * 64,
            stratum=("model-a", "voting"),
        )
        for index in range(4)
    }
    frame.update(
        {
            ("model-a", f"b-{index}", 1): LoggedResponse(
                automated_class=None,
                response_sha256="b" * 64,
                stratum=("model-a", "mps"),
            )
            for index in range(2)
        }
    )
    selected = _stratified_probability_sample(frame, 3, "frozen-seed")
    assert len(selected) == 3
    assert {frame[key].stratum for key in selected} == {
        ("model-a", "voting"),
        ("model-a", "mps"),
    }
    assert all(0 < probability <= 1 for probability in selected.values())


def test_validation_evidence_preserves_independent_labels() -> None:
    payload = {
        "schema_version": "atb-validation-evidence-v0.1",
        "protocol_id": "protocol",
        "codebook_version": "atb-human-codebook-v0.1",
        "blinded_fields": [
            "model",
            "provider",
            "organisation",
            "release_date",
            "automated_score",
        ],
        "rows": [
            {
                "condition_id": "model-a",
                "sample_id": "sample-a",
                "epoch": 1,
                "sampling_frame": "probability_validation",
                "inclusion_probability": 0.5,
                "response_sha256": "a" * 64,
                "oracle_class": "refuse",
                "independent_labels": [
                    {"reviewer_pseudonym": "r1", "native_class": "refuse"},
                    {"reviewer_pseudonym": "r2", "native_class": "refuse"},
                ],
                "adjudication_status": "agreement",
                "adjudicator_pseudonym": None,
                "adjudicator_label": None,
            }
        ],
    }
    assert ValidationEvidence.model_validate(payload).rows[0].oracle_class == "refuse"
    schema = json.loads(
        (REPO_ROOT / "evals/schemas/validation-evidence-v0.1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(payload)


def test_validation_adjudication_requires_disagreement_and_recorded_label() -> None:
    row = {
        "condition_id": "model-a",
        "sample_id": "sample-a",
        "epoch": 1,
        "sampling_frame": "disagreement_audit",
        "inclusion_probability": None,
        "response_sha256": "a" * 64,
        "oracle_class": "refuse",
        "independent_labels": [
            {"reviewer_pseudonym": "r1", "native_class": "comply"},
            {"reviewer_pseudonym": "r2", "native_class": "refuse"},
        ],
        "adjudication_status": "adjudicated",
        "adjudicator_pseudonym": "r3",
        "adjudicator_label": "refuse",
    }
    payload = {
        "schema_version": "atb-validation-evidence-v0.1",
        "protocol_id": "protocol",
        "codebook_version": "atb-human-codebook-v0.1",
        "blinded_fields": [
            "model",
            "provider",
            "organisation",
            "release_date",
            "automated_score",
        ],
        "rows": [row],
    }
    evidence = ValidationEvidence.model_validate(payload)
    assert evidence.rows[0].adjudicator_label == "refuse"
    schema = json.loads(
        (REPO_ROOT / "evals/schemas/validation-evidence-v0.1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(payload)

    invented_oracle = deepcopy(payload)
    invented_oracle["rows"][0]["independent_labels"][0]["native_class"] = "refuse"
    with pytest.raises(ValidationError, match="only valid when independent reviewers disagree"):
        ValidationEvidence.model_validate(invented_oracle)

    missing_label = deepcopy(payload)
    missing_label["rows"][0]["adjudicator_label"] = None
    with pytest.raises(ValidationError, match="must determine the oracle class"):
        ValidationEvidence.model_validate(missing_label)

    blank_reviewer = deepcopy(payload)
    blank_reviewer["rows"][0]["independent_labels"][0]["reviewer_pseudonym"] = "  "
    with pytest.raises(ValidationError, match="cannot be blank"):
        ValidationEvidence.model_validate(blank_reviewer)


def test_fake_candidate_cannot_pass_without_frozen_external_evidence(tmp_path: Path) -> None:
    candidate = ReleaseCandidate.model_validate(_candidate())
    failures, manifest = verify_release_evidence(
        candidate,
        manifest_path=REPO_ROOT / "evals/manifests/diselect-wave1a-v0.1.json",
        lock_path=REPO_ROOT / "uv.lock",
        log_dir=tmp_path / "missing-logs",
        source_dir=tmp_path / "missing-source",
        validation_evidence_path=tmp_path / "missing-validation.json",
        repo_root=REPO_ROOT,
    )
    assert manifest is not None
    assert "protocol manifest hash does not match candidate" in failures
    assert "public release requires a frozen protocol manifest" in failures
    assert "frozen manifest does not permit a public aggregate candidate" in failures
    assert "no Inspect .eval logs were supplied" in failures
    assert "human-validation evidence file is missing" in failures


def test_release_receipt_reprojects_fresh_raw_provider_evidence() -> None:
    manifest = load_manifest(REPO_ROOT / "evals/manifests/diselect-route-preflight-v0.1.json")
    condition = manifest.models[0]
    revision = condition.revision
    assert revision is not None
    evidence = json.loads((REPO_ROOT / revision.evidence_path).read_text(encoding="utf-8"))
    raw_files = {
        field: REPO_ROOT / f"evals/model-revisions/provider-responses/{digest}.json"
        for field, digest in {
            "model_response_sha256": revision.model_response_sha256,
            "models_response_sha256": revision.models_response_sha256,
            "endpoint_response_sha256": revision.endpoint_response_sha256,
            "zdr_response_sha256": revision.zdr_response_sha256,
        }.items()
        if digest is not None
    }
    assert _fresh_route_raw_matches(condition, evidence, raw_files)
    assert not _fresh_route_raw_matches(condition, {}, raw_files)
