#!/usr/bin/env python3
"""Publish the prepared, validated beta through the dedicated release workflow."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path

import yaml
from prepare_hf_release import (
    STATIC_FILES,
    STATIC_TREE_NAMES,
    ensure_safe_file,
    ensure_safe_tree,
)
from public_contract import PUBLIC_TABLE_STEMS, validate_csv_contract
from release_config import CURATION_VERSION, VERSION

ROOT = Path(__file__).resolve().parents[1]
REPO_ID = "apol/agency-transfer-policy-atlas"

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
DOI_FIELD_PATTERN = re.compile(r"(?:[a-z0-9]+[-_])?doi(?:[-_][a-z0-9]+)?", re.IGNORECASE)
DOI_VALUE_PATTERN = re.compile(
    r"(?:https?://(?:dx\.)?doi\.org/)?10\.\d{4,9}/[-._;()/:A-Z0-9]+",
    re.IGNORECASE,
)


def reject_doi_metadata(value: object, *, location: str) -> None:
    """Reject DOI fields, identifier types, and DOI values anywhere in beta metadata."""

    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            if DOI_FIELD_PATTERN.fullmatch(key_text):
                raise SystemExit(
                    f"Research-preview {location} must not contain DOI metadata: {key_text}"
                )
            reject_doi_metadata(child, location=location)
        return
    if isinstance(value, list):
        for child in value:
            reject_doi_metadata(child, location=location)
        return
    if isinstance(value, str) and (
        value.strip().casefold() == "doi" or DOI_VALUE_PATTERN.search(value)
    ):
        raise SystemExit(f"Research-preview {location} must not contain DOI metadata")


def file_contains_credential(path: Path) -> bool:
    """Scan text and binary containers for ASCII credential markers."""

    candidate_text = path.read_bytes().decode("utf-8", errors="ignore")
    return CREDENTIAL_PATTERN.search(candidate_text) is not None


def load_and_validate_citation(
    path: Path, *, required_release_date: str | None = None
) -> dict[str, object]:
    """Parse the CFF as YAML and enforce the immutable beta citation contract."""

    try:
        citation = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        raise SystemExit(f"CITATION.cff cannot be parsed safely: {error}") from error
    if not isinstance(citation, dict):
        raise SystemExit("CITATION.cff must contain a YAML mapping")
    reject_doi_metadata(citation, location="CITATION.cff")
    if str(citation.get("version", "")) != VERSION.removeprefix("v"):
        raise SystemExit("CITATION.cff version does not match release_config.py")
    expected_url = f"https://huggingface.co/datasets/{REPO_ID}/tree/{VERSION}"
    if citation.get("url") != expected_url:
        raise SystemExit("CITATION.cff URL must point to the immutable HF release tag")
    expected_repository = f"https://github.com/apolmig/agencytransfer/tree/{VERSION}/policy-atlas"
    if citation.get("repository-code") != expected_repository:
        raise SystemExit("CITATION.cff repository-code must point to the immutable Git tag")
    released = citation.get("date-released")
    if released is not None:
        released = released.isoformat() if hasattr(released, "isoformat") else str(released)
        if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", released) is None:
            raise SystemExit("CITATION.cff date-released must be an ISO date")
    if required_release_date is not None and released != required_release_date:
        raise SystemExit(
            "CITATION.cff date-released must equal the UTC publication date "
            f"({required_release_date})"
        )
    return citation


def validate_publication_changelog(path: Path, *, required_release_date: str) -> None:
    """Reject a release whose changelog still calls the version a candidate."""

    try:
        headings = [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("## ")
        ]
    except (OSError, UnicodeDecodeError) as error:
        raise SystemExit(f"CHANGELOG.md cannot be read: {error}") from error
    expected = f"## {VERSION} — {required_release_date}"
    if not headings or headings[0] != expected:
        raise SystemExit(
            "CHANGELOG.md first release heading must exactly match the version "
            f"and UTC publication date: {expected}"
        )


def validate_staged_release(destination: Path) -> set[str]:
    manifest = json.loads((destination / "manifests" / "release.json").read_text(encoding="utf-8"))
    if manifest.get("artifact") != "Agency Transfer Policy Atlas":
        raise SystemExit("Unexpected staged artifact")
    if manifest.get("artifact_version") != VERSION.removeprefix("v"):
        raise SystemExit("Staged manifest version does not match release_config.py")
    if manifest.get("curation_version") != CURATION_VERSION:
        raise SystemExit("Unexpected staged curation version")
    if (
        manifest.get("release_stage") != "research-preview"
        or manifest.get("stable_release_ready") is not False
        or not isinstance(manifest.get("stable_release_blockers"), list)
        or not manifest["stable_release_blockers"]
    ):
        raise SystemExit("Publisher accepts only a blocked research-preview manifest")
    reject_doi_metadata(manifest, location="manifest")
    if (
        manifest.get("ranking_preregistration_status") != "draft_not_preregistered"
        or manifest.get("counts", {}).get("rank_eligible_core_candidates") != 0
    ):
        raise SystemExit("Publisher refuses a staged beta with ranking eligibility")
    if set(manifest.get("formats", [])) != {"csv", "parquet"}:
        raise SystemExit("Staged release must contain CSV and Parquet")
    manifest_data_paths = set(manifest.get("files", {}))
    if any(not path.endswith((".csv", ".parquet")) for path in manifest_data_paths):
        raise SystemExit("Staged release contains a non-tabular data artifact")
    csv_stems = {path.removesuffix(".csv") for path in manifest_data_paths if path.endswith(".csv")}
    parquet_stems = {
        path.removesuffix(".parquet") for path in manifest_data_paths if path.endswith(".parquet")
    }
    if csv_stems != PUBLIC_TABLE_STEMS or parquet_stems != PUBLIC_TABLE_STEMS:
        raise SystemExit("Staged CSV/Parquet inventory differs from the frozen public contract")
    try:
        validate_csv_contract(destination)
    except ValueError as error:
        raise SystemExit(f"Staged CSV contract violation: {error}") from error
    from validate_release import Validation, validate_csv_parquet_pair

    parity = Validation()
    for stem in sorted(PUBLIC_TABLE_STEMS):
        validate_csv_parquet_pair(
            parity,
            destination / f"{stem}.csv",
            destination / f"{stem}.parquet",
            stem,
        )
    if parity.errors:
        raise SystemExit(
            "Staged CSV/Parquet semantic validation failed: " + "; ".join(parity.errors)
        )
    static_sources = dict(STATIC_FILES)
    for tree_name in STATIC_TREE_NAMES:
        directory = ROOT / tree_name
        ensure_safe_tree(directory, tree_name)
        for path in directory.rglob("*"):
            if path.is_file():
                static_sources[path.relative_to(ROOT).as_posix()] = path
    for relative, source in STATIC_FILES.items():
        ensure_safe_file(source, relative)

    load_and_validate_citation(destination / "CITATION.cff")

    expected = set(manifest["files"])
    expected.update(static_sources)
    expected.update({"manifests/release.json", "manifests/checksums.sha256"})
    actual = {
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file()
    }
    if actual != expected:
        raise SystemExit(
            f"Staged inventory mismatch: missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)}"
        )

    for relative, metadata in manifest["files"].items():
        path = destination / relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != metadata["sha256"] or path.stat().st_size != metadata["bytes"]:
            raise SystemExit(f"Manifest integrity mismatch: {relative}")
    manifest_path = destination / "manifests" / "release.json"
    expected_checksums = {
        **{relative: metadata["sha256"] for relative, metadata in manifest["files"].items()},
        "manifests/release.json": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    }
    actual_checksums: dict[str, str] = {}
    for line_number, line in enumerate(
        (destination / "manifests" / "checksums.sha256").read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        parts = line.split("  ", 1)
        if len(parts) != 2:
            raise SystemExit(f"Malformed checksum line {line_number}")
        digest, relative = parts
        if relative in actual_checksums:
            raise SystemExit(f"Duplicate checksum entry: {relative}")
        actual_checksums[relative] = digest
    if actual_checksums != expected_checksums:
        raise SystemExit("Checksum manifest does not match staged release")

    for relative, source in static_sources.items():
        staged = destination / relative
        if (
            hashlib.sha256(staged.read_bytes()).digest()
            != hashlib.sha256(source.read_bytes()).digest()
        ):
            raise SystemExit(f"Staged static file differs from canonical source: {relative}")

    for path in destination.rglob("*"):
        relative = path.relative_to(destination)
        if path.is_symlink():
            raise SystemExit(f"Symlink is forbidden: {relative}")
        if path.is_file() and (
            path.suffix in {".eval", ".log"}
            or FORBIDDEN_PATH_PARTS.intersection(part.lower() for part in relative.parts)
            or path.name.lower() in FORBIDDEN_FILE_NAMES
        ):
            raise SystemExit(f"Controlled artifact is forbidden: {relative}")
        if path.is_file() and file_contains_credential(path):
            raise SystemExit(f"Credential marker found in staged release: {relative}")
    return expected


def main() -> None:
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise SystemExit("HF_TOKEN is required")
    source_commit = os.environ.get("GITHUB_SHA", "")
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise SystemExit("GITHUB_SHA must contain the full reviewed source commit")

    destination = ROOT / "dist" / "huggingface"
    expected = validate_staged_release(destination)
    publication_date = datetime.now(UTC).date().isoformat()
    load_and_validate_citation(destination / "CITATION.cff", required_release_date=publication_date)
    validate_publication_changelog(
        destination / "CHANGELOG.md", required_release_date=publication_date
    )

    from huggingface_hub import HfApi

    api = HfApi(token=token)
    identity = api.whoami()
    if identity.get("name") != "apol":
        raise SystemExit(
            f"Refusing to publish as unexpected Hugging Face identity: {identity.get('name')!r}"
        )
    main_info = api.repo_info(REPO_ID, repo_type="dataset", revision="main")
    refs = api.list_repo_refs(REPO_ID, repo_type="dataset")
    if any(
        getattr(tag, "name", None) == VERSION or getattr(tag, "ref", None) == f"refs/tags/{VERSION}"
        for tag in refs.tags
    ):
        raise SystemExit(
            f"Immutable release tag {VERSION} already exists; bump VERSION instead of moving it"
        )
    expected_remote = expected | {".gitattributes"}
    run_id = re.sub(r"[^A-Za-z0-9.-]", "-", os.environ.get("GITHUB_RUN_ID", "manual"))
    run_attempt = re.sub(r"[^A-Za-z0-9.-]", "-", os.environ.get("GITHUB_RUN_ATTEMPT", "1"))
    candidate_branch = f"release-candidate-{VERSION}-{run_id}-{run_attempt}"
    branch_created = False
    try:
        api.create_branch(
            repo_id=REPO_ID,
            repo_type="dataset",
            branch=candidate_branch,
            revision="main",
            exist_ok=False,
        )
        branch_created = True
        candidate_commit = api.upload_folder(
            repo_id=REPO_ID,
            repo_type="dataset",
            revision=candidate_branch,
            folder_path=destination,
            delete_patterns="*",
            commit_message=f"Stage {VERSION} from GitHub {source_commit}",
        )
        candidate_remote = set(
            api.list_repo_files(
                REPO_ID,
                repo_type="dataset",
                revision=candidate_commit.oid,
            )
        )
        if candidate_remote != expected_remote:
            raise SystemExit(
                "Remote candidate inventory mismatch: "
                f"missing={sorted(expected_remote - candidate_remote)}, "
                f"unexpected={sorted(candidate_remote - expected_remote)}"
            )
        api.create_tag(
            repo_id=REPO_ID,
            repo_type="dataset",
            tag=VERSION,
            revision=candidate_commit.oid,
            exist_ok=False,
        )
        main_commit = api.upload_folder(
            repo_id=REPO_ID,
            repo_type="dataset",
            revision="main",
            folder_path=destination,
            delete_patterns="*",
            parent_commit=main_info.sha,
            commit_message=f"Publish {VERSION} from GitHub {source_commit}",
        )
        main_remote = set(
            api.list_repo_files(REPO_ID, repo_type="dataset", revision=main_commit.oid)
        )
        if main_remote != expected_remote:
            raise SystemExit(
                "Published main inventory mismatch after immutable tag creation: "
                f"missing={sorted(expected_remote - main_remote)}, "
                f"unexpected={sorted(main_remote - expected_remote)}"
            )
        print(
            f"Published https://huggingface.co/datasets/{REPO_ID}/tree/{VERSION} "
            f"and promoted commit {main_commit.oid} to main"
        )
    finally:
        if branch_created:
            try:
                api.delete_branch(
                    repo_id=REPO_ID,
                    repo_type="dataset",
                    branch=candidate_branch,
                )
            except Exception as error:  # cleanup does not invalidate an immutable release
                print(f"WARNING: could not delete temporary HF branch: {error}")


if __name__ == "__main__":
    main()
