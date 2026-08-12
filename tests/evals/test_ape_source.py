from __future__ import annotations

import json
from pathlib import Path

import pytest
from atb_eval.runner import verify_ape_dataset
from inspect_ai import Task
from inspect_ai.dataset import Sample
from inspect_evals.ape.prompts import USER_OR_ASSISTANT1
from inspect_evals.utils import create_stable_id


def _source(root: Path) -> tuple[Path, str, str]:
    text = "Should {user_or_assistant1} adopt the proposal?"
    path = root / "src/topics/diverse_topics.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "category": "BenignOpinion",
                "short_title": "fixture",
                "text": text,
                "subject": "fixture",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    rendered = text.replace("{user_or_assistant1}", USER_OR_ASSISTANT1)
    return root, create_stable_id(rendered, prefix="ape"), rendered


def test_native_ape_samples_must_match_the_pinned_source(tmp_path: Path) -> None:
    source, sample_id, rendered = _source(tmp_path)
    task = Task(
        dataset=[
            Sample(
                id=sample_id,
                input=rendered,
                metadata={
                    "category": "BenignOpinion",
                    "short_title": "fixture",
                    "subject": "fixture",
                },
            )
        ]
    )
    verify_ape_dataset(task, source, ["BenignOpinion"])

    task.dataset[0].id = "ape_wrong"
    with pytest.raises(ValueError, match="does not match"):
        verify_ape_dataset(task, source, ["BenignOpinion"])
