"""Validate and render the public APE-120 primary-research candidate packet."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

ALLOWED_SOURCE_FILES = {
    "ape120-primary-public-candidate.json",
    "checkpoint-results.csv",
    "primary-secondary-ledger.csv",
    "README.md",
    "BRIDGE-MANIFEST.json",
}
FORBIDDEN_KEY_FRAGMENTS = (
    "prompt",
    "completion",
    "message",
    "input",
    "output",
    "trace",
    "event",
    "request",
    "response",
    "content",
    "api_key",
    "secret",
    "raw_log",
)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_public_structure(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in FORBIDDEN_KEY_FRAGMENTS):
                raise ValueError(f"forbidden public field at {path}.{key}")
            validate_public_structure(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            validate_public_structure(item, f"{path}[{index}]")
    elif isinstance(value, str) and len(value) > 2_000:
        raise ValueError(f"unexpectedly long public string at {path}")


def percent(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "—"
    if not math.isfinite(float(value)):
        return "—"
    return f"{100 * float(value):.1f}%"


def money(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "—"
    if not math.isfinite(float(value)):
        return "—"
    return f"${float(value):.4f}"


def delta(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "—"
    if not math.isfinite(float(value)):
        return "—"
    return f"{100 * float(value):+.1f} pp"


def ci(value: Any) -> str:
    if not isinstance(value, list) or len(value) != 2:
        return "—"
    if not all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value):
        return "—"
    return f"[{100 * float(value[0]):+.1f}, {100 * float(value[1]):+.1f}] pp"


def cell(value: Any) -> str:
    text = "—" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def render_results(payload: dict[str, Any]) -> str:
    models = payload.get("model_results") or []
    pairwise = payload.get("pairwise_adjacent_release_comparisons") or []
    ledger = payload.get("primary_secondary_ledger") or []
    if not isinstance(models, list) or not isinstance(pairwise, list) or not isinstance(ledger, list):
        raise ValueError("candidate packet contains malformed result arrays")

    decisions = Counter(
        str(row.get("decision") or "unknown") for row in ledger if isinstance(row, dict)
    )
    exact_secondary = sum(
        isinstance(row, dict)
        and row.get("decision_reason") == "exact_checkpoint_has_secondary_ape_result"
        for row in ledger
    )
    complete_models = sum(
        isinstance(row, dict)
        and row.get("observed_topic_n") == 120
        and (row.get("rates") or {}).get("unscored") == 0
        for row in models
    )

    lines = [
        "# APE-120 longitudinal primary wave",
        "",
        "## Result status",
        "",
        f"- Controlled source run: `{cell(payload.get('source_run_id'))}`",
        f"- Source conclusion: **{cell(payload.get('source_conclusion'))}**",
        f"- Directly observed checkpoints: **{len(models)}**",
        f"- Checkpoints with 120/120 scored observations: **{complete_models}**",
        f"- Provider-reported spend delta: **{money(payload.get('provider_reported_spend_delta_usd'))}**",
        f"- Frozen helper model: `{cell(payload.get('helper_model_id'))}`",
        f"- Exact-checkpoint secondary APE exclusions: **{exact_secondary}**",
        "",
        "This is direct primary research. It measures APE turn-1 response-class behaviour under a fixed simulated interaction. It does not measure realised belief change or democratic effects.",
        "",
        "## Checkpoint results",
        "",
        "| Release | Checkpoint | Family | n | Attempt | Refusal | Non-persuasive | Unscored | Billed cost |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in sorted(
        (item for item in models if isinstance(item, dict)),
        key=lambda item: (str(item.get("release_date") or "9999-99-99"), str(item.get("model_id") or "")),
    ):
        rates = row.get("rates") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    cell(row.get("release_date")),
                    f"`{cell(row.get('model_id'))}`",
                    cell(row.get("family")),
                    cell(row.get("observed_topic_n")),
                    percent(rates.get("attempt")),
                    percent(rates.get("refusal")),
                    percent(rates.get("non_persuasive")),
                    percent(rates.get("unscored")),
                    money(row.get("provider_billed_cost_usd")),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Adjacent-release comparisons",
            "",
            "Differences are right checkpoint minus left checkpoint, using shared complete topics. Confidence intervals are deterministic topic-level bootstrap intervals.",
            "",
            "| Family | Transition | Complete n | Attempt Δ [95% CI] | Refusal Δ [95% CI] | Non-persuasive Δ [95% CI] |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for comparison in pairwise:
        if not isinstance(comparison, dict):
            continue
        differences = comparison.get("differences") or {}
        rendered: list[str] = []
        for outcome in ("attempt", "refusal", "non_persuasive"):
            item = differences.get(outcome) or {}
            rendered.append(
                f"{delta(item.get('delta'))} {ci(item.get('bootstrap_95_ci'))}"
            )
        lines.append(
            "| "
            + " | ".join(
                [
                    cell(comparison.get("family")),
                    f"`{cell(comparison.get('left_model_id'))}` → `{cell(comparison.get('right_model_id'))}`",
                    cell(comparison.get("complete_case_n")),
                    *rendered,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Inclusion and missingness audit",
            "",
            f"The machine-readable ledger contains {len(ledger)} model decisions: "
            + ", ".join(f"{key}={value}" for key, value in sorted(decisions.items()))
            + ".",
            "",
            "A family is not excluded because one release has secondary evidence. Only the same checkpoint or provider-bound revision is excluded. Missing model routes and unscored observations remain explicit; they are not converted into refusal or non-persuasion.",
            "",
            "## Claim ceiling",
            "",
            str(payload.get("claim_ceiling") or "No claim ceiling was supplied."),
            "",
            "Within the Capability–Deployment–Effect framework, these observations inform the capability layer. They do not establish deployment at scale, aggregate agency transfer, concentrated control, electoral consequences, or democratic harm.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_dir.resolve()
    output = args.output_dir.resolve()

    actual = {path.name for path in source.iterdir() if path.is_file()}
    if actual != ALLOWED_SOURCE_FILES:
        raise ValueError(f"source file allowlist mismatch: {sorted(actual)}")

    bridge = load_json(source / "BRIDGE-MANIFEST.json")
    files = bridge.get("files")
    if not isinstance(files, dict):
        raise ValueError("bridge manifest lacks file hashes")
    expected_hashed_files = ALLOWED_SOURCE_FILES - {"BRIDGE-MANIFEST.json"}
    if set(files) != expected_hashed_files:
        raise ValueError("bridge manifest file allowlist mismatch")
    for name, expected in files.items():
        if not isinstance(expected, str) or len(expected) != 64:
            raise ValueError(f"invalid digest for {name}")
        if sha256(source / name) != expected:
            raise ValueError(f"bridge digest mismatch for {name}")

    payload = load_json(source / "ape120-primary-public-candidate.json")
    if payload.get("schema_version") != "atb-ape120-primary-public-candidate-v0.1":
        raise ValueError("unexpected candidate schema")
    validate_public_structure(payload)

    with (source / "checkpoint-results.csv").open(encoding="utf-8", newline="") as handle:
        checkpoint_rows = list(csv.DictReader(handle))
    with (source / "primary-secondary-ledger.csv").open(encoding="utf-8", newline="") as handle:
        ledger_rows = list(csv.DictReader(handle))
    if len(checkpoint_rows) != len(payload.get("model_results") or []):
        raise ValueError("checkpoint CSV and JSON row counts differ")
    if len(ledger_rows) != len(payload.get("primary_secondary_ledger") or []):
        raise ValueError("ledger CSV and JSON row counts differ")

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for name in sorted(ALLOWED_SOURCE_FILES):
        shutil.copy2(source / name, output / name)
    (output / "RESULTS.md").write_text(render_results(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
