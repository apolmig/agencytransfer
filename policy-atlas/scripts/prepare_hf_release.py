#!/usr/bin/env python3
"""Prepare a self-contained Hugging Face dataset folder without uploading it."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from public_contract import PUBLIC_TABLE_STEMS, validate_csv_contract
from release_config import VERSION

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "release" / VERSION
DESTINATION = ROOT / "dist" / "huggingface"

STATIC_FILES = {
    "README.md": ROOT / "huggingface" / "README.md",
    "CITATION.cff": ROOT / "CITATION.cff",
    "DATA_DICTIONARY.md": ROOT / "DATA_DICTIONARY.md",
    "PUBLICATION_STATUS.md": ROOT / "PUBLICATION_STATUS.md",
    "METHODS.md": ROOT / "METHODS.md",
    "CHANGELOG.md": ROOT / "CHANGELOG.md",
    "GOVERNANCE.md": ROOT / "GOVERNANCE.md",
    "CONTRIBUTING.md": ROOT / "CONTRIBUTING.md",
    "MAINTAINERS.md": ROOT / "MAINTAINERS.md",
    "CODE_OF_CONDUCT.md": ROOT / "CODE_OF_CONDUCT.md",
    "CORRECTIONS.md": ROOT / "CORRECTIONS.md",
    "DOI_RELEASE.md": ROOT / "DOI_RELEASE.md",
    "LICENSE": ROOT / "LICENSE",
    "LICENSES/Apache-2.0.txt": ROOT / "LICENSES" / "Apache-2.0.txt",
    "LICENSES/CODE": ROOT / "LICENSES" / "CODE",
    "LICENSES/DATA.md": ROOT / "LICENSES" / "DATA.md",
    "schemas/atlas.schema.json": ROOT / "schemas" / "atlas.schema.json",
    "schemas/candidate-registry.schema.json": ROOT / "schemas" / "candidate-registry.schema.json",
    "schemas/claim.schema.json": ROOT / "schemas" / "claim.schema.json",
    "schemas/implementation.schema.json": ROOT / "schemas" / "implementation.schema.json",
    "schemas/public-implementation.schema.json": (
        ROOT / "schemas" / "public-implementation.schema.json"
    ),
    "schemas/public-table-columns.json": ROOT / "schemas" / "public-table-columns.json",
    "schemas/release-manifest.schema.json": ROOT / "schemas" / "release-manifest.schema.json",
    "schemas/source.schema.json": ROOT / "schemas" / "source.schema.json",
    "schemas/stable-core-candidate.schema.json": (
        ROOT / "schemas" / "stable-core-candidate.schema.json"
    ),
    "schemas/stable-release-gate.schema.json": ROOT / "schemas" / "stable-release-gate.schema.json",
    "review/PRIORITY_VERIFICATION.md": ROOT / "review" / "PRIORITY_VERIFICATION.md",
    "review/priority_claim_review.csv": ROOT / "review" / "priority_claim_review.csv",
    "review/stable_release_gates.csv": ROOT / "review" / "stable_release_gates.csv",
    "protocol/RANKING_PROTOCOL.md": ROOT / "protocol" / "RANKING_PROTOCOL.md",
    "protocol/STABLE_CORE_SELECTION.md": ROOT / "protocol" / "STABLE_CORE_SELECTION.md",
}
STATIC_TREE_NAMES: tuple[str, ...] = ()


def ensure_safe_file(path: Path, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise SystemExit(f"Unsafe or missing staging source {label}: {path}")


def ensure_safe_tree(directory: Path, label: str) -> None:
    if directory.is_symlink() or not directory.is_dir():
        raise SystemExit(f"Unsafe or missing staging tree {label}: {directory}")
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise SystemExit(f"Symlink is forbidden in staging source {label}: {path}")
        if not path.is_file() and not path.is_dir():
            raise SystemExit(f"Unsupported staging source entry {label}: {path}")


def main() -> None:
    ensure_safe_tree(SOURCE / "data", "release data")
    ensure_safe_tree(SOURCE / "manifests", "release manifests")
    for relative, source in STATIC_FILES.items():
        ensure_safe_file(source, relative)
    for tree_name in STATIC_TREE_NAMES:
        ensure_safe_tree(ROOT / tree_name, tree_name)

    manifest = json.loads((SOURCE / "manifests" / "release.json").read_text(encoding="utf-8"))
    if manifest.get("artifact_version") != VERSION.removeprefix("v"):
        raise SystemExit("Release manifest version does not match release_config.py")
    if set(manifest.get("formats", [])) != {"csv", "parquet"}:
        raise SystemExit("Refusing to stage a release without both CSV and Parquet")
    csv_stems = {
        path.relative_to(SOURCE / "data").with_suffix("").as_posix()
        for path in (SOURCE / "data").rglob("*.csv")
    }
    parquet_stems = {
        path.relative_to(SOURCE / "data").with_suffix("").as_posix()
        for path in (SOURCE / "data").rglob("*.parquet")
    }
    if not csv_stems or csv_stems != parquet_stems:
        raise SystemExit("Refusing to stage a release with CSV/Parquet table mismatch")
    manifest_data_paths = set(manifest.get("files", {}))
    if any(not path.endswith((".csv", ".parquet")) for path in manifest_data_paths):
        raise SystemExit("Refusing to stage a non-tabular release data artifact")
    if {
        path.removesuffix(".csv") for path in manifest_data_paths if path.endswith(".csv")
    } != PUBLIC_TABLE_STEMS:
        raise SystemExit("Release table inventory differs from the frozen public contract")
    try:
        validate_csv_contract(SOURCE)
    except ValueError as error:
        raise SystemExit(f"Release CSV contract violation: {error}") from error
    if DESTINATION.is_symlink():
        raise SystemExit(f"Staging destination must not be a symlink: {DESTINATION}")
    if DESTINATION.exists():
        shutil.rmtree(DESTINATION)
    shutil.copytree(SOURCE / "data", DESTINATION / "data")
    shutil.copytree(SOURCE / "manifests", DESTINATION / "manifests")
    for relative, source in STATIC_FILES.items():
        destination = DESTINATION / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    for tree_name in STATIC_TREE_NAMES:
        shutil.copytree(ROOT / tree_name, DESTINATION / tree_name)
    print(f"Prepared {DESTINATION}")


if __name__ == "__main__":
    main()
