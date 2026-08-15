"""Inspect Scout QA scanners.

Scanner outputs are diagnostics, not benchmark outcomes. Deterministic scanners
only report persisted execution anomalies. LLM entry points remain fail-closed
until ATB has a target-only projection and a frozen, human-calibrated judge.
"""

import json
from collections.abc import AsyncIterator, Mapping
from typing import Any, Literal

from inspect_ai.event import ErrorEvent, ModelEvent, SampleLimitEvent
from inspect_ai.model import ChatMessage
from inspect_scout import Loader, Result, Scanner, Transcript, TranscriptContent, loader, scanner
from pydantic import BaseModel, Field

APE_ROLES = ("persuadee", "target", "evaluator", "refusal_judge")
APE_PAIRED_SCHEDULE = "paired-common-interlocutor-cache-v0.1"


class RefusalDiagnostic(BaseModel):
    value: Literal["none", "soft", "full", "unclear"] = Field(
        description="Observable refusal class in the evaluated target's response."
    )
    explanation: str = Field(description="Brief reason without reproducing sensitive text.")


class EvalAwarenessDiagnostic(BaseModel):
    value: Literal["yes", "no", "unclear"]
    explanation: str = Field(description="Brief reason without reproducing sensitive text.")


def _mapping(value: Any) -> Mapping[str, Any] | None:
    if isinstance(value, Mapping):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None
        return parsed if isinstance(parsed, Mapping) else None
    return None


def _text(value: Any) -> str:
    try:
        return str(value or "")
    except (AttributeError, IndexError, TypeError, ValueError):
        return ""


def _finding_result(
    findings: list[str],
    *,
    model_event_count: int,
    role_counts: Mapping[str, int] | None = None,
) -> Result:
    codes = sorted(set(findings))
    metadata: dict[str, Any] = {
        "finding_codes": codes,
        "model_event_count": model_event_count,
        "diagnostic_only": True,
    }
    if role_counts is not None:
        metadata["role_counts"] = dict(role_counts)
    return Result(
        value=bool(codes),
        explanation=(f"Deterministic QA findings: {', '.join(codes)}." if codes else None),
        metadata=metadata,
    )


def _observable_route_findings(event: ModelEvent) -> list[str]:
    """Report route anomalies only when explicit in persisted raw data.

    Missing optional metadata is not route verification. The manifest-aware
    runner postflight remains authoritative for the configured route.
    """

    findings: list[str] = []
    output = getattr(event, "output", None)
    if output is not None and getattr(output, "fallback", None) is not None:
        findings.append("model_fallback")

    call = getattr(event, "call", None)
    request = _mapping(getattr(call, "request", None))
    response = _mapping(getattr(call, "response", None))
    if response is None:
        return findings

    response_model = response.get("model")
    output_model = getattr(output, "model", None)
    if (
        isinstance(response_model, str)
        and response_model
        and isinstance(output_model, str)
        and output_model
        and response_model != output_model
    ):
        findings.append("response_output_model_mismatch")

    metadata = _mapping(response.get("openrouter_metadata"))
    if metadata is None:
        return findings

    requested = metadata.get("requested")
    request_model = request.get("model") if request is not None else None
    if isinstance(requested, str) and isinstance(request_model, str) and requested != request_model:
        findings.append("route_requested_model_mismatch")
    if (
        metadata.get("strategy") == "direct"
        and isinstance(requested, str)
        and isinstance(response_model, str)
        and requested != response_model
    ):
        findings.append("served_model_substitution")

    pipeline = metadata.get("pipeline")
    if pipeline not in (None, []):
        findings.append("route_pipeline_substitution")

    attempt = metadata.get("attempt")
    if attempt is not None and (type(attempt) is not int or attempt != 1):
        findings.append("route_retry")
    attempts = metadata.get("attempts")
    if attempts is not None and (not isinstance(attempts, list) or len(attempts) > 1):
        findings.append("route_retry")

    endpoints = _mapping(metadata.get("endpoints"))
    available = endpoints.get("available") if endpoints is not None else None
    if isinstance(available, list):
        selected = [
            endpoint
            for endpoint in available
            if isinstance(endpoint, Mapping) and endpoint.get("selected") is True
        ]
        if len(selected) != 1:
            findings.append("route_selection_ambiguous")
        else:
            response_provider = response.get("provider")
            selected_provider = selected[0].get("provider")
            if (
                isinstance(response_provider, str)
                and isinstance(selected_provider, str)
                and response_provider != selected_provider
            ):
                findings.append("served_provider_substitution")
    return findings


def _model_event_findings(transcript: Transcript) -> tuple[list[str], list[ModelEvent]]:
    findings: list[str] = []
    model_events = [event for event in transcript.events if isinstance(event, ModelEvent)]
    if not model_events:
        findings.append("model_event_missing")
    if _text(transcript.error).strip():
        findings.append("transcript_error")
    if _text(transcript.limit).strip():
        findings.append("transcript_limit")
    if any(isinstance(event, ErrorEvent) for event in transcript.events):
        findings.append("error_event")
    if any(isinstance(event, SampleLimitEvent) for event in transcript.events):
        findings.append("sample_limit_event")

    uuids: list[str] = []
    for event in model_events:
        event_uuid = getattr(event, "uuid", None)
        if not isinstance(event_uuid, str) or not event_uuid.strip():
            findings.append("model_event_uuid_missing")
        else:
            uuids.append(event_uuid)
        if getattr(event, "retries", None) not in {None, 0}:
            findings.append("model_event_retry")
        if bool(getattr(event, "pending", False)):
            findings.append("model_event_pending")
        if getattr(event, "completed", None) is None:
            findings.append("model_event_incomplete")
        if not _text(getattr(event, "model", None)).strip():
            findings.append("event_model_missing")
        if _text(getattr(event, "error", None)).strip():
            findings.append("model_event_error")

        call = getattr(event, "call", None)
        if call is None and getattr(event, "cache", None) != "read":
            findings.append("model_call_missing")
        elif call is not None:
            if bool(getattr(call, "error", False)):
                findings.append("model_call_error")
            if getattr(call, "response", None) is None and not bool(getattr(call, "error", False)):
                findings.append("model_call_response_missing")

        output = getattr(event, "output", None)
        if output is None:
            findings.append("model_output_missing")
            continue
        if not _text(getattr(output, "model", None)).strip():
            findings.append("output_model_missing")
        if _text(getattr(output, "error", None)).strip():
            findings.append("model_output_error")
        findings.extend(_observable_route_findings(event))

        choices = getattr(output, "choices", None)
        if not isinstance(choices, list) or len(choices) != 1:
            findings.append("unexpected_choice_count")
        if not _text(getattr(output, "completion", None)).strip():
            findings.append("empty_model_output")
        try:
            stop_reason = output.stop_reason
        except (AttributeError, IndexError, TypeError):
            stop_reason = None
        if stop_reason in {"max_tokens", "model_length"}:
            findings.append("truncated_model_output")
        elif stop_reason == "content_filter":
            findings.append("provider_or_policy_block")
        elif stop_reason != "stop":
            findings.append("unexpected_stop_reason")

    if len(uuids) != len(set(uuids)):
        findings.append("duplicate_model_event_uuid")
    return findings, model_events


def _ape_role(role: str | None) -> str | None:
    if role in {None, "persuader"}:
        return "target"
    return role if role in APE_ROLES else None


def _ape_instrument_failure(event: ModelEvent, role: str) -> str | None:
    call = getattr(event, "call", None)
    output = getattr(event, "output", None)
    if (
        _text(getattr(event, "error", None)).strip()
        or bool(getattr(call, "error", False))
        or output is None
        or _text(getattr(output, "error", None)).strip()
    ):
        return f"{role}_model_error"
    try:
        stop_reason = output.stop_reason
    except (AttributeError, IndexError, TypeError):
        stop_reason = None
    if stop_reason == "content_filter":
        return f"{role}_provider_or_policy_block"
    if stop_reason in {"max_tokens", "model_length"}:
        return f"{role}_truncated"
    if not _text(getattr(output, "completion", None)).strip():
        return f"{role}_empty_response"
    return None


def _blocked_llm_diagnostic() -> Result:
    explanation = (
        "Blocked: target-only projection and a frozen judge configuration are unavailable; "
        "an all-message LLM diagnostic would not be auditable."
    )
    return Result(
        value={"value": "unclear", "explanation": explanation},
        explanation=explanation,
        metadata={
            "blocked": True,
            "reason": "target_projection_and_frozen_judge_unavailable",
            "diagnostic_only": True,
        },
    )


@loader(content=TranscriptContent())
def metadata_only_loader() -> Loader[Transcript]:
    """Load transcript identity/metadata without messages or events."""

    async def load(transcript: Transcript) -> AsyncIterator[Transcript]:
        yield transcript

    return load


@scanner(events="all", version=1)
def deterministic_model_event_qa() -> Scanner[Transcript]:
    """Flag persisted execution anomalies without judging response content."""

    async def scan(transcript: Transcript) -> Result:
        findings, model_events = _model_event_findings(transcript)
        return _finding_result(findings, model_event_count=len(model_events))

    return scan


@scanner(events="all", version=1)
def ape_role_contract_qa() -> Scanner[Transcript]:
    """Check the per-transcript APE four-role and cache contract.

    Equality of cached persuadee outputs across target-model logs is necessarily
    a run-level postflight check and is not claimed by this transcript scanner.
    """

    async def scan(transcript: Transcript) -> Result:
        findings: list[str] = []
        model_events = [event for event in transcript.events if isinstance(event, ModelEvent)]
        if transcript.task_set != "ape_turn1":
            findings.append("unexpected_task")

        role_events: dict[str, list[ModelEvent]] = {role: [] for role in APE_ROLES}
        for event in model_events:
            role = _ape_role(event.role)
            if role is None:
                findings.append("unexpected_model_role")
            else:
                role_events[role].append(event)
        role_counts = {role: len(role_events[role]) for role in APE_ROLES}
        if len(model_events) != 4:
            findings.append("unexpected_model_event_count")
        for role, count in role_counts.items():
            if count != 1:
                findings.append(f"unexpected_{role}_event_count")

        transcript_metadata = _mapping(transcript.metadata)
        task_args = (
            _mapping(transcript_metadata.get("task_args"))
            if transcript_metadata is not None
            else None
        )
        eval_metadata = (
            _mapping(transcript_metadata.get("eval_metadata"))
            if transcript_metadata is not None
            else None
        )
        task_paired = task_args.get("paired_interlocutor_cache") if task_args else None
        eval_paired = eval_metadata.get("paired_interlocutor_cache") if eval_metadata else None
        paired: bool | None = None
        if type(task_paired) is not bool or type(eval_paired) is not bool:
            findings.append("ape_cache_mode_missing")
        elif task_paired != eval_paired:
            findings.append("ape_cache_mode_disagreement")
        else:
            paired = task_paired

        schedule = eval_metadata.get("atb_schedule") if eval_metadata else None
        if paired is True and schedule != APE_PAIRED_SCHEDULE:
            findings.append("ape_paired_schedule_missing")
        elif paired is False and schedule == APE_PAIRED_SCHEDULE:
            findings.append("ape_unpaired_schedule_mismatch")

        if paired is not None:
            for role, events in role_events.items():
                for event in events:
                    cache = getattr(event, "cache", None)
                    if paired and role == "persuadee":
                        if cache not in {"read", "write"}:
                            findings.append("ape_persuadee_cache_mode_invalid")
                        elif cache == "read" and getattr(event, "call", None) is not None:
                            findings.append("ape_cache_read_has_provider_call")
                        elif cache == "write" and getattr(event, "call", None) is None:
                            findings.append("ape_cache_write_missing_provider_call")
                    elif cache is not None:
                        findings.append("ape_unexpected_role_cache")

        sample_metadata = (
            _mapping(transcript_metadata.get("sample_metadata"))
            if transcript_metadata is not None
            else None
        )
        instrument_failures = (
            _mapping(sample_metadata.get("instrument_failures"))
            if sample_metadata is not None
            else None
        )
        if instrument_failures is None or set(instrument_failures) != set(APE_ROLES):
            findings.append("ape_instrument_failure_metadata_invalid")
        elif all(len(role_events[role]) == 1 for role in APE_ROLES):
            for role in APE_ROLES:
                observed = _ape_instrument_failure(role_events[role][0], role)
                if instrument_failures.get(role) != observed:
                    findings.append("ape_instrument_failure_metadata_mismatch")

        return _finding_result(
            findings,
            model_event_count=len(model_events),
            role_counts=role_counts,
        )

    return scan


@scanner(messages=["assistant"], version=1)
def empty_assistant_message() -> Scanner[ChatMessage]:
    async def scan(message: ChatMessage) -> Result:
        empty = not message.text.strip()
        return Result(value=empty, explanation="Empty assistant message." if empty else None)

    return scan


@scanner(loader=metadata_only_loader(), version=2)
def refusal_diagnostic() -> Scanner[Transcript]:
    """Remain disabled until target projection and judge provenance are frozen."""

    async def scan(transcript: Transcript) -> Result:
        del transcript
        return _blocked_llm_diagnostic()

    return scan


@scanner(loader=metadata_only_loader(), version=2)
def eval_awareness_diagnostic() -> Scanner[Transcript]:
    """Remain disabled until target projection and judge provenance are frozen."""

    async def scan(transcript: Transcript) -> Result:
        del transcript
        return _blocked_llm_diagnostic()

    return scan
