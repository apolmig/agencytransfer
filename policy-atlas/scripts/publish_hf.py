#!/usr/bin/env python3
"""Publish a prepared, validated beta to Hugging Face after explicit dispatch."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ID = "apol/agency-transfer-policy-atlas"
VERSION = "v0.1.0-beta.1"


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

    from huggingface_hub import HfApi

    api = HfApi(token=token)
    api.create_repo(REPO_ID, repo_type="dataset", exist_ok=True, private=False)
    api.upload_folder(
        repo_id=REPO_ID,
        repo_type="dataset",
        folder_path=ROOT / "dist" / "huggingface",
        commit_message=f"Publish {VERSION} research preview",
    )
    api.create_tag(repo_id=REPO_ID, repo_type="dataset", tag=VERSION, exist_ok=True)
    print(f"Published https://huggingface.co/datasets/{REPO_ID}/tree/{VERSION}")


if __name__ == "__main__":
    main()
