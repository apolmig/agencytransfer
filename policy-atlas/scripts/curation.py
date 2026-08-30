"""Apply transparent curation overlays without rewriting the Sheets snapshot."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "draft-v0.3"
CURATION = ROOT / "data" / "curation-v0.4"

CORRECTION_FILES = {
    "claims.csv": [("claim_corrections.csv", "claim_id")],
    "implementations.csv": [
        ("implementation_corrections.csv", "implementation_id"),
        ("legal_implementation_corrections.csv", "implementation_id"),
    ],
    "sources.csv": [("source_corrections.csv", "source_id")],
    "claim_sources.csv": [("claim_source_corrections.csv", "relation_id")],
    "implementation_claims.csv": [("implementation_claim_corrections.csv", "relation_id")],
    "legal_instruments.csv": [("legal_instrument_corrections.csv", "legal_id")],
}

ADDITION_FILES = {
    "sources.csv": "source_additions.csv",
    "claim_sources.csv": "claim_source_additions.csv",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def apply_corrections(
    rows: list[dict[str, str]], corrections: list[dict[str, str]], key: str
) -> list[dict[str, str]]:
    index = {row[key]: dict(row) for row in rows}
    if len(index) != len(rows):
        raise ValueError(f"Cannot curate table with duplicate {key}")
    correction_ids = [row[key] for row in corrections]
    if len(correction_ids) != len(set(correction_ids)):
        raise ValueError(f"Correction file contains duplicate {key}")
    for correction in corrections:
        identifier = correction[key]
        if identifier not in index:
            raise ValueError(f"Correction targets missing {key}: {identifier}")
        for field, value in correction.items():
            if field != key and value:
                if field not in index[identifier]:
                    raise ValueError(f"Correction targets unknown field {field!r}")
                index[identifier][field] = value
    return [index[row[key]] for row in rows]


def load_table(name: str) -> list[dict[str, str]]:
    rows = read_csv(BASE / name)
    if name in CORRECTION_FILES:
        for correction_name, key in CORRECTION_FILES[name]:
            corrections = read_csv(CURATION / correction_name)
            rows = apply_corrections(rows, corrections, key)
    if name in ADDITION_FILES:
        additions = read_csv(CURATION / ADDITION_FILES[name])
        key = CORRECTION_FILES[name][0][1]
        existing_ids = {row[key] for row in rows}
        addition_ids = [row[key] for row in additions]
        if len(addition_ids) != len(set(addition_ids)) or existing_ids.intersection(addition_ids):
            raise ValueError(f"Addition file contains duplicate {key}")
        rows.extend(additions)
    return rows
