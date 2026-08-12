from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import atb_eval.execution_receipt as receipt
import pytest


def _log(model: str, event_id: str, tokens: int, cost: float, billed: float, failure: str | None):
    score = SimpleNamespace(metadata={"instrument_failure": failure} if failure else {})
    return SimpleNamespace(
        eval=SimpleNamespace(model=model),
        status="success",
        samples=[SimpleNamespace(scores={"primary": score})],
        stats=SimpleNamespace(),
        event_id=event_id,
        tokens=tokens,
        cost=cost,
        billed=billed,
    )


def test_controlled_usage_summary_reconciles_events_and_preserves_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = tmp_path / "a.eval"
    second = tmp_path / "b.eval"
    first.touch()
    second.touch()
    logs = {
        first: _log("openrouter/model-a", "a", 10, 0.001, 0.001, None),
        second: _log("openrouter/model-b", "b", 20, 0.002, 0.002, "truncated"),
    }
    monkeypatch.setattr(receipt, "read_eval_log", lambda path: logs[path])
    monkeypatch.setattr(
        receipt, "recorded_log_usage", lambda log, require_cost: (log.tokens, log.cost)
    )
    monkeypatch.setattr(
        receipt,
        "recorded_event_usage",
        lambda log, require_cost: {log.event_id: (log.tokens, log.cost, log.event_id)},
    )
    monkeypatch.setattr(
        receipt,
        "recorded_openrouter_billed_costs",
        lambda log: {log.event_id: (log.billed, log.event_id)},
    )

    summary = receipt.controlled_usage_summary(tmp_path)
    assert summary["eval_log_count"] == 2
    assert summary["inspect_tokens"] == 30
    assert summary["inspect_estimated_cost_usd"] == pytest.approx(0.003)
    assert summary["openrouter_billed_cost_usd"] == pytest.approx(0.003)
    assert summary["conditions"][1]["instrument_failures"] == ["truncated"]
    assert summary["conditions"][0]["target_model"] == "openrouter/model-a"
    assert summary["conditions"][0]["all_roles_inspect_tokens"] == 10


def test_controlled_usage_summary_requires_evidence(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no Inspect eval evidence"):
        receipt.controlled_usage_summary(tmp_path)


def test_controlled_usage_summary_rejects_aggregate_event_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "a.eval"
    path.touch()
    log = _log("openrouter/model-a", "a", 10, 0.001, 0.001, None)
    monkeypatch.setattr(receipt, "read_eval_log", lambda unused: log)
    monkeypatch.setattr(receipt, "recorded_log_usage", lambda item, require_cost: (10, 0.001))
    monkeypatch.setattr(
        receipt,
        "recorded_event_usage",
        lambda item, require_cost: {"a": (9, 0.001, "digest")},
    )
    monkeypatch.setattr(
        receipt,
        "recorded_openrouter_billed_costs",
        lambda item: {"a": (0.001, "digest")},
    )
    with pytest.raises(ValueError, match="aggregate usage"):
        receipt.controlled_usage_summary(tmp_path)


def test_controlled_usage_summary_requires_matching_billed_events(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "a.eval"
    path.touch()
    log = _log("openrouter/model-a", "a", 10, 0.001, 0.001, None)
    monkeypatch.setattr(receipt, "read_eval_log", lambda unused: log)
    monkeypatch.setattr(receipt, "recorded_log_usage", lambda item, require_cost: (10, 0.001))
    monkeypatch.setattr(
        receipt,
        "recorded_event_usage",
        lambda item, require_cost: {"a": (10, 0.001, "digest")},
    )
    monkeypatch.setattr(receipt, "recorded_openrouter_billed_costs", lambda item: {})
    with pytest.raises(ValueError, match="aggregate usage"):
        receipt.controlled_usage_summary(tmp_path)


def test_receipt_cli_fails_without_rendering_parser_exception(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        receipt,
        "controlled_usage_summary",
        lambda root: (_ for _ in ()).throw(ValueError("sk-or-v1-secret-in-exception")),
    )
    monkeypatch.setattr(
        "sys.argv", ["execution_receipt", str(tmp_path), str(tmp_path / "receipt.json")]
    )
    with pytest.raises(SystemExit, match="could not be derived safely"):
        receipt.main()
    assert "secret-in-exception" not in capsys.readouterr().err
