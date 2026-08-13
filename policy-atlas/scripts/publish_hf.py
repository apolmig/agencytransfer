#!/usr/bin/env python3
"""Publish the prepared, validated beta through the dedicated release workflow."""

from __future__ import annotations

import os
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ID = "apol/agency-transfer-policy-atlas"
VERSION = "v0.1.0-beta.1"

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

    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_release.py")], check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_release.py")], check=True)
    subprocess.run(["npm", "ci", "--prefix", str(ROOT)], check=True)
    subprocess.run(["npm", "--prefix", str(ROOT), "run", "build:parquet"], check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_release.py")], check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "prepare_hf_release.py")], check=True)
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
    api.create_tag(
        repo_id=REPO_ID,
        repo_type="dataset",
        tag=VERSION,
        revision=commit.oid,
        exist_ok=False,
    )
    remote = set(api.list_repo_files(REPO_ID, repo_type="dataset"))
    expected_remote = expected | {".gitattributes"}
    if remote != expected_remote:
        raise SystemExit(
            f"Remote inventory mismatch: missing={sorted(expected_remote - remote)}, "
            f"unexpected={sorted(remote - expected_remote)}"
        )
    print(f"Published https://huggingface.co/datasets/{REPO_ID}/tree/{VERSION}")


if __name__ == "__main__":
    main()
