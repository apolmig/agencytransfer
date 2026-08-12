"""Controlled DisElect adaptation for Inspect.

Prompts are loaded from an independently pinned upstream checkout at runtime.
They are never copied into this public repository.
"""

from __future__ import annotations

import csv
import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Any

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import GenerateConfig
from inspect_ai.solver import generate, system_message

from atb_eval.scorers import diselect_response_class, operational_actionability

HARMFUL_SUBSETS = ("voting", "mps")
ALL_SUBSETS = (*HARMFUL_SUBSETS, "baseline")


def _stable_digest(seed: str, value: str) -> str:
    return hashlib.sha256(f"{seed}:{value}".encode()).hexdigest()


def _read_prompt_rows(source_dir: Path, subset: str) -> list[dict[str, str]]:
    if subset not in ALL_SUBSETS:
        raise ValueError(f"unknown DisElect subset: {subset}")
    path = source_dir / "data" / "evals" / subset / "prompts.csv"
    if not path.is_file():
        raise ValueError(f"missing pinned DisElect prompt file: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    ids = [row.get("id", "") for row in rows]
    if not ids or any(not item_id for item_id in ids) or len(ids) != len(set(ids)):
        raise ValueError(f"{subset} prompts require non-empty unique ids")
    if any(not row.get("prompt") or not row.get("task") for row in rows):
        raise ValueError(f"{subset} prompts contain a missing prompt or task")
    return rows


def _harmful_selection(
    source_dir: Path, selection_seed: str, per_stratum: int
) -> list[tuple[str, dict[str, str]]]:
    selected: list[tuple[str, dict[str, str]]] = []
    for subset in HARMFUL_SUBSETS:
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in _read_prompt_rows(source_dir, subset):
            grouped[row["task"]].append(row)
        if len(grouped) != 4:
            raise ValueError(f"expected four task strata in {subset}; found {len(grouped)}")
        for task_name, rows in sorted(grouped.items()):
            ordered = sorted(
                rows,
                key=lambda row: _stable_digest(selection_seed, f"{subset}:{task_name}:{row['id']}"),
            )
            if len(ordered) < per_stratum:
                raise ValueError(f"stratum {subset}/{task_name} has too few prompts")
            selected.extend((subset, row) for row in ordered[:per_stratum])
    return selected


def _benign_selection(
    source_dir: Path, selection_seed: str, count: int
) -> list[tuple[str, dict[str, str]]]:
    rows = _read_prompt_rows(source_dir, "baseline")
    ordered = sorted(
        rows,
        key=lambda row: _stable_digest(selection_seed, f"baseline:{row['id']}"),
    )
    if len(ordered) < count:
        raise ValueError("baseline subset has too few prompts")
    return [("baseline", row) for row in ordered[:count]]


def load_diselect_pilot_samples(
    source_dir: Path,
    source_revision: str,
    selection_seed: str,
    harmful_per_stratum: int = 5,
    benign_count: int = 10,
) -> list[Sample]:
    rows = [
        *_harmful_selection(source_dir, selection_seed, harmful_per_stratum),
        *_benign_selection(source_dir, selection_seed, benign_count),
    ]
    samples: list[Sample] = []
    for subset, row in rows:
        subject = row.get("subject") or "not_applicable"
        family = _stable_digest("scenario-family-v0.1", f"{subset}:{row['task']}:{subject}")[:16]
        is_harmful = subset in HARMFUL_SUBSETS
        metadata: dict[str, Any] = {
            "source_item_id": row["id"],
            "source_revision_required": source_revision,
            "subset": "harmful" if is_harmful else "benign",
            "use_case": subset,
            "template_id": row["task"],
            "scenario_family_id": family,
            "applicable_axes": (
                ["diselect_response_class", "operational_actionability"]
                if is_harmful
                else ["diselect_response_class"]
            ),
            "release_tier": "controlled",
        }
        samples.append(
            Sample(
                id=f"diselect-{subset}-{row['id']}",
                input=row["prompt"],
                metadata=metadata,
            )
        )
    return samples


@task
def diselect_pilot(
    source_dir: str,
    source_revision: str,
    selection_seed: str,
    harmful_per_stratum: int = 5,
    benign_count: int = 10,
    include_actionability: bool = False,
    temperature: float = 0.0,
    max_tokens: int = 700,
) -> Task:
    scorers = [diselect_response_class()]
    if include_actionability:
        scorers.append(operational_actionability())
    return Task(
        dataset=load_diselect_pilot_samples(
            Path(source_dir),
            source_revision=source_revision,
            selection_seed=selection_seed,
            harmful_per_stratum=harmful_per_stratum,
            benign_count=benign_count,
        ),
        solver=[system_message("You are a helpful assistant."), generate()],
        scorer=scorers,
        config=GenerateConfig(temperature=temperature, max_tokens=max_tokens),
        version="0.1.0",
        metadata={
            "adaptation": "ATB Inspect adaptation of DisElect",
            "primary_outcome": "diselect_response_class",
            "cluster_key": "scenario_family_id",
            "explicit_non_claim": (
                "Does not measure persuasion, agency transfer, or electoral effect."
            ),
        },
    )
