import asyncio
import json
from datetime import UTC, datetime

import atb_eval.scanners as scanner_module
import pytest
from atb_eval.scanners import (
    APE_PAIRED_SCHEDULE,
    ape_role_contract_qa,
    deterministic_model_event_qa,
    empty_assistant_message,
    eval_awareness_diagnostic,
    refusal_diagnostic,
)
from inspect_ai._util.registry import registry_info
from inspect_ai.event import ErrorEvent, ModelEvent, SampleLimitEvent
from inspect_ai.log import EvalError
from inspect_ai.model import (
    ChatCompletionChoice,
    ChatMessageAssistant,
    GenerateConfig,
    ModelCall,
    ModelFallback,
    ModelOutput,
)
from inspect_scout import Transcript
from inspect_scout._scanner.loader import config_for_loader


def _output(
    content: str = "answer",
    *,
    model: str = "org/model",
    stop_reason: str = "stop",
    choice_count: int = 1,
) -> ModelOutput:
    choices = [
        ChatCompletionChoice(
            message=ChatMessageAssistant(content=content),
            stop_reason=stop_reason,
        )
        for _ in range(choice_count)
    ]
    return ModelOutput(model=model, choices=choices, completion=content)


def _call(
    *,
    model: str = "org/model",
    response: dict[str, object] | None = None,
    error: bool | None = None,
) -> ModelCall:
    return ModelCall(
        request={"model": model},
        response={"model": model} if response is None else response,
        error=error,
    )


def _event(
    role: str | None = None,
    *,
    uuid: str = "event-1",
    cache: str | None = None,
    call: ModelCall | None | object = ...,
    output: ModelOutput | None = None,
    retries: int | None = None,
    error: str | None = None,
    pending: bool | None = None,
) -> ModelEvent:
    resolved_call = _call() if call is ... else call
    return ModelEvent(
        uuid=uuid,
        model="openrouter/org/model",
        role=role,
        input=[],
        tools=[],
        tool_choice="none",
        config=GenerateConfig(),
        output=output or _output(),
        retries=retries,
        error=error,
        cache=cache,
        call=resolved_call,
        pending=pending,
        completed=datetime.now(UTC),
    )


def _ape_events(*, persuadee_cache: str | None = None) -> list[ModelEvent]:
    persuadee_call: ModelCall | None = None if persuadee_cache == "read" else _call()
    return [
        _event(
            "persuadee",
            uuid="persuadee-event",
            cache=persuadee_cache,
            call=persuadee_call,
        ),
        _event(None, uuid="target-event"),
        _event("evaluator", uuid="evaluator-event"),
        _event("refusal_judge", uuid="refusal-event"),
    ]


def _transcript(
    events: list[object],
    *,
    paired: bool = False,
    task_set: str | None = "ape_turn1",
    task_paired: bool | object = ...,
    eval_paired: bool | object = ...,
    instrument_failures: dict[str, str | None] | None | object = ...,
    error: str | None = None,
    limit: str | None = None,
) -> Transcript:
    task_flag = paired if task_paired is ... else task_paired
    eval_flag = paired if eval_paired is ... else eval_paired
    failures = (
        {
            "persuadee": None,
            "target": None,
            "evaluator": None,
            "refusal_judge": None,
        }
        if instrument_failures is ...
        else instrument_failures
    )
    task_args = {"paired_interlocutor_cache": task_flag} if task_flag is not None else {}
    eval_metadata = {"paired_interlocutor_cache": eval_flag} if eval_flag is not None else {}
    if paired:
        eval_metadata["atb_schedule"] = APE_PAIRED_SCHEDULE
    sample_metadata = {"instrument_failures": failures} if failures is not None else {}
    return Transcript.model_construct(
        transcript_id="transcript-1",
        task_set=task_set,
        error=error,
        limit=limit,
        metadata={
            "task_args": task_args,
            "eval_metadata": eval_metadata,
            "sample_metadata": sample_metadata,
        },
        messages=[],
        events=events,
        timelines=[],
    )


def _scan(factory, transcript: Transcript):
    return asyncio.run(factory()(transcript))


def _codes(result) -> set[str]:
    return set(result.metadata["finding_codes"])


def test_scout_scanners_construct_with_pinned_api() -> None:
    assert empty_assistant_message() is not None
    assert deterministic_model_event_qa() is not None
    assert ape_role_contract_qa() is not None
    assert refusal_diagnostic() is not None
    assert eval_awareness_diagnostic() is not None


def test_empty_assistant_message_flags_empty_content() -> None:
    result = asyncio.run(empty_assistant_message()(ChatMessageAssistant(content=" \n")))

    assert result.value is True
    assert result.explanation == "Empty assistant message."


def test_empty_assistant_message_accepts_nonempty_content() -> None:
    result = asyncio.run(empty_assistant_message()(ChatMessageAssistant(content="answer")))

    assert result.value is False
    assert result.explanation is None


def test_deterministic_model_event_qa_accepts_complete_event() -> None:
    result = _scan(deterministic_model_event_qa, _transcript([_event()]))

    assert result.value is False
    assert result.explanation is None
    assert result.metadata == {
        "finding_codes": [],
        "model_event_count": 1,
        "diagnostic_only": True,
    }


def test_deterministic_model_event_qa_fails_closed_without_model_event() -> None:
    result = _scan(deterministic_model_event_qa, _transcript([]))

    assert result.value is True
    assert _codes(result) == {"model_event_missing"}


def test_deterministic_model_event_qa_detects_duplicate_uuid_and_retry() -> None:
    events = [_event(uuid="duplicate"), _event("grader", uuid="duplicate", retries=1)]
    result = _scan(deterministic_model_event_qa, _transcript(events))

    assert {"duplicate_model_event_uuid", "model_event_retry"}.issubset(_codes(result))


def test_deterministic_model_event_qa_detects_explicit_fallback() -> None:
    output = _output().model_copy(
        update={
            "fallback": ModelFallback(
                model="org/model",
                fallback_model="other/model",
            )
        }
    )
    result = _scan(deterministic_model_event_qa, _transcript([_event(output=output)]))

    assert "model_fallback" in _codes(result)


def test_deterministic_model_event_qa_detects_observable_route_substitution() -> None:
    response = {
        "model": "other/model",
        "provider": "Provider B",
        "openrouter_metadata": {
            "requested": "org/model",
            "strategy": "direct",
            "attempt": 2,
            "pipeline": ["fallback"],
            "attempts": [{"provider": "Provider A"}, {"provider": "Provider B"}],
            "endpoints": {
                "available": [
                    {"provider": "Provider A", "selected": True},
                    {"provider": "Provider B", "selected": True},
                ]
            },
        },
    }
    event = _event(call=_call(response=response))
    result = _scan(deterministic_model_event_qa, _transcript([event]))

    assert {
        "response_output_model_mismatch",
        "route_pipeline_substitution",
        "route_retry",
        "route_selection_ambiguous",
        "served_model_substitution",
    }.issubset(_codes(result))


def test_deterministic_model_event_qa_allows_declared_openrouter_alias() -> None:
    response = {
        "model": "org/model-2026-08-01",
        "provider": "Provider A",
        "openrouter_metadata": {
            "requested": "org/model",
            "strategy": "alias",
            "attempt": 1,
            "pipeline": [],
            "attempts": [{"provider": "Provider A"}],
            "endpoints": {
                "available": [{"provider": "Provider A", "model": "model-build", "selected": True}]
            },
        },
    }
    event = _event(
        call=_call(response=response),
        output=_output(model="org/model-2026-08-01"),
    )
    result = _scan(deterministic_model_event_qa, _transcript([event]))

    assert result.value is False


def test_deterministic_model_event_qa_detects_provider_substitution() -> None:
    response = {
        "model": "org/model",
        "provider": "Provider B",
        "openrouter_metadata": {
            "requested": "org/model",
            "strategy": "direct",
            "attempt": 1,
            "pipeline": [],
            "endpoints": {"available": [{"provider": "Provider A", "selected": True}]},
        },
    }
    result = _scan(
        deterministic_model_event_qa,
        _transcript([_event(call=_call(response=response))]),
    )

    assert "served_provider_substitution" in _codes(result)


def test_deterministic_model_event_qa_detects_transcript_and_event_errors() -> None:
    events = [
        _event(error="model failed"),
        ErrorEvent(
            error=EvalError(
                message="sample failed",
                traceback="fixture",
                traceback_ansi="fixture",
            )
        ),
        SampleLimitEvent(type="token", message="token limit"),
    ]
    result = _scan(
        deterministic_model_event_qa,
        _transcript(events, error="sample failed", limit="token"),
    )

    assert {
        "error_event",
        "model_event_error",
        "sample_limit_event",
        "transcript_error",
        "transcript_limit",
    }.issubset(_codes(result))


def test_deterministic_model_event_qa_detects_call_and_output_errors() -> None:
    output = _output().model_copy(update={"error": "provider failure"})
    event = _event(call=_call(error=True), output=output)
    result = _scan(deterministic_model_event_qa, _transcript([event]))

    assert {"model_call_error", "model_output_error"}.issubset(_codes(result))


def test_deterministic_model_event_qa_fails_closed_on_truthy_call_error() -> None:
    call = _call().model_copy(update={"error": "malformed-truthy-value"})
    result = _scan(
        deterministic_model_event_qa,
        _transcript([_event(call=call)]),
    )

    assert "model_call_error" in _codes(result)


def test_deterministic_model_event_qa_detects_pending_or_incomplete_event() -> None:
    pending = _event(pending=True).model_copy(update={"completed": None})
    result = _scan(deterministic_model_event_qa, _transcript([pending]))

    assert {"model_event_incomplete", "model_event_pending"}.issubset(_codes(result))


def test_deterministic_model_event_qa_detects_missing_call_and_response() -> None:
    missing_call = _event(uuid="missing-call", call=None)
    missing_response = _event(
        "grader",
        uuid="missing-response",
        call=ModelCall(request={"model": "org/model"}, response=None),
    )
    result = _scan(
        deterministic_model_event_qa,
        _transcript([missing_call, missing_response]),
    )

    assert {"model_call_missing", "model_call_response_missing"}.issubset(_codes(result))


def test_deterministic_model_event_qa_allows_local_cache_read_without_call() -> None:
    cached = _event("persuadee", cache="read", call=None)
    result = _scan(deterministic_model_event_qa, _transcript([cached]))

    assert "model_call_missing" not in _codes(result)
    assert result.value is False


def test_deterministic_model_event_qa_detects_empty_or_choice_less_output() -> None:
    output = _output("", choice_count=0)
    result = _scan(deterministic_model_event_qa, _transcript([_event(output=output)]))

    assert {
        "empty_model_output",
        "unexpected_choice_count",
        "unexpected_stop_reason",
    }.issubset(_codes(result))


def test_deterministic_model_event_qa_detects_multiple_choices() -> None:
    result = _scan(
        deterministic_model_event_qa,
        _transcript([_event(output=_output(choice_count=2))]),
    )

    assert "unexpected_choice_count" in _codes(result)


def test_deterministic_model_event_qa_detects_truncation_and_policy_block() -> None:
    events = [
        _event(uuid="truncated", output=_output(stop_reason="max_tokens")),
        _event("grader", uuid="blocked", output=_output(stop_reason="content_filter")),
    ]
    result = _scan(deterministic_model_event_qa, _transcript(events))

    assert {"provider_or_policy_block", "truncated_model_output"}.issubset(_codes(result))


def test_ape_role_contract_accepts_unpaired_four_role_transcript() -> None:
    result = _scan(ape_role_contract_qa, _transcript(_ape_events()))

    assert result.value is False
    assert result.metadata["role_counts"] == {
        "persuadee": 1,
        "target": 1,
        "evaluator": 1,
        "refusal_judge": 1,
    }


def test_ape_role_contract_accepts_paired_cache_write() -> None:
    result = _scan(
        ape_role_contract_qa,
        _transcript(_ape_events(persuadee_cache="write"), paired=True),
    )

    assert result.value is False


def test_ape_role_contract_accepts_paired_local_cache_read() -> None:
    result = _scan(
        ape_role_contract_qa,
        _transcript(_ape_events(persuadee_cache="read"), paired=True),
    )

    assert result.value is False


def test_ape_role_contract_accepts_scout_json_encoded_metadata() -> None:
    transcript = _transcript(_ape_events(persuadee_cache="read"), paired=True)
    transcript.metadata["task_args"] = json.dumps(transcript.metadata["task_args"])
    transcript.metadata["eval_metadata"] = json.dumps(transcript.metadata["eval_metadata"])
    transcript.metadata["sample_metadata"] = json.dumps(transcript.metadata["sample_metadata"])

    result = _scan(ape_role_contract_qa, transcript)

    assert result.value is False


def test_ape_role_contract_detects_missing_duplicate_and_unknown_roles() -> None:
    events = _ape_events()
    events.pop()
    events.append(_event("evaluator", uuid="second-evaluator"))
    events.append(_event("other", uuid="unknown-role"))
    result = _scan(ape_role_contract_qa, _transcript(events))

    assert {
        "unexpected_evaluator_event_count",
        "unexpected_model_event_count",
        "unexpected_model_role",
        "unexpected_refusal_judge_event_count",
    }.issubset(_codes(result))


def test_ape_role_contract_treats_persuader_as_target_but_rejects_two_targets() -> None:
    events = _ape_events()
    events.append(_event("persuader", uuid="second-target"))
    result = _scan(ape_role_contract_qa, _transcript(events))

    assert "unexpected_target_event_count" in _codes(result)


def test_ape_role_contract_detects_paired_cache_violations() -> None:
    events = _ape_events(persuadee_cache="write")
    events[0] = events[0].model_copy(update={"call": None})
    events[1] = events[1].model_copy(update={"cache": "read"})
    result = _scan(ape_role_contract_qa, _transcript(events, paired=True))

    assert {
        "ape_cache_write_missing_provider_call",
        "ape_unexpected_role_cache",
    }.issubset(_codes(result))


def test_ape_role_contract_detects_cache_read_with_provider_call() -> None:
    events = _ape_events(persuadee_cache="read")
    events[0] = events[0].model_copy(update={"call": _call()})
    result = _scan(ape_role_contract_qa, _transcript(events, paired=True))

    assert "ape_cache_read_has_provider_call" in _codes(result)


def test_ape_role_contract_detects_missing_cache_mode_and_schedule() -> None:
    transcript = _transcript(
        _ape_events(persuadee_cache="write"),
        task_paired=None,
        eval_paired=None,
    )
    result = _scan(ape_role_contract_qa, transcript)

    assert "ape_cache_mode_missing" in _codes(result)


def test_ape_role_contract_detects_cache_mode_disagreement() -> None:
    transcript = _transcript(
        _ape_events(persuadee_cache="write"),
        task_paired=True,
        eval_paired=False,
    )
    result = _scan(ape_role_contract_qa, transcript)

    assert "ape_cache_mode_disagreement" in _codes(result)


def test_ape_role_contract_detects_missing_paired_schedule() -> None:
    transcript = _transcript(_ape_events(persuadee_cache="write"), paired=True)
    transcript.metadata["eval_metadata"].pop("atb_schedule")
    result = _scan(ape_role_contract_qa, transcript)

    assert "ape_paired_schedule_missing" in _codes(result)


def test_ape_role_contract_detects_instrument_failure_metadata_mismatch() -> None:
    events = _ape_events()
    events[1] = events[1].model_copy(update={"output": _output("")})
    result = _scan(ape_role_contract_qa, _transcript(events))

    assert "ape_instrument_failure_metadata_mismatch" in _codes(result)


def test_ape_role_contract_accepts_matching_instrument_failure_metadata() -> None:
    events = _ape_events()
    events[1] = events[1].model_copy(update={"output": _output("")})
    failures = {
        "persuadee": None,
        "target": "target_empty_response",
        "evaluator": None,
        "refusal_judge": None,
    }
    result = _scan(
        ape_role_contract_qa,
        _transcript(events, instrument_failures=failures),
    )

    assert result.value is False


def test_ape_role_contract_detects_invalid_instrument_failure_metadata() -> None:
    result = _scan(
        ape_role_contract_qa,
        _transcript(_ape_events(), instrument_failures=None),
    )

    assert "ape_instrument_failure_metadata_invalid" in _codes(result)


def test_ape_role_contract_rejects_non_ape_transcript() -> None:
    result = _scan(
        ape_role_contract_qa,
        _transcript(_ape_events(), task_set="different_task"),
    )

    assert "unexpected_task" in _codes(result)


def test_llm_diagnostics_are_universally_blocked_without_sending_any_role_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invocations: list[object] = []

    def forbidden_llm_scanner(**arguments: object):
        invocations.append(arguments)
        raise AssertionError("disabled diagnostic constructed an LLM scanner")

    monkeypatch.setattr(
        scanner_module,
        "llm_scanner",
        forbidden_llm_scanner,
        raising=False,
    )
    events = _ape_events()
    markers = [
        "PERSUADEE_SECRET_MARKER",
        "TARGET_SECRET_MARKER",
        "EVALUATOR_SECRET_MARKER",
        "REFUSAL_SECRET_MARKER",
    ]
    for index, marker in enumerate(markers):
        events[index] = events[index].model_copy(update={"output": _output(marker)})
    for task_set in ("ape_turn1", "unknown_task", None):
        transcript = _transcript(events, task_set=task_set)
        transcript.messages = [ChatMessageAssistant(content="MAIN_THREAD_SECRET_MARKER")]
        for factory in (
            scanner_module.refusal_diagnostic,
            scanner_module.eval_awareness_diagnostic,
        ):
            result = _scan(factory, transcript)
            assert result.value["value"] == "unclear"
            assert result.metadata == {
                "blocked": True,
                "reason": "target_projection_and_frozen_judge_unavailable",
                "diagnostic_only": True,
            }
    assert invocations == []


def test_disabled_llm_diagnostics_load_metadata_only() -> None:
    for factory in (
        scanner_module.refusal_diagnostic,
        scanner_module.eval_awareness_diagnostic,
    ):
        config = registry_info(factory()).metadata["scanner_config"]
        assert config.content.messages is None
        assert config.content.events is None
        assert config.content.timeline is None
        loader_content = config_for_loader(config.loader).content
        assert loader_content.messages is None
        assert loader_content.events is None
        assert loader_content.timeline is None
