from __future__ import annotations

import json
import os
import shutil
import socket
import sys
from pathlib import Path
from types import SimpleNamespace

import atb_eval.petri_exploratory as exploratory
import atb_eval.runner as runner
import pytest
from atb_eval.manifest import ProtocolManifest, ProtocolStatus, ReleaseTier, load_manifest
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
PETRI_MANIFEST = REPO_ROOT / "evals/manifests/petri-discovery-v0.1.json"
BLOOM_MANIFEST = REPO_ROOT / "evals/manifests/bloom-discovery-v0.1.json"


@pytest.mark.parametrize(
    ("path", "kind", "roles", "items", "package", "version"),
    [
        (
            PETRI_MANIFEST,
            "petri_discovery",
            ["auditor", "target", "judge"],
            1,
            "inspect-petri",
            "3.0.11",
        ),
        (
            BLOOM_MANIFEST,
            "bloom_discovery",
            ["scenarios", "auditor", "target", "judge"],
            2,
            "petri-bloom",
            "0.2.6",
        ),
    ],
)
def test_exploratory_manifests_are_draft_zero_cost_and_nonpublic(
    path: Path,
    kind: str,
    roles: list[str],
    items: int,
    package: str,
    version: str,
) -> None:
    manifest = load_manifest(path)
    assert manifest.status is ProtocolStatus.DRAFT
    assert manifest.task.kind == kind
    assert (manifest.task.package, manifest.task.package_version) == (package, version)
    assert manifest.exploratory_lane is not None
    assert manifest.exploratory_lane.roles == roles
    assert manifest.exploratory_lane.expected_plan_items == items
    assert manifest.models == [] and manifest.model_roles == {}
    assert not manifest.is_paid
    assert manifest.run.sample_cost_limit_usd == 0
    assert manifest.run.planned_run_cost_envelope_usd == 0
    assert manifest.run.provider_key_limit_usd is None
    assert manifest.dataset.release_tier is ReleaseTier.PUBLIC
    assert {
        manifest.release.raw_logs,
        manifest.release.target_outputs,
        manifest.release.judge_traces,
    } == {ReleaseTier.WITHHELD}
    assert manifest.release.public_aggregate_candidate is False


@pytest.mark.parametrize(
    ("path", "sample_ids", "dataset_sha256"),
    [
        (
            PETRI_MANIFEST,
            ["preference_correction"],
            "10edc89d8c08b0a5150f4e328e9ef9a745d2b48a6003220cc219f87cbe4f6edb",
        ),
        (
            BLOOM_MANIFEST,
            ["document_format_correction", "restaurant_preference_correction"],
            "22231c0f5533d735c9708e75b398435bae07638197475259250b20dba04afb27",
        ),
    ],
)
def test_plan_constructs_only_bound_official_tasks_without_provider_state(
    monkeypatch: pytest.MonkeyPatch,
    path: Path,
    sample_ids: list[str],
    dataset_sha256: str,
) -> None:
    for name in exploratory.CREDENTIAL_ENV_NAMES:
        monkeypatch.setenv(name, f"sentinel-{name}")
    receipt = exploratory.build_exploratory_plan(path, REPO_ROOT)
    canary = receipt["official_task_canary"]
    assert canary["sample_ids"] == sample_ids
    assert canary["dataset_projection_sha256"] == dataset_sha256
    assert canary["network_calls"] == canary["model_calls"] == 0
    assert canary["model_roles_resolved"] is False
    assert canary["provider_key_env_absent"] == sorted(exploratory.CREDENTIAL_ENV_NAMES)
    assert receipt["execution_status"] == "blocked"
    assert receipt["paid"] is False
    assert receipt["public_aggregate_candidate"] is False
    assert receipt["input_release_tier"] == "public"
    assert receipt["generated_artifact_release_tier"] == "withheld"
    assert receipt["dependency_pins"] == exploratory.PLAN_RUNTIME_PINS
    for name in exploratory.CREDENTIAL_ENV_NAMES:
        assert os.environ[name] == f"sentinel-{name}"


def test_constructor_rejects_and_cleans_credentials_loaded_by_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = load_manifest(PETRI_MANIFEST)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def injected_factory(**kwargs: object) -> object:
        os.environ["OPENAI_API_KEY"] = "injected-by-import"
        return object()

    monkeypatch.setattr(
        exploratory.importlib,
        "import_module",
        lambda name: SimpleNamespace(audit=injected_factory),
    )
    with pytest.raises(ValueError, match="populated provider credential"):
        exploratory.verify_official_task_construction(manifest, REPO_ROOT)
    assert "OPENAI_API_KEY" not in os.environ


def test_constructor_blocks_network_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = load_manifest(PETRI_MANIFEST)

    def network_factory(**kwargs: object) -> object:
        socket.socket().connect(("example.invalid", 443))
        return object()

    monkeypatch.setattr(
        exploratory.importlib,
        "import_module",
        lambda name: SimpleNamespace(audit=network_factory),
    )
    with pytest.raises(RuntimeError, match="network access is forbidden"):
        exploratory.verify_official_task_construction(manifest, REPO_ROOT)


def test_runner_blocks_exploratory_lane_before_log_or_task_setup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = load_manifest(PETRI_MANIFEST)
    with pytest.raises(ValueError, match="deliberately unsupported"):
        runner.build_task(manifest, None)

    def log_dir_must_not_run(*args: object, **kwargs: object) -> Path:
        raise AssertionError("controlled log setup ran before exploratory block")

    monkeypatch.setattr(runner, "require_controlled_log_dir", log_dir_must_not_run)
    with pytest.raises(ValueError, match="deliberately unsupported"):
        runner.preflight(PETRI_MANIFEST, Path("/unused"), REPO_ROOT, None)


def test_exploratory_cli_has_no_execute_surface(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["atb-exploratory-plan", "--manifest", str(PETRI_MANIFEST), "--execute"],
    )
    with pytest.raises(SystemExit):
        exploratory.parse_args()


@pytest.mark.parametrize(
    ("manifest_path", "mutation", "message"),
    [
        (PETRI_MANIFEST, ("status", "frozen"), "must remain draft"),
        (
            PETRI_MANIFEST,
            ("release.public_aggregate_candidate", True),
            "cannot be a public aggregate",
        ),
        (PETRI_MANIFEST, ("dataset.split", "confirmation"), "dataset metadata"),
        (PETRI_MANIFEST, ("run.fail_on_error", False), "zero-cost blocked lane"),
        (PETRI_MANIFEST, ("validation.cluster_key", "sample_id"), "completed human validation"),
        (PETRI_MANIFEST, ("task.expected_metadata", {"claim": "runtime"}), "runtime metadata"),
        (
            BLOOM_MANIFEST,
            ("exploratory_lane.roles", ["auditor", "target", "judge"]),
            "exact role contract",
        ),
    ],
)
def test_exploratory_manifest_mutations_fail_closed(
    manifest_path: Path,
    mutation: tuple[str, object],
    message: str,
) -> None:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    target: dict[str, object] = payload
    parts = mutation[0].split(".")
    for part in parts[:-1]:
        target = target[part]  # type: ignore[assignment]
    target[parts[-1]] = mutation[1]
    if mutation == ("status", "frozen"):
        payload["frozen_at"] = "2026-08-15T00:00:00Z"
    with pytest.raises(ValidationError, match=message):
        ProtocolManifest.model_validate(payload)


@pytest.mark.parametrize(
    ("config_path", "config_type", "field", "value"),
    [
        (
            REPO_ROOT / "evals/exploratory/petri/v0.1/config.json",
            exploratory.PetriPlanConfig,
            "enable_rollback",
            True,
        ),
        (
            REPO_ROOT / "evals/exploratory/petri/v0.1/config.json",
            exploratory.PetriPlanConfig,
            "target_display_name",
            "real-model-id",
        ),
        (
            REPO_ROOT / "evals/exploratory/petri/v0.1/config.json",
            exploratory.PetriPlanConfig,
            "reproducibility_blockers",
            ["none", "none"],
        ),
        (
            REPO_ROOT / "evals/exploratory/bloom/v0.1/config.json",
            exploratory.BloomPlanConfig,
            "turn_counter",
            True,
        ),
        (
            REPO_ROOT / "evals/exploratory/bloom/v0.1/config.json",
            exploratory.BloomPlanConfig,
            "compaction",
            True,
        ),
        (
            REPO_ROOT / "evals/exploratory/bloom/v0.1/config.json",
            exploratory.BloomPlanConfig,
            "unexpected",
            "field",
        ),
    ],
)
def test_exploratory_config_controls_are_closed(
    config_path: Path,
    config_type: type[exploratory.PetriPlanConfig] | type[exploratory.BloomPlanConfig],
    field: str,
    value: object,
) -> None:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload[field] = value
    with pytest.raises(ValidationError):
        config_type.model_validate(payload)


def _copy_content_root(tmp_path: Path, manifest_path: Path) -> tuple[ProtocolManifest, Path]:
    manifest = load_manifest(manifest_path)
    assert manifest.exploratory_lane is not None
    fake_repo = tmp_path / "repo"
    source = REPO_ROOT / manifest.exploratory_lane.content_root
    destination = fake_repo / manifest.exploratory_lane.content_root
    destination.parent.mkdir(parents=True)
    shutil.copytree(source, destination)
    return manifest, fake_repo


def test_content_inventory_rejects_unbound_files(tmp_path: Path) -> None:
    manifest, fake_repo = _copy_content_root(tmp_path, PETRI_MANIFEST)
    root = fake_repo / manifest.exploratory_lane.content_root  # type: ignore[union-attr]
    (root / "unbound.md").write_text("not bound", encoding="utf-8")
    with pytest.raises(ValueError, match="inventory is not closed"):
        exploratory.verify_content_bindings(manifest, fake_repo)


def test_content_inventory_rejects_symlinked_root(tmp_path: Path) -> None:
    manifest = load_manifest(PETRI_MANIFEST)
    assert manifest.exploratory_lane is not None
    fake_repo = tmp_path / "repo"
    real = fake_repo / "real-content"
    shutil.copytree(REPO_ROOT / manifest.exploratory_lane.content_root, real)
    declared = fake_repo / manifest.exploratory_lane.content_root
    declared.parent.mkdir(parents=True)
    declared.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink components"):
        exploratory.verify_content_bindings(manifest, fake_repo)


def test_frontmatter_duplicate_keys_and_version_comment_bypass_are_rejected(
    tmp_path: Path,
) -> None:
    duplicate = tmp_path / "seed.md"
    duplicate.write_text(
        "---\nid: seed\nversion: wrong\nversion: atb-seed-v0.1\n---\nbody\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="invalid exploratory YAML frontmatter"):
        exploratory._read_frontmatter(duplicate)


def test_manifest_loader_rejects_duplicate_json_keys(tmp_path: Path) -> None:
    text = PETRI_MANIFEST.read_text(encoding="utf-8")
    text = text.replace(
        '"protocol_id": "atb-petri-discovery-v0.1",',
        '"protocol_id": "atb-petri-discovery-v0.1",\n  "protocol_id": "shadow",',
        1,
    )
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        load_manifest(duplicate)


def test_confirmatory_runtime_package_set_is_not_retroactively_expanded() -> None:
    manifest = load_manifest(REPO_ROOT / "evals/manifests/inspect-canary-v0.1.json")
    packages = runner.expected_runtime_packages(manifest)
    assert packages == {
        "agency-transfer-evals": "0.1.0",
        "anthropic": "0.121.0",
        "google-genai": "1.75.0",
        "inspect-ai": "0.3.257",
        "inspect-evals": "0.16.0",
        "inspect-scout": "0.4.46",
        "mistralai": "2.9.2",
        "openai": "2.54.0",
        "pydantic": "2.13.4",
    }
