#!/usr/bin/env python3
"""Validate the Policy Atlas source snapshot and generated research preview."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from curation import load_table
from release_config import CURATION_VERSION, VERSION


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "draft-v0.3"
PRIORITY_REVIEW = ROOT / "review" / "priority_claim_review.csv"
RELEASE = ROOT / "release" / VERSION
PRIORITY_CLAIM_IDS = {
    "CLM-0016",
    "CLM-0115",
    "CLM-0181",
    "CLM-0184",
    "CLM-0232",
    "CLM-0235",
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
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        output[relative] = digest
    return output


def unique_ids(check: Validation, rows: list[dict[str, str]], field: str, pattern: str, table: str) -> set[str]:
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


def controlled(check: Validation, rows: list[dict[str, str]], field: str, allowed: set[str]) -> None:
    invalid = sorted({row[field] for row in rows if row[field] not in allowed})
    check.require(not invalid, f"implementations: invalid {field}: {invalid}")


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
    implementation_ids = unique_ids(check, implementations, "implementation_id", r"I-\d{3}", "implementations")
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
    package_ids = unique_ids(check, packages, "package_id", r"(?:G0|P\d{2})", "policy packages")
    review_claim_ids = unique_ids(
        check,
        priority_reviews,
        "claim_id",
        r"CLM-\d{4}",
        "priority claim reviews",
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
    foreign_keys(check, implementation_claims, "implementation_id", implementation_ids, "implementation_claims")
    foreign_keys(check, implementation_claims, "claim_id", claim_ids, "implementation_claims")
    foreign_keys(check, implementation_mechanisms, "implementation_id", implementation_ids, "implementation_mechanisms")
    foreign_keys(check, implementation_mechanisms, "mechanism_id", mechanism_ids, "implementation_mechanisms")
    foreign_keys(check, implementation_contexts, "implementation_id", implementation_ids, "implementation_contexts")
    foreign_keys(check, implementation_contexts, "entity_id", context_ids, "implementation_contexts")
    foreign_keys(check, implementation_gaps, "implementation_id", implementation_ids, "implementation_gaps")
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
    check.require(linked_claims == implementation_ids, "not every implementation has a claim relation")
    check.require(linked_mechanisms == implementation_ids, "not every implementation has a mechanism relation")

    for package in packages:
        members = {item.strip() for item in package["implementation_ids"].split(";") if item.strip()}
        check.require(members <= implementation_ids, f"{package['package_id']}: invalid implementation member")

    controlled(check, implementations, "legal_force", {
        "Binding", "Binding — limited scope", "Binding — phased",
        "Mandatory administrative policy — limited scope", "Mixed",
        "Non-binding official guidance", "Voluntary / private",
        "Planned / no legal force", "Proposed", "Research",
    })
    controlled(check, implementations, "operational_maturity", {
        "Operational", "Partial / uneven", "Pilot", "Design-ready", "Research", "Not applicable yet",
    })
    controlled(check, implementations, "mechanism_evidence_tier", {
        "Project-C", "Project-X", "E0", "E1", "E2", "E3", "None",
    })
    controlled(check, implementations, "decision_tier", {
        "Enforce now", "Implement now", "Prepare", "Pilot", "Research / hold", "Monitor / shape",
    })

    urls = [row["direct_url"].strip() for row in sources]
    check.require(all(re.fullmatch(r"https?://\S+", url) for url in urls), "sources: invalid URL")
    check.require(len(urls) == len(set(urls)), "sources: duplicate canonical URL")

    pairs = [(row["claim_id"], row["source_id"]) for row in claim_sources]
    duplicate_pairs = len(pairs) - len(set(pairs))
    check.warn(duplicate_pairs == 0, f"source snapshot has {duplicate_pairs} duplicate claim-source rows; release must deduplicate")

    empirically_checked_claims = {
        row["claim_id"]
        for row in claim_sources
        if row["verification_level"] == "Claim checked — empirical source"
    }
    checked_levels = {
        "Claim checked — primary legal source",
        "Claim checked — primary official policy source",
        "Claim checked — empirical source",
    }
    effect_claims = effect_claims_by_type
    checked_effect_claims = empirically_checked_claims & effect_claims
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
        f"{len(missing_legal_sources)} legal instruments have no source_id: {missing_legal_sources}",
    )

    release_manifest = RELEASE / "manifests" / "release.json"
    check.require(release_manifest.exists(), "generated release manifest missing; run build_release.py")
    if release_manifest.exists():
        manifest = json.loads(release_manifest.read_text(encoding="utf-8"))
        check.require(
            manifest.get("artifact_version") == expected_package_version,
            "manifest artifact version mismatch",
        )
        check.require(manifest["stable_release_ready"] is False, "beta must not claim stable release readiness")
        check.require(
            manifest.get("curation_version") == CURATION_VERSION,
            "manifest curation version mismatch",
        )
        check.require(
            manifest["counts"]["control_effectiveness_claims_checked"] == len(checked_effect_claims),
            "manifest checked-effect count mismatch",
        )
        check.require(
            manifest["counts"]["priority_effect_claims_reviewed"] == len(priority_reviews),
            "manifest priority-review count mismatch",
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
                check.require(path.stat().st_size == metadata["bytes"], f"byte-size mismatch: {relative}")
        data_files = {
            path.relative_to(RELEASE).as_posix()
            for path in (RELEASE / "data").rglob("*")
            if path.is_file()
        }
        csv_files = {path for path in data_files if path.endswith(".csv")}
        parquet_files = {path for path in data_files if path.endswith(".parquet")}
        if set(manifest.get("formats", [])) == {"csv", "parquet"}:
            check.require(
                {path.removesuffix(".csv") for path in csv_files}
                == {path.removesuffix(".parquet") for path in parquet_files},
                "CSV/Parquet table parity mismatch",
            )
        else:
            check.require(
                manifest.get("formats") == ["csv"] and not parquet_files,
                "intermediate release must contain CSV only",
            )
        checksums_path = RELEASE / "manifests" / "checksums.sha256"
        check.require(checksums_path.exists(), "checksum manifest missing")
        if checksums_path.exists():
            checksums = read_checksums(checksums_path)
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
