"""Frozen public table and column contract for the Policy Atlas release."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "schemas" / "public-table-columns.json"
PUBLIC_TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    stem: tuple(columns)
    for stem, columns in json.loads(CONTRACT_PATH.read_text(encoding="utf-8")).items()
}
PUBLIC_TABLE_STEMS = frozenset(PUBLIC_TABLE_COLUMNS)


def validate_row_contract(stem: str, rows: list[dict[str, object]]) -> tuple[str, ...]:
    if stem not in PUBLIC_TABLE_COLUMNS:
        raise ValueError(f"Unknown public table: {stem}")
    expected = PUBLIC_TABLE_COLUMNS[stem]
    for index, row in enumerate(rows, start=1):
        if tuple(row) != expected:
            missing = sorted(set(expected) - set(row))
            extra = sorted(set(row) - set(expected))
            raise ValueError(
                f"{stem} row {index} violates public column contract: "
                f"missing={missing}, extra={extra}"
            )
    return expected


def validate_csv_contract(release_root: Path) -> None:
    actual: set[str] = set()
    for path in sorted((release_root / "data").rglob("*.csv")):
        stem = path.relative_to(release_root).with_suffix("").as_posix()
        actual.add(stem)
        with path.open(newline="", encoding="utf-8") as handle:
            header = tuple(next(csv.reader(handle)))
        if header != PUBLIC_TABLE_COLUMNS.get(stem):
            raise ValueError(f"{stem} CSV header violates public column contract")
    if actual != PUBLIC_TABLE_STEMS:
        raise ValueError(
            "Public CSV table inventory mismatch: "
            f"missing={sorted(PUBLIC_TABLE_STEMS - actual)}, "
            f"unexpected={sorted(actual - PUBLIC_TABLE_STEMS)}"
        )
