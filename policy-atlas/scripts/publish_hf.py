#!/usr/bin/env python3
"""Publish the prepared, validated beta through the dedicated release workflow."""

from __future__ import annotations

import os
import hashlib
import json
import re
from pathlib import Path

from release_config import CURATION_VERSION, VERSION


ROOT = Path(__file__).resolve().parents[1]
REPO_ID = "apol/agency-transfer-policy-atlas"

FORBIDDEN_PATH_PARTS = {"logs", "raw", "private", "scans"}
CREDENTIAL_PATTERN = re.compile(
    r"(?:\bsk-[A-Za-z0-9_-]{20,}|\bhf_[A-Za-z0-9]{20,}|"
    r"bearer\s+[A-Za-z0-9._-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)",
    re.IGNORECASE,
)


def validate_staged_release(destination: Path) -> set[str]:
    manifest = json.loads(
        (destination / "manifests" / "release.json").read_text(encoding="utf-8")
    )
    if manifest.get("artifact") != "Agency Transfer Policy Atlas":
        raise SystemExit("Unexpected staged artifact")
    if manifest.get("artifact_version") != VERSION.removeprefix("v"):
        raise SystemExit("Staged manifest version does not match release_config.py")
    if manifest.get("curation_version") != CURATION_VERSION:
        raise SystemExit("Unexpected staged curation version")
    if set(manifest.get("formats", [])) != {"csv", "parquet"}:
        raise SystemExit("Staged release must contain CSV and Parquet")
    expected = set(manifest["files"])
    expected.update(
        {
            "README.md",
            "CITATION.cff",
            "DATA_DICTIONARY.md",
            "PUBLICATION_STATUS.md",
            "LICENSE.md",
            "manifests/release.json",
            "manifests/checksums.sha256",
            "schemas/claim.schema.json",
            "schemas/implementation.schema.json",
            "schemas/release-manifest.schema.json",
            "schemas/source.schema.json",
            "review/PRIORITY_VERIFICATION.md",
            "review/priority_claim_review.csv",
        }
    )
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
    for line in (destination / "manifests" / "checksums.sha256").read_text(
        encoding="utf-8"
    ).splitlines():
        digest, relative = line.split("  ", 1)
        actual_checksums[relative] = digest
    if actual_checksums != expected_checksums:
        raise SystemExit("Checksum manifest does not match staged release")

    static_sources = {
        "README.md": ROOT / "huggingface" / "README.md",
        "CITATION.cff": ROOT / "CITATION.cff",
        "DATA_DICTIONARY.md": ROOT / "DATA_DICTIONARY.md",
        "PUBLICATION_STATUS.md": ROOT / "PUBLICATION_STATUS.md",
        "LICENSE.md": ROOT / "LICENSES" / "DATA.md",
    }
    # The strict inventory above defines this release. Later companion reviews
    # must not be silently incorporated or treated as missing release files.
    for relative in expected:
        if relative.startswith(("schemas/", "review/")):
            static_sources[relative] = ROOT / relative
    for relative, source in static_sources.items():
        staged = destination / relative
        if hashlib.sha256(staged.read_bytes()).digest() != hashlib.sha256(
            source.read_bytes()
        ).digest():
            raise SystemExit(f"Staged static file differs from canonical source: {relative}")

    for path in destination.rglob("*"):
        relative = path.relative_to(destination)
        if path.is_symlink():
            raise SystemExit(f"Symlink is forbidden: {relative}")
        if path.is_file() and (
            path.suffix in {".eval", ".log"}
            or FORBIDDEN_PATH_PARTS.intersection(part.lower() for part in relative.parts)
        ):
            raise SystemExit(f"Controlled artifact is forbidden: {relative}")
        if path.is_file() and path.suffix.lower() in {".md", ".json", ".csv", ".cff"}:
            text = path.read_text(encoding="utf-8")
            if CREDENTIAL_PATTERN.search(text):
                raise SystemExit(f"Credential marker found in staged release: {relative}")
    return expected


def main() -> None:
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise SystemExit("HF_TOKEN is required")

    destination = ROOT / "dist" / "huggingface"
    expected = validate_staged_release(destination)

    from huggingface_hub import HfApi

    api = HfApi(token=token)
    identity = api.whoami()
    if identity.get("name") != "apol":
        raise SystemExit(f"Refusing to publish as unexpected Hugging Face identity: {identity.get('name')!r}")
    api.create_repo(REPO_ID, repo_type="dataset", exist_ok=True, private=False)
    refs = api.list_repo_refs(REPO_ID, repo_type="dataset")
    if any(
        getattr(tag, "name", None) == VERSION or getattr(tag, "ref", None) == f"refs/tags/{VERSION}"
        for tag in refs.tags
    ):
        raise SystemExit(
            f"Immutable release tag {VERSION} already exists; bump VERSION instead of moving it"
        )
    commit = api.upload_folder(
        repo_id=REPO_ID,
        repo_type="dataset",
        folder_path=destination,
        delete_patterns="*",
        commit_message=f"Publish {VERSION} research preview",
    )
    remote = set(
        api.list_repo_files(REPO_ID, repo_type="dataset", revision=commit.oid)
    )
    expected_remote = expected | {".gitattributes"}
    if remote != expected_remote:
        raise SystemExit(
            f"Remote inventory mismatch: missing={sorted(expected_remote - remote)}, "
            f"unexpected={sorted(remote - expected_remote)}"
        )
    api.create_tag(
        repo_id=REPO_ID,
        repo_type="dataset",
        tag=VERSION,
        revision=commit.oid,
        exist_ok=False,
    )
    print(f"Published https://huggingface.co/datasets/{REPO_ID}/tree/{VERSION}")


if __name__ == "__main__":
    main()
