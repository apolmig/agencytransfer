#!/usr/bin/env python3
"""Fail closed unless a Scout canary scan has the exact expected result shape."""

import argparse
from pathlib import Path

from inspect_scout import scan_results_df

SCANNER_NAME = "empty_assistant_message"
EXPECTED_ROWS = 6


def fail(message: str) -> None:
    raise SystemExit(f"Scout canary verification failed: {message}")


def resolve_scan_dir(scans_path: Path) -> Path:
    if not scans_path.is_dir():
        fail(f"scan location is not a directory: {scans_path}")

    if scans_path.name.startswith("scan_id="):
        return scans_path

    candidates = sorted(
        path for path in scans_path.iterdir() if path.is_dir() and path.name.startswith("scan_id=")
    )
    if len(candidates) != 1:
        fail(f"expected exactly one scan_id directory, found {len(candidates)}")
    return candidates[0]


def verify(scan_dir: Path) -> None:
    results = scan_results_df(str(scan_dir))

    if not results.complete or not results.summary.complete:
        fail("scan is incomplete")
    if results.errors:
        fail(f"scan recorded {len(results.errors)} top-level error(s)")

    scanner_names = set(results.scanners)
    if scanner_names != {SCANNER_NAME}:
        fail(f"unexpected scanner set: {sorted(scanner_names)}")

    summary = results.summary.scanners.get(SCANNER_NAME)
    if summary is None:
        fail("scanner summary is missing")
    if summary.errors != 0:
        fail(f"scanner recorded {summary.errors} error(s)")
    if summary.scans != EXPECTED_ROWS:
        fail(f"scanner summary contains {summary.scans} scans, expected {EXPECTED_ROWS}")
    if summary.results != 0:
        fail(f"scanner summary contains {summary.results} positive result(s)")

    frame = results.scanners[SCANNER_NAME]
    if len(frame.index) != EXPECTED_ROWS:
        fail(f"scanner output contains {len(frame.index)} rows, expected {EXPECTED_ROWS}")

    required_columns = {"transcript_id", "value"}
    missing_columns = required_columns.difference(frame.columns)
    if missing_columns:
        fail(f"scanner output is missing columns: {sorted(missing_columns)}")
    if frame["transcript_id"].isna().any():
        fail("scanner output contains a missing transcript id")
    if frame["transcript_id"].nunique() != EXPECTED_ROWS:
        fail("scanner output does not contain six distinct transcripts")

    values = frame["value"]
    if values.isna().any():
        fail("scanner output contains a missing value")
    boolean_values = values.tolist()
    if any(type(value) is not bool for value in boolean_values):
        fail(f"scanner values are not boolean: {values.dtype}")
    if any(boolean_values):
        fail("empty-message scanner returned a positive result")

    print(f"Scout canary verified: {EXPECTED_ROWS} complete negative results.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "scans_path",
        type=Path,
        help="Scout scans root or the single scan_id directory to verify.",
    )
    args = parser.parse_args()
    verify(resolve_scan_dir(args.scans_path))


if __name__ == "__main__":
    main()
