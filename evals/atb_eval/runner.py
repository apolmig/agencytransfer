"""Manifest-driven Inspect runner.

Dry-run is the default. Paid execution requires a frozen manifest, an explicit
flag, present credentials, and a controlled log directory outside this repo.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import os
import secrets
import stat
import subprocess
import tomllib
from hashlib import sha256
from pathlib import Path
from typing import Any

from inspect_ai import Task, eval_set
from inspect_ai.log import read_eval_log
from inspect_ai.model import GenerateConfig, Model, get_model
from inspect_evals.ape import ape_eval
from inspect_evals.ape.prompts import USER_OR_ASSISTANT1, USER_OR_ASSISTANT2
from inspect_evals.utils import create_stable_id

from atb_eval.manifest import (
    ModelCondition,
    ProtocolManifest,
    ProtocolStatus,
    forbidden_runtime_overrides,
    load_manifest_with_hash,
    missing_credentials,
    require_controlled_log_dir,
    require_path_outside_repo,
    sha256_file,
    verify_committed_file,
    verify_model_revision_evidence,
    verify_source_checkout,
)
from atb_eval.scorers import ACTIONABILITY_PROMPT, RESPONSE_CLASS_PROMPT
from atb_eval.tasks.canary import inspect_canary
from atb_eval.tasks.diselect import diselect_pilot

HARNESS_PACKAGE = "agency-transfer-evals"
HARNESS_VERSION = "0.1.0"
INSPECT_PACKAGE = "inspect-ai"
INSPECT_VERSION = "0.3.257"
NATIVE_RESPONSE_CLASSES = {"comply", "soft_refuse", "refuse", "incoherent"}
PAIRED_SCHEDULE = "paired-concurrent-sample-order-v0.1"
DIRECT_RUNTIME_PACKAGES = {
    HARNESS_PACKAGE,
    "anthropic",
    "google-genai",
    INSPECT_PACKAGE,
    "inspect-evals",
    "inspect-scout",
    "mistralai",
    "openai",
    "pydantic",
}


def repository_root() -> Path:
    """Return the public repository root containing ``evals/``."""

    return Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--log-dir", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--allow-paid",
        action="store_true",
        help="Acknowledge that the frozen manifest may make paid API calls.",
    )
    return parser.parse_args()


def build_task(manifest: ProtocolManifest, source_dir: Path | None) -> Task:
    spec = manifest.task
    if spec.kind == "canary":
        return inspect_canary()
    if spec.kind == "diselect":
        if source_dir is None:
            raise ValueError("DisElect requires --source-dir pointing to the pinned checkout")
        return diselect_pilot(
            source_dir=str(source_dir.resolve()),
            source_revision=manifest.dataset.source_revision,
            **spec.args,
        )
    if spec.kind == "ape":
        if source_dir is None:
            raise ValueError("native APE requires --source-dir pointing to the pinned checkout")
        args = dict(spec.args)
        if isinstance(args.get("belief_range"), list):
            args["belief_range"] = tuple(args["belief_range"])
        task = ape_eval(**args)
        verify_ape_dataset(task, source_dir.resolve(), args.get("categories"))
        return task
    raise AssertionError(f"unsupported task kind: {spec.kind}")


def verify_ape_dataset(task: Task, source_dir: Path, categories: list[str] | None) -> None:
    topics_path = source_dir / "src/topics/diverse_topics.jsonl"
    expected: dict[str, tuple[str, str, str, str]] = {}
    with topics_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                row = json.loads(line)
                category = row["category"]
                text = row["text"]
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                raise ValueError(f"invalid pinned APE topic at line {line_number}") from exc
            if categories is not None and category not in categories:
                continue
            text = text.replace("{user_or_assistant1}", USER_OR_ASSISTANT1)
            text = text.replace("{user_or_assistant2}", USER_OR_ASSISTANT2)
            sample_id = create_stable_id(text, prefix="ape")
            if sample_id in expected:
                raise ValueError("pinned APE topics do not produce unique stable sample ids")
            expected[sample_id] = (
                str(category),
                str(row.get("short_title", "")),
                str(row.get("subject", "")),
                text,
            )
    actual = {
        str(sample.id): (
            str((sample.metadata or {}).get("category", "")),
            str((sample.metadata or {}).get("short_title", "")),
            str((sample.metadata or {}).get("subject", "")),
            str(sample.input),
        )
        for sample in task.dataset
    }
    if len(actual) != len(task.dataset) or actual != expected:
        raise ValueError("native APE cached dataset does not match the pinned source checkout")


def build_model(condition: ModelCondition, run_max_connections: int, max_retries: int) -> Model:
    config_values: dict[str, Any] = dict(condition.generate_config)
    config_values.setdefault("max_connections", run_max_connections)
    config_values.setdefault("max_retries", max_retries)
    return get_model(
        condition.model,
        config=GenerateConfig(**config_values),
        api_key=os.environ.get(condition.api_key_env) if condition.api_key_env else None,
        **condition.inspect_model_args(),
    )


def expected_served_model(condition: ModelCondition) -> str:
    if condition.model.startswith("mockllm/"):
        return "mockllm"
    return condition.model.partition("/")[2]


def effective_generate_config(
    condition: ModelCondition, manifest: ProtocolManifest
) -> dict[str, Any]:
    config = dict(condition.generate_config)
    config.setdefault("max_connections", manifest.run.max_connections)
    config.setdefault("max_retries", manifest.run.max_retries)
    return config


def effective_event_generate_config(
    condition: ModelCondition,
    manifest: ProtocolManifest,
    role: str | None = None,
) -> dict[str, Any]:
    """Resolve the settings Inspect actually attaches to each model call."""

    config = effective_generate_config(condition, manifest)
    target_call = role is None or role == "persuader"
    if manifest.task.kind == "diselect" and target_call:
        config["temperature"] = manifest.task.args["temperature"]
        config["max_tokens"] = manifest.task.args["max_tokens"]
    elif manifest.task.kind == "ape":
        config["temperature"] = manifest.task.args["temperature"]
    config["seed"] = manifest.run.seed
    return config


def generate_config_matches(config: Any, expected: dict[str, Any]) -> bool:
    return config.model_dump() == GenerateConfig(**expected).model_dump()


def request_parameters_match(
    request: Any,
    condition: ModelCondition,
    expected: dict[str, Any],
) -> bool:
    if condition.model.startswith("mockllm/"):
        return True
    if not isinstance(request, dict):
        return False
    service = condition.model.partition("/")[0]
    if service not in {"openai", "openrouter", "mistral"}:
        return False
    if request.get("model") != expected_served_model(condition):
        return False
    if not isinstance(request.get("messages"), list):
        return False
    header_field = "http_headers" if service == "mistral" else "extra_headers"
    headers = request.get(header_field)
    if (
        not isinstance(headers, dict)
        or set(headers) != {"x-irid"}
        or not isinstance(headers["x-irid"], str)
        or not headers["x-irid"]
    ):
        return False

    fields = {"temperature": "temperature", "top_p": "top_p"}
    fields["seed"] = "random_seed" if service == "mistral" else "seed"
    for config_key, request_key in fields.items():
        value = expected.get(config_key)
        if request.get(request_key) != value:
            return False

    max_tokens = expected.get("max_tokens")
    token_keys = (
        ("max_tokens", "max_completion_tokens")
        if service in {"openai", "openrouter"}
        else ("max_tokens",)
    )
    transmitted = [request.get(key) for key in token_keys if request.get(key) is not None]
    if max_tokens is not None:
        if transmitted != [max_tokens]:
            return False
    elif transmitted:
        return False

    reasoning_effort = expected.get("reasoning_effort")
    reasoning_tokens = expected.get("reasoning_tokens")
    if service == "openrouter":
        extra_body = request.get("extra_body")
        if not isinstance(extra_body, dict) or extra_body.get("provider") != (
            condition.inspect_model_args().get("provider")
        ):
            return False
        expected_extra_keys = {"provider"}
        if reasoning_effort is not None or reasoning_tokens is not None:
            expected_extra_keys.add("reasoning")
        if set(extra_body) != expected_extra_keys:
            return False
        reasoning = extra_body.get("reasoning")
        if reasoning_effort is not None:
            expected_effort = "xhigh" if reasoning_effort == "max" else reasoning_effort
            if reasoning != {"effort": expected_effort}:
                return False
        if reasoning_tokens is not None and reasoning != {"max_tokens": reasoning_tokens}:
            return False
        if request.get("reasoning_effort") is not None:
            return False
    elif reasoning_tokens is not None:
        return False
    elif reasoning_effort is not None:
        expected_effort = (
            "high" if service == "mistral" and reasoning_effort != "none" else reasoning_effort
        )
        if request.get("reasoning_effort") != expected_effort:
            return False
    elif request.get("reasoning_effort") is not None:
        return False

    forbidden_request_fields = {
        "frequency_penalty",
        "logit_bias",
        "logprobs",
        "n",
        "parallel_tool_calls",
        "presence_penalty",
        "response_format",
        "stop",
        "top_logprobs",
        "tool_choice",
    }
    if any(request.get(key) is not None for key in forbidden_request_fields):
        return False
    if request.get("tools") not in (None, []):
        return False
    common_allowed = {"messages", "model", "tool_choice", "tools", header_field}
    service_allowed = {
        "openai": {
            "max_completion_tokens",
            "max_tokens",
            "reasoning_effort",
            "seed",
            "temperature",
            "top_p",
        },
        "openrouter": {
            "extra_body",
            "max_completion_tokens",
            "max_tokens",
            "seed",
            "temperature",
            "top_p",
        },
        "mistral": {
            "max_tokens",
            "random_seed",
            "reasoning_effort",
            "temperature",
            "top_p",
        },
    }[service]
    if set(request) - common_allowed - service_allowed:
        return False
    return service == "openrouter" or request.get("extra_body") in (None, {})


def condition_execution_signature(condition: ModelCondition, manifest: ProtocolManifest) -> str:
    material = json.dumps(
        {
            "model": condition.model,
            "model_args": condition.inspect_model_args(),
            "generate_config": effective_generate_config(condition, manifest),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return sha256(material).hexdigest()


def condition_map(manifest: ProtocolManifest) -> dict[str, str]:
    return {
        condition.condition_id: condition_execution_signature(condition, manifest)
        for condition in manifest.models
    }


def log_matches_condition(log: Any, condition: ModelCondition, manifest: ProtocolManifest) -> bool:
    if log.eval.model != condition.model:
        return False
    if (log.eval.model_args or {}) != condition.inspect_model_args():
        return False
    return generate_config_matches(
        log.eval.model_generate_config,
        effective_generate_config(condition, manifest),
    )


def paired_dataset_identity(log: Any) -> tuple[tuple[str, ...], tuple[tuple[str, int, str], ...]]:
    """Return a content-bound identity for the shared paired sample schedule."""

    sample_ids = tuple(str(sample_id) for sample_id in (log.eval.dataset.sample_ids or []))
    inventory: list[tuple[str, int, str]] = []
    for sample in log.samples or []:
        dumped = sample.model_dump(mode="json")
        material = json.dumps(
            {"input": dumped.get("input"), "metadata": dumped.get("metadata")},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        inventory.append((str(sample.id), int(sample.epoch), sha256(material).hexdigest()))
    return sample_ids, tuple(sorted(inventory))


def dataset_inventory_sha256(samples: Any) -> str:
    """Hash selected sample IDs, exact inputs, and all stratum/provenance metadata."""

    inventory: dict[str, dict[str, Any]] = {}
    for sample in samples:
        if hasattr(sample, "model_dump"):
            dumped = sample.model_dump(mode="json")
            sample_input = dumped.get("input")
            metadata = dumped.get("metadata") or {}
        else:
            sample_input = getattr(sample, "input", None)
            metadata = getattr(sample, "metadata", None) or {}
        item = {"id": str(sample.id), "input": sample_input, "metadata": metadata}
        if item["id"] in inventory and inventory[item["id"]] != item:
            raise ValueError(f"dataset id {item['id']} maps to inconsistent content")
        inventory[item["id"]] = item
    canonical = json.dumps(
        [inventory[item_id] for item_id in sorted(inventory)],
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return sha256(canonical).hexdigest()


def task_retry_chain_failures(logs: list[Any], manifest: ProtocolManifest) -> list[str]:
    """Require one successful, non-retried Inspect log per condition."""

    failures: list[str] = []
    grouped: dict[str, list[Any]] = {condition.condition_id: [] for condition in manifest.models}
    shared_run_ids: set[str] = set()
    eval_ids: set[str] = set()
    condition_task_ids: dict[str, str] = {}
    for log in logs:
        matches = [
            condition
            for condition in manifest.models
            if log_matches_condition(log, condition, manifest)
        ]
        if len(matches) != 1:
            failures.append("eval log does not map to exactly one frozen condition")
            continue
        condition_id = matches[0].condition_id
        grouped[condition_id].append(log)
        run_id = str(log.eval.run_id or "")
        eval_id = str(log.eval.eval_id or "")
        task_id = str(log.eval.task_id or "")
        if not run_id:
            failures.append(f"{condition_id}: eval log lacks run_id")
        else:
            shared_run_ids.add(run_id)
        if not eval_id:
            failures.append(f"{condition_id}: eval log lacks eval_id")
        elif eval_id in eval_ids:
            failures.append(f"{condition_id}: duplicate eval_id")
        else:
            eval_ids.add(eval_id)
        if not task_id:
            failures.append(f"{condition_id}: eval log lacks task_id")
        else:
            condition_task_ids[condition_id] = task_id

    if logs and len(shared_run_ids) != 1:
        failures.append("all condition logs must share one Inspect run_id")
    task_ids = list(condition_task_ids.values())
    if len(task_ids) != len(set(task_ids)):
        failures.append("different frozen conditions must have distinct Inspect task_ids")

    for condition_id, condition_logs in grouped.items():
        if len(condition_logs) != 1:
            failures.append(f"{condition_id}: exactly one non-retried eval log is required")
            continue
        log = condition_logs[0]
        if str(log.status) != "success":
            failures.append(f"{condition_id}: the sole eval log must be successful")
        if log.samples is None:
            failures.append(f"{condition_id}: successful eval log lacks samples")
            continue
        if any(sample.error_retries for sample in log.samples):
            failures.append(f"{condition_id}: sample or task retry history is forbidden")
    return failures


def required_sample_roles(sample: Any, manifest: ProtocolManifest) -> set[str]:
    if manifest.task.kind == "ape":
        return set(manifest.model_roles)
    if manifest.task.kind != "diselect":
        return set()
    if not target_output_scorable(sample):
        return set()
    required = {"grader"}
    applicable_axes = (sample.metadata or {}).get("applicable_axes", [])
    if (
        manifest.task.args.get("include_actionability")
        and "operational_actionability" in applicable_axes
    ):
        required.add("mechanism_grader")
    return required


def target_output_scorable(sample: Any) -> bool:
    output = getattr(sample, "output", None)
    return bool(
        getattr(sample, "error", None) is None
        and output is not None
        and getattr(output, "error", None) is None
        and output.stop_reason not in {"content_filter", "max_tokens", "model_length"}
        and output.completion.strip()
    )


def sample_target_output_matches(sample: Any, target_roles: set[str | None] | None = None) -> bool:
    """Bind the sample's final target output to exactly one logged target call."""

    target_roles = target_roles or {None}
    target_events = [
        event
        for event in (sample.events or [])
        if type(event).__name__ == "ModelEvent" and getattr(event, "role", None) in target_roles
    ]
    if len(target_events) != 1:
        return False
    event_output = getattr(target_events[0], "output", None)
    sample_output = getattr(sample, "output", None)
    if event_output is None or sample_output is None:
        return False

    def serialise(output: Any) -> str:
        payload = output.model_dump(mode="json") if hasattr(output, "model_dump") else vars(output)
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)

    return serialise(event_output) == serialise(sample_output)


def _resolved_text(value: Any, sample: Any) -> str | None:
    if not isinstance(value, str):
        return None
    prefix = "attachment://"
    if value.startswith(prefix):
        return (sample.attachments or {}).get(value.removeprefix(prefix))
    return value


def _message_sequence(
    messages: Any,
    sample: Any,
    *,
    request_payload: bool = False,
) -> tuple[tuple[str, str], ...] | None:
    if not isinstance(messages, list):
        return None
    sequence: list[tuple[str, str]] = []
    for message in messages:
        if isinstance(message, dict):
            if request_payload and set(message) != {"role", "content"}:
                return None
            role = message.get("role")
            content = message.get("content")
        else:
            role = getattr(message, "role", None)
            dumped = message.model_dump(mode="json") if hasattr(message, "model_dump") else {}
            if dumped.get("metadata") is not None or any(
                dumped.get(field) is not None
                for field in ("tool_call_id", "tool_calls", "function", "error")
            ):
                return None
            content = getattr(message, "content", None)
        text = _resolved_text(content, sample)
        if not isinstance(role, str) or text is None:
            return None
        sequence.append((role, text))
    return tuple(sequence)


def _event_messages_match(
    event: Any,
    expected: tuple[tuple[str, str], ...],
    sample: Any,
    condition: ModelCondition,
    *,
    allow_missing_request: bool = False,
) -> bool:
    if _message_sequence(event.input, sample) != expected:
        return False
    if condition.model.startswith("mockllm/"):
        return True
    call = getattr(event, "call", None)
    request = getattr(call, "request", None) if call is not None else None
    if not isinstance(request, dict):
        return allow_missing_request
    request_messages = _message_sequence(request.get("messages"), sample, request_payload=True)
    if request_messages is None:
        return False
    if condition.model.startswith("openai/"):
        request_messages = tuple(
            ("system" if role == "developer" else role, text) for role, text in request_messages
        )
    return request_messages == expected


def sample_model_inputs_match(
    sample: Any, target: ModelCondition, manifest: ProtocolManifest
) -> bool:
    """Bind text-only target and judge calls to the frozen task prompts."""

    if manifest.task.kind not in {"canary", "diselect"} or not isinstance(sample.input, str):
        return manifest.task.kind not in {"canary", "diselect"}
    target_events = [
        event
        for event in (sample.events or [])
        if type(event).__name__ == "ModelEvent" and getattr(event, "role", None) is None
    ]
    if len(target_events) != 1:
        return False
    target_messages = (
        (("user", sample.input),)
        if manifest.task.kind == "canary"
        else (("system", "You are a helpful assistant."), ("user", sample.input))
    )
    target_event = target_events[0]
    if not _event_messages_match(
        target_event,
        target_messages,
        sample,
        target,
        allow_missing_request=bool(getattr(target_event, "error", None)),
    ):
        return False
    if manifest.task.kind == "canary":
        return True

    expected_role_prompts: dict[str, str] = {}
    for role in required_sample_roles(sample, manifest):
        if role == "grader":
            expected_role_prompts[role] = RESPONSE_CLASS_PROMPT.format(
                request=sample.input,
                response=sample.output.completion,
            )
        elif role == "mechanism_grader":
            expected_role_prompts[role] = ACTIONABILITY_PROMPT.format(
                request=sample.input,
                response=sample.output.completion,
            )
    role_events: dict[str, list[Any]] = {
        role: [
            event
            for event in (sample.events or [])
            if type(event).__name__ == "ModelEvent" and getattr(event, "role", None) == role
        ]
        for role in expected_role_prompts
    }
    for role, prompt in expected_role_prompts.items():
        if len(role_events[role]) != 1:
            return False
        role_event = role_events[role][0]
        if not _event_messages_match(
            role_event,
            (("user", prompt),),
            sample,
            manifest.model_roles[role],
            allow_missing_request=bool(getattr(role_event, "error", None)),
        ):
            return False
    return True


def official_base_url(condition: ModelCondition, value: str | None) -> bool:
    if value is None:
        return True
    service = condition.model.partition("/")[0]
    official = {
        "openrouter": "https://openrouter.ai/api/v1",
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com",
        "google": "https://generativelanguage.googleapis.com",
        "mistral": "https://api.mistral.ai/v1",
    }.get(service)
    return official is not None and value.rstrip("/") == official.rstrip("/")


def _events_routes_match(
    events: list[Any] | None,
    target: ModelCondition,
    model_roles: dict[str, ModelCondition] | None = None,
    *,
    target_roles: set[str | None] | None = None,
    required_roles: set[str] | None = None,
    manifest: ProtocolManifest | None = None,
    require_target: bool,
    allow_failed_response: bool,
) -> bool:
    model_roles = model_roles or {}
    target_roles = target_roles or {None}
    required_roles = required_roles or set()
    target_seen = False
    seen_roles: set[str] = set()
    for event in events or []:
        if type(event).__name__ != "ModelEvent":
            continue
        event_role = getattr(event, "role", None)
        if event_role in target_roles:
            configured = target
            target_seen = True
        elif isinstance(event_role, str) and event_role in model_roles:
            configured = model_roles[event_role]
            seen_roles.add(event_role)
        else:
            return False
        if getattr(event, "retries", 0) not in {None, 0}:
            return False
        if getattr(event, "tools", None):
            return False
        if event.model != configured.model:
            return False
        expected = expected_served_model(configured)
        output = getattr(event, "output", None)
        call = getattr(event, "call", None)
        event_failed = bool(getattr(event, "error", None)) or bool(getattr(call, "error", None))
        if event_failed and str(getattr(output, "completion", "") or "").strip():
            return False
        if (
            output is None
            or output.fallback is not None
            or (
                output.model != expected and not (event_failed and output.model == configured.model)
            )
        ):
            return False
        if any(
            getattr(choice.message, "tool_calls", None)
            for choice in (getattr(output, "choices", None) or [])
        ):
            return False
        if manifest is not None:
            event_config = getattr(event, "config", None)
            if event_config is None:
                return False
            if not generate_config_matches(
                event_config,
                effective_event_generate_config(configured, manifest, event_role),
            ):
                return False
            request = getattr(call, "request", None) if call is not None else None
            if configured.model.startswith("mockllm/") and request is None:
                pass
            elif isinstance(request, dict) and request:
                if not request_parameters_match(
                    request,
                    configured,
                    effective_event_generate_config(configured, manifest, event_role),
                ):
                    return False
            elif not (allow_failed_response and event_failed):
                return False
        if configured.route is not None:
            response = getattr(call, "response", None) if call is not None else None
            response_matches = (
                isinstance(response, dict)
                and response.get("provider") == (configured.route.provider_only[0])
            )
            if isinstance(response, dict) and response.get("provider") not in {
                None,
                configured.route.provider_only[0],
            }:
                return False
            if not response_matches and not (allow_failed_response and event_failed):
                return False
    roles_match = (
        seen_roles == required_roles if require_target else required_roles.issubset(seen_roles)
    )
    return (target_seen or not require_target) and roles_match


def sample_routes_match(
    sample: Any,
    target: ModelCondition,
    model_roles: dict[str, ModelCondition] | None = None,
    *,
    target_roles: set[str | None] | None = None,
    required_roles: set[str] | None = None,
    manifest: ProtocolManifest | None = None,
) -> bool:
    return _events_routes_match(
        sample.events,
        target,
        model_roles,
        target_roles=target_roles,
        required_roles=required_roles,
        manifest=manifest,
        require_target=True,
        allow_failed_response=True,
    )


def retry_events_routes_match(
    retry: Any,
    target: ModelCondition,
    model_roles: dict[str, ModelCondition] | None = None,
    *,
    target_roles: set[str | None] | None = None,
    manifest: ProtocolManifest | None = None,
) -> bool:
    """Validate every model call retained from a failed sample attempt."""

    return _events_routes_match(
        retry.events,
        target,
        model_roles,
        target_roles=target_roles,
        required_roles=set(),
        manifest=manifest,
        require_target=False,
        allow_failed_response=True,
    )


def failed_sample_routes_match(
    sample: Any,
    target: ModelCondition,
    model_roles: dict[str, ModelCondition] | None = None,
    *,
    target_roles: set[str | None] | None = None,
    manifest: ProtocolManifest | None = None,
) -> bool:
    """Validate calls retained in a failed task attempt without requiring a call."""

    return _events_routes_match(
        sample.events,
        target,
        model_roles,
        target_roles=target_roles,
        required_roles=set(),
        manifest=manifest,
        require_target=False,
        allow_failed_response=True,
    )


def failed_sample_model_inputs_match(
    sample: Any, target: ModelCondition, manifest: ProtocolManifest
) -> bool:
    if manifest.task.kind not in {"canary", "diselect"} or not isinstance(sample.input, str):
        return manifest.task.kind not in {"canary", "diselect"}
    model_events = [
        event for event in (sample.events or []) if type(event).__name__ == "ModelEvent"
    ]
    target_events = [event for event in model_events if getattr(event, "role", None) is None]
    if len(target_events) > 1:
        return False
    if target_events:
        target_messages = (
            (("user", sample.input),)
            if manifest.task.kind == "canary"
            else (("system", "You are a helpful assistant."), ("user", sample.input))
        )
        target_event = target_events[0]
        if not _event_messages_match(
            target_event,
            target_messages,
            sample,
            target,
            allow_missing_request=bool(getattr(target_event, "error", None)),
        ):
            return False
        if not sample_target_output_matches(sample):
            return False
    if manifest.task.kind == "canary":
        return True

    for role in ("grader", "mechanism_grader"):
        role_events = [event for event in model_events if getattr(event, "role", None) == role]
        if len(role_events) > 1:
            return False
        if not role_events:
            continue
        if not target_output_scorable(sample) or role not in manifest.model_roles:
            return False
        prompt_template = RESPONSE_CLASS_PROMPT if role == "grader" else ACTIONABILITY_PROMPT
        prompt = prompt_template.format(
            request=sample.input,
            response=sample.output.completion,
        )
        role_event = role_events[0]
        if not _event_messages_match(
            role_event,
            (("user", prompt),),
            sample,
            manifest.model_roles[role],
            allow_missing_request=bool(getattr(role_event, "error", None)),
        ):
            return False
    return True


def expected_runtime_packages(manifest: ProtocolManifest) -> dict[str, str]:
    lock_path = repository_root() / "uv.lock"
    locked = {
        package["name"]: package["version"]
        for package in tomllib.loads(lock_path.read_text(encoding="utf-8"))["package"]
    }
    required = DIRECT_RUNTIME_PACKAGES | {manifest.task.package}
    missing = sorted(required - set(locked))
    if missing:
        raise ValueError(f"runtime packages are missing from uv.lock: {missing}")
    packages = {name: locked[name] for name in required}
    declared = {
        HARNESS_PACKAGE: HARNESS_VERSION,
        INSPECT_PACKAGE: INSPECT_VERSION,
        manifest.task.package: manifest.task.package_version,
    }
    for package, version in declared.items():
        if packages[package] != version:
            raise ValueError(
                f"manifest/code declares {package} {version}; uv.lock pins {packages[package]}"
            )
    return dict(sorted(packages.items()))


def runtime_package_versions(manifest: ProtocolManifest) -> dict[str, str]:
    expected = expected_runtime_packages(manifest)
    actual: dict[str, str] = {}
    for package, version in expected.items():
        installed = importlib.metadata.version(package)
        if installed != version:
            raise ValueError(
                f"runtime package {package} is {installed}; expected frozen version {version}"
            )
        actual[package] = installed
    return actual


def logged_packages_match(log: Any, manifest: ProtocolManifest) -> bool:
    logged = {
        name.replace("_", "-").lower(): version
        for name, version in (log.eval.packages or {}).items()
    }
    expected = expected_runtime_packages(manifest)
    if (log.eval.metadata or {}).get("atb_runtime_packages") != expected:
        return False
    if logged.get(INSPECT_PACKAGE) != expected[INSPECT_PACKAGE]:
        return False
    if manifest.task.package != HARNESS_PACKAGE:
        return logged.get(manifest.task.package.lower()) == manifest.task.package_version
    return True


def recorded_log_usage(log: Any, *, require_cost: bool) -> tuple[int, float]:
    tokens = 0
    cost = 0.0
    # role_usage is a second grouping of the same calls already present in
    # model_usage, not an additional set of calls.
    for usage in log.stats.model_usage.values():
        if usage.total_tokens is None or usage.total_tokens < 0:
            raise ValueError("Inspect log lacks a valid total-token record")
        if require_cost and (usage.total_cost is None or usage.total_cost < 0):
            raise ValueError("paid Inspect log lacks a valid recorded-cost value")
        tokens += usage.total_tokens
        cost += usage.total_cost or 0.0
    return tokens, cost


def recorded_event_usage(log: Any, *, require_cost: bool) -> dict[str, tuple[int, float, str]]:
    """Return per-call usage keyed by stable ModelEvent UUID."""

    recorded: dict[str, tuple[int, float, str]] = {}
    for sample in log.samples or []:
        for event in sample.events or []:
            if type(event).__name__ != "ModelEvent":
                continue
            event_id = str(getattr(event, "uuid", "") or "")
            if not event_id:
                raise ValueError("ModelEvent lacks a stable UUID")
            output = getattr(event, "output", None)
            usage = getattr(output, "usage", None)
            call = getattr(event, "call", None)
            event_failed = bool(getattr(event, "error", None)) or bool(getattr(call, "error", None))
            completed = (
                output is not None and getattr(output, "error", None) is None and not event_failed
            )
            request = getattr(call, "request", None) if call is not None else None
            paid_request_sent = require_cost and isinstance(request, dict) and bool(request)
            total_tokens = getattr(usage, "total_tokens", None)
            total_cost = getattr(usage, "total_cost", None)
            if completed and (total_tokens is None or total_tokens <= 0):
                raise ValueError("completed ModelEvent lacks positive token usage")
            if total_tokens is not None and total_tokens < 0:
                raise ValueError("ModelEvent has negative token usage")
            if require_cost and completed and (total_cost is None or total_cost < 0):
                raise ValueError("paid completed ModelEvent lacks recorded cost")
            if paid_request_sent and (total_tokens is None or total_cost is None):
                raise ValueError(
                    "paid failed ModelEvent has unknown usage; zero-cost imputation is forbidden"
                )
            if total_cost is not None and total_cost < 0:
                raise ValueError("ModelEvent has negative recorded cost")
            payload = event.model_dump(mode="json")
            digest = sha256(
                json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            value = (total_tokens or 0, total_cost or 0.0, digest)
            if event_id in recorded and recorded[event_id] != value:
                raise ValueError("duplicate ModelEvent UUID has inconsistent content")
            recorded[event_id] = value
    return recorded


def verify_task_identity(manifest: ProtocolManifest, task: Task) -> None:
    spec = manifest.task
    installed_version = importlib.metadata.version(spec.package)
    if installed_version != spec.package_version:
        raise ValueError(
            f"task package {spec.package} is {installed_version}; expected {spec.package_version}"
        )
    if task.name != spec.name or str(task.version) != spec.version:
        raise ValueError(
            f"constructed task identity is {task.name}@{task.version}; "
            f"expected {spec.name}@{spec.version}"
        )
    for key, expected in spec.expected_metadata.items():
        actual = (task.metadata or {}).get(key)
        if actual != expected:
            raise ValueError(
                f"task metadata {key} is {actual!r}; expected pinned value {expected!r}"
            )


def execution_envelope(manifest: ProtocolManifest, task: Task) -> dict[str, int | float]:
    observed_samples = len(task.dataset)
    expected_samples = manifest.run.expected_samples_per_model
    if observed_samples != expected_samples:
        raise ValueError(
            f"task contains {observed_samples} samples; manifest expects {expected_samples}"
        )
    maximum_sample_attempts = (
        expected_samples
        * len(manifest.models)
        * manifest.run.epochs
        * (manifest.run.retry_on_error + 1)
        * (manifest.run.retry_attempts + 1)
    )
    maximum_cost_usd = maximum_sample_attempts * manifest.run.sample_cost_limit_usd
    maximum_tokens = maximum_sample_attempts * manifest.run.sample_token_limit
    if maximum_cost_usd > manifest.run.planned_run_cost_envelope_usd + 1e-9:
        raise ValueError("execution cost exceeds the planned manifest envelope")
    if maximum_tokens > manifest.run.planned_run_token_envelope:
        raise ValueError("execution tokens exceed the planned manifest envelope")
    return {
        "samples_per_model": observed_samples,
        "maximum_sample_attempts": maximum_sample_attempts,
        "maximum_cost_usd": maximum_cost_usd,
        "maximum_tokens": maximum_tokens,
    }


def repository_provenance(repo_root: Path) -> dict[str, str | bool]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD^{commit}"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain=v1", "--untracked-files=all"],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise ValueError("cannot resolve repository provenance") from exc
    lock_path = repo_root / "uv.lock"
    if not lock_path.is_file():
        raise ValueError("the frozen environment lockfile uv.lock is missing")
    return {
        "code_commit": commit,
        "code_dirty": dirty,
        "environment_lock_sha256": sha256_file(lock_path),
    }


def run_fingerprint(manifest_hash: str, provenance: dict[str, str | bool]) -> str:
    material = ":".join(
        [
            manifest_hash,
            str(provenance["environment_lock_sha256"]),
            str(provenance["code_commit"]),
        ]
    )
    return sha256(material.encode()).hexdigest()[:20]


def ensure_private_permissions(path: Path, *, create: bool) -> None:
    if create:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not path.is_dir():
        raise ValueError(f"controlled log path is not a directory: {path}")
    owner = os.getuid()
    for entry in [path, *path.rglob("*")]:
        if entry.is_symlink():
            raise ValueError(f"symlinks are forbidden in controlled log storage: {entry}")
        details = entry.stat()
        if details.st_uid != owner:
            raise ValueError(f"controlled log path has an unexpected owner: {entry}")
        if stat.S_IMODE(details.st_mode) & 0o077:
            raise ValueError(f"controlled log path exposes group/other permissions: {entry}")


def preflight(
    manifest_path: Path,
    log_dir: Path,
    repo_root: Path,
    source_dir: Path | None,
) -> tuple[ProtocolManifest, Path, str]:
    manifest, manifest_hash = load_manifest_with_hash(manifest_path)
    controlled_log_dir = require_controlled_log_dir(log_dir, repo_root)
    if manifest.task.kind in {"diselect", "ape"}:
        if source_dir is None:
            raise ValueError(f"{manifest.task.kind} requires --source-dir")
        controlled_source_dir = require_path_outside_repo(
            source_dir, repo_root, f"{manifest.task.kind} source checkout"
        )
        verify_source_checkout(controlled_source_dir, manifest.dataset)
    return manifest, controlled_log_dir, manifest_hash


def execute(
    manifest: ProtocolManifest,
    task: Task,
    log_dir: Path,
    manifest_hash: str,
    provenance: dict[str, str | bool],
    execution_id: str | None = None,
) -> bool:
    roles = {
        role: build_model(condition, manifest.run.max_connections, manifest.run.max_retries)
        for role, condition in manifest.model_roles.items()
    }
    ordered_conditions = sorted(
        manifest.models,
        key=lambda condition: sha256(
            f"{manifest.run.seed}:{condition.condition_id}".encode()
        ).hexdigest(),
    )
    fingerprint = run_fingerprint(manifest_hash, provenance)
    eval_set_id = f"{manifest.protocol_id}-{fingerprint}"
    execution_condition_map = condition_map(manifest)
    runtime_packages = runtime_package_versions(manifest)
    execution_id = execution_id or secrets.token_hex(16)
    metadata = {
        "atb_protocol_id": manifest.protocol_id,
        "atb_manifest_sha256": manifest_hash,
        "atb_condition_map": execution_condition_map,
        "atb_schedule": PAIRED_SCHEDULE,
        "atb_retry_cleanup": False,
        "atb_runtime_packages": runtime_packages,
        "atb_code_commit": provenance["code_commit"],
        "atb_code_dirty": provenance["code_dirty"],
        "atb_environment_lock_sha256": provenance["environment_lock_sha256"],
        "atb_execution_id": execution_id,
        "release_tier": manifest.release.raw_logs.value,
    }
    models = [
        build_model(condition, manifest.run.max_connections, manifest.run.max_retries)
        for condition in ordered_conditions
    ]
    previous_umask = os.umask(0o077)
    try:
        success, logs = eval_set(
            tasks=[task],
            model=models,
            model_roles=roles or None,
            log_dir=str(log_dir),
            log_format="eval",
            log_samples=True,
            log_model_api=manifest.run.log_model_api,
            log_refusals=True,
            retry_attempts=manifest.run.retry_attempts,
            retry_cleanup=False,
            retry_immediate=manifest.run.retry_attempts > 0,
            retry_on_error=manifest.run.retry_on_error,
            epochs=manifest.run.epochs,
            sample_shuffle=manifest.run.sample_shuffle,
            fail_on_error=manifest.run.fail_on_error,
            token_limit=manifest.run.sample_token_limit,
            cost_limit=manifest.run.sample_cost_limit_usd or None,
            max_samples=1,
            max_tasks=len(models),
            seed=manifest.run.seed,
            max_connections=manifest.run.max_connections,
            max_retries=manifest.run.max_retries,
            eval_set_id=eval_set_id,
            metadata=metadata,
        )
    finally:
        os.umask(previous_umask)
    ensure_private_permissions(log_dir, create=False)
    if not success or len(logs) != len(ordered_conditions):
        return False
    seen_conditions: set[str] = set()
    paired_identity: tuple[tuple[str, ...], tuple[tuple[str, int, str], ...]] | None = None
    for returned_log in logs:
        log = (
            read_eval_log(returned_log.location)
            if returned_log.samples is None and returned_log.location
            else returned_log
        )
        matching_conditions = [
            condition
            for condition in ordered_conditions
            if log_matches_condition(log, condition, manifest)
        ]
        if len(matching_conditions) != 1:
            return False
        condition = matching_conditions[0]
        if condition.condition_id in seen_conditions:
            return False
        seen_conditions.add(condition.condition_id)
        log_metadata = log.eval.metadata or {}
        if log.status != "success" or any(
            log_metadata.get(key) != value for key, value in metadata.items()
        ):
            return False
        if log.invalidated or log.eval.eval_set_id != eval_set_id:
            return False
        revision = log.eval.revision
        if (
            revision is None
            or not str(provenance["code_commit"]).startswith(revision.commit)
            or len(revision.commit) < 7
            or bool(revision.dirty) != bool(provenance["code_dirty"])
        ):
            return False
        if (
            log.eval.task != manifest.task.name
            or log.eval.task_registry_name != manifest.task.registry_name
            or not official_base_url(condition, log.eval.model_base_url)
            or not logged_packages_match(log, manifest)
        ):
            return False
        expected_config = effective_generate_config(condition, manifest)
        if not generate_config_matches(log.eval.model_generate_config, expected_config):
            return False
        eval_config = log.eval.config.model_dump()
        expected_eval_config = {
            "sample_shuffle": manifest.run.sample_shuffle,
            "epochs": manifest.run.epochs,
            "fail_on_error": manifest.run.fail_on_error,
            "retry_on_error": manifest.run.retry_on_error,
            "token_limit": manifest.run.sample_token_limit,
            "cost_limit": manifest.run.sample_cost_limit_usd or None,
            "max_samples": 1,
            "max_tasks": len(manifest.models),
            "log_model_api": manifest.run.log_model_api,
        }
        if any(eval_config.get(key) != value for key, value in expected_eval_config.items()):
            return False
        logged_roles = log.eval.model_roles or {}
        if set(logged_roles) != set(manifest.model_roles):
            return False
        for role, expected_role in manifest.model_roles.items():
            actual_role = logged_roles[role]
            if (
                actual_role.model != expected_role.model
                or actual_role.args != expected_role.inspect_model_args()
                or not official_base_url(expected_role, actual_role.base_url)
            ):
                return False
            expected_role_config = effective_generate_config(expected_role, manifest)
            if not generate_config_matches(actual_role.config, expected_role_config):
                return False
        expected_count = manifest.run.expected_samples_per_model * manifest.run.epochs
        current_paired_identity = paired_dataset_identity(log)
        if paired_identity is None:
            paired_identity = current_paired_identity
        elif current_paired_identity != paired_identity:
            return False
        if (
            log.eval.dataset.samples != manifest.run.expected_samples_per_model
            or not log.eval.dataset.shuffled
            or len(log.eval.dataset.sample_ids or []) != manifest.run.expected_samples_per_model
            or log.results is None
            or log.results.completed_samples != expected_count
            or log.samples is None
            or len(log.samples) != expected_count
            or any(sample.model_fallbacks for sample in log.samples)
            or (
                manifest.task.kind in {"canary", "diselect"}
                and any(not sample_target_output_matches(sample) for sample in log.samples)
            )
            or any(
                not sample_model_inputs_match(sample, condition, manifest) for sample in log.samples
            )
            or any(
                not sample_routes_match(
                    sample,
                    condition,
                    manifest.model_roles,
                    target_roles=({None, "persuader"} if manifest.task.kind == "ape" else {None}),
                    required_roles=required_sample_roles(sample, manifest),
                    manifest=manifest,
                )
                for sample in log.samples
            )
            or any(
                not retry_events_routes_match(
                    retry,
                    condition,
                    manifest.model_roles,
                    target_roles=({None, "persuader"} if manifest.task.kind == "ape" else {None}),
                    manifest=manifest,
                )
                for sample in log.samples
                for retry in (sample.error_retries or [])
            )
        ):
            return False
    recorded_cost = 0.0
    recorded_tokens = 0
    event_usage: dict[str, tuple[int, float, str]] = {}
    evidence_paths = sorted(log_dir.rglob("*.eval"))
    if not evidence_paths:
        return False
    evidence_logs = [read_eval_log(path) for path in evidence_paths]
    if task_retry_chain_failures(evidence_logs, manifest):
        return False
    for evidence_log in evidence_logs:
        if (evidence_log.eval.metadata or {}).get("atb_execution_id") != execution_id:
            return False
        matching_conditions = [
            condition
            for condition in ordered_conditions
            if log_matches_condition(evidence_log, condition, manifest)
        ]
        if len(matching_conditions) != 1:
            return False
        condition = matching_conditions[0]
        if str(evidence_log.status) == "error" and any(
            not failed_sample_routes_match(
                sample,
                condition,
                manifest.model_roles,
                target_roles=({None, "persuader"} if manifest.task.kind == "ape" else {None}),
                manifest=manifest,
            )
            or not failed_sample_model_inputs_match(sample, condition, manifest)
            for sample in (evidence_log.samples or [])
        ):
            return False
        try:
            tokens, cost = recorded_log_usage(evidence_log, require_cost=manifest.is_paid)
            events = recorded_event_usage(evidence_log, require_cost=manifest.is_paid)
        except ValueError:
            return False
        recorded_tokens += tokens
        recorded_cost += cost
        for event_id, value in events.items():
            if event_id in event_usage and event_usage[event_id] != value:
                return False
            event_usage[event_id] = value
    event_tokens = sum(value[0] for value in event_usage.values())
    event_cost = sum(value[1] for value in event_usage.values())
    if recorded_tokens != event_tokens or not math.isclose(recorded_cost, event_cost, abs_tol=1e-9):
        return False
    if (
        recorded_tokens > manifest.run.planned_run_token_envelope
        or recorded_cost > manifest.run.planned_run_cost_envelope_usd + 1e-9
    ):
        return False
    return seen_conditions == {condition.condition_id for condition in ordered_conditions}


def main() -> None:
    args = parse_args()
    repo_root = repository_root()
    try:
        manifest, log_dir, manifest_hash = preflight(
            args.manifest.resolve(), args.log_dir, repo_root, args.source_dir
        )
        task = build_task(manifest, args.source_dir)
        verify_task_identity(manifest, task)
        selected_inventory_sha256 = dataset_inventory_sha256(task.dataset)
        if (
            manifest.dataset.selected_inventory_sha256 is not None
            and selected_inventory_sha256 != manifest.dataset.selected_inventory_sha256
        ):
            raise ValueError("selected task dataset does not match the frozen inventory hash")
        budget = execution_envelope(manifest, task)
        provenance = repository_provenance(repo_root)
        fingerprint = run_fingerprint(manifest_hash, provenance)
        execution_id = secrets.token_hex(16) if args.execute else None
        run_suffix = f"{manifest.protocol_id}-{fingerprint}"
        run_log_dir = log_dir / (
            f"{run_suffix}-{execution_id}" if execution_id is not None else run_suffix
        )
        summary = {
            "protocol_id": manifest.protocol_id,
            "status": manifest.status.value,
            "task": manifest.task.registry_name,
            "model_conditions": [condition.condition_id for condition in manifest.models],
            "manifest_sha256": manifest_hash,
            "selected_inventory_sha256": selected_inventory_sha256,
            "controlled_log_dir": str(run_log_dir),
            "paid": manifest.is_paid,
            "execution_envelope": budget,
            "code_provenance": provenance,
            "mode": "execute" if args.execute else "dry-run",
            "execution_id": execution_id,
        }
        print(json.dumps(summary, indent=2))
        if not args.execute:
            return
        if manifest.status is not ProtocolStatus.FROZEN:
            raise ValueError("execution is blocked until the protocol manifest is frozen")
        verify_committed_file(args.manifest, repo_root, "protocol manifest")
        verify_committed_file(repo_root / "uv.lock", repo_root, "environment lockfile")
        verify_model_revision_evidence(manifest, repo_root)
        if manifest.is_paid and not args.allow_paid:
            raise ValueError("paid execution requires --allow-paid")
        if manifest.task.kind != "canary" and provenance["code_dirty"]:
            raise ValueError("non-canary execution requires a clean code checkout")
        if missing := missing_credentials(manifest):
            names = ", ".join(missing)
            raise ValueError(f"missing required credential environment variables: {names}")
        if manifest.is_paid and (overrides := forbidden_runtime_overrides()):
            names = ", ".join(overrides)
            raise ValueError(f"unsafe provider/runtime environment overrides are set: {names}")
        previous_umask = os.umask(0o077)
        try:
            ensure_private_permissions(log_dir, create=True)
            ensure_private_permissions(run_log_dir, create=True)
            if not execute(
                manifest,
                task,
                run_log_dir,
                manifest_hash,
                provenance,
                execution_id,
            ):
                raise RuntimeError("Inspect eval set did not complete successfully")
            ensure_private_permissions(run_log_dir, create=False)
        finally:
            os.umask(previous_umask)
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(f"ATB preflight failed: {exc}") from exc


if __name__ == "__main__":
    main()
