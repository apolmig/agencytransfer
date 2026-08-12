import asyncio

from atb_eval.scanners import (
    empty_assistant_message,
    eval_awareness_diagnostic,
    refusal_diagnostic,
)
from inspect_ai.model import ChatMessageAssistant


def test_scout_scanners_construct_with_pinned_api() -> None:
    assert empty_assistant_message() is not None
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
