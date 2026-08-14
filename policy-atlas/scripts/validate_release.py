#!/usr/bin/env python3
"""Validate the Policy Atlas source snapshot and generated research preview."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

from curation import load_table
from jsonschema import Draft202012Validator, FormatChecker
from public_contract import PUBLIC_TABLE_STEMS, validate_csv_contract
from release_config import (
    CURATION_VERSION,
    HISTORICAL_RELEASE_MANIFEST_SHA256,
    RANKING_PROTOCOL_VERSION,
    STABLE_CORE_SELECTION_VERSION,
    STABLE_CORE_SOURCE_MANIFEST_SHA256,
    STABLE_CORE_SOURCE_VERSION,
    VERSION,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "draft-v0.3"
PRIORITY_REVIEW = ROOT / "review" / "priority_claim_review.csv"
STABLE_RELEASE_GATES = ROOT / "review" / "stable_release_gates.csv"
STABLE_CORE_SELECTION = ROOT / "data" / "curation-v0.5" / "stable_core_selection.csv"
RANKING_TEMPLATES = ROOT / "data" / "ranking-v0.1"
RANKING_TEMPLATE_FILES = (
    "ranking_scenarios.csv",
    "scenario_candidates.csv",
    "criterion_definitions.csv",
    "implementation_gate_assessments.csv",
    "criterion_scores.csv",
    "weight_scenarios.csv",
    "sensitivity_plans.csv",
    "sensitivity_results.csv",
    "analysis_runs.csv",
    "protocol_deviations.csv",
    "review_signoffs.csv",
    "rank_acceptability.csv",
    "pairwise_results.csv",
    "rank_results.csv",
)
RELEASE = ROOT / "release" / VERSION
PRIORITY_CLAIM_IDS = {
    "CLM-0016",
    "CLM-0115",
    "CLM-0181",
    "CLM-0184",
    "CLM-0232",
    "CLM-0235",
}
ELIGIBLE_LEVELS_BY_CLAIM_TYPE = {
    "Control effectiveness": {"Claim checked — empirical source"},
    "Mechanism": {"Claim checked — empirical source"},
    "Legal status / scope": {
        "Claim checked — primary legal source",
        "Claim checked — primary official policy source",
    },
}
CHECKED_LEVELS = set().union(*ELIGIBLE_LEVELS_BY_CLAIM_TYPE.values())
LIST_COLUMNS = {
    "legacy_ids",
    "implementation_ids",
    "linked_source_ids",
    "merged_relation_ids",
    "mechanism_ids",
    "context_entity_ids",
    "research_gap_ids",
    "claim_ids",
    "effect_claim_ids",
    "legal_claim_ids",
    "mechanism_claim_ids",
    "source_ids",
    "policy_package_ids",
    "priority_effect_review_outcomes",
    "priority_effect_publication_actions",
    "linked_gap_ids",
}
BOOLEAN_COLUMNS = {
    "effect_claim_checked",
    "effect_claim_reviewed",
    "legal_claim_checked",
    "mechanism_claim_checked",
    "effect_direction_used_for_selection",
    "human_signoff_required",
    "stable_core_ready",
    "ranking_ready",
}
INTEGER_COLUMNS = {"implementation_count", "display_order"}
PUBLIC_TABLE_SCHEMAS = {
    "data/core/implementations": "public-implementation.schema.json",
    "data/core/claims": "claim.schema.json",
    "data/core/sources": "source.schema.json",
    "data/core/stable_release_gates": "stable-release-gate.schema.json",
    "data/derived/atlas": "atlas.schema.json",
    "data/derived/stable_core_candidates": "stable-core-candidate.schema.json",
    "data/derived/candidate_registry": "candidate-registry.schema.json",
}


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)

    def warn(self, condition: bool, message: str) -> None:
        if not condition:
            self.warnings.append(message)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def read_checksums(path: Path) -> dict[str, str]:
    output: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        parts = line.split("  ", 1)
        if len(parts) != 2:
            raise ValueError(f"malformed checksum line {line_number}")
        digest, relative = parts
        if relative in output:
            raise ValueError(f"duplicate checksum entry: {relative}")
        output[relative] = digest
    return output


def unique_ids(
    check: Validation, rows: list[dict[str, str]], field: str, pattern: str, table: str
) -> set[str]:
    values = [row[field] for row in rows]
    check.require(all(values), f"{table}: blank {field}")
    duplicates = [value for value, count in Counter(values).items() if count > 1]
    check.require(not duplicates, f"{table}: duplicate {field}: {duplicates[:10]}")
    invalid = [value for value in values if not re.fullmatch(pattern, value)]
    check.require(not invalid, f"{table}: invalid {field}: {invalid[:10]}")
    return set(values)


def foreign_keys(
    check: Validation,
    rows: list[dict[str, str]],
    field: str,
    targets: set[str],
    table: str,
) -> None:
    missing = sorted({row[field] for row in rows if row[field] not in targets})
    check.require(not missing, f"{table}: orphan {field}: {missing[:10]}")


def controlled(
    check: Validation,
    rows: list[dict[str, str]],
    field: str,
    allowed: set[str],
    table: str = "implementations",
) -> None:
    invalid = sorted({row[field] for row in rows if row[field] not in allowed})
    check.require(not invalid, f"{table}: invalid {field}: {invalid}")


def validate_schema(
    check: Validation,
    rows: list[dict[str, object]],
    schema_name: str,
    table: str,
) -> None:
    schema_path = ROOT / "schemas" / schema_name
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        for error in validator.iter_errors(row):
            location = ".".join(str(part) for part in error.absolute_path)
            errors.append(f"row {index}{'.' + location if location else ''}: {error.message}")
            if len(errors) >= 10:
                break
        if len(errors) >= 10:
            break
    check.require(not errors, f"{table}: JSON Schema errors: {errors}")


def validate_archived_release(
    check: Validation, version: str, expected_manifest_sha256: str
) -> list[dict[str, str]]:
    """Verify one immutable, previously published release directory."""

    archived_release = ROOT / "release" / version
    manifest_path = archived_release / "manifests" / "release.json"
    check.require(manifest_path.is_file(), f"archived {version} manifest is missing")
    if not manifest_path.is_file():
        return []
    check.require(
        sha256(manifest_path) == expected_manifest_sha256,
        f"archived {version} manifest SHA-256 mismatch",
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    check.require(
        manifest.get("artifact_version") == version.removeprefix("v"),
        f"archived {version} artifact version mismatch",
    )
    declared = set(manifest.get("files", {}))
    actual = {
        path.relative_to(archived_release).as_posix()
        for path in (archived_release / "data").rglob("*")
        if path.is_file()
    }
    check.require(actual == declared, f"archived {version} data inventory mismatch")
    for relative, metadata in manifest.get("files", {}).items():
        path = archived_release / relative
        check.require(path.is_file(), f"archived {version} file missing: {relative}")
        if path.is_file():
            check.require(
                sha256(path) == metadata.get("sha256"),
                f"archived {version} checksum mismatch: {relative}",
            )
            check.require(
                path.stat().st_size == metadata.get("bytes"),
                f"archived {version} byte-size mismatch: {relative}",
            )
    checksums_path = archived_release / "manifests" / "checksums.sha256"
    try:
        checksums = read_checksums(checksums_path)
    except (OSError, ValueError) as error:
        check.require(False, f"invalid archived {version} checksums: {error}")
        checksums = {}
    expected_checksums = declared | {"manifests/release.json"}
    check.require(
        set(checksums) == expected_checksums,
        f"archived {version} checksum inventory mismatch",
    )
    for relative, digest in checksums.items():
        path = archived_release / relative
        check.require(
            path.is_file() and sha256(path) == digest,
            f"archived {version} checksum file mismatch: {relative}",
        )
    implementations_path = archived_release / "data" / "core" / "implementations.csv"
    return read_csv(implementations_path) if implementations_path.is_file() else []


def semantic_value(column: str, value: object) -> object:
    """Normalize CSV strings and typed Parquet values to one comparison form."""

    if column in LIST_COLUMNS:
        if isinstance(value, list):
            return tuple(str(item) for item in value)
        if value in (None, ""):
            return ()
        return tuple(item.strip() for item in re.split(r"[;|]", str(value)) if item.strip())
    if column in BOOLEAN_COLUMNS:
        if isinstance(value, bool):
            return value
        return str(value).lower() == "true"
    if column in INTEGER_COLUMNS:
        return None if value in (None, "") else int(value)
    return "" if value is None else str(value)


def validate_csv_parquet_pair(
    check: Validation, csv_path: Path, parquet_path: Path, table: str
) -> list[dict[str, object]]:
    """Check row order, columns, and cell semantics across both formats."""

    try:
        import pyarrow.parquet as parquet

        csv_rows = read_csv(csv_path)
        parquet_rows = parquet.read_table(parquet_path).to_pylist()
    except Exception as error:  # pragma: no cover - surfaced as validation output
        check.require(False, f"{table}: cannot read CSV/Parquet pair: {error}")
        return []
    check.require(
        len(csv_rows) == len(parquet_rows),
        f"{table}: CSV/Parquet row-count mismatch",
    )
    differences: list[str] = []
    for row_number, (csv_row, parquet_row) in enumerate(
        zip(csv_rows, parquet_rows, strict=False), start=1
    ):
        if list(csv_row) != list(parquet_row):
            differences.append(f"row {row_number}: column order/set mismatch")
            continue
        for column in csv_row:
            if semantic_value(column, csv_row[column]) != semantic_value(
                column, parquet_row[column]
            ):
                differences.append(f"row {row_number}, column {column}")
                if len(differences) >= 10:
                    break
        if len(differences) >= 10:
            break
    check.require(
        not differences,
        f"{table}: CSV/Parquet semantic mismatch: {differences}",
    )
    return parquet_rows


def main() -> int:
    check = Validation()
    required = [
        "intervention_families.csv",
        "implementations.csv",
        "claims.csv",
        "sources.csv",
        "claim_sources.csv",
        "implementation_claims.csv",
        "mechanisms.csv",
        "implementation_mechanisms.csv",
        "legal_instruments.csv",
        "case_index.csv",
        "implementation_cases.csv",
        "research_gaps.csv",
        "implementation_gaps.csv",
        "policy_packages.csv",
        "decision_gates.csv",
    ]
    for name in required:
        check.require((SOURCE / name).exists(), f"missing source table: {name}")
    if check.errors:
        for error in check.errors:
            print(f"ERROR: {error}")
        return 1

    families = load_table("intervention_families.csv")
    implementations = load_table("implementations.csv")
    claims = load_table("claims.csv")
    sources = load_table("sources.csv")
    claim_sources = load_table("claim_sources.csv")
    implementation_claims = load_table("implementation_claims.csv")
    mechanisms = load_table("mechanisms.csv")
    implementation_mechanisms = load_table("implementation_mechanisms.csv")
    legal = load_table("legal_instruments.csv")
    contexts = load_table("case_index.csv")
    implementation_contexts = load_table("implementation_cases.csv")
    gaps = load_table("research_gaps.csv")
    implementation_gaps = load_table("implementation_gaps.csv")
    packages = load_table("policy_packages.csv")
    gates = load_table("decision_gates.csv")
    priority_reviews = read_csv(PRIORITY_REVIEW)
    stable_release_gates = read_csv(STABLE_RELEASE_GATES)
    stable_core_selection = read_csv(STABLE_CORE_SELECTION)
    archived_implementations = {
        version: validate_archived_release(check, version, manifest_sha256)
        for version, manifest_sha256 in HISTORICAL_RELEASE_MANIFEST_SHA256.items()
    }
    frozen_source_implementations = archived_implementations.get(STABLE_CORE_SOURCE_VERSION, [])
    ranking_templates = {
        name: read_csv(RANKING_TEMPLATES / name) for name in RANKING_TEMPLATE_FILES
    }
    package_metadata = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    package_lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    expected_package_version = VERSION.removeprefix("v")
    check.require(
        package_metadata.get("version") == expected_package_version,
        "package.json version does not match release_config.py",
    )
    check.require(
        package_lock.get("version") == expected_package_version
        and package_lock.get("packages", {}).get("", {}).get("version") == expected_package_version,
        "package-lock.json version does not match release_config.py",
    )

    family_ids = unique_ids(check, families, "control_family_id", r"CF-\d{3}", "families")
    implementation_ids = unique_ids(
        check, implementations, "implementation_id", r"I-\d{3}", "implementations"
    )
    selected_implementation_ids = unique_ids(
        check,
        stable_core_selection,
        "implementation_id",
        r"I-\d{3}",
        "stable core selection",
    )
    claim_ids = unique_ids(check, claims, "claim_id", r"CLM-\d{4}", "claims")
    source_ids = unique_ids(check, sources, "source_id", r"SRC-\d{3}", "sources")
    unique_ids(check, claim_sources, "relation_id", r"CS-\d{4}", "claim_sources")
    mechanism_ids = unique_ids(check, mechanisms, "mechanism_id", r"M-\d{2}", "mechanisms")
    unique_ids(check, legal, "legal_id", r"L-\d{3}", "legal instruments")
    context_ids = unique_ids(
        check,
        contexts,
        "entity_id",
        r"(?:C|D|X|S)-\d{2}",
        "context entities",
    )
    gap_ids = unique_ids(check, gaps, "gap_id", r"G-\d{2}", "research gaps")
    unique_ids(check, packages, "package_id", r"(?:G0|P\d{2})", "policy packages")
    review_claim_ids = unique_ids(
        check,
        priority_reviews,
        "claim_id",
        r"CLM-\d{4}",
        "priority claim reviews",
    )
    stable_gate_ids = unique_ids(
        check,
        stable_release_gates,
        "gate_id",
        r"SR-\d{2}",
        "stable release gates",
    )
    check.require(
        stable_gate_ids == {f"SR-{index:02d}" for index in range(1, 14)},
        "stable release gates must contain the frozen SR-01 through SR-13 set",
    )
    controlled(
        check,
        stable_release_gates,
        "status",
        {"blocked", "in_progress", "satisfied"},
        "stable release gates",
    )
    controlled(
        check,
        stable_release_gates,
        "human_signoff_required",
        {"true", "false"},
        "stable release gates",
    )
    controlled(
        check,
        stable_release_gates,
        "human_signoff_role",
        {"", "evidence", "legal", "methods", "independent", "release"},
        "stable release gates",
    )
    check.require(
        all(
            (row["human_signoff_required"] == "true" and row["human_signoff_role"])
            or (row["human_signoff_required"] == "false" and not row["human_signoff_role"])
            for row in stable_release_gates
        ),
        "stable release gates: human sign-off role mismatch",
    )
    check.require(
        not any(row["evidence_sha256"] for row in stable_release_gates),
        "beta stable-release gates must not claim frozen evidence hashes",
    )
    check.require(
        all(
            row["requirement"].strip() and row["blocking_reason"].strip()
            for row in stable_release_gates
        ),
        "stable release gates: requirement and blocking_reason are required in beta",
    )
    check.require(
        not any(row["status"] == "satisfied" for row in stable_release_gates),
        "beta foundation must not mark a stable-release gate satisfied",
    )
    validate_schema(check, implementations, "implementation.schema.json", "implementations")
    validate_schema(check, claims, "claim.schema.json", "claims")
    validate_schema(check, sources, "source.schema.json", "sources")
    validate_schema(
        check,
        stable_release_gates,
        "stable-release-gate.schema.json",
        "stable release gates",
    )
    check.require(
        20 <= len(stable_core_selection) <= 30,
        "stable core selection must contain 20 to 30 provisional candidates",
    )
    check.require(
        selected_implementation_ids <= implementation_ids,
        "stable core selection contains an unknown implementation_id",
    )
    frozen_implementation_by_id = {
        row["implementation_id"]: row for row in frozen_source_implementations
    }
    mismatched_selection_metadata = [
        row["implementation_id"]
        for row in stable_core_selection
        if row["implementation_id"] in frozen_implementation_by_id
        and (
            row["control_family_id"]
            != frozen_implementation_by_id[row["implementation_id"]]["control_family_id"]
            or row["intervention"]
            != frozen_implementation_by_id[row["implementation_id"]]["intervention"]
        )
    ]
    check.require(
        not mismatched_selection_metadata,
        "stable core selection metadata mismatch against frozen beta.2: "
        f"{mismatched_selection_metadata}",
    )
    check.require(
        selected_implementation_ids <= set(frozen_implementation_by_id),
        "stable core selection contains an ID absent from frozen beta.2",
    )
    check.require(
        {row["control_family_id"] for row in stable_core_selection} <= family_ids,
        "stable core selection contains an unknown control_family_id",
    )
    invalid_selection_gaps = sorted(
        {
            gap_id
            for row in stable_core_selection
            for gap_id in row["linked_gap_ids"].split("|")
            if gap_id and gap_id not in gap_ids
        }
    )
    check.require(
        not invalid_selection_gaps,
        f"stable core selection contains unknown linked gaps: {invalid_selection_gaps}",
    )
    canonical_gaps_by_implementation: dict[str, set[str]] = {}
    for relation in implementation_gaps:
        canonical_gaps_by_implementation.setdefault(relation["implementation_id"], set()).add(
            relation["gap_id"]
        )
    inconsistent_selection_gaps = [
        row["implementation_id"]
        for row in stable_core_selection
        if not {gap_id for gap_id in row["linked_gap_ids"].split("|") if gap_id}
        <= canonical_gaps_by_implementation.get(row["implementation_id"], set())
    ]
    check.require(
        not inconsistent_selection_gaps,
        "stable core selection gaps disagree with canonical relations: "
        f"{inconsistent_selection_gaps}",
    )
    controlled(
        check,
        stable_core_selection,
        "electoral_relevance_code",
        {"direct", "enabling"},
        "stable core selection",
    )
    controlled(
        check,
        stable_core_selection,
        "auditability_code",
        {"high", "medium"},
        "stable core selection",
    )
    controlled(
        check,
        stable_core_selection,
        "nonduplication_code",
        {"unique_function", "cross_layer_complement", "cross_jurisdiction_comparator"},
        "stable core selection",
    )
    controlled(
        check,
        stable_core_selection,
        "rank_eligibility",
        {
            "not_eligible_now__comparison_class_possible",
            "not_eligible_now__contextual_assessment_only",
            "not_eligible_now__pilot_evidence_required",
        },
        "stable core selection",
    )
    check.require(
        [int(row["display_order"]) for row in stable_core_selection]
        == list(range(1, len(stable_core_selection) + 1)),
        "stable core display_order must be contiguous and deterministic",
    )
    check.require(
        [row["implementation_id"] for row in stable_core_selection]
        == sorted(selected_implementation_ids),
        "stable core display_order must follow ascending implementation_id "
        "and has no priority meaning",
    )
    check.require(
        {row["selection_protocol_version"] for row in stable_core_selection}
        == {"stable-core-selection-v0.1"},
        "stable core selection has an unexpected protocol version",
    )
    check.require(
        {row["source_release"] for row in stable_core_selection} == {STABLE_CORE_SOURCE_VERSION},
        "stable core selection must identify the frozen beta.2 source release",
    )
    check.require(
        {row["selection_design"] for row in stable_core_selection}
        == {"retrospective_editorial_selection"}
        and {row["preregistration_status"] for row in stable_core_selection}
        == {"not_preregistered"},
        "stable core selection must remain retrospective and non-preregistered",
    )
    check.require(
        {row["inclusion_status"] for row in stable_core_selection} == {"proposed_core_candidate"},
        "selection rows must remain explicitly provisional",
    )
    check.require(
        all(
            row["rank_eligibility"].startswith("not_eligible_now__")
            for row in stable_core_selection
        ),
        "no proposed core candidate may be rank-eligible in this release",
    )
    check.require(
        {row["effect_direction_used_for_selection"] for row in stable_core_selection} == {"false"},
        "stable core selection process declaration must record effect direction as unused",
    )
    for field in (
        "selection_rationale",
        "evidence_gap",
        "rank_eligibility_rationale",
        "primary_policy_function",
        "causal_chain_stage",
        "accountable_actor_code",
        "auditability_code",
    ):
        check.require(
            all(row[field].strip() for row in stable_core_selection),
            f"stable core selection: blank {field}",
        )
    for name, rows in ranking_templates.items():
        check.require(
            len(rows) == 1,
            f"ranking template {name} must contain exactly one metadata placeholder",
        )
        if rows:
            row = rows[0]
            check.require(
                row.get("record_status") == "template_placeholder",
                f"ranking template {name} contains a non-placeholder record",
            )
            check.require(
                row.get("protocol_version") == "ranking-protocol-v0.1",
                f"ranking template {name} has an unexpected protocol version",
            )
            check.require(
                row.get("preregistration_status") == "draft_not_preregistered",
                f"ranking template {name} must remain explicitly non-preregistered",
            )
            check.require(
                "TEMPLATE-DO-NOT-ANALYZE" in "|".join(row.values()),
                f"ranking template {name} lacks the do-not-analyze marker",
            )
    ranking_result_rows = ranking_templates["rank_results.csv"]
    ranking_result_template = ranking_result_rows[0] if ranking_result_rows else {}
    check.require(
        ranking_result_template.get("publication_status") == "prohibited_draft"
        and ranking_result_template.get("independent_review_status") == "not_reviewed",
        "rank-results template must remain prohibited and unreviewed",
    )
    unique_ids(
        check,
        gates,
        "criterion_code",
        r"(?:G\d-[A-Z]\d{2}|OBS-\d{2})",
        "decision gates",
    )

    foreign_keys(check, implementations, "control_family_id", family_ids, "implementations")
    foreign_keys(check, claim_sources, "claim_id", claim_ids, "claim_sources")
    foreign_keys(check, claim_sources, "source_id", source_ids, "claim_sources")
    foreign_keys(check, legal, "source_id", source_ids, "legal instruments")
    foreign_keys(
        check,
        implementation_claims,
        "implementation_id",
        implementation_ids,
        "implementation_claims",
    )
    foreign_keys(check, implementation_claims, "claim_id", claim_ids, "implementation_claims")
    foreign_keys(
        check,
        implementation_mechanisms,
        "implementation_id",
        implementation_ids,
        "implementation_mechanisms",
    )
    foreign_keys(
        check, implementation_mechanisms, "mechanism_id", mechanism_ids, "implementation_mechanisms"
    )
    foreign_keys(
        check,
        implementation_contexts,
        "implementation_id",
        implementation_ids,
        "implementation_contexts",
    )
    foreign_keys(
        check, implementation_contexts, "entity_id", context_ids, "implementation_contexts"
    )
    foreign_keys(
        check, implementation_gaps, "implementation_id", implementation_ids, "implementation_gaps"
    )
    foreign_keys(check, implementation_gaps, "gap_id", gap_ids, "implementation_gaps")
    check.require(review_claim_ids <= claim_ids, "priority claim reviews: orphan claim_id")
    check.require(
        review_claim_ids == PRIORITY_CLAIM_IDS,
        "priority claim review must contain the six frozen wave-1 claims",
    )

    established_effect_implementations = {
        row["implementation_id"]
        for row in implementations
        if row["claim_class"] == "Established — component effect"
    }
    effect_claims_by_type = {
        row["claim_id"] for row in claims if row["claim_type"] == "Control effectiveness"
    }
    established_effect_claims = {
        row["claim_id"]
        for row in implementation_claims
        if row["implementation_id"] in established_effect_implementations
        and row["claim_id"] in effect_claims_by_type
    }
    check.require(
        established_effect_claims <= review_claim_ids,
        "priority review must cover every established component-effect claim",
    )

    family_counts = Counter(row["control_family_id"] for row in implementations)
    mismatched = [
        row["control_family_id"]
        for row in families
        if int(row["implementation_count"]) != family_counts[row["control_family_id"]]
    ]
    check.require(not mismatched, f"family implementation counts mismatch: {mismatched}")

    linked_claims = {row["implementation_id"] for row in implementation_claims}
    linked_mechanisms = {row["implementation_id"] for row in implementation_mechanisms}
    check.require(
        linked_claims == implementation_ids, "not every implementation has a claim relation"
    )
    check.require(
        linked_mechanisms == implementation_ids, "not every implementation has a mechanism relation"
    )

    for package in packages:
        members = {
            item.strip() for item in package["implementation_ids"].split(";") if item.strip()
        }
        check.require(
            members <= implementation_ids, f"{package['package_id']}: invalid implementation member"
        )

    controlled(
        check,
        implementations,
        "legal_force",
        {
            "Binding",
            "Binding — limited scope",
            "Binding — phased",
            "Mandatory administrative policy — limited scope",
            "Mixed",
            "Non-binding official guidance",
            "Voluntary / private",
            "Planned / no legal force",
            "Proposed",
            "Research",
        },
    )
    controlled(
        check,
        implementations,
        "operational_maturity",
        {
            "Operational",
            "Partial / uneven",
            "Pilot",
            "Design-ready",
            "Research",
            "Not applicable yet",
        },
    )
    controlled(
        check,
        implementations,
        "mechanism_evidence_tier",
        {
            "Project-C",
            "Project-X",
            "E0",
            "E1",
            "E2",
            "E3",
            "None",
        },
    )
    controlled(
        check,
        implementations,
        "decision_tier",
        {
            "Enforce now",
            "Implement now",
            "Prepare",
            "Pilot",
            "Research / hold",
            "Monitor / shape",
        },
    )

    urls = [row["direct_url"].strip() for row in sources]
    check.require(all(re.fullmatch(r"https?://\S+", url) for url in urls), "sources: invalid URL")
    check.require(len(urls) == len(set(urls)), "sources: duplicate canonical URL")

    pairs = [(row["claim_id"], row["source_id"]) for row in claim_sources]
    duplicate_pairs = len(pairs) - len(set(pairs))
    check.warn(
        duplicate_pairs == 0,
        f"source snapshot has {duplicate_pairs} duplicate claim-source rows; "
        "release must deduplicate",
    )

    claim_type_by_id = {row["claim_id"]: row["claim_type"] for row in claims}
    eligible_checked_edges = {
        (row["claim_id"], row["source_id"])
        for row in claim_sources
        if row["support_relation"] == "Supports"
        and row["verification_level"]
        in ELIGIBLE_LEVELS_BY_CLAIM_TYPE[claim_type_by_id[row["claim_id"]]]
    }
    eligible_checked_source_ids = {source_id for _, source_id in eligible_checked_edges}
    empirically_checked_claims = {
        row["claim_id"]
        for row in claim_sources
        if row["verification_level"] == "Claim checked — empirical source"
        and row["support_relation"] == "Supports"
    }
    effect_claims = effect_claims_by_type
    checked_effect_claims = empirically_checked_claims & effect_claims
    mechanism_claims = {row["claim_id"] for row in claims if row["claim_type"] == "Mechanism"}
    checked_mechanism_claims = empirically_checked_claims & mechanism_claims
    check.require(
        review_claim_ids <= checked_effect_claims,
        "every priority effect claim must have a checked empirical relation after curation wave 1",
    )
    check.warn(
        bool(checked_effect_claims),
        "no control-effectiveness claim has a checked source; stable release is blocked",
    )
    missing_legal_sources = [row["legal_id"] for row in legal if not row["source_id"].strip()]
    check.require(
        not missing_legal_sources,
        f"{len(missing_legal_sources)} legal instruments have no source_id: "
        f"{missing_legal_sources}",
    )

    release_manifest = RELEASE / "manifests" / "release.json"
    check.require(
        release_manifest.exists(), "generated release manifest missing; run build_release.py"
    )
    if release_manifest.exists():
        manifest = json.loads(release_manifest.read_text(encoding="utf-8"))
        check.require(
            manifest.get("artifact_version") == expected_package_version,
            "manifest artifact version mismatch",
        )
        check.require(
            manifest["stable_release_ready"] is False,
            "beta must not claim stable release readiness",
        )
        check.require(
            manifest.get("curation_version") == CURATION_VERSION,
            "manifest curation version mismatch",
        )
        check.require(
            manifest.get("stable_core_selection_version") == STABLE_CORE_SELECTION_VERSION,
            "manifest stable-core selection version mismatch",
        )
        check.require(
            manifest.get("stable_core_source_version") == STABLE_CORE_SOURCE_VERSION
            and manifest.get("stable_core_source_manifest_sha256")
            == STABLE_CORE_SOURCE_MANIFEST_SHA256,
            "manifest frozen stable-core source mismatch",
        )
        check.require(
            manifest.get("ranking_protocol_version") == RANKING_PROTOCOL_VERSION
            and manifest.get("ranking_preregistration_status") == "draft_not_preregistered",
            "manifest must expose the draft, non-preregistered ranking protocol",
        )
        validate_schema(
            check,
            [manifest],
            "release-manifest.schema.json",
            "release manifest",
        )
        check.require(
            manifest["counts"]["control_effectiveness_claims_checked"]
            == len(checked_effect_claims),
            "manifest checked-effect count mismatch",
        )
        check.require(
            manifest["counts"]["mechanism_claims_checked"] == len(checked_mechanism_claims),
            "manifest checked-mechanism count mismatch",
        )
        check.require(
            manifest["counts"]["claim_source_edges_checked"] == len(eligible_checked_edges)
            and manifest["counts"]["source_records_checked"] == len(eligible_checked_source_ids),
            "manifest type-eligible claim/source coverage mismatch",
        )
        check.require(
            manifest["counts"]["priority_effect_claims_reviewed"] == len(priority_reviews),
            "manifest priority-review count mismatch",
        )
        check.require(
            manifest["counts"]["stable_release_gates"] == len(stable_release_gates),
            "manifest stable-release gate count mismatch",
        )
        check.require(
            manifest["counts"]["stable_release_gates_blocked"]
            == sum(row["status"] == "blocked" for row in stable_release_gates),
            "manifest blocked stable-release gate count mismatch",
        )
        check.require(
            manifest["counts"]["proposed_stable_core_candidates"] == len(stable_core_selection),
            "manifest stable-core candidate count mismatch",
        )
        check.require(
            manifest["counts"]["candidate_registry_implementations"]
            == len(implementations) - len(stable_core_selection),
            "manifest candidate-registry count mismatch",
        )
        check.require(
            manifest["counts"]["rank_eligible_core_candidates"] == 0,
            "beta foundation must expose zero rank-eligible core candidates",
        )
        check.require(
            manifest["counts"]["publication_decision_postures_assessed"] == 0,
            "beta foundation must not publish assessed decision postures",
        )
        check.require(
            manifest["counts"]["established_legal_status_implementations_checked"]
            < manifest["counts"]["established_legal_status_implementations"],
            "beta manifest must expose unchecked established legal-status implementations",
        )
        check.require(
            manifest["counts"]["established_project_mechanism_implementations_checked"]
            < manifest["counts"]["established_project_mechanism_implementations"],
            "beta manifest must expose unchecked established project mechanisms",
        )
        for relative, metadata in manifest["files"].items():
            path = RELEASE / relative
            check.require(path.exists(), f"manifest file missing: {relative}")
            if path.exists():
                check.require(sha256(path) == metadata["sha256"], f"checksum mismatch: {relative}")
                check.require(
                    path.stat().st_size == metadata["bytes"], f"byte-size mismatch: {relative}"
                )
        data_files = {
            path.relative_to(RELEASE).as_posix()
            for path in (RELEASE / "data").rglob("*")
            if path.is_file()
        }
        check.require(
            data_files == set(manifest["files"]),
            "release data inventory differs from the manifest file inventory",
        )
        csv_files = {path for path in data_files if path.endswith(".csv")}
        parquet_files = {path for path in data_files if path.endswith(".parquet")}
        check.require(
            not (data_files - csv_files - parquet_files),
            "release data inventory contains a non-CSV/Parquet artifact",
        )
        check.require(
            {path.removesuffix(".csv") for path in csv_files} == PUBLIC_TABLE_STEMS,
            "release CSV table inventory differs from the frozen public contract",
        )
        if set(manifest.get("formats", [])) == {"csv", "parquet"}:
            check.require(
                {path.removesuffix(".csv") for path in csv_files}
                == {path.removesuffix(".parquet") for path in parquet_files},
                "CSV/Parquet table parity mismatch",
            )
            for csv_relative in sorted(csv_files):
                stem = csv_relative.removesuffix(".csv")
                parquet_rows = validate_csv_parquet_pair(
                    check,
                    RELEASE / csv_relative,
                    RELEASE / f"{stem}.parquet",
                    stem,
                )
                schema_name = PUBLIC_TABLE_SCHEMAS.get(stem)
                if schema_name and parquet_rows:
                    validate_schema(
                        check,
                        parquet_rows,
                        schema_name,
                        f"{stem} Parquet",
                    )
        else:
            check.require(
                manifest.get("formats") == ["csv"] and not parquet_files,
                "intermediate release must contain CSV only",
            )
        try:
            validate_csv_contract(RELEASE)
        except ValueError as error:
            check.require(False, f"public CSV contract violation: {error}")
        checksums_path = RELEASE / "manifests" / "checksums.sha256"
        check.require(checksums_path.exists(), "checksum manifest missing")
        if checksums_path.exists():
            try:
                checksums = read_checksums(checksums_path)
            except ValueError as error:
                check.require(False, f"invalid checksum manifest: {error}")
                checksums = {}
            expected_paths = set(manifest["files"]) | {"manifests/release.json"}
            check.require(set(checksums) == expected_paths, "checksum path set mismatch")
            for relative, digest in checksums.items():
                path = RELEASE / relative
                check.require(path.exists(), f"checksum target missing: {relative}")
                if path.exists():
                    check.require(sha256(path) == digest, f"checksum file mismatch: {relative}")

    release_claim_sources = RELEASE / "data" / "relations" / "claim_sources.csv"
    if release_claim_sources.exists():
        released = read_csv(release_claim_sources)
        released_pairs = [(row["claim_id"], row["source_id"]) for row in released]
        check.require(
            len(released_pairs) == len(set(released_pairs)),
            "release contains duplicate claim-source edges",
        )
        invalid_relation_statuses: list[str] = []
        for row in released:
            eligible_level = (
                row["verification_level"]
                in ELIGIBLE_LEVELS_BY_CLAIM_TYPE[claim_type_by_id[row["claim_id"]]]
            )
            if eligible_level and row["support_relation"] == "Supports":
                expected_status = "claim_support_checked"
            elif eligible_level:
                expected_status = "checked_source_without_full_support"
            elif row["verification_level"] in CHECKED_LEVELS:
                expected_status = "source_checked_not_eligible_for_claim_type"
            else:
                expected_status = "pending_claim_check"
            if row.get("publication_relation_status") != expected_status:
                invalid_relation_statuses.append(row["relation_id"])
        check.require(
            not invalid_relation_statuses,
            f"release claim-source relation status mismatch: {invalid_relation_statuses[:10]}",
        )

    for release_name in ("implementations.csv", "policy_packages.csv"):
        public_rows = read_csv(RELEASE / "data" / "core" / release_name)
        check.require(
            all(
                "decision_tier" not in row
                and row.get("working_register_decision_tier")
                and row.get("publication_decision_posture") == "not_assessed"
                for row in public_rows
            ),
            f"{release_name}: imperative decision tier leaked into public core table",
        )
        if release_name == "implementations.csv":
            validate_schema(
                check,
                public_rows,
                "public-implementation.schema.json",
                "public implementations",
            )
    public_families = read_csv(RELEASE / "data" / "core" / "intervention_families.csv")
    check.require(
        all(
            "decision_posture" not in row
            and row.get("working_register_decision_posture")
            and row.get("publication_decision_posture") == "not_assessed"
            for row in public_families
        ),
        "intervention_families.csv: imperative posture leaked into public core table",
    )

    release_stable_gates = RELEASE / "data" / "core" / "stable_release_gates.csv"
    if release_stable_gates.exists():
        check.require(
            read_csv(release_stable_gates) == stable_release_gates,
            "generated stable-release gates differ from the canonical review table",
        )

    release_core_candidates = RELEASE / "data" / "derived" / "stable_core_candidates.csv"
    release_candidate_registry = RELEASE / "data" / "derived" / "candidate_registry.csv"
    release_atlas = RELEASE / "data" / "derived" / "atlas.csv"
    if (
        release_core_candidates.exists()
        and release_candidate_registry.exists()
        and release_atlas.exists()
    ):
        core_candidates = read_csv(release_core_candidates)
        candidate_registry = read_csv(release_candidate_registry)
        public_atlas = read_csv(release_atlas)
        check.require(
            {row["implementation_id"] for row in core_candidates} == selected_implementation_ids,
            "generated core-candidate IDs differ from the frozen selection",
        )
        check.require(
            {row["implementation_id"] for row in candidate_registry}
            == implementation_ids - selected_implementation_ids,
            "candidate registry is not the exact complement of the frozen selection",
        )
        check.require(
            all(
                row["stable_core_admission_status"] == "blocked_pending_verification"
                and row["ranking_ready"] == "false"
                for row in core_candidates
            ),
            "proposed core candidates must remain blocked and unranked",
        )
        check.require(
            not (RELEASE / "data" / "derived" / "rank_results.csv").exists(),
            "rank_results must not be released before preregistration and review",
        )
        validate_schema(
            check,
            core_candidates,
            "stable-core-candidate.schema.json",
            "stable core candidates",
        )
        validate_schema(
            check,
            candidate_registry,
            "candidate-registry.schema.json",
            "candidate registry",
        )
        validate_schema(
            check,
            public_atlas,
            "atlas.schema.json",
            "public atlas",
        )

    release_claims = RELEASE / "data" / "core" / "claims.csv"
    if release_claims.exists():
        for claim in read_csv(release_claims):
            if (
                claim["epistemic_status"] == "Established evidence"
                and claim["publication_verification_status"] != "claim_checked"
            ):
                check.require(
                    claim["publication_epistemic_status"] == "Unverified candidate",
                    f"{claim['claim_id']}: unchecked established claim was not downgraded",
                )

    for warning in check.warnings:
        print(f"WARNING: {warning}")
    for error in check.errors:
        print(f"ERROR: {error}")

    print(
        json.dumps(
            {
                "families": len(families),
                "implementations": len(implementations),
                "claims": len(claims),
                "sources": len(sources),
                "duplicate_claim_source_rows_raw": duplicate_pairs,
                "checked_control_effectiveness_claims": len(checked_effect_claims),
                "errors": len(check.errors),
                "warnings": len(check.warnings),
            },
            indent=2,
        )
    )
    return 1 if check.errors else 0


if __name__ == "__main__":
    sys.exit(main())
