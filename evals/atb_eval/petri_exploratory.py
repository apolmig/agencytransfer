"""Network-free validation for the blocked Petri/Bloom exploratory lane.

This module only verifies pinned packages, content bindings, and construction of
the official Inspect tasks over benign fixtures. It deliberately exposes no
execution path and never resolves model roles or credentials.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import os
import socket
import tomllib
from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal
from unittest.mock import patch

import yaml
from pydantic import BaseModel, ConfigDict

from atb_eval.manifest import (
    EXPLORATORY_TASK_KINDS,
    ExploratoryContentBinding,
    ProtocolManifest,
    load_manifest_with_hash,
    sha256_file,
)

TASK_PACKAGE_PINS = {
    "inspect-petri": "3.0.11",
    "petri-bloom": "0.2.6",
}
PLAN_RUNTIME_PINS = {
    **TASK_PACKAGE_PINS,
    "inspect-ai": "0.3.257",
    "inspect-scout": "0.4.46",
    "pyyaml": "6.0.3",
}
IMPORT_CONTRACT = {
    "petri_discovery": ("inspect_petri", "audit"),
    "bloom_discovery": ("petri_bloom", "bloom_audit"),
}
CREDENTIAL_ENV_NAMES = frozenset(
    {
        "ANTHROPIC_API_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AZURE_OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "MISTRAL_API_KEY",
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "OPENROUTER_MANAGEMENT_KEY",
    }
)


class _StrictConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PetriPlanConfig(_StrictConfig):
    schema_version: Literal["atb-petri-config-v0.1"]
    engine: Literal["inspect-petri"]
    engine_version: Literal["3.0.11"]
    lane: Literal["exploratory"]
    execution_status: Literal["blocked"]
    roles: list[Literal["auditor", "target", "judge"]]
    seed_set_version: Literal["atb-petri-benign-seeds-v0.1"]
    dimension_set_version: Literal["atb-petri-agency-dimensions-v0.1"]
    max_turns: Literal[4]
    compaction: Literal[False]
    cache: Literal[False]
    enable_prefill: Literal[False]
    enable_rollback: Literal[False]
    target_tools: Literal["none"]
    realism_filter: Literal[False]
    turn_counter: Literal[False]
    target_display_name: Literal["planning assistant"]
    epochs: Literal[1]
    reproducibility_blockers: tuple[
        Literal[
            "Petri auditor prompt contains a runtime date unless wrapped and postflight-verified"
        ],
        Literal[
            "ATB has not implemented role-aware route, retry, cost, rollback-branch, "
            "or transcript postflight"
        ],
        Literal[
            "Model-role generation seeds and effective parameters are not transmitted or audited"
        ],
    ]
    interpretation: Literal[
        "hypothesis discovery only; scores do not estimate prevalence or benchmark rank"
    ]


class BloomPlanConfig(_StrictConfig):
    schema_version: Literal["atb-bloom-config-v0.1"]
    engine: Literal["petri-bloom"]
    engine_version: Literal["0.2.6"]
    lane: Literal["exploratory"]
    execution_status: Literal["blocked"]
    roles: list[Literal["scenarios", "auditor", "target", "judge"]]
    behavior_seed_version: Literal["atb-bloom-agency-behavior-v0.1"]
    scenario_set_version: Literal["atb-bloom-benign-scenarios-v0.1"]
    dimension_set_version: Literal["atb-bloom-agency-dimensions-v0.1"]
    scenario_source: Literal["human-authored mock fixtures; not Bloom-generated evidence"]
    num_scenarios: Literal[2]
    max_turns: Literal[4]
    compaction: Literal[False]
    enable_prefill: Literal[False]
    enable_rollback: Literal[False]
    realism_filter: Literal[False]
    target_tools: Literal["none"]
    turn_counter: Literal[False]
    epochs: Literal[1]
    reproducibility_blockers: tuple[
        Literal["Bloom scenario generation has not been executed or frozen"],
        Literal["Bloom does not expose Petri target_display_name in its standard task surface"],
        Literal[
            "ATB has not implemented role-aware route, retry, cost, or multi-turn "
            "transcript postflight"
        ],
        Literal[
            "Model-role generation seeds and effective parameters are not transmitted or audited"
        ],
    ]
    interpretation: Literal[
        "suite-design exploration only; scores do not estimate prevalence or benchmark rank"
    ]


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid exploratory JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"exploratory JSON must be an object: {path}")
    return value


class _UniqueSafeLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(
    loader: _UniqueSafeLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _read_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"invalid exploratory markdown: {path}") from exc
    if not text.startswith("---\n"):
        raise ValueError(f"exploratory markdown requires YAML frontmatter: {path}")
    try:
        end = text.index("\n---\n", 4)
        frontmatter = yaml.load(text[4:end], Loader=_UniqueSafeLoader)
    except (ValueError, yaml.YAMLError) as exc:
        raise ValueError(f"invalid exploratory YAML frontmatter: {path}") from exc
    if not isinstance(frontmatter, dict):
        raise ValueError(f"exploratory frontmatter must be an object: {path}")
    return frontmatter, text[end + 5 :].strip()


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def verify_dependency_contract(manifest: ProtocolManifest, repo_root: Path) -> dict[str, str]:
    """Verify exact exploratory runtime declarations and lockfile pins."""

    expected = TASK_PACKAGE_PINS.get(manifest.task.package)
    if expected is None or manifest.task.package_version != expected:
        raise ValueError("manifest does not use a supported exploratory package pin")

    project = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    declared = set(project["project"]["dependencies"])
    expected_declarations = {f"{name}=={version}" for name, version in PLAN_RUNTIME_PINS.items()}
    if not expected_declarations.issubset(declared):
        raise ValueError("pyproject exploratory dependency pins are not exact")

    lock = tomllib.loads((repo_root / "uv.lock").read_text(encoding="utf-8"))
    locked = {package["name"]: package["version"] for package in lock["package"]}
    for name, version in PLAN_RUNTIME_PINS.items():
        if locked.get(name) != version:
            raise ValueError(f"uv.lock must pin {name}=={version}")
        if importlib.metadata.version(name) != version:
            raise ValueError(f"installed exploratory runtime must be {name}=={version}")
    return dict(PLAN_RUNTIME_PINS)


def _safe_bound_path(
    repo_root: Path,
    binding: ExploratoryContentBinding,
) -> Path:
    path = repo_root / binding.path
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"exploratory content must be a regular non-symlink file: {binding.path}")
    try:
        path.resolve().relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError("exploratory content resolves outside the repository") from exc
    if sha256_file(path) != binding.sha256:
        raise ValueError(f"exploratory content hash mismatch: {binding.path}")
    _verify_content_identity(binding, path)
    return path


def _verify_content_identity(binding: ExploratoryContentBinding, path: Path) -> None:
    if path.suffix == ".json":
        payload = _read_json(path)
        if payload.get("schema_version") != binding.content_version:
            raise ValueError(f"exploratory JSON version does not match binding: {binding.path}")
        expected_canary_ids = {
            "atb-petri-mock-canary-v0.1": "petri-benign-agency-canary-v0.1",
            "atb-bloom-mock-canary-v0.1": "bloom-benign-agency-canary-v0.1",
        }
        expected_canary = expected_canary_ids.get(binding.content_version)
        if expected_canary is not None and payload.get("canary_id") != expected_canary:
            raise ValueError(f"exploratory mock canary id is invalid: {binding.path}")
        return

    frontmatter, body = _read_frontmatter(path)
    if frontmatter.get("version") != binding.content_version or not body:
        raise ValueError(f"exploratory markdown version/body is invalid: {binding.path}")
    if binding.kind in {"seed", "scenario", "dimension"}:
        if frontmatter.get("id") != path.stem:
            raise ValueError(f"exploratory markdown id does not match filename: {binding.path}")
    elif binding.kind == "behavior_seed":
        if frontmatter.get("id") != "benign_preference_override_attempt":
            raise ValueError("Bloom behavior id is invalid")
        if (
            frontmatter.get("modality") != "conversation"
            or "target_sysprompt_prefix" in frontmatter
        ):
            raise ValueError("Bloom behavior must be conversation-only without target prefix")
    if binding.kind in {"seed", "scenario"} and frontmatter.get("tools") not in (None, []):
        raise ValueError("exploratory benign fixtures cannot expose tools")


def verify_content_bindings(
    manifest: ProtocolManifest,
    repo_root: Path,
) -> tuple[dict[str, Path], list[dict[str, str]]]:
    lane = manifest.exploratory_lane
    if lane is None or manifest.task.kind not in EXPLORATORY_TASK_KINDS:
        raise ValueError("manifest is not a Petri/Bloom exploratory plan")

    bound: dict[str, Path] = {}
    receipt: list[dict[str, str]] = []
    expected_paths: set[Path] = set()
    for item in lane.content:
        path = _safe_bound_path(repo_root, item)
        bound[item.content_id] = path
        expected_paths.add(path.resolve())
        receipt.append(
            {
                "content_id": item.content_id,
                "content_version": item.content_version,
                "kind": item.kind,
                "path": item.path,
                "sha256": item.sha256,
            }
        )

    declared_root = repo_root / lane.content_root
    current = repo_root
    for part in Path(lane.content_root).parts:
        current /= part
        if current.is_symlink():
            raise ValueError("exploratory content_root cannot contain symlink components")
    content_root = declared_root.resolve()
    if not content_root.is_dir():
        raise ValueError("exploratory content_root must be a regular directory")
    actual_paths = {
        path.resolve()
        for path in content_root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    if any(path.is_symlink() for path in content_root.rglob("*")):
        raise ValueError("exploratory content_root cannot contain symlinks")
    if actual_paths != expected_paths:
        extra = sorted(str(path.relative_to(repo_root)) for path in actual_paths - expected_paths)
        missing = sorted(str(path.relative_to(repo_root)) for path in expected_paths - actual_paths)
        raise ValueError(
            f"exploratory content inventory is not closed; extra={extra}, missing={missing}"
        )

    _verify_config(manifest, lane.content, repo_root)
    _verify_mock_canary(manifest, lane.content, repo_root)
    _verify_engine_input_inventory(manifest, lane.content, repo_root)
    return bound, sorted(receipt, key=lambda item: item["content_id"])


def _one_binding(content: list[ExploratoryContentBinding], kind: str) -> ExploratoryContentBinding:
    matches = [item for item in content if item.kind == kind]
    if len(matches) != 1:
        raise ValueError(f"exploratory plan requires exactly one {kind}")
    return matches[0]


def _verify_config(
    manifest: ProtocolManifest,
    content: list[ExploratoryContentBinding],
    repo_root: Path,
) -> None:
    lane = manifest.exploratory_lane
    assert lane is not None
    config = _validated_config(manifest, content, repo_root)
    if config.roles != lane.roles or config.engine_version != manifest.task.package_version:
        raise ValueError("exploratory config does not match its manifest contract")


def _validated_config(
    manifest: ProtocolManifest,
    content: list[ExploratoryContentBinding],
    repo_root: Path,
) -> PetriPlanConfig | BloomPlanConfig:
    payload = _read_json(repo_root / _one_binding(content, "config").path)
    config_type = PetriPlanConfig if manifest.task.kind == "petri_discovery" else BloomPlanConfig
    return config_type.model_validate(payload)


def _verify_mock_canary(
    manifest: ProtocolManifest,
    content: list[ExploratoryContentBinding],
    repo_root: Path,
) -> None:
    lane = manifest.exploratory_lane
    assert lane is not None
    canary = _read_json(repo_root / _one_binding(content, "mock_canary").path)
    if canary.get("network_calls") != 0 or canary.get("roles") != lane.roles:
        raise ValueError("mock canary must be network-free and use the exact role contract")
    expected = canary.get("expected")
    if not isinstance(expected, dict):
        raise ValueError("mock canary lacks an expected result")
    if manifest.task.kind == "petri_discovery":
        messages = canary.get("messages")
        if not isinstance(messages, list) or [row.get("role") for row in messages] != lane.roles:
            raise ValueError("Petri mock canary role sequence is invalid")
        if expected != {"dimension": "agency_override_attempt", "score": 1}:
            raise ValueError("Petri mock canary expected score is invalid")
    else:
        if expected != {
            "generated_scenarios": 0,
            "mock_scenarios": lane.expected_plan_items,
            "execution_status": "blocked",
        }:
            raise ValueError("Bloom mock canary cannot claim generated scenarios or execution")
        scenario_ids = sorted(Path(item.path).stem for item in content if item.kind == "scenario")
        if canary.get("scenario_ids") != scenario_ids:
            raise ValueError("Bloom mock canary does not bind the exact scenario ids")


def _verify_engine_input_inventory(
    manifest: ProtocolManifest,
    content: list[ExploratoryContentBinding],
    repo_root: Path,
) -> None:
    lane = manifest.exploratory_lane
    assert lane is not None
    root = repo_root / lane.content_root
    if manifest.task.kind == "petri_discovery":
        expected_seeds = {repo_root / item.path for item in content if item.kind == "seed"}
        expected_dimensions = {
            repo_root / item.path for item in content if item.kind == "dimension"
        }
        if set((root / "seeds").glob("*.md")) != expected_seeds:
            raise ValueError("Petri seed directory contains an unbound or missing seed")
        if set((root / "dimensions").glob("*.md")) != expected_dimensions:
            raise ValueError("Petri dimension directory contains an unbound or missing rubric")
    else:
        behavior = _one_binding(content, "behavior_seed")
        if Path(behavior.path) != Path(lane.content_root) / "BEHAVIOR.md":
            raise ValueError("Bloom behavior binding must be the official BEHAVIOR.md input")
        expected_scenarios = {repo_root / item.path for item in content if item.kind == "scenario"}
        expected_dimensions = {
            repo_root / item.path for item in content if item.kind == "dimension"
        }
        if set((root / "scenarios/seeds").glob("*.md")) != expected_scenarios:
            raise ValueError("Bloom scenario directory contains an unbound or missing seed")
        if set((root / "scenarios/dimensions").glob("*.md")) != expected_dimensions:
            raise ValueError("Bloom dimension directory contains an unbound or missing rubric")
        if (root / "scenarios/understanding.md").exists():
            raise ValueError("Bloom plan cannot load an unbound generated understanding")
        examples = root / "examples"
        if examples.exists() and any(path.is_file() for path in examples.rglob("*")):
            raise ValueError("Bloom plan cannot load unbound behavior examples")


@contextmanager
def _without_provider_credentials() -> Iterator[None]:
    saved = {name: os.environ.pop(name) for name in CREDENTIAL_ENV_NAMES if name in os.environ}
    try:
        yield
    finally:
        for name in CREDENTIAL_ENV_NAMES:
            os.environ.pop(name, None)
        os.environ.update(saved)


def _blocked_network(*args: object, **kwargs: object) -> None:
    raise RuntimeError("network access is forbidden during exploratory task construction")


def verify_official_task_construction(
    manifest: ProtocolManifest,
    repo_root: Path,
) -> dict[str, Any]:
    """Import pinned packages and construct their official task without model calls."""

    lane = manifest.exploratory_lane
    if lane is None:
        raise ValueError("missing exploratory lane")
    module_name, factory_name = IMPORT_CONTRACT[manifest.task.kind]
    actual_version = importlib.metadata.version(manifest.task.package)
    if actual_version != manifest.task.package_version:
        raise ValueError(
            f"installed {manifest.task.package} is {actual_version}; "
            f"expected {manifest.task.package_version}"
        )

    config = _validated_config(manifest, lane.content, repo_root)

    with (
        _without_provider_credentials(),
        patch.object(socket.socket, "connect", _blocked_network),
        patch.object(socket.socket, "connect_ex", _blocked_network),
    ):
        module = importlib.import_module(module_name)
        factory = getattr(module, factory_name, None)
        if not callable(factory):
            raise ValueError(f"{module_name}.{factory_name} is not callable")
        root = repo_root / lane.content_root
        if manifest.task.kind == "petri_discovery":
            assert isinstance(config, PetriPlanConfig)
            task = factory(
                seed_instructions=str(root / "seeds"),
                judge_dimensions=str(root / "dimensions"),
                max_turns=config.max_turns,
                compaction=config.compaction,
                enable_prefill=config.enable_prefill,
                enable_rollback=config.enable_rollback,
                target_tools=config.target_tools,
                realism_filter=config.realism_filter,
                turn_counter=config.turn_counter,
                cache=config.cache,
                target_display_name=config.target_display_name,
            )
        else:
            assert isinstance(config, BloomPlanConfig)
            task = factory(
                root,
                max_turns=config.max_turns,
                enable_prefill=config.enable_prefill,
                enable_rollback=config.enable_rollback,
                compaction=config.compaction,
                realism_filter=config.realism_filter,
                turn_counter=config.turn_counter,
            )
        injected_credentials = sorted(CREDENTIAL_ENV_NAMES.intersection(os.environ))
        if injected_credentials:
            raise ValueError(
                "exploratory task construction populated provider credential variables: "
                + ", ".join(injected_credentials)
            )

    from inspect_ai import Task
    from inspect_ai._util.registry import registry_info

    if not isinstance(task, Task):
        raise ValueError("official exploratory factory did not construct an Inspect Task")
    if registry_info(task).name != manifest.task.registry_name:
        raise ValueError("constructed task registry identity does not match manifest")
    if str(task.version) != manifest.task.version:
        raise ValueError("constructed task version does not match manifest")

    expected_ids = sorted(
        Path(item.path).stem
        for item in lane.content
        if item.kind in ({"seed"} if manifest.task.kind == "petri_discovery" else {"scenario"})
    )
    samples = list(task.dataset)
    actual_ids = sorted(str(sample.id) for sample in samples)
    if actual_ids != expected_ids or len(samples) != lane.expected_plan_items:
        raise ValueError("official task did not load exactly the bound benign fixtures")
    projection = [
        {
            "id": str(sample.id),
            "input": sample.input,
            "metadata": sample.metadata,
        }
        for sample in sorted(samples, key=lambda sample: str(sample.id))
    ]
    return {
        "package": manifest.task.package,
        "package_version": actual_version,
        "module": module_name,
        "factory": factory_name,
        "task_registry_name": registry_info(task).name,
        "task_version": str(task.version),
        "sample_ids": actual_ids,
        "dataset_projection_sha256": _canonical_sha256(projection),
        "network_calls": 0,
        "provider_key_env_absent": sorted(CREDENTIAL_ENV_NAMES),
        "model_roles_resolved": False,
        "model_calls": 0,
    }


def build_exploratory_plan(manifest_path: Path, repo_root: Path | None = None) -> dict[str, Any]:
    """Return a content-bound, non-executable plan receipt."""

    root = (repo_root or repository_root()).resolve()
    manifest, manifest_hash = load_manifest_with_hash(manifest_path.resolve())
    if manifest.task.kind not in EXPLORATORY_TASK_KINDS:
        raise ValueError("atb-exploratory-plan only accepts Petri/Bloom discovery manifests")
    packages = verify_dependency_contract(manifest, root)
    _, content = verify_content_bindings(manifest, root)
    import_canary = verify_official_task_construction(manifest, root)
    lane = manifest.exploratory_lane
    assert lane is not None
    receipt: dict[str, Any] = {
        "schema_version": "atb-exploratory-plan-receipt-v0.1",
        "protocol_id": manifest.protocol_id,
        "manifest_sha256": manifest_hash,
        "status": manifest.status.value,
        "lane": lane.lane,
        "engine": lane.engine,
        "roles": lane.roles,
        "execution_status": lane.execution_status,
        "paid": False,
        "public_aggregate_candidate": False,
        "input_release_tier": manifest.dataset.release_tier.value,
        "generated_artifact_release_tier": manifest.release.raw_logs.value,
        "dependency_pins": packages,
        "content": content,
        "official_task_canary": import_canary,
    }
    receipt["plan_sha256"] = _canonical_sha256(receipt)
    return receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        receipt = build_exploratory_plan(args.manifest)
        print(json.dumps(receipt, indent=2, sort_keys=True))
    except (OSError, RuntimeError, ValueError, importlib.metadata.PackageNotFoundError) as exc:
        raise SystemExit(f"exploratory plan validation failed: {exc}") from exc


if __name__ == "__main__":
    main()
