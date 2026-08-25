from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType, SimpleNamespace

from atb_eval.ape_primary_runner import aggregate_log, condition_from_plan

ROOT = Path(__file__).resolve().parents[2]


def _load_script(path: str, module_name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, ROOT / path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load test dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_plan = _load_script(
    "scripts/build_ape120_primary_plan.py", "build_ape120_primary_plan"
).build_plan


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
    assert plan["execution"]["max_samples"] == 120
    assert plan["execution"]["planned_execution_envelope_usd"] == 29.25
    assert plan["execution"]["minimum_stop_reserve_usd"] == 0.75
    assert plan["execution"]["max_retries"] == 0
    assert plan["execution"]["retry_attempts"] == 0
    assert plan["protocol_id"] == "atb-ape120-primary-20260825-v0.2"
    assert plan["target_count"] == len(plan["targets"])
    assert plan["target_count"] >= 50


def test_primary_plan_prioritises_old_family_coverage() -> None:
    plan = _load("evals/config/ape120-primary-v0.2.json")
    first_ids = [item["model_id"] for item in plan["targets"][:30]]
    assert "openai/gpt-3.5-turbo" in first_ids
    assert "openai/gpt-4" in first_ids
    assert "mistralai/mixtral-8x22b-instruct" in first_ids
    assert "deepseek/deepseek-chat" in first_ids
    assert [item["priority"] for item in plan["targets"]] == list(
        range(1, plan["target_count"] + 1)
    )


def test_secondary_ape_cohorts_are_not_retested() -> None:
    plan = _load("evals/config/ape120-primary-v0.2.json")
    target_ids = {item["model_id"] for item in plan["targets"]}
    excluded = {
        "openai/gpt-4.1",
        "openai/o3",
        "openai/gpt-4o-2024-05-13",
        "openai/gpt-4o-2024-08-06",
        "openai/gpt-4o-2024-11-20",
        "anthropic/claude-sonnet-4",
        "anthropic/claude-opus-4",
        "google/gemini-2.5-pro-preview-05-06",
        "google/gemini-2.5-pro",
        "openai/gpt-5.1",
        "anthropic/claude-opus-4.5",
        "openai/gpt-5.5",
        "anthropic/claude-opus-4.7",
        "z-ai/glm-5.2",
    }
    assert not excluded & target_ids
    assert excluded.issubset(set(plan["secondary_exclusion_ledger"]["excluded_model_ids"]))


def test_condition_pins_one_provider_and_no_fallback() -> None:
    plan = _load("evals/config/ape120-primary-v0.2.json")
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
