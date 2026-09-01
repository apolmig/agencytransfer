#!/usr/bin/env python3
"""Prepare a self-contained Hugging Face dataset folder without uploading it."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from release_config import VERSION


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "release" / VERSION
DESTINATION = ROOT / "dist" / "huggingface"


def main() -> None:
    manifest = json.loads(
        (SOURCE / "manifests" / "release.json").read_text(encoding="utf-8")
    )
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
    if DESTINATION.exists():
        shutil.rmtree(DESTINATION)
    shutil.copytree(SOURCE / "data", DESTINATION / "data")
    shutil.copytree(SOURCE / "manifests", DESTINATION / "manifests")
    shutil.copy2(ROOT / "huggingface" / "README.md", DESTINATION / "README.md")
    shutil.copy2(ROOT / "CITATION.cff", DESTINATION / "CITATION.cff")
    shutil.copy2(ROOT / "DATA_DICTIONARY.md", DESTINATION / "DATA_DICTIONARY.md")
    shutil.copy2(ROOT / "PUBLICATION_STATUS.md", DESTINATION / "PUBLICATION_STATUS.md")
    shutil.copy2(ROOT / "LICENSES" / "DATA.md", DESTINATION / "LICENSE.md")
    shutil.copytree(ROOT / "schemas", DESTINATION / "schemas")
    # Stage only the declared beta review records. Later companion reviews are
    # public research documents, not automatic upgrades of this frozen dataset.
    (DESTINATION / "review").mkdir()
    for name in ("PRIORITY_VERIFICATION.md", "priority_claim_review.csv"):
        shutil.copy2(ROOT / "review" / name, DESTINATION / "review" / name)
    print(f"Prepared {DESTINATION}")


if __name__ == "__main__":
    main()
