#!/usr/bin/env python3
"""Build a deterministic local Zenodo bundle after the stable gates pass.

This module deliberately contains no network or deposition code. The command
line entry point always reads VERSION from release_config.py and validates that
version's release manifest before it writes anything.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from public_contract import PUBLIC_TABLE_STEMS, validate_csv_contract
from release_config import VERSION

ROOT = Path(__file__).resolve().parents[1]
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
STABLE_VERSION = re.compile(r"v[1-9][0-9]*\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
SHA256 = re.compile(r"[0-9a-f]{64}")
ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
FORBIDDEN_PATH_PARTS = {"logs", "raw", "private", "scans"}
FORBIDDEN_FILE_NAMES = {".env", ".npmrc", "credentials.json", "secrets.json"}
CREDENTIAL_PATTERN = re.compile(
    r"(?:\bsk-[A-Za-z0-9_-]{20,}|\bhf_[A-Za-z0-9]{20,}|"
    r"\bgh[pousr]_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}|"
    r"\b(?:AKIA|ASIA)[A-Z0-9]{16}|\bxox[baprs]-[A-Za-z0-9-]{10,}|"
    r"\bAIza[0-9A-Za-z_-]{35}|\bnpm_[A-Za-z0-9]{36}|"
    r"\b(?:sk|rk)_(?:live|test)_[0-9A-Za-z]{16,}|"
    r"bearer\s+[A-Za-z0-9._-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)",
    re.IGNORECASE,
)
REQUIRED_SIGNOFF_ROLES = {"evidence", "legal", "methods", "independent", "release"}
ZENODO_DOI = re.compile(r"10\.5281/zenodo\.[0-9]+")

DOCUMENTATION_FILES = (
    "README.md",
    "METHODS.md",
    "DATA_DICTIONARY.md",
    "PUBLICATION_STATUS.md",
    "CHANGELOG.md",
    "CITATION.cff",
    "DOI_RELEASE.md",
)
GOVERNANCE_FILES = (
    "GOVERNANCE.md",
    "CONTRIBUTING.md",
    "MAINTAINERS.md",
    "CODE_OF_CONDUCT.md",
    "CORRECTIONS.md",
)
LICENSE_FILES = (
    "LICENSE",
    "LICENSES/Apache-2.0.txt",
    "LICENSES/CODE",
    "LICENSES/DATA.md",
)
SUPPORT_FILES = (
    "protocol/RANKING_PROTOCOL.md",
    "protocol/STABLE_CORE_SELECTION.md",
    "schemas/atlas.schema.json",
    "schemas/candidate-registry.schema.json",
    "schemas/claim.schema.json",
    "schemas/implementation.schema.json",
    "schemas/public-implementation.schema.json",
    "schemas/public-table-columns.json",
    "schemas/release-manifest.schema.json",
    "schemas/source.schema.json",
    "schemas/stable-core-candidate.schema.json",
    "schemas/stable-release-gate.schema.json",
    "review/PRIORITY_VERIFICATION.md",
    "review/priority_claim_review.csv",
    "review/stable_release_gates.csv",
)
REQUIRED_PROTOCOL_FILES = (
    "protocol/STABLE_CORE_SELECTION.md",
    "protocol/RANKING_PROTOCOL.md",
)
REPRODUCIBILITY_FILES = (
    "package.json",
    "package-lock.json",
    "scripts/build_parquet.cjs",
    "scripts/build_release.py",
    "scripts/curation.py",
    "scripts/prepare_hf_release.py",
    "scripts/prepare_zenodo_bundle.py",
    "scripts/public_contract.py",
    "scripts/publish_hf.py",
    "scripts/release_config.py",
    "scripts/validate_release.py",
    "tests/test_policy_atlas.py",
    "tests/test_zenodo_bundle.py",
    "data/draft-v0.3/case_index.csv",
    "data/draft-v0.3/changelog.csv",
    "data/draft-v0.3/claim_sources.csv",
    "data/draft-v0.3/claims.csv",
    "data/draft-v0.3/codebook.csv",
    "data/draft-v0.3/decision_gates.csv",
    "data/draft-v0.3/implementation_cases.csv",
    "data/draft-v0.3/implementation_claims.csv",
    "data/draft-v0.3/implementation_findings.csv",
    "data/draft-v0.3/implementation_gaps.csv",
    "data/draft-v0.3/implementation_mechanisms.csv",
    "data/draft-v0.3/implementations.csv",
    "data/draft-v0.3/intervention_families.csv",
    "data/draft-v0.3/legal_instruments.csv",
    "data/draft-v0.3/mechanisms.csv",
    "data/draft-v0.3/policy_packages.csv",
    "data/draft-v0.3/project_findings.csv",
    "data/draft-v0.3/research_gaps.csv",
    "data/draft-v0.3/sources.csv",
    "data/draft-v0.3/verification_log.csv",
    "data/curation-v0.4/README.md",
    "data/curation-v0.4/claim_corrections.csv",
    "data/curation-v0.4/claim_source_additions.csv",
    "data/curation-v0.4/claim_source_corrections.csv",
    "data/curation-v0.4/implementation_claim_corrections.csv",
    "data/curation-v0.4/implementation_corrections.csv",
    "data/curation-v0.4/legal_implementation_corrections.csv",
    "data/curation-v0.4/legal_instrument_corrections.csv",
    "data/curation-v0.4/source_additions.csv",
    "data/curation-v0.4/source_corrections.csv",
    "data/curation-v0.5/README.md",
    "data/curation-v0.5/stable_core_selection.csv",
    "data/ranking-v0.1/README.md",
    "data/ranking-v0.1/analysis_runs.csv",
    "data/ranking-v0.1/criterion_definitions.csv",
    "data/ranking-v0.1/criterion_scores.csv",
    "data/ranking-v0.1/implementation_gate_assessments.csv",
    "data/ranking-v0.1/pairwise_results.csv",
    "data/ranking-v0.1/protocol_deviations.csv",
    "data/ranking-v0.1/rank_acceptability.csv",
    "data/ranking-v0.1/rank_results.csv",
    "data/ranking-v0.1/ranking_scenarios.csv",
    "data/ranking-v0.1/review_signoffs.csv",
    "data/ranking-v0.1/scenario_candidates.csv",
    "data/ranking-v0.1/sensitivity_plans.csv",
    "data/ranking-v0.1/sensitivity_results.csv",
    "data/ranking-v0.1/weight_scenarios.csv",
)
REPOSITORY_LEVEL_FILES = {
    "environment/pyproject.toml": "pyproject.toml",
    "environment/uv.lock": "uv.lock",
}


class BundleError(RuntimeError):
    """A release is ineligible for a preservation bundle."""


def git_output(repository: Path, *arguments: str) -> str:
    """Run one read-only Git query and translate failures into a closed gate."""

    try:
        result = subprocess.run(
            ["git", "-C", str(repository), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        detail = ""
        if isinstance(error, subprocess.CalledProcessError):
            detail = (error.stderr or error.stdout or "").strip()
        suffix = f": {detail}" if detail else ""
        raise BundleError(f"Git repository-state check failed{suffix}") from error
    return result.stdout.strip()


def resolve_repository_state(root: Path, version: str) -> str:
    """Require a clean, tagged commit for every file class preserved in the ZIP."""

    repository = Path(git_output(root, "rev-parse", "--show-toplevel")).resolve()
    try:
        atlas_relative = root.resolve().relative_to(repository).as_posix()
    except ValueError as error:
        raise BundleError("Policy Atlas root is outside the Git repository") from error
    head = git_output(repository, "rev-parse", "HEAD")
    if re.fullmatch(r"[0-9a-f]{40}", head) is None:
        raise BundleError("Git HEAD did not resolve to a full commit SHA")
    tag_commit = git_output(repository, "rev-parse", f"refs/tags/{version}^{{commit}}")
    if tag_commit != head:
        raise BundleError(f"Git tag {version} does not point to the exact repository HEAD")
    relevant_status = git_output(
        repository,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        atlas_relative,
        "pyproject.toml",
        "uv.lock",
    )
    if relevant_status:
        raise BundleError("preservation inputs are not clean at the tagged repository commit")
    return head


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative_path(value: str) -> str:
    """Return a canonical POSIX path or reject unsafe inventory input."""

    if not value or "\\" in value or "\x00" in value:
        raise BundleError(f"unsafe inventory path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value:
        raise BundleError(f"non-canonical inventory path: {value!r}")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise BundleError(f"unsafe inventory path: {value!r}")
    return value


def regular_file_inventory(directory: Path) -> dict[str, Path]:
    if not directory.is_dir() or directory.is_symlink():
        raise BundleError(f"required directory is missing or is a symlink: {directory}")
    inventory: dict[str, Path] = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise BundleError(f"symlinks are not allowed in a preservation bundle: {path}")
        if path.is_file():
            relative = path.relative_to(directory).as_posix()
            safe_relative_path(relative)
            inventory[relative] = path
        elif not path.is_dir():
            raise BundleError(f"unsupported filesystem entry: {path}")
    return inventory


def load_manifest(root: Path, version: str) -> tuple[Path, dict[str, Any]]:
    release_directory = root / "release" / version
    manifest_path = release_directory / "manifests" / "release.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise BundleError(f"release manifest is missing: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BundleError(f"release manifest cannot be read: {error}") from error
    if not isinstance(manifest, dict):
        raise BundleError("release manifest must be a JSON object")
    return release_directory, manifest


def validate_stable_gate(version: str, manifest: dict[str, Any]) -> None:
    stage = manifest.get("release_stage")
    ready = manifest.get("stable_release_ready")
    if stage != "stable" or ready is not True:
        raise BundleError(
            "stable release gate is closed "
            f"(release_stage={stage!r}, stable_release_ready={ready!r})"
        )
    if STABLE_VERSION.fullmatch(version) is None:
        raise BundleError(f"stable release version must be final SemVer: {version!r}")
    expected_artifact_version = version.removeprefix("v")
    if manifest.get("artifact_version") != expected_artifact_version:
        raise BundleError("release manifest version does not match scripts/release_config.py")
    if manifest.get("artifact") != "Agency Transfer Policy Atlas":
        raise BundleError("release manifest names an unexpected artifact")
    blockers = manifest.get("stable_release_blockers")
    if not isinstance(blockers, list) or blockers:
        raise BundleError("stable release blockers must be present and empty")
    formats = manifest.get("formats")
    if not isinstance(formats, list) or set(formats) != {"csv", "parquet"}:
        raise BundleError("stable release must declare both CSV and Parquet formats")
    counts = manifest.get("counts")
    if (
        not isinstance(counts, dict)
        or counts.get("stable_release_gates") != 13
        or counts.get("stable_release_gates_blocked") != 0
    ):
        raise BundleError("stable manifest must record 13 gates and zero blocked gates")
    validate_human_signoffs(manifest)
    validate_reserved_doi(manifest)


def review_subject_sha256(manifest: dict[str, Any]) -> str:
    """Hash the manifest subject without the sign-off envelope itself."""

    subject = {key: value for key, value in manifest.items() if key != "human_review_signoffs"}
    serialized = json.dumps(
        subject, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def validate_reserved_doi(manifest: dict[str, Any]) -> None:
    doi = manifest.get("doi")
    if not isinstance(doi, dict) or doi.get("authority") != "Zenodo":
        raise BundleError("stable manifest must name Zenodo as its DOI authority")
    version_doi = doi.get("version_doi")
    concept_doi = doi.get("concept_doi")
    if not isinstance(version_doi, str) or ZENODO_DOI.fullmatch(version_doi) is None:
        raise BundleError("stable manifest lacks a valid reserved Zenodo version DOI")
    concept_status = doi.get("concept_doi_status")
    if concept_status == "known_existing_concept":
        if not isinstance(concept_doi, str) or ZENODO_DOI.fullmatch(concept_doi) is None:
            raise BundleError("stable manifest lacks a valid existing Zenodo concept DOI")
        if version_doi == concept_doi:
            raise BundleError("Zenodo version DOI and concept DOI must be distinct")
    elif concept_status == "pending_first_publication":
        if concept_doi is not None:
            raise BundleError("first-publication concept DOI must be null until Zenodo issues it")
    else:
        raise BundleError("stable manifest has an invalid concept DOI status")
    if doi.get("reservation_status") != "reserved_not_deposited":
        raise BundleError("stable DOI metadata must remain reserved_not_deposited")


def validate_human_signoffs(manifest: dict[str, Any]) -> None:
    signoffs = manifest.get("human_review_signoffs")
    if not isinstance(signoffs, list):
        raise BundleError("stable manifest is missing human review sign-offs")
    by_role: dict[str, dict[str, Any]] = {}
    for signoff in signoffs:
        if not isinstance(signoff, dict):
            raise BundleError("human review sign-offs must be objects")
        role = signoff.get("role")
        if role in by_role:
            raise BundleError(f"duplicate human review sign-off role: {role!r}")
        if isinstance(role, str):
            by_role[role] = signoff
    if set(by_role) != REQUIRED_SIGNOFF_ROLES:
        raise BundleError(
            "human review sign-off roles mismatch "
            f"(missing={sorted(REQUIRED_SIGNOFF_ROLES - set(by_role))}, "
            f"extra={sorted(set(by_role) - REQUIRED_SIGNOFF_ROLES)})"
        )
    placeholders = {"", "tbd", "todo", "vacant", "pending", "unassigned"}
    for role, signoff in by_role.items():
        reviewer_id = str(signoff.get("reviewer_id", "")).strip()
        signed_on = str(signoff.get("signed_on", "")).strip()
        if reviewer_id.lower() in placeholders:
            raise BundleError(f"{role} sign-off has no named reviewer identifier")
        if signoff.get("decision") != "approved":
            raise BundleError(f"{role} sign-off is not approved")
        if ISO_DATE.fullmatch(signed_on) is None:
            raise BundleError(f"{role} sign-off has an invalid signed_on date")
        if SHA256.fullmatch(str(signoff.get("review_subject_sha256", ""))) is None:
            raise BundleError(f"{role} sign-off lacks a preservation-subject SHA-256")
    if by_role["independent"]["reviewer_id"] == by_role["release"]["reviewer_id"]:
        raise BundleError("independent and release sign-offs must use different reviewers")


def validate_stable_gate_evidence(
    root: Path, release_directory: Path, manifest: dict[str, Any]
) -> dict[str, Path]:
    relative = "data/core/stable_release_gates.csv"
    if relative not in manifest.get("files", {}):
        raise BundleError("stable release does not inventory stable_release_gates.csv")
    release_path = release_directory / relative
    canonical_path = root / "review" / "stable_release_gates.csv"
    if canonical_path.is_symlink() or not canonical_path.is_file():
        raise BundleError("canonical stable-release gate ledger is missing or unsafe")
    if release_path.read_bytes() != canonical_path.read_bytes():
        raise BundleError(
            "released stable-release gate ledger differs from canonical review ledger"
        )
    try:
        with release_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except (OSError, UnicodeDecodeError, csv.Error) as error:
        raise BundleError(f"stable-release gate ledger cannot be read: {error}") from error
    expected_ids = {f"SR-{index:02d}" for index in range(1, 14)}
    if {row.get("gate_id") for row in rows} != expected_ids or len(rows) != 13:
        raise BundleError("stable-release gate ledger must contain SR-01 through SR-13 once")
    signoff_roles = {
        str(signoff["role"])
        for signoff in manifest["human_review_signoffs"]
        if isinstance(signoff, dict) and "role" in signoff
    }
    evidence_files: dict[str, Path] = {}
    for row in rows:
        expected_status = "ready_for_deposit" if row.get("gate_id") == "SR-13" else "satisfied"
        if row.get("status") != expected_status:
            raise BundleError(f"stable-release gate is not satisfied: {row.get('gate_id')}")
        evidence_relative = row.get("evidence_path", "").strip()
        evidence_digest = row.get("evidence_sha256", "").strip()
        if not evidence_relative:
            raise BundleError(f"stable-release gate lacks evidence: {row.get('gate_id')}")
        safe_relative_path(evidence_relative)
        if SHA256.fullmatch(evidence_digest) is None:
            raise BundleError(
                f"stable-release gate lacks an evidence SHA-256: {row.get('gate_id')}"
            )
        evidence_path = (
            release_directory / evidence_relative
            if evidence_relative.startswith("data/")
            else root / evidence_relative
        )
        if evidence_path.is_symlink() or not evidence_path.is_file():
            raise BundleError(
                f"stable-release gate evidence is missing or unsafe: {evidence_relative}"
            )
        if sha256_file(evidence_path) != evidence_digest:
            raise BundleError(f"stable-release gate evidence hash mismatch: {evidence_relative}")
        if (
            evidence_relative in evidence_files
            and evidence_files[evidence_relative] != evidence_path
        ):
            raise BundleError(f"ambiguous stable-release evidence path: {evidence_relative}")
        evidence_files[evidence_relative] = evidence_path
        signoff_required = row.get("human_signoff_required") == "true"
        signoff_role = row.get("human_signoff_role", "").strip()
        if signoff_required and signoff_role not in signoff_roles:
            raise BundleError(
                f"stable-release gate lacks its required sign-off role: {row.get('gate_id')}"
            )
        if not signoff_required and signoff_role:
            raise BundleError(
                "machine-only stable-release gate names a human sign-off role: "
                f"{row.get('gate_id')}"
            )
        if row.get("blocking_reason", "").strip():
            raise BundleError(
                f"satisfied stable-release gate retains a blocker: {row.get('gate_id')}"
            )
        if row.get("gate_id") == "SR-09":
            validate_stable_qa_report(root, evidence_path, manifest)
    return evidence_files


def stable_data_subject_sha256(manifest: dict[str, Any]) -> str:
    """Hash released data metadata without the gate ledger that cites the report."""

    files = manifest.get("files", {})
    if not isinstance(files, dict):
        raise BundleError("stable manifest file inventory is invalid")
    gate_paths = {
        "data/core/stable_release_gates.csv",
        "data/core/stable_release_gates.parquet",
    }
    subject = {key: files[key] for key in sorted(files) if key not in gate_paths}
    return hashlib.sha256(
        json.dumps(subject, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def validate_stable_qa_report(root: Path, report_path: Path, manifest: dict[str, Any]) -> None:
    """Require SR-09 to cite a machine-readable, release-bound zero-warning report."""

    if report_path.suffix.lower() != ".json":
        raise BundleError("SR-09 evidence must be a machine-readable JSON QA report")
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BundleError(f"SR-09 QA report cannot be parsed: {error}") from error
    if not isinstance(report, dict):
        raise BundleError("SR-09 QA report must be a JSON object")
    expected = {
        "artifact_version": manifest.get("artifact_version"),
        "release_data_subject_sha256": stable_data_subject_sha256(manifest),
        "validator_sha256": sha256_file(root / "scripts" / "validate_release.py"),
        "environment_lock_sha256": sha256_file(root.parent / "uv.lock"),
        "errors": 0,
        "warnings": 0,
        "csv_parquet_semantic_parity": True,
        "two_clean_builds_byte_identical": True,
        "fresh_checkout_validation_passed": True,
        "hf_viewer_smoke_test_passed": True,
    }
    for key, expected_value in expected.items():
        if report.get(key) != expected_value:
            raise BundleError(f"SR-09 QA report field {key!r} does not match the stable release")
    generated_at = report.get("generated_at")
    if not isinstance(generated_at, str) or not generated_at.strip():
        raise BundleError("SR-09 QA report lacks a generation timestamp")


def parse_checksum_inventory(path: Path) -> dict[str, str]:
    if path.is_symlink() or not path.is_file():
        raise BundleError(f"checksum inventory is missing: {path}")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise BundleError(f"checksum inventory cannot be read: {error}") from error
    if not lines:
        raise BundleError("checksum inventory is empty")
    checksums: dict[str, str] = {}
    for line_number, line in enumerate(lines, start=1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            raise BundleError(f"malformed checksum line {line_number}")
        digest, relative = match.groups()
        relative = safe_relative_path(relative)
        if relative in checksums:
            raise BundleError(f"duplicate checksum entry: {relative}")
        checksums[relative] = digest
    return checksums


def validate_release_inventory(
    release_directory: Path, manifest: dict[str, Any]
) -> dict[str, Path]:
    """Verify manifest metadata, checksum inventory, and directory completeness."""

    actual_files = regular_file_inventory(release_directory)
    manifest_files = manifest.get("files")
    if not isinstance(manifest_files, dict) or not manifest_files:
        raise BundleError("release manifest file inventory is missing or empty")

    declared_paths: set[str] = set()
    for raw_relative, metadata in manifest_files.items():
        if not isinstance(raw_relative, str):
            raise BundleError("release manifest file paths must be strings")
        relative = safe_relative_path(raw_relative)
        if relative in declared_paths:
            raise BundleError(f"duplicate manifest file entry: {relative}")
        declared_paths.add(relative)
        if not isinstance(metadata, dict):
            raise BundleError(f"invalid manifest metadata for {relative}")
        digest = metadata.get("sha256")
        byte_count = metadata.get("bytes")
        if not isinstance(digest, str) or SHA256.fullmatch(digest) is None:
            raise BundleError(f"invalid manifest SHA-256 for {relative}")
        if type(byte_count) is not int or byte_count <= 0:
            raise BundleError(f"invalid manifest byte count for {relative}")

    checksum_path = release_directory / "manifests" / "checksums.sha256"
    checksums = parse_checksum_inventory(checksum_path)
    expected_checksum_paths = declared_paths | {"manifests/release.json"}
    if set(checksums) != expected_checksum_paths:
        missing = sorted(expected_checksum_paths - set(checksums))
        extra = sorted(set(checksums) - expected_checksum_paths)
        raise BundleError(f"checksum inventory mismatch (missing={missing}, extra={extra})")

    expected_actual_paths = expected_checksum_paths | {"manifests/checksums.sha256"}
    if set(actual_files) != expected_actual_paths:
        missing = sorted(expected_actual_paths - set(actual_files))
        extra = sorted(set(actual_files) - expected_actual_paths)
        raise BundleError(f"release inventory mismatch (missing={missing}, extra={extra})")

    for relative in sorted(expected_checksum_paths):
        path = actual_files[relative]
        actual_digest = sha256_file(path)
        if actual_digest != checksums[relative]:
            raise BundleError(f"checksum mismatch for {relative}")
        if relative in manifest_files:
            metadata = manifest_files[relative]
            if metadata["sha256"] != actual_digest:
                raise BundleError(f"manifest checksum mismatch for {relative}")
            if metadata["bytes"] != path.stat().st_size:
                raise BundleError(f"manifest byte-count mismatch for {relative}")

    csv_stems = {
        PurePosixPath(path).with_suffix("").as_posix()
        for path in declared_paths
        if path.endswith(".csv")
    }
    parquet_stems = {
        PurePosixPath(path).with_suffix("").as_posix()
        for path in declared_paths
        if path.endswith(".parquet")
    }
    if not csv_stems or csv_stems != parquet_stems:
        raise BundleError("release CSV and Parquet table inventories do not match")
    if csv_stems != PUBLIC_TABLE_STEMS:
        raise BundleError("stable release table inventory differs from public contract")
    try:
        validate_csv_contract(release_directory)
    except ValueError as error:
        raise BundleError(f"stable release CSV contract violation: {error}") from error

    # The preservation gate independently opens every Parquet file and compares
    # typed cell semantics with its CSV twin. A signed report alone is not
    # sufficient evidence that the archived bytes are readable and equivalent.
    from validate_release import Validation, validate_csv_parquet_pair

    parity = Validation()
    for stem in sorted(csv_stems):
        validate_csv_parquet_pair(
            parity,
            release_directory / f"{stem}.csv",
            release_directory / f"{stem}.parquet",
            stem,
        )
    if parity.errors:
        raise BundleError(
            "stable release CSV/Parquet semantic validation failed: " + "; ".join(parity.errors)
        )

    row_counts: dict[str, int] = {}
    for stem in sorted(csv_stems):
        try:
            with (release_directory / f"{stem}.csv").open(newline="", encoding="utf-8") as handle:
                row_counts[stem] = sum(1 for _ in csv.DictReader(handle))
        except (OSError, UnicodeDecodeError, csv.Error) as error:
            raise BundleError(f"cannot count stable table {stem}: {error}") from error
    required_nonempty = PUBLIC_TABLE_STEMS - {"data/derived/candidate_registry"}
    empty_required = sorted(stem for stem in required_nonempty if row_counts[stem] == 0)
    if empty_required:
        raise BundleError(f"stable release has empty required tables: {empty_required}")
    if row_counts["data/derived/atlas"] != row_counts["data/core/implementations"]:
        raise BundleError("stable atlas row count must equal implementation count")
    if (
        row_counts["data/derived/stable_core_candidates"]
        + row_counts["data/derived/candidate_registry"]
        != row_counts["data/core/implementations"]
    ):
        raise BundleError("stable core and registry must partition implementations")
    if row_counts["data/core/stable_release_gates"] != 13:
        raise BundleError("stable release must contain exactly 13 release gates")
    if row_counts["data/relations/implementation_claims"] != row_counts["data/core/claims"]:
        raise BundleError("every stable claim must map to exactly one implementation")
    if row_counts["data/relations/claim_sources"] < row_counts["data/core/claims"]:
        raise BundleError("stable claims require a complete source/disposition relation ledger")

    def stable_rows(stem: str) -> list[dict[str, str]]:
        with (release_directory / f"{stem}.csv").open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    claims = stable_rows("data/core/claims")
    sources = stable_rows("data/core/sources")
    implementations = stable_rows("data/core/implementations")
    claim_sources = stable_rows("data/relations/claim_sources")
    implementation_claims = stable_rows("data/relations/implementation_claims")
    claim_ids = {row["claim_id"] for row in claims}
    source_ids = {row["source_id"] for row in sources}
    implementation_ids = {row["implementation_id"] for row in implementations}
    if len(claim_ids) != len(claims) or len(source_ids) != len(sources):
        raise BundleError("stable claims and sources require unique primary keys")
    if len(implementation_ids) != len(implementations):
        raise BundleError("stable implementations require unique primary keys")
    linked_claim_ids = {row["claim_id"] for row in claim_sources}
    linked_source_ids = {row["source_id"] for row in claim_sources}
    if linked_claim_ids != claim_ids or not linked_source_ids <= source_ids:
        raise BundleError("stable claim-source ledger has incomplete or orphan links")
    mapped_claim_ids = [row["claim_id"] for row in implementation_claims]
    mapped_implementation_ids = {row["implementation_id"] for row in implementation_claims}
    if (
        set(mapped_claim_ids) != claim_ids
        or len(mapped_claim_ids) != len(set(mapped_claim_ids))
        or not mapped_implementation_ids <= implementation_ids
    ):
        raise BundleError("stable implementation-claim ledger is incomplete or orphaned")

    count_contract = {
        "control_families": "data/core/intervention_families",
        "implementations": "data/core/implementations",
        "claims": "data/core/claims",
        "sources": "data/core/sources",
        "mechanisms": "data/core/mechanisms",
        "legal_instruments": "data/core/legal_instruments",
        "policy_packages": "data/core/policy_packages",
        "decision_gates": "data/core/decision_gates",
        "context_entities": "data/core/context_entities",
        "research_gaps": "data/core/research_gaps",
        "claim_source_edges_unique": "data/relations/claim_sources",
        "stable_release_gates": "data/core/stable_release_gates",
        "proposed_stable_core_candidates": "data/derived/stable_core_candidates",
        "candidate_registry_implementations": "data/derived/candidate_registry",
    }
    counts = manifest.get("counts", {})
    for key, stem in count_contract.items():
        if counts.get(key) != row_counts[stem]:
            raise BundleError(f"stable manifest count {key!r} does not match released rows")

    return actual_files


def collect_bundle_files(
    root: Path,
    release_files: dict[str, Path],
    gate_evidence_files: dict[str, Path],
) -> dict[str, Path]:
    """Collect the exact release and its required preservation context."""

    files = dict(release_files)

    required_files = DOCUMENTATION_FILES + GOVERNANCE_FILES + LICENSE_FILES
    for relative in required_files:
        safe_relative_path(relative)
        path = root / PurePosixPath(relative)
        if path.is_symlink() or not path.is_file():
            raise BundleError(f"required preservation file is missing: {relative}")
        if relative in files:
            raise BundleError(f"bundle path collision: {relative}")
        files[relative] = path

    for relative in SUPPORT_FILES:
        safe_relative_path(relative)
        path = root / PurePosixPath(relative)
        if path.is_symlink() or not path.is_file():
            raise BundleError(f"required preservation support file is missing: {relative}")
        if relative in files:
            raise BundleError(f"bundle path collision: {relative}")
        files[relative] = path

    for relative in REPRODUCIBILITY_FILES:
        safe_relative_path(relative)
        path = root / PurePosixPath(relative)
        if path.is_symlink() or not path.is_file():
            raise BundleError(f"required reproducibility file is missing: {relative}")
        if relative in files:
            raise BundleError(f"bundle path collision: {relative}")
        files[relative] = path

    for archive_relative, repository_relative in REPOSITORY_LEVEL_FILES.items():
        safe_relative_path(archive_relative)
        safe_relative_path(repository_relative)
        path = root.parent / PurePosixPath(repository_relative)
        if path.is_symlink() or not path.is_file():
            raise BundleError(
                f"required repository environment file is missing: {repository_relative}"
            )
        if archive_relative in files:
            raise BundleError(f"bundle path collision: {archive_relative}")
        files[archive_relative] = path

    for relative, path in gate_evidence_files.items():
        existing = files.get(relative)
        if existing is not None and existing.resolve() != path.resolve():
            raise BundleError(f"bundle path collision: {relative}")
        files[relative] = path

    for relative in REQUIRED_PROTOCOL_FILES:
        if relative not in files:
            raise BundleError(f"required protocol is missing: {relative}")

    return files


def preservation_subject_sha256(files: dict[str, Path], release_manifest: dict[str, Any]) -> str:
    """Hash all preservation inputs without the self-referential sign-off envelope."""

    excluded = {"manifests/release.json", "manifests/checksums.sha256"}
    inventory = {
        relative: sha256_file(path)
        for relative, path in sorted(files.items())
        if relative not in excluded
    }
    return preservation_subject_from_hashes(inventory, release_manifest)


def preservation_subject_from_hashes(
    inventory: dict[str, str], release_manifest: dict[str, Any]
) -> str:
    """Calculate the review digest from a canonical path-to-SHA inventory."""

    subject = {
        "release_manifest_subject_sha256": review_subject_sha256(release_manifest),
        "files": {relative: inventory[relative] for relative in sorted(inventory)},
    }
    return hashlib.sha256(
        json.dumps(subject, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def validate_signoff_subjects(manifest: dict[str, Any], files: dict[str, Path]) -> str:
    """Ensure every reviewer approved the exact data, methods, code, and docs."""

    expected = preservation_subject_sha256(files, manifest)
    for signoff in manifest["human_review_signoffs"]:
        if signoff.get("review_subject_sha256") != expected:
            raise BundleError(
                f"{signoff.get('role')} sign-off is not bound to the preservation subject"
            )
    return expected


def validate_archived_preservation_subject(
    archive: zipfile.ZipFile,
    archive_root: str,
    version: str,
    generated_inventory: dict[str, dict[str, Any]],
) -> None:
    """Revalidate approvals against the bytes actually written to the ZIP."""

    manifest_relative = "manifests/release.json"
    try:
        archived_manifest = json.loads(archive.read(f"{archive_root}/{manifest_relative}"))
    except (KeyError, json.JSONDecodeError) as error:
        raise BundleError(f"archived release manifest cannot be parsed: {error}") from error
    validate_stable_gate(version, archived_manifest)
    try:
        checksum_lines = (
            archive.read(f"{archive_root}/manifests/checksums.sha256").decode("utf-8").splitlines()
        )
    except (KeyError, UnicodeDecodeError) as error:
        raise BundleError(f"archived checksum inventory cannot be read: {error}") from error
    archived_checksums: dict[str, str] = {}
    for line_number, line in enumerate(checksum_lines, start=1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if match is None:
            raise BundleError(f"malformed archived checksum line {line_number}")
        digest, relative = match.groups()
        safe_relative_path(relative)
        if relative in archived_checksums:
            raise BundleError(f"duplicate archived checksum entry: {relative}")
        archived_checksums[relative] = digest
    expected_checksum_paths = set(archived_manifest.get("files", {})) | {manifest_relative}
    if set(archived_checksums) != expected_checksum_paths:
        raise BundleError("archived checksum inventory does not match release manifest")
    for relative, digest in archived_checksums.items():
        archived_bytes = archive.read(f"{archive_root}/{relative}")
        if hashlib.sha256(archived_bytes).hexdigest() != digest:
            raise BundleError(f"archived checksum mismatch: {relative}")
    excluded = {manifest_relative, "manifests/checksums.sha256"}
    subject_inventory = {
        relative: metadata["sha256"]
        for relative, metadata in generated_inventory.items()
        if relative not in excluded
    }
    expected_subject = preservation_subject_from_hashes(subject_inventory, archived_manifest)
    for signoff in archived_manifest.get("human_review_signoffs", []):
        if signoff.get("review_subject_sha256") != expected_subject:
            raise BundleError(
                "archived bytes differ from the preservation subject approved by "
                f"{signoff.get('role')}"
            )
    for relative, metadata in archived_manifest.get("files", {}).items():
        archived_bytes = archive.read(f"{archive_root}/{relative}")
        if len(archived_bytes) != metadata.get("bytes") or hashlib.sha256(
            archived_bytes
        ).hexdigest() != metadata.get("sha256"):
            raise BundleError(
                f"archived release data differs from its release manifest: {relative}"
            )


def validate_bundle_safety(files: dict[str, Path]) -> None:
    for relative, path in files.items():
        relative_path = PurePosixPath(relative)
        if (
            path.suffix.lower() in {".eval", ".log"}
            or path.name.lower() in FORBIDDEN_FILE_NAMES
            or FORBIDDEN_PATH_PARTS.intersection(part.lower() for part in relative_path.parts)
        ):
            raise BundleError(f"controlled artifact is forbidden: {relative}")
        candidate_text = path.read_bytes().decode("utf-8", errors="ignore")
        if CREDENTIAL_PATTERN.search(candidate_text):
            raise BundleError(f"credential marker found in bundle source: {relative}")


def validate_doi_metadata_files(files: dict[str, Path], release_manifest: dict[str, Any]) -> None:
    version_doi = release_manifest["doi"]["version_doi"]
    concept_doi = release_manifest["doi"]["concept_doi"]
    try:
        citation = yaml.safe_load(files["CITATION.cff"].read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        raise BundleError(f"stable CITATION.cff cannot be parsed: {error}") from error
    if not isinstance(citation, dict):
        raise BundleError("stable CITATION.cff must be a YAML mapping")
    doi_keys = {key for key in citation if isinstance(key, str) and key.casefold() == "doi"}
    if doi_keys != {"doi"} or citation.get("doi") != version_doi:
        raise BundleError("CITATION.cff DOI must exactly match the reserved version DOI")
    if str(citation.get("version", "")) != str(release_manifest["artifact_version"]):
        raise BundleError("CITATION.cff version does not match the stable release")
    released = citation.get("date-released")
    released = released.isoformat() if hasattr(released, "isoformat") else str(released)
    if ISO_DATE.fullmatch(released) is None:
        raise BundleError("CITATION.cff date-released must be an ISO date")
    if citation.get("url") != f"https://doi.org/{version_doi}":
        raise BundleError("CITATION.cff URL must resolve through the reserved version DOI")
    readme = files["README.md"].read_text(encoding="utf-8")
    if version_doi not in readme:
        raise BundleError("README.md does not contain the reserved version DOI")
    if concept_doi is not None and concept_doi not in readme:
        raise BundleError("README.md does not contain the existing concept DOI")
    if concept_doi is None and "Concept DOI: pending first publication" not in readme:
        raise BundleError("README.md does not disclose the pending first concept DOI")


def bundle_manifest_bytes(
    version: str,
    files: dict[str, Path],
    release_manifest: dict[str, Any],
    repository_commit: str,
) -> bytes:
    inventory: dict[str, dict[str, Any]] = {}
    for relative in sorted(files):
        path = files[relative]
        inventory[relative] = {
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
    metadata = {
        "artifact": "Agency Transfer Policy Atlas",
        "artifact_version": version.removeprefix("v"),
        "release_stage": release_manifest["release_stage"],
        "source_release_manifest": "manifests/release.json",
        "repository_commit": repository_commit,
        "doi_authority": "Zenodo",
        "deposit_status": "reserved_not_deposited",
        "version_doi": release_manifest["doi"]["version_doi"],
        "concept_doi": release_manifest["doi"]["concept_doi"],
        "concept_doi_status": release_manifest["doi"]["concept_doi_status"],
        "files": inventory,
    }
    return (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode("utf-8")


def zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.flag_bits = 0
    return info


def prepare_bundle(root: Path, version: str, output: Path, force: bool = False) -> str:
    """Validate and create a reproducible ZIP, returning its SHA-256 digest."""

    release_directory, manifest = load_manifest(root, version)
    validate_stable_gate(version, manifest)
    repository_commit = resolve_repository_state(root, version)
    release_files = validate_release_inventory(release_directory, manifest)
    gate_evidence_files = validate_stable_gate_evidence(root, release_directory, manifest)
    files = collect_bundle_files(root, release_files, gate_evidence_files)
    validate_signoff_subjects(manifest, files)
    validate_bundle_safety(files)
    validate_doi_metadata_files(files, manifest)
    generated_manifest = bundle_manifest_bytes(version, files, manifest, repository_commit)

    if output.exists() and not force:
        raise BundleError(f"output already exists (use --force to replace it): {output}")
    if output.is_symlink():
        raise BundleError(f"output path must not be a symlink: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    archive_root = f"agency-transfer-policy-atlas-{version}"
    expected_names = [
        f"{archive_root}/BUNDLE-MANIFEST.json",
        *[f"{archive_root}/{relative}" for relative in sorted(files)],
    ]

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w+b",
            prefix=f".{output.name}.",
            suffix=".tmp",
            dir=output.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
        with zipfile.ZipFile(temporary_path, mode="w", compression=zipfile.ZIP_STORED) as archive:
            archive.writestr(zip_info(f"{archive_root}/BUNDLE-MANIFEST.json"), generated_manifest)
            for relative in sorted(files):
                archive.writestr(
                    zip_info(f"{archive_root}/{relative}"),
                    files[relative].read_bytes(),
                )

        with zipfile.ZipFile(temporary_path, mode="r") as archive:
            if archive.namelist() != expected_names:
                raise BundleError("generated ZIP inventory or ordering is incorrect")
            if archive.testzip() is not None:
                raise BundleError("generated ZIP failed its CRC check")
            if archive.read(expected_names[0]) != generated_manifest:
                raise BundleError("generated bundle manifest is not reproducible")
            generated_inventory = json.loads(generated_manifest)["files"]
            for relative, metadata in generated_inventory.items():
                archived_bytes = archive.read(f"{archive_root}/{relative}")
                if (
                    len(archived_bytes) != metadata["bytes"]
                    or hashlib.sha256(archived_bytes).hexdigest() != metadata["sha256"]
                ):
                    raise BundleError(
                        f"generated ZIP entry differs from bundle manifest: {relative}"
                    )
            validate_archived_preservation_subject(
                archive, archive_root, version, generated_inventory
            )

        if output.exists() and not force:
            raise BundleError(f"output appeared during preparation: {output}")
        os.replace(temporary_path, output)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return sha256_file(output)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a local, deterministic Zenodo bundle after stable gates pass."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist" / "zenodo" / f"agency-transfer-policy-atlas-{VERSION}.zip",
        help="ZIP destination (default: policy-atlas/dist/zenodo/<version>.zip)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing local ZIP after all gates pass",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    try:
        digest = prepare_bundle(ROOT, VERSION, arguments.output, force=arguments.force)
    except BundleError as error:
        print(f"Refusing to prepare Zenodo bundle: {error}", file=sys.stderr)
        return 1
    print(f"Prepared local Zenodo bundle: {arguments.output}")
    print(f"SHA-256: {digest}")
    print("No network request or Zenodo deposition was performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
