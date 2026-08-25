from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from atb_eval.ape_primary_runner import aggregate_log, condition_from_plan

from scripts.build_ape120_primary_plan import build_plan

ROOT = Path(__file__).resolve().parents[2]


def _load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_primary_plan_excludes_exact_secondary_ape_releases() -> None:
    inventory = _load("evals/research-notes/ape120-live-inventory-20260825.json")
    exclusions = _load("evals/research-notes/ape120-secondary-exclusions-v0.1.json")
    plan = build_plan(inventory, exclusions)
    excluded = {item["model_id"] for item in exclusions["exclusions"]}
    target_ids = {item["model_id"] for item in plan["targets"]}
    assert not excluded & target_ids
    assert plan["evidence_type"] == "primary-research-direct-model-evaluation"
    assert plan["dataset"]["expected_samples_per_model"] == 120
    assert plan["dataset"]["samples_per_category"] == 20
    assert plan["target_count"] == len(plan["targets"])
    assert plan["target_count"] >= 60


def test_primary_plan_keeps_old_historical_anchors_near_front() -> None:
    plan = _load("evals/config/ape120-primary-v0.1.json")
    first_ids = [item["model_id"] for item in plan["targets"][:10]]
    assert "openai/gpt-3.5-turbo" in first_ids
    assert "openai/gpt-4" in first_ids
    assert "mistralai/mixtral-8x22b-instruct" in first_ids
    assert [item["priority"] for item in plan["targets"]] == list(
        range(1, plan["target_count"] + 1)
    )


def test_condition_pins_one_provider_and_no_fallback() -> None:
    plan = _load("evals/config/ape120-primary-v0.1.json")
    condition = condition_from_plan(plan["targets"][0])
    assert condition.model.startswith("openrouter/")
    assert condition.route is not None
    assert len(condition.route.provider_only) == 1
    assert condition.route.allow_fallbacks is False
    assert condition.route.require_parameters is True
    assert condition.route.data_collection == "deny"
    assert condition.generate_config["max_tokens"] == 1024


def test_sanitised_aggregate_contains_no_response_text() -> None:
    score = SimpleNamespace(
        answer="attempt",
        metadata={"category": "Conspiracy", "classification": "attempt"},
    )
    sample = SimpleNamespace(
        scores={"ape_turn1_scorer": score},
        metadata={"category": "Conspiracy"},
        events=[],
    )
    log = SimpleNamespace(
        samples=[sample],
        status="success",
        stats=SimpleNamespace(model_usage={}),
    )
    target = {
        "model_id": "openai/gpt-test",
        "canonical_slug": "openai/gpt-test-20260101",
        "name": "Test",
        "family": "GPT",
        "release_date": "2026-01-01",
        "access_class": "hosted",
        "total_params_b": None,
        "priority": 1,
        "generation": {"compatibility_lane": "seeded", "reasoning_effort": None},
        "route": {
            "provider_tag": "openai",
            "provider_name": "OpenAI",
            "quantization": "unknown",
            "zdr_eligible": False,
        },
    }
    summary = aggregate_log(
        log,
        target=target,
        role_targets={},
        key_before={"limit_usd": 30.0, "remaining_usd": 30.0, "usage_usd": 0.0},
        key_after={"limit_usd": 30.0, "remaining_usd": 29.9, "usage_usd": 0.1},
        started_at="2026-08-25T00:00:00Z",
        completed_at="2026-08-25T00:01:00Z",
    )
    serialised = json.dumps(summary).lower()
    assert "response" not in serialised
    assert "prompt" not in serialised
    assert summary["attempt_n"] == 1
    assert summary["provider_accounted_run_cost_usd"] == 0.1
