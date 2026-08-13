#!/usr/bin/env python3
"""Prepare a self-contained Hugging Face dataset folder without uploading it."""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "v0.1.0-beta.1"
SOURCE = ROOT / "release" / VERSION
DESTINATION = ROOT / "dist" / "huggingface"


def main() -> None:
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
    shutil.copytree(ROOT / "review", DESTINATION / "review")
    print(f"Prepared {DESTINATION}")


if __name__ == "__main__":
    main()
