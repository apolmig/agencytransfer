#!/usr/bin/env python3
"""Recompute the DisElect aggregate used by the public Wave 0 chart.

The script reads the published result CSVs from a pinned checkout of
alan-turing-institute/election-ai-safety. It never reads or republishes model
responses; the upstream release contains judgements only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from collections.abc import Mapping
from pathlib import Path

SOURCE_URL = "https://github.com/alan-turing-institute/election-ai-safety"
SOURCE_COMMIT = "915a8f8c22fb9cd8a2e4ae6824513760f0468f69"
JUDGE_MODEL = "GPT-3.5 Turbo (zero-shot; upstream protocol)"

SOURCE_INPUT_SHA256 = {
    "data/models.csv": "5497250888e8ecf94d01e1bbef12af293ab74b2d6935aa497578fb427e6e643c",
    "data/evals/voting/results.csv": (
        "0fe4dda02c58f4953dd33f028f9638118d963e4de03f432457f796c563b957fb"
    ),
    "data/evals/mps/results.csv": (
        "c511505a46b6570ebedbeb8de4350c48a57171dd643e70f7548f429f2993f3fa"
    ),
    "data/evals/baseline/results.csv": (
        "d9853091878f3a37d68d14a8544560c3567759cf0e9290a1241a5054cb2b6706"
    ),
}

MODEL_META = {
    "GPT-2": ("GPT", "OpenAI", "open-weight"),
    "T5": ("T5", "Google", "open-weight"),
    "GPT-Neo": ("GPT-Neo", "EleutherAI", "open-weight"),
    "Flan-T5": ("T5", "Google", "open-weight"),
    "GPT-3": ("GPT", "OpenAI", "hosted"),
    "GPT-3.5 Turbo": ("GPT", "OpenAI", "hosted"),
    "GPT-4": ("GPT", "OpenAI", "hosted"),
    "Llama 2": ("Llama", "Meta", "open-weight"),
    "Mistral": ("Mistral", "Mistral AI", "open-weight"),
    "Gemini 1.0 Pro": ("Gemini", "Google", "hosted"),
    "Phi-2": ("Phi", "Microsoft", "open-weight"),
    "Gemma": ("Gemma", "Google", "open-weight"),
    "Llama 3": ("Llama", "Meta", "open-weight"),
}

MODEL_ALIAS = {"GPT-3": "GPT-3.5 (t-d-003)"}

SUBSETS = {
    "voter-targeting": ("evals/voting/results.csv",),
    "mp-targeting": ("evals/mps/results.csv",),
    "all-harmful": ("evals/voting/results.csv", "evals/mps/results.csv"),
    "benign": ("evals/baseline/results.csv",),
}

LABELS = ("comply", "softrefuse", "refuse", "incoherent")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-dir",
        type=Path,
        required=True,
        help="Path to the pinned election-ai-safety repository checkout",
    )
    parser.add_argument("--repo-dir", type=Path, default=Path.cwd())
    return parser.parse_args()


def run_git(source_dir: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(source_dir), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise SystemExit("Cannot verify upstream checkout: git is not installed") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or "git command failed"
        raise SystemExit(f"Cannot verify upstream checkout {source_dir}: {detail}") from exc
    return result.stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_source_checkout(
    source_dir: Path,
    *,
    expected_commit: str = SOURCE_COMMIT,
    expected_input_sha256: Mapping[str, str] = SOURCE_INPUT_SHA256,
) -> Path:
    """Fail closed unless source_dir is the exact clean, pinned upstream tree."""
    source_dir = source_dir.resolve()
    if not source_dir.is_dir():
        raise SystemExit(f"Upstream checkout is not a directory: {source_dir}")

    checkout_root = Path(run_git(source_dir, "rev-parse", "--show-toplevel")).resolve()
    if checkout_root != source_dir:
        raise SystemExit(
            f"Upstream path must be the checkout root: {source_dir} (root is {checkout_root})"
        )

    actual_commit = run_git(source_dir, "rev-parse", "--verify", "HEAD^{commit}")
    if actual_commit != expected_commit:
        raise SystemExit(
            f"Upstream checkout is at {actual_commit}; expected pinned commit {expected_commit}"
        )

    status = run_git(
        source_dir,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--ignore-submodules=none",
    )
    if status:
        raise SystemExit(f"Upstream checkout is dirty; refusing to generate:\n{status}")

    for relative_path, expected_hash in expected_input_sha256.items():
        input_path = source_dir / relative_path
        if not input_path.is_file():
            raise SystemExit(f"Required upstream input is missing: {relative_path}")
        actual_hash = sha256_file(input_path)
        if actual_hash != expected_hash:
            raise SystemExit(
                f"Upstream input hash mismatch for {relative_path}: "
                f"got {actual_hash}, expected {expected_hash}"
            )

    return source_dir


def load_model_rows(data_dir: Path) -> dict[str, dict[str, str]]:
    with (data_dir / "models.csv").open(newline="", encoding="utf-8") as handle:
        return {row["model"]: row for row in csv.DictReader(handle)}


def aggregate(paths: list[Path]) -> dict[str, Counter[str]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for path in paths:
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                counts[row["model"]][row["judgement"]] += 1
    return counts


def normalise_number(raw: str) -> float | None:
    return float(raw) if raw else None


def build_rows(data_dir: Path) -> list[dict[str, object]]:
    models = load_model_rows(data_dir)
    rows: list[dict[str, object]] = []
    for subset, relative_paths in SUBSETS.items():
        counts = aggregate([data_dir / path for path in relative_paths])
        for model, model_counts in counts.items():
            model_key = MODEL_ALIAS.get(model, model)
            source_model = models[model_key]
            family, organisation, access_type = MODEL_META[model]
            total = sum(model_counts.values())
            values = {label: model_counts.get(label, 0) for label in LABELS}
            rows.append(
                {
                    "benchmarkId": "diselect",
                    "model": model,
                    "canonicalModelId": source_model["model_id"],
                    "family": family,
                    "organisation": organisation,
                    "accessType": access_type,
                    "releaseDate": source_model["release_date"],
                    "releaseDateBasis": "original model announcement date (upstream paper)",
                    "evaluationDate": "",
                    "totalParamsB": normalise_number(source_model["params"]),
                    "quantisationBits": normalise_number(source_model["quantisation"]),
                    "subset": subset,
                    "n": total,
                    "complyCount": values["comply"],
                    "softRefuseCount": values["softrefuse"],
                    "refuseCount": values["refuse"],
                    "incoherentCount": values["incoherent"],
                    "complyPct": round(values["comply"] / total * 100, 3),
                    "softRefusePct": round(values["softrefuse"] / total * 100, 3),
                    "refusePct": round(values["refuse"] / total * 100, 3),
                    "incoherentPct": round(values["incoherent"] / total * 100, 3),
                    "sourceType": "recomputed from published aggregate labels",
                    "sourceUrl": SOURCE_URL,
                    "sourceCommit": SOURCE_COMMIT,
                    "judgeModel": JUDGE_MODEL,
                }
            )
    return sorted(rows, key=lambda row: (str(row["releaseDate"]), str(row["subset"])))


def write_outputs(rows: list[dict[str, object]], repo_dir: Path) -> None:
    json_path = repo_dir / "public/data/diselect-results.json"
    csv_path = repo_dir / "data/published/diselect-summary.csv"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    source_dir = verify_source_checkout(args.source_dir)
    data_dir = source_dir / "data"
    write_outputs(build_rows(data_dir), args.repo_dir)


if __name__ == "__main__":
    main()
