"""Validate and render the coherent-log APE-120 public candidate v0.2."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ingest_ape120_public_candidate as base  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_dir.resolve()
    output = args.output_dir.resolve()

    actual = {path.name for path in source.iterdir() if path.is_file()}
    if actual != base.ALLOWED_SOURCE_FILES:
        raise ValueError(f"source file allowlist mismatch: {sorted(actual)}")

    bridge = base.load_json(source / "BRIDGE-MANIFEST.json")
    files = bridge.get("files")
    if not isinstance(files, dict):
        raise ValueError("bridge manifest lacks file hashes")
    expected = base.ALLOWED_SOURCE_FILES - {"BRIDGE-MANIFEST.json"}
    if set(files) != expected:
        raise ValueError("bridge manifest file allowlist mismatch")
    for name, digest in files.items():
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError(f"invalid digest for {name}")
        if base.sha256(source / name) != digest:
            raise ValueError(f"bridge digest mismatch for {name}")

    payload = base.load_json(source / "ape120-primary-public-candidate.json")
    if payload.get("schema_version") != "atb-ape120-primary-public-candidate-v0.2":
        raise ValueError("unexpected coherent-log candidate schema")
    if payload.get("partial_logs_stitched") is not False:
        raise ValueError("candidate must explicitly forbid partial-log stitching")
    base.validate_public_structure(payload)

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
    for name in sorted(base.ALLOWED_SOURCE_FILES):
        shutil.copy2(source / name, output / name)
    rendered = base.render_results(payload)
    rendered = rendered.replace(
        "This is direct primary research.",
        "Each checkpoint result is selected from one coherent private log; partial runs are never stitched. Provider cost accounting includes all attempts. This is direct primary research.",
        1,
    )
    (output / "RESULTS.md").write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
