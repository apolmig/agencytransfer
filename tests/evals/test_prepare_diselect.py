from __future__ import annotations

import hashlib
import subprocess
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parents[2] / "scripts/prepare_diselect.py"
SPEC = spec_from_file_location("prepare_diselect", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
prepare_diselect = module_from_spec(SPEC)
SPEC.loader.exec_module(prepare_diselect)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _checkout(tmp_path: Path) -> tuple[Path, str, dict[str, str]]:
    repo = tmp_path / "upstream"
    contents = {
        "data/models.csv": "model,model_id\nfixture,fixture-id\n",
        "data/evals/voting/results.csv": "model,judgement\nfixture,comply\n",
        "data/evals/mps/results.csv": "model,judgement\nfixture,refuse\n",
        "data/evals/baseline/results.csv": "model,judgement\nfixture,softrefuse\n",
    }
    for relative_path, content in contents.items():
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    _git(repo, "init", "--quiet")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "add", ".")
    _git(repo, "commit", "--quiet", "-m", "fixture")
    commit = _git(repo, "rev-parse", "HEAD")
    hashes = {relative_path: _sha256(repo / relative_path) for relative_path in contents}
    return repo, commit, hashes


def test_accepts_clean_checkout_at_expected_commit_with_expected_inputs(tmp_path: Path) -> None:
    repo, commit, hashes = _checkout(tmp_path)

    assert (
        prepare_diselect.verify_source_checkout(
            repo,
            expected_commit=commit,
            expected_input_sha256=hashes,
        )
        == repo.resolve()
    )


def test_rejects_wrong_commit(tmp_path: Path) -> None:
    repo, _commit, hashes = _checkout(tmp_path)

    with pytest.raises(SystemExit, match="expected pinned commit"):
        prepare_diselect.verify_source_checkout(
            repo,
            expected_commit="0" * 40,
            expected_input_sha256=hashes,
        )


def test_rejects_dirty_checkout(tmp_path: Path) -> None:
    repo, commit, hashes = _checkout(tmp_path)
    (repo / "untracked.txt").write_text("dirty\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="checkout is dirty"):
        prepare_diselect.verify_source_checkout(
            repo,
            expected_commit=commit,
            expected_input_sha256=hashes,
        )


def test_rejects_input_hash_mismatch_in_clean_checkout(tmp_path: Path) -> None:
    repo, commit, hashes = _checkout(tmp_path)
    hashes["data/models.csv"] = "f" * 64

    with pytest.raises(SystemExit, match=r"hash mismatch for data/models\.csv"):
        prepare_diselect.verify_source_checkout(
            repo,
            expected_commit=commit,
            expected_input_sha256=hashes,
        )
