#!/usr/bin/env python3
"""Build the public Policy Atlas research-preview release from the Sheets snapshot."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from collections import defaultdict
from pathlib import Path

from curation import load_table
from public_contract import validate_row_contract
from release_config import (
    CURATION_VERSION,
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
RELEASE = ROOT / "release" / VERSION

CHECKED_LEVELS = {
    "Claim checked — primary legal source",
    "Claim checked — primary official policy source",
    "Claim checked — empirical source",
}
ELIGIBLE_LEVELS_BY_CLAIM_TYPE = {
    "Control effectiveness": {"Claim checked — empirical source"},
    "Mechanism": {"Claim checked — empirical source"},
    "Legal status / scope": {
        "Claim checked — primary legal source",
        "Claim checked — primary official policy source",
    },
}

CORE_FILES = {
    "intervention_families.csv": "intervention_families.csv",
    "implementations.csv": "implementations.csv",
    "claims.csv": "claims.csv",
    "sources.csv": "sources.csv",
    "mechanisms.csv": "mechanisms.csv",
    "legal_instruments.csv": "legal_instruments.csv",
    "case_index.csv": "context_entities.csv",
    "research_gaps.csv": "research_gaps.csv",
    "policy_packages.csv": "policy_packages.csv",
    "decision_gates.csv": "decision_gates.csv",
}

RELATION_FILES = {
    "implementation_claims.csv": "implementation_claims.csv",
    "implementation_mechanisms.csv": "implementation_mechanisms.csv",
    "implementation_cases.csv": "implementation_contexts.csv",
    "implementation_gaps.csv": "implementation_gaps.csv",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_relative_to(RELEASE / "data"):
        stem = path.relative_to(RELEASE).with_suffix("").as_posix()
        contract_fields = validate_row_contract(stem, rows)
        if fields is not None and tuple(fields) != contract_fields:
            raise ValueError(f"{stem}: explicit fields differ from public contract")
        fields = list(contract_fields)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def split_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split(";") if item.strip()]


def join_ids(values: set[str] | list[str]) -> str:
    return "; ".join(sorted(set(values)))


def with_withheld_decision_posture(
    rows: list[dict[str, str]],
    source_field: str,
    provenance_field: str,
) -> list[dict[str, str]]:
    """Preserve beta provenance without publishing an imperative posture."""

    output: list[dict[str, str]] = []
    for source_row in rows:
        row = dict(source_row)
        row[provenance_field] = row.pop(source_field)
        row["publication_decision_posture"] = "not_assessed"
        output.append(row)
    return output


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def deduplicate_claim_sources(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["claim_id"], row["source_id"])].append(row)

    output: list[dict[str, str]] = []
    for key in sorted(grouped):
        members = grouped[key]
        for field in ("support_relation", "applicability_scope", "verification_level"):
            values = {row[field] for row in members}
            if len(values) != 1:
                raise ValueError(
                    f"Conflicting duplicate claim-source edge {key}: {field}={sorted(values)}"
                )
        first = dict(members[0])
        first["merged_relation_ids"] = join_ids({row["relation_id"] for row in members})
        basis_notes = [row["basis_note"].strip() for row in members if row["basis_note"].strip()]
        first["basis_note"] = " | ".join(dict.fromkeys(basis_notes))
        notes = [row["notes"].strip() for row in members if row["notes"].strip()]
        first["notes"] = " | ".join(dict.fromkeys(notes))
        output.append(first)
    return output


def eligible_levels_for_claim_type(claim_type: str) -> set[str]:
    try:
        return ELIGIBLE_LEVELS_BY_CLAIM_TYPE[claim_type]
    except KeyError as error:
        raise ValueError(f"Unsupported claim type: {claim_type!r}") from error


def annotate_claim_source_relations(
    relations: list[dict[str, str]], claim_types: dict[str, str]
) -> list[dict[str, str]]:
    """Expose whether a checked source is eligible for the linked claim type."""

    output: list[dict[str, str]] = []
    for source_relation in relations:
        row = dict(source_relation)
        claim_type = claim_types[row["claim_id"]]
        verification_level = row["verification_level"]
        if (
            verification_level in eligible_levels_for_claim_type(claim_type)
            and row["support_relation"] == "Supports"
        ):
            status = "claim_support_checked"
        elif verification_level in eligible_levels_for_claim_type(claim_type):
            status = "checked_source_without_full_support"
        elif verification_level in CHECKED_LEVELS:
            status = "source_checked_not_eligible_for_claim_type"
        else:
            status = "pending_claim_check"
        row["publication_relation_status"] = status
        output.append(row)
    return output


def claim_verification(
    claims: list[dict[str, str]], claim_sources: list[dict[str, str]]
) -> tuple[list[dict[str, str]], dict[str, str], dict[str, set[str]]]:
    edges: dict[str, list[dict[str, str]]] = defaultdict(list)
    source_ids: dict[str, set[str]] = defaultdict(set)
    for relation in claim_sources:
        edges[relation["claim_id"]].append(relation)
        source_ids[relation["claim_id"]].add(relation["source_id"])

    statuses: dict[str, str] = {}
    output: list[dict[str, str]] = []
    for claim in claims:
        claim_id = claim["claim_id"]
        linked = edges.get(claim_id, [])
        claim_type = claim["claim_type"]
        required_levels = eligible_levels_for_claim_type(claim_type)
        if any(
            edge["verification_level"] in required_levels and edge["support_relation"] == "Supports"
            for edge in linked
        ):
            status = "claim_checked"
        elif linked:
            status = "source_link_pending_claim_check"
        else:
            status = "no_source_link"
        statuses[claim_id] = status

        row = dict(claim)
        row["publication_verification_status"] = status
        row["linked_source_ids"] = join_ids(source_ids.get(claim_id, set()))
        if claim["epistemic_status"] == "Established evidence" and status != "claim_checked":
            row["publication_epistemic_status"] = "Unverified candidate"
        else:
            row["publication_epistemic_status"] = claim["epistemic_status"]
        output.append(row)
    return output, statuses, source_ids


def build_package_relations(packages: list[dict[str, str]]) -> list[dict[str, str]]:
    output = []
    index = 1
    for package in packages:
        for implementation_id in split_ids(package["implementation_ids"]):
            output.append(
                {
                    "relation_id": f"PI-{index:04d}",
                    "package_id": package["package_id"],
                    "implementation_id": implementation_id,
                }
            )
            index += 1
    return output


def build_atlas(
    implementations: list[dict[str, str]],
    families: list[dict[str, str]],
    implementation_claims: list[dict[str, str]],
    claim_types: dict[str, str],
    claim_statuses: dict[str, str],
    claim_sources: dict[str, set[str]],
    empirically_checked_claims: set[str],
    legally_checked_claims: set[str],
    implementation_mechanisms: list[dict[str, str]],
    implementation_contexts: list[dict[str, str]],
    implementation_gaps: list[dict[str, str]],
    package_relations: list[dict[str, str]],
    priority_reviews: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    family_names = {row["control_family_id"]: row["family_name"] for row in families}
    claims_by_implementation: dict[str, set[str]] = defaultdict(set)
    effects_by_implementation: dict[str, set[str]] = defaultdict(set)
    legal_claims_by_implementation: dict[str, set[str]] = defaultdict(set)
    mechanism_claims_by_implementation: dict[str, set[str]] = defaultdict(set)
    sources_by_implementation: dict[str, set[str]] = defaultdict(set)
    mechanisms_by_implementation: dict[str, set[str]] = defaultdict(set)
    contexts_by_implementation: dict[str, set[str]] = defaultdict(set)
    gaps_by_implementation: dict[str, set[str]] = defaultdict(set)
    packages_by_implementation: dict[str, set[str]] = defaultdict(set)

    for relation in implementation_claims:
        implementation_id = relation["implementation_id"]
        claim_id = relation["claim_id"]
        claims_by_implementation[implementation_id].add(claim_id)
        sources_by_implementation[implementation_id].update(claim_sources.get(claim_id, set()))
        if claim_types.get(claim_id) == "Control effectiveness":
            effects_by_implementation[implementation_id].add(claim_id)
        if claim_types.get(claim_id) == "Legal status / scope":
            legal_claims_by_implementation[implementation_id].add(claim_id)
        if claim_types.get(claim_id) == "Mechanism":
            mechanism_claims_by_implementation[implementation_id].add(claim_id)
    for relation in implementation_mechanisms:
        mechanisms_by_implementation[relation["implementation_id"]].add(relation["mechanism_id"])
    for relation in implementation_contexts:
        contexts_by_implementation[relation["implementation_id"]].add(relation["entity_id"])
    for relation in implementation_gaps:
        gaps_by_implementation[relation["implementation_id"]].add(relation["gap_id"])
    for relation in package_relations:
        packages_by_implementation[relation["implementation_id"]].add(relation["package_id"])

    output = []
    for implementation in implementations:
        implementation_id = implementation["implementation_id"]
        effect_claims = effects_by_implementation.get(implementation_id, set())
        checked_effects = {
            claim_id for claim_id in effect_claims if claim_id in empirically_checked_claims
        }
        legal_claims = legal_claims_by_implementation.get(implementation_id, set())
        checked_legal_claims = {
            claim_id for claim_id in legal_claims if claim_id in legally_checked_claims
        }
        mechanism_claims = mechanism_claims_by_implementation.get(implementation_id, set())
        checked_mechanism_claims = {
            claim_id
            for claim_id in mechanism_claims
            if claim_statuses.get(claim_id) == "claim_checked"
        }
        reviewed_effects = [
            priority_reviews[claim_id]
            for claim_id in sorted(effect_claims)
            if claim_id in priority_reviews
        ]
        row = dict(implementation)
        row["family_name"] = family_names.get(implementation["control_family_id"], "")
        row["mechanism_ids"] = join_ids(mechanisms_by_implementation.get(implementation_id, set()))
        row["context_entity_ids"] = join_ids(
            contexts_by_implementation.get(implementation_id, set())
        )
        row["research_gap_ids"] = join_ids(gaps_by_implementation.get(implementation_id, set()))
        row["claim_ids"] = join_ids(claims_by_implementation.get(implementation_id, set()))
        row["effect_claim_ids"] = join_ids(effect_claims)
        row["legal_claim_ids"] = join_ids(legal_claims)
        row["mechanism_claim_ids"] = join_ids(mechanism_claims)
        row["source_ids"] = join_ids(sources_by_implementation.get(implementation_id, set()))
        row["policy_package_ids"] = join_ids(
            packages_by_implementation.get(implementation_id, set())
        )
        row["effect_claim_checked"] = "true" if checked_effects else "false"
        row["legal_claim_checked"] = "true" if checked_legal_claims else "false"
        row["mechanism_claim_checked"] = "true" if checked_mechanism_claims else "false"
        row["effect_claim_reviewed"] = "true" if reviewed_effects else "false"
        row["priority_effect_review_outcomes"] = join_ids(
            [review["review_outcome"] for review in reviewed_effects]
        )
        row["priority_effect_publication_actions"] = join_ids(
            [review["publication_action"] for review in reviewed_effects]
        )
        if (
            implementation["claim_class"] == "Established — component effect"
            and not checked_effects
        ):
            row["publication_claim_class"] = "Provisional — effect evidence not claim-checked"
        elif (
            implementation["claim_class"] == "Established — legal status"
            and not checked_legal_claims
        ):
            row["publication_claim_class"] = "Provisional — legal status not claim-checked"
        elif (
            implementation["claim_class"] == "Established — project mechanism"
            and not checked_mechanism_claims
        ):
            row["publication_claim_class"] = "Provisional — project mechanism not claim-checked"
        else:
            row["publication_claim_class"] = implementation["claim_class"]
        row.pop("decision_tier")
        row["publication_decision_posture"] = "not_assessed"
        row["publication_status"] = "research_preview"
        output.append(row)
    return output


def build_stable_core_views(
    atlas: list[dict[str, str]],
    selection_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Join the provisional selection to readiness fields and retain the complement."""

    selection_by_id = {row["implementation_id"]: row for row in selection_rows}
    core_candidates: list[dict[str, str]] = []
    candidate_registry: list[dict[str, str]] = []

    for atlas_row in atlas:
        implementation_id = atlas_row["implementation_id"]
        selected = selection_by_id.get(implementation_id)
        if selected:
            row = dict(selected)
            for field in (
                "jurisdiction",
                "legal_force",
                "legal_status",
                "operational_maturity",
                "publication_claim_class",
                "effect_claim_checked",
                "legal_claim_checked",
                "mechanism_claim_checked",
                "publication_decision_posture",
                "effect_claim_ids",
                "legal_claim_ids",
                "mechanism_claim_ids",
                "source_ids",
            ):
                row[field] = atlas_row[field]
            row["claim_disposition_status"] = "incomplete"
            row["gate_assessment_status"] = "not_assessed"
            row["independent_review_status"] = "pending"
            row["stable_core_admission_status"] = "blocked_pending_verification"
            row["ranking_ready"] = "false"
            core_candidates.append(row)
        else:
            candidate_registry.append(
                {
                    "implementation_id": implementation_id,
                    "control_family_id": atlas_row["control_family_id"],
                    "intervention": atlas_row["intervention"],
                    "jurisdiction": atlas_row["jurisdiction"],
                    "operational_maturity": atlas_row["operational_maturity"],
                    "publication_claim_class": atlas_row["publication_claim_class"],
                    "publication_decision_posture": atlas_row["publication_decision_posture"],
                    "registry_status": "candidate_registry",
                    "verification_wave": "outside_stable_core_selection_v0.1",
                    "rank_eligibility": "not_assessed_outside_core_wave",
                    "nonselection_meaning": (
                        "Outside this verification wave; not rejected and not "
                        "evidence of ineffectiveness"
                    ),
                }
            )

    return core_candidates, candidate_registry


def main() -> None:
    if RELEASE.exists():
        shutil.rmtree(RELEASE)
    (RELEASE / "data" / "core").mkdir(parents=True)
    (RELEASE / "data" / "relations").mkdir(parents=True)
    (RELEASE / "data" / "derived").mkdir(parents=True)
    (RELEASE / "manifests").mkdir(parents=True)

    families = load_table("intervention_families.csv")
    implementations = load_table("implementations.csv")
    claims = load_table("claims.csv")
    sources = load_table("sources.csv")
    packages = load_table("policy_packages.csv")
    implementation_claims = load_table("implementation_claims.csv")
    implementation_mechanisms = load_table("implementation_mechanisms.csv")
    implementation_contexts = load_table("implementation_cases.csv")
    implementation_gaps = load_table("implementation_gaps.csv")
    priority_review_rows = read_csv(PRIORITY_REVIEW)
    priority_reviews = {row["claim_id"]: row for row in priority_review_rows}
    stable_release_gates = read_csv(STABLE_RELEASE_GATES)
    stable_core_selection = read_csv(STABLE_CORE_SELECTION)

    claim_sources_raw = load_table("claim_sources.csv")
    claim_sources = deduplicate_claim_sources(claim_sources_raw)
    claim_types = {row["claim_id"]: row["claim_type"] for row in claims}
    public_claim_sources = annotate_claim_source_relations(claim_sources, claim_types)
    public_claims, claim_statuses, sources_by_claim = claim_verification(claims, claim_sources)
    empirically_checked_claim_ids = {
        relation["claim_id"]
        for relation in claim_sources
        if relation["verification_level"] == "Claim checked — empirical source"
        and relation["support_relation"] == "Supports"
    }
    legally_checked_claim_ids = {
        relation["claim_id"]
        for relation in claim_sources
        if (
            relation["verification_level"]
            in {
                "Claim checked — primary legal source",
                "Claim checked — primary official policy source",
            }
            and relation["support_relation"] == "Supports"
        )
    }
    public_sources = []
    checked_source_ids_in_relations = {
        relation["source_id"]
        for relation in public_claim_sources
        if relation["publication_relation_status"] == "claim_support_checked"
    }
    for source in sources:
        row = dict(source)
        row["publication_status"] = (
            "used_in_claim_checked_relation"
            if source["source_id"] in checked_source_ids_in_relations
            else "candidate_source"
        )
        public_sources.append(row)

    package_relations = build_package_relations(packages)
    atlas = build_atlas(
        implementations,
        families,
        implementation_claims,
        claim_types,
        claim_statuses,
        sources_by_claim,
        empirically_checked_claim_ids,
        legally_checked_claim_ids,
        implementation_mechanisms,
        implementation_contexts,
        implementation_gaps,
        package_relations,
        priority_reviews,
    )
    stable_selection_by_id = {row["implementation_id"]: row for row in stable_core_selection}
    for row in atlas:
        selected = stable_selection_by_id.get(row["implementation_id"])
        if selected:
            row["verification_wave"] = "proposed_stable_core_v0.1"
            row["stable_core_selection_status"] = selected["inclusion_status"]
            row["rank_eligibility"] = selected["rank_eligibility"]
        else:
            row["verification_wave"] = "candidate_registry"
            row["stable_core_selection_status"] = "candidate_registry"
            row["rank_eligibility"] = "not_assessed_outside_core_wave"
        row["stable_core_ready"] = "false"
        row["ranking_ready"] = "false"

    stable_core_candidates, candidate_registry = build_stable_core_views(
        atlas,
        stable_core_selection,
    )

    for source_name, release_name in CORE_FILES.items():
        if source_name == "claims.csv":
            rows = public_claims
        elif source_name == "sources.csv":
            rows = public_sources
        elif source_name == "intervention_families.csv":
            rows = with_withheld_decision_posture(
                load_table(source_name),
                "decision_posture",
                "working_register_decision_posture",
            )
        elif source_name in {"implementations.csv", "policy_packages.csv"}:
            rows = with_withheld_decision_posture(
                load_table(source_name),
                "decision_tier",
                "working_register_decision_tier",
            )
        else:
            rows = load_table(source_name)
        write_csv(RELEASE / "data" / "core" / release_name, rows)

    for source_name, release_name in RELATION_FILES.items():
        write_csv(
            RELEASE / "data" / "relations" / release_name,
            load_table(source_name),
        )

    write_csv(
        RELEASE / "data" / "relations" / "claim_sources.csv",
        public_claim_sources,
    )
    write_csv(
        RELEASE / "data" / "relations" / "package_implementations.csv",
        package_relations,
    )
    write_csv(RELEASE / "data" / "derived" / "atlas.csv", atlas)
    write_csv(
        RELEASE / "data" / "derived" / "stable_core_candidates.csv",
        stable_core_candidates,
    )
    write_csv(
        RELEASE / "data" / "derived" / "candidate_registry.csv",
        candidate_registry,
    )
    write_csv(
        RELEASE / "data" / "core" / "priority_claim_reviews.csv",
        priority_review_rows,
    )
    write_csv(
        RELEASE / "data" / "core" / "stable_release_gates.csv",
        stable_release_gates,
    )

    effect_claims = [row for row in public_claims if row["claim_type"] == "Control effectiveness"]
    checked_effect_claims = [
        row for row in effect_claims if row["claim_id"] in empirically_checked_claim_ids
    ]
    established_legal_implementations = [
        row for row in atlas if row["claim_class"] == "Established — legal status"
    ]
    checked_legal_implementations = [
        row for row in established_legal_implementations if row["legal_claim_checked"] == "true"
    ]
    established_project_mechanisms = [
        row for row in atlas if row["claim_class"] == "Established — project mechanism"
    ]
    checked_project_mechanisms = [
        row for row in established_project_mechanisms if row["mechanism_claim_checked"] == "true"
    ]
    duplicate_edges_removed = len(claim_sources_raw) - len(claim_sources)
    checked_source_records = [
        row for row in sources if row["source_id"] in checked_source_ids_in_relations
    ]
    unchecked_source_records = len(sources) - len(checked_source_records)
    checked_relations = [
        row
        for row in public_claim_sources
        if row["publication_relation_status"] == "claim_support_checked"
    ]
    mechanism_claims = [row for row in public_claims if row["claim_type"] == "Mechanism"]
    checked_mechanism_claims = [
        row for row in mechanism_claims if row["publication_verification_status"] == "claim_checked"
    ]
    unchecked_effect_claims = len(effect_claims) - len(checked_effect_claims)
    blocked_stable_gates = [row for row in stable_release_gates if row["status"] == "blocked"]
    rank_eligible_core_candidates = [
        row for row in stable_core_candidates if row["rank_eligibility"] == "eligible"
    ]

    files = sorted(
        path
        for path in RELEASE.rglob("*")
        if path.is_file() and path.name not in {"release.json", "checksums.sha256"}
    )
    manifest = {
        "artifact": "Agency Transfer Policy Atlas",
        "artifact_version": VERSION.removeprefix("v"),
        "release_stage": "research-preview",
        "source_snapshot_version": "sheets-v0.3",
        "curation_version": CURATION_VERSION,
        "curation_as_of_date": "2026-08-14",
        "stable_core_selection_version": STABLE_CORE_SELECTION_VERSION,
        "stable_core_source_version": STABLE_CORE_SOURCE_VERSION,
        "stable_core_source_manifest_sha256": STABLE_CORE_SOURCE_MANIFEST_SHA256,
        "ranking_protocol_version": RANKING_PROTOCOL_VERSION,
        "ranking_preregistration_status": "draft_not_preregistered",
        "source_spreadsheet_id": "1uL9hoNdWo_5PMEmgFnBkUrNHJSB9Hd53YTNqJYIrqYY",
        "source_as_of_date": "2026-08-11",
        "release_prepared_on": "2026-08-15",
        "formats": ["csv"],
        "stable_release_ready": False,
        "stable_release_blockers": [
            f"{unchecked_source_records} of {len(sources)} source records do not "
            "participate in a checked claim-source relation",
            f"{unchecked_effect_claims} of {len(effect_claims)} control-effectiveness "
            "claims lack a checked empirical source",
            f"{len(established_legal_implementations) - len(checked_legal_implementations)} "
            f"of {len(established_legal_implementations)} established legal-status "
            "implementations lack a checked primary-legal claim",
            f"{len(established_project_mechanisms) - len(checked_project_mechanisms)} "
            f"of {len(established_project_mechanisms)} project-mechanism "
            "implementations lack claim-specific verification",
            f"{len(blocked_stable_gates)} of {len(stable_release_gates)} "
            "machine-readable stable-release gates are blocked",
            f"{len(stable_core_candidates)} proposed stable-core candidates remain "
            "blocked pending verification and human review",
            f"{len(stable_core_candidates) - len(rank_eligible_core_candidates)} of "
            f"{len(stable_core_candidates)} proposed core candidates are not "
            "rank-eligible",
            f"{len(implementations)} of {len(implementations)} public implementation "
            "decision postures remain not assessed because gate assessments are "
            "incomplete",
            "portfolio packages require independent review",
            "context entities require stable links to the Part 3 dataset",
        ],
        "counts": {
            "control_families": len(families),
            "implementations": len(implementations),
            "claims": len(claims),
            "sources": len(sources),
            "mechanisms": len(load_table("mechanisms.csv")),
            "legal_instruments": len(load_table("legal_instruments.csv")),
            "policy_packages": len(packages),
            "decision_gates": len(load_table("decision_gates.csv")),
            "context_entities": len(load_table("case_index.csv")),
            "research_gaps": len(load_table("research_gaps.csv")),
            "claim_source_rows_raw": len(claim_sources_raw),
            "claim_source_edges_unique": len(claim_sources),
            "duplicate_claim_source_edges_removed": duplicate_edges_removed,
            "control_effectiveness_claims": len(effect_claims),
            "control_effectiveness_claims_checked": len(checked_effect_claims),
            "source_records_checked": len(checked_source_records),
            "source_records_pending_claim_check": unchecked_source_records,
            "claim_source_edges_checked": len(checked_relations),
            "mechanism_claims": len(mechanism_claims),
            "mechanism_claims_checked": len(checked_mechanism_claims),
            "established_legal_status_implementations": len(established_legal_implementations),
            "established_legal_status_implementations_checked": len(checked_legal_implementations),
            "established_project_mechanism_implementations": len(established_project_mechanisms),
            "established_project_mechanism_implementations_checked": len(
                checked_project_mechanisms
            ),
            "priority_effect_claims_reviewed": len(priority_review_rows),
            "stable_release_gates": len(stable_release_gates),
            "stable_release_gates_blocked": len(blocked_stable_gates),
            "proposed_stable_core_candidates": len(stable_core_candidates),
            "candidate_registry_implementations": len(candidate_registry),
            "rank_eligible_core_candidates": len(rank_eligible_core_candidates),
            "publication_decision_postures_assessed": 0,
        },
        "claim_boundary": (
            "Legal existence, mechanism plausibility, and control effectiveness "
            "are separate. This preview is not evidence that the mapped controls work."
        ),
        "files": {},
    }

    for path in files:
        relative = path.relative_to(RELEASE).as_posix()
        manifest["files"][relative] = {
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        }

    manifest_path = RELEASE / "manifests" / "release.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    checksum_paths = [*files, manifest_path]
    checksums = "\n".join(
        f"{sha256(path)}  {path.relative_to(RELEASE).as_posix()}" for path in checksum_paths
    )
    (RELEASE / "manifests" / "checksums.sha256").write_text(checksums + "\n", encoding="utf-8")

    print(json.dumps(manifest["counts"], indent=2))
    print(f"Built {RELEASE}")


if __name__ == "__main__":
    main()
