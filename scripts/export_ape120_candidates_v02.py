from __future__ import annotations

import csv
import json
from pathlib import Path

PLAN_PATH = Path("evals/config/ape120-primary-v0.2.json")
OUTPUT_PATH = Path("evals/research-notes/ape120-primary-candidates-v0.2.csv")
EXPECTED_TARGETS = 66
PUBLIC_COMMIT = "5a7ab5a1868802b7ce91afc2d85c3a9221428cfc"

LEGACY_PROJECT_EVIDENCE = {
    "openai/gpt-3.5-turbo": "exploratory_complete_120_nonconfirmatory",
    "x-ai/grok-4.20": "exploratory_complete_120_nonconfirmatory",
    "deepseek/deepseek-v3.1-terminus": "exploratory_partial_112_nonconfirmatory",
}

FIELDS = [
    "priority",
    "model_id",
    "name",
    "family",
    "release_date",
    "release_date_source",
    "access_class",
    "total_params_b",
    "size_disclosure",
    "identity_tier",
    "canonical_slug",
    "inclusion_basis",
    "openrouter_url",
    "hugging_face_id",
    "hugging_face_url",
    "provider_tag",
    "provider_name",
    "endpoint_name",
    "quantization",
    "zdr_eligible",
    "seed_supported",
    "reasoning_effort_supported",
    "compatibility_lane",
    "reasoning_effort",
    "input_usd_per_million",
    "output_usd_per_million",
    "expected_target_cost_usd_120",
    "maximum_target_cost_usd_120",
    "expected_auxiliary_cost_usd_per_target",
    "conservative_start_forecast_usd",
    "secondary_ape_status",
    "legacy_project_evidence",
    "recommended_action",
    "protocol_id",
    "expected_samples_per_model",
    "samples_per_category",
    "candidate_status",
    "source_plan_url",
]


def main() -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    targets = plan.get("targets")
    if not isinstance(targets, list) or len(targets) != EXPECTED_TARGETS:
        raise SystemExit(
            f"expected {EXPECTED_TARGETS} targets in the frozen v0.2 plan, "
            f"found {len(targets) if isinstance(targets, list) else 'non-list'}"
        )
    model_ids = [str(target.get("model_id") or "") for target in targets]
    if any(not model_id for model_id in model_ids) or len(model_ids) != len(set(model_ids)):
        raise SystemExit("candidate model IDs are empty or duplicated")

    execution = plan["execution"]
    auxiliary = float(execution["expected_auxiliary_cost_usd_per_target"])
    multiplier = float(execution["maximum_model_forecast_multiplier"])
    protocol_id = str(plan["protocol_id"])
    dataset = plan["dataset"]
    source_plan_url = (
        "https://github.com/apolmig/agencytransfer/blob/"
        f"{PUBLIC_COMMIT}/evals/config/ape120-primary-v0.2.json"
    )

    rows: list[dict[str, object]] = []
    for target in targets:
        route = target["route"]
        generation = target["generation"]
        pricing = target["pricing_usd_per_million"]
        model_id = str(target["model_id"])
        hf_id = str(target.get("hugging_face_id") or "")
        total_params = target.get("total_params_b")
        legacy = LEGACY_PROJECT_EVIDENCE.get(model_id, "")
        expected_target = float(target["expected_target_cost_usd_120"])
        rows.append(
            {
                "priority": int(target["priority"]),
                "model_id": model_id,
                "name": target.get("name") or "",
                "family": target.get("family") or "",
                "release_date": target.get("release_date") or "",
                "release_date_source": target.get("release_date_source") or "",
                "access_class": target.get("access_class") or "",
                "total_params_b": "" if total_params is None else total_params,
                "size_disclosure": (
                    "documented_total_parameters"
                    if total_params is not None
                    else "undisclosed_or_not_bound_in_frozen_plan"
                ),
                "identity_tier": target.get("identity_tier") or "",
                "canonical_slug": target.get("canonical_slug") or "",
                "inclusion_basis": target.get("inclusion_basis") or "",
                "openrouter_url": f"https://openrouter.ai/{model_id}",
                "hugging_face_id": hf_id,
                "hugging_face_url": f"https://huggingface.co/{hf_id}" if hf_id else "",
                "provider_tag": route.get("provider_tag") or "",
                "provider_name": route.get("provider_name") or "",
                "endpoint_name": route.get("endpoint_name") or "",
                "quantization": route.get("quantization") or "",
                "zdr_eligible": bool(route.get("zdr_eligible")),
                "seed_supported": bool(route.get("seed_supported")),
                "reasoning_effort_supported": bool(route.get("reasoning_effort_supported")),
                "compatibility_lane": generation.get("compatibility_lane") or "",
                "reasoning_effort": generation.get("reasoning_effort") or "",
                "input_usd_per_million": pricing.get("input"),
                "output_usd_per_million": pricing.get("output"),
                "expected_target_cost_usd_120": expected_target,
                "maximum_target_cost_usd_120": target.get("maximum_target_cost_usd_120"),
                "expected_auxiliary_cost_usd_per_target": auxiliary,
                "conservative_start_forecast_usd": round(
                    (expected_target + auxiliary) * multiplier, 9
                ),
                "secondary_ape_status": (
                    "eligible_no_exact_secondary_ape_in_frozen_ledger"
                ),
                "legacy_project_evidence": legacy,
                "recommended_action": (
                    "rerun_under_strict_v0.2" if legacy else "run_primary_v0.2"
                ),
                "protocol_id": protocol_id,
                "expected_samples_per_model": dataset["expected_samples_per_model"],
                "samples_per_category": dataset["samples_per_category"],
                "candidate_status": "frozen_candidate_queue",
                "source_plan_url": source_plan_url,
            }
        )

    rows.sort(key=lambda row: int(row["priority"]))
    if [int(row["priority"]) for row in rows] != list(range(1, EXPECTED_TARGETS + 1)):
        raise SystemExit("candidate priorities are not contiguous")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)

    with OUTPUT_PATH.open(encoding="utf-8", newline="") as handle:
        emitted = list(csv.DictReader(handle))
    if len(emitted) != EXPECTED_TARGETS or set(emitted[0]) != set(FIELDS):
        raise SystemExit("exported candidate CSV failed round-trip verification")

    print(
        json.dumps(
            {
                "protocol_id": protocol_id,
                "candidate_count": len(rows),
                "hosted_count": sum(row["access_class"] == "hosted" for row in rows),
                "open_weight_count": sum(
                    row["access_class"] == "open-weight" for row in rows
                ),
                "output": str(OUTPUT_PATH),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
