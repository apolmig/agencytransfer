from __future__ import annotations

import csv
from pathlib import Path

import pytest
from atb_eval.tasks.diselect import load_diselect_pilot_samples


def _write_prompts(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _fake_checkout(root: Path) -> Path:
    for subset in ("voting", "mps"):
        rows = [
            {
                "id": f"{subset}-{task}-{index}",
                "prompt": f"Benign synthetic fixture {subset} {task} {index}",
                "task": f"task-{task}",
                "subject": f"subject-{index % 2}",
            }
            for task in range(4)
            for index in range(7)
        ]
        _write_prompts(root / f"data/evals/{subset}/prompts.csv", rows)
    baseline = [
        {
            "id": f"baseline-{index}",
            "prompt": f"Benign baseline fixture {index}",
            "task": "baseline",
        }
        for index in range(15)
    ]
    _write_prompts(root / "data/evals/baseline/prompts.csv", baseline)
    return root


def test_selection_is_deterministic_stratified_and_unique(tmp_path: Path) -> None:
    checkout = _fake_checkout(tmp_path)
    first = load_diselect_pilot_samples(checkout, "test-revision", "frozen-seed")
    second = load_diselect_pilot_samples(checkout, "test-revision", "frozen-seed")
    assert [sample.id for sample in first] == [sample.id for sample in second]
    assert len(first) == 50
    assert len({sample.id for sample in first}) == 50
    assert {sample.metadata["source_revision_required"] for sample in first} == {"test-revision"}
    harmful = [sample for sample in first if sample.metadata["subset"] == "harmful"]
    benign = [sample for sample in first if sample.metadata["subset"] == "benign"]
    assert len(harmful) == 40
    assert len(benign) == 10
    strata = {(sample.metadata["use_case"], sample.metadata["template_id"]) for sample in harmful}
    assert len(strata) == 8
    for stratum in strata:
        assert (
            sum(
                (sample.metadata["use_case"], sample.metadata["template_id"]) == stratum
                for sample in harmful
            )
            == 5
        )
    assert all(
        "operational_actionability" in sample.metadata["applicable_axes"] for sample in harmful
    )
    assert all(
        "operational_actionability" not in sample.metadata["applicable_axes"] for sample in benign
    )


def test_duplicate_ids_are_rejected(tmp_path: Path) -> None:
    checkout = _fake_checkout(tmp_path)
    path = checkout / "data/evals/voting/prompts.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    rows[1]["id"] = rows[0]["id"]
    _write_prompts(path, rows)
    with pytest.raises(ValueError, match="unique ids"):
        load_diselect_pilot_samples(checkout, "test-revision", "seed")
