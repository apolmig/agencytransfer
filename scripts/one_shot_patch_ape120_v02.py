"""One-shot repository patch for corrected APE-120 protocol v0.2."""

from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    builder_path = Path("scripts/build_ape120_primary_plan.py")
    builder = builder_path.read_text(encoding="utf-8")
    replacements = (
        (
            'OUTPUT_PATH = Path("evals/config/ape120-primary-v0.1.json")',
            'OUTPUT_PATH = Path("evals/config/ape120-primary-v0.2.json")',
            "builder output path",
        ),
        (
            '"protocol_id": "atb-ape120-primary-20260825-v0.1",',
            '"protocol_id": "atb-ape120-primary-20260825-v0.2",',
            "protocol id",
        ),
        (
            '"planned_execution_envelope_usd": 29.5,',
            '"planned_execution_envelope_usd": 29.25,',
            "execution envelope",
        ),
        (
            '"minimum_stop_reserve_usd": 0.25,',
            '"minimum_stop_reserve_usd": 0.75,',
            "stop reserve",
        ),
        (
            '"maximum_model_forecast_multiplier": 1.35,',
            '"maximum_model_forecast_multiplier": 1.75,',
            "forecast multiplier",
        ),
        ('"max_samples": 4,', '"max_samples": 120,', "sample count"),
        ('"max_connections": 4,', '"max_connections": 3,', "connection count"),
    )
    for old, new, label in replacements:
        builder = replace_once(builder, old, new, label)
    builder_path.write_text(builder, encoding="utf-8")

    runner_path = Path("evals/atb_eval/ape_primary_runner.py")
    runner = runner_path.read_text(encoding="utf-8")
    anchor = (
        '    if plan.get("evidence_type") != '
        '"primary-research-direct-model-evaluation":\n'
        '        raise ValueError("APE primary plan has the wrong evidence type")\n'
    )
    hardening = anchor + (
        '    if plan.get("protocol_id") != "atb-ape120-primary-20260825-v0.2":\n'
        '        raise ValueError("APE primary runner accepts only the corrected v0.2 protocol")\n'
        '    dataset = plan.get("dataset")\n'
        '    execution = plan.get("execution")\n'
        '    if not isinstance(dataset, dict) or not isinstance(execution, dict):\n'
        '        raise ValueError("APE primary plan lacks dataset or execution configuration")\n'
        '    expected_categories = [\n'
        '        "Conspiracy",\n'
        '        "BenignOpinion",\n'
        '        "BenignFactual",\n'
        '        "Controversial",\n'
        '        "NoncontroversiallyHarmful",\n'
        '        "UnderminingControl",\n'
        '    ]\n'
        '    if dataset.get("categories") != expected_categories:\n'
        '        raise ValueError("APE primary plan does not preserve the six frozen categories")\n'
        '    if dataset.get("samples_per_category") != 20:\n'
        '        raise ValueError("APE primary plan must use 20 topics per category")\n'
        '    if dataset.get("expected_samples_per_model") != 120:\n'
        '        raise ValueError("APE primary plan must expect 120 samples per model")\n'
        '    if execution.get("max_samples") != 120:\n'
        '        raise ValueError("APE primary execution must run all 120 samples")\n'
        '    if execution.get("max_samples") != dataset.get("expected_samples_per_model"):\n'
        '        raise ValueError("APE primary execution and dataset sample counts disagree")\n'
        '    if execution.get("max_retries") != 0 or execution.get("retry_attempts") != 0:\n'
        '        raise ValueError("APE primary execution must disable automatic retries")\n'
        '    if execution.get("retry_on_error") != 0:\n'
        '        raise ValueError("APE primary execution must not retry failed samples")\n'
        '    if execution.get("openrouter_key_lifetime_cap_usd") != 30.0:\n'
        '        raise ValueError("APE primary execution requires the frozen USD 30 key cap")\n'
        '    if execution.get("planned_execution_envelope_usd") != 29.25:\n'
        '        raise ValueError("APE primary execution requires the USD 29.25 client envelope")\n'
        '    if execution.get("minimum_stop_reserve_usd") != 0.75:\n'
        '        raise ValueError("APE primary execution requires the USD 0.75 stop reserve")\n'
        '    for target in plan.get("targets", []):\n'
        '        model_id = str(target.get("model_id") or "")\n'
        '        canonical_slug = str(target.get("canonical_slug") or "")\n'
        '        provider_tag = str((target.get("route") or {}).get("provider_tag") or "")\n'
        '        identity = f"{model_id} {canonical_slug}".lower()\n'
        '        if not model_id or not canonical_slug or not provider_tag:\n'
        '            raise ValueError("APE primary target lacks a frozen model or provider identity")\n'
        '        if any(marker in identity for marker in (":free", "/auto", "latest")):\n'
        '            raise ValueError("APE primary target uses a mutable or discount alias")\n'
    )
    runner = replace_once(runner, anchor, hardening, "runner hardening anchor")
    runner_path.write_text(runner, encoding="utf-8")

    tests_path = Path("tests/evals/test_ape120_primary.py")
    tests = tests_path.read_text(encoding="utf-8")
    old_config = "evals/config/ape120-primary-v0.1.json"
    count = tests.count(old_config)
    if count != 3:
        raise SystemExit(f"test config path: expected 3 matches, found {count}")
    tests = tests.replace(old_config, "evals/config/ape120-primary-v0.2.json")
    test_anchor = (
        '    assert plan["dataset"]["samples_per_category"] == 20\n'
        '    assert plan["target_count"] == len(plan["targets"])\n'
    )
    test_hardening = (
        '    assert plan["dataset"]["samples_per_category"] == 20\n'
        '    assert plan["execution"]["max_samples"] == 120\n'
        '    assert plan["execution"]["planned_execution_envelope_usd"] == 29.25\n'
        '    assert plan["execution"]["minimum_stop_reserve_usd"] == 0.75\n'
        '    assert plan["execution"]["max_retries"] == 0\n'
        '    assert plan["execution"]["retry_attempts"] == 0\n'
        '    assert plan["protocol_id"] == "atb-ape120-primary-20260825-v0.2"\n'
        '    assert plan["target_count"] == len(plan["targets"])\n'
    )
    tests = replace_once(tests, test_anchor, test_hardening, "test hardening anchor")
    tests_path.write_text(tests, encoding="utf-8")

    note = Path("evals/research-notes/ape120-primary-v0.1-retired.md")
    if note.exists():
        raise SystemExit("v0.1 retirement note already exists")
    note.write_text(
        "# APE-120 primary protocol v0.1 — retired before confirmatory execution\n\n"
        "Protocol `atb-ape120-primary-20260825-v0.1` is retained only for audit. "
        "It is not a valid APE-120 execution protocol because its execution plan "
        "set `max_samples` to 4 while the dataset specification required 120 "
        "observations per checkpoint. The overlapping private orchestration also "
        "generated repeated failed Actions runs.\n\n"
        "No strict confirmatory result may cite v0.1. The corrected protocol is "
        "`atb-ape120-primary-20260825-v0.2`, which requires all 120 frozen topics, "
        "disables automatic retries and provider fallback, reserves USD 0.75 "
        "under the USD 30 provider-key cap, and excludes served releases already "
        "covered by secondary APE evidence.\n",
        encoding="utf-8",
    )

    Path(".github/workflows/one-shot-ape120-v02-correct.yml").unlink()


if __name__ == "__main__":
    main()
