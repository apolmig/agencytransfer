from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/verify_scout_canary.py"
SPEC = importlib.util.spec_from_file_location("verify_scout_canary", SCRIPT)
assert SPEC and SPEC.loader
verify_scout = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_scout)


def _results(values: list[bool], *, summary_results: int | None = None) -> SimpleNamespace:
    frame = pd.DataFrame(
        {"transcript_id": [f"transcript-{index}" for index in range(len(values))], "value": values}
    )
    scanner_summary = SimpleNamespace(
        errors=0,
        scans=len(values),
        results=sum(values) if summary_results is None else summary_results,
    )
    return SimpleNamespace(
        complete=True,
        errors=[],
        summary=SimpleNamespace(
            complete=True,
            scanners={verify_scout.SCANNER_NAME: scanner_summary},
        ),
        scanners={verify_scout.SCANNER_NAME: frame},
    )


def test_diagnostic_scan_allows_reconciled_findings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(verify_scout, "scan_results_df", lambda unused: _results([False, True]))
    verify_scout.verify(Path("unused"), 2, require_negative=False)


def test_negative_canary_rejects_findings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(verify_scout, "scan_results_df", lambda unused: _results([False, True]))
    with pytest.raises(SystemExit, match="positive result"):
        verify_scout.verify(Path("unused"), 2, require_negative=True)


def test_scan_rejects_summary_row_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        verify_scout,
        "scan_results_df",
        lambda unused: _results([False, True], summary_results=0),
    )
    with pytest.raises(SystemExit, match="does not match row values"):
        verify_scout.verify(Path("unused"), 2, require_negative=False)
