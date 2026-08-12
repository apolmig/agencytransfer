from atb_eval.scanners import (
    empty_assistant_message,
    eval_awareness_diagnostic,
    refusal_diagnostic,
)


def test_scout_scanners_construct_with_pinned_api() -> None:
    assert empty_assistant_message() is not None
    assert refusal_diagnostic() is not None
    assert eval_awareness_diagnostic() is not None
