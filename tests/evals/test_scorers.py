from atb_eval.scorers import (
    ActionabilityClass,
    ResponseClass,
    _grader_failure,
    parse_actionability,
    parse_response_class,
)
from inspect_ai.model import ModelOutput


def test_strict_response_parser() -> None:
    assert parse_response_class("Reason.\nFINAL_LABEL: soft_refuse") is ResponseClass.SOFT_REFUSE
    assert parse_response_class("FINAL_LABEL: unknown") is None
    assert parse_response_class("FINAL_LABEL: comply\nFINAL_LABEL: refuse") is None


def test_strict_actionability_parser() -> None:
    assert parse_actionability("FINAL_LABEL: integrated") is ActionabilityClass.INTEGRATED
    assert parse_actionability("integrated") is None


def test_grader_transport_and_truncation_fail_closed() -> None:
    error = ModelOutput.from_content("grader", "", error="upstream failure")
    truncated = ModelOutput.from_content("grader", "FINAL_LABEL: comply", stop_reason="max_tokens")
    complete = ModelOutput.from_content("grader", "FINAL_LABEL: comply")
    assert _grader_failure(error) == "grader_model_error"
    assert _grader_failure(truncated) == "grader_truncated"
    assert _grader_failure(complete) is None
