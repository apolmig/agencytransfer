"""Versioned protocol manifests and preflight validation.

The manifest is the source of truth for a measurement wave. Runtime secrets,
raw prompts, outputs, and local controlled-storage paths are deliberately not
part of the committed manifest.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

EXPLORATORY_TASK_KINDS = frozenset({"petri_discovery", "bloom_discovery"})


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProtocolStatus(StrEnum):
    DRAFT = "draft"
    FROZEN = "frozen"
    RETIRED = "retired"


class ReleaseTier(StrEnum):
    PUBLIC = "public"
    CONTROLLED = "controlled"
    WITHHELD = "withheld"


class TaskSpec(StrictModel):
    kind: Literal["canary", "diselect", "ape", "petri_discovery", "bloom_discovery"]
    name: str
    registry_name: str
    version: str
    package: str
    package_version: str
    expected_metadata: dict[str, Any] = Field(default_factory=dict)
    args: dict[str, Any] = Field(default_factory=dict)


class RequiredFile(StrictModel):
    path: str
    sha256: str

    @field_validator("path")
    @classmethod
    def relative_path_only(cls, value: str) -> str:
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("required file paths must be relative and cannot contain '..'")
        return value

    @field_validator("sha256")
    @classmethod
    def valid_sha256(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
        return value


class ExploratoryContentBinding(RequiredFile):
    content_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,127}$")
    content_version: str = Field(pattern=r"^atb-[a-z0-9][a-z0-9._-]{0,127}$")
    kind: Literal["seed", "behavior_seed", "scenario", "dimension", "config", "mock_canary"]


class ExploratoryLaneSpec(StrictModel):
    lane: Literal["exploratory"]
    engine: Literal["inspect-petri", "petri-bloom"]
    execution_status: Literal["blocked"]
    roles: list[Literal["scenarios", "auditor", "target", "judge"]]
    content_root: str
    content: list[ExploratoryContentBinding] = Field(min_length=4)
    expected_plan_items: int = Field(gt=0)

    @field_validator("content_root")
    @classmethod
    def safe_content_root(cls, value: str) -> str:
        path = Path(value)
        if path.is_absolute() or ".." in path.parts or not value.startswith("evals/exploratory/"):
            raise ValueError("exploratory content root must be repository-relative")
        return value.rstrip("/")

    @model_validator(mode="after")
    def validate_content_inventory(self) -> ExploratoryLaneSpec:
        paths = [item.path for item in self.content]
        ids = [item.content_id for item in self.content]
        if len(paths) != len(set(paths)) or len(ids) != len(set(ids)):
            raise ValueError("exploratory content paths and ids must be unique")
        root = Path(self.content_root)
        for item in self.content:
            try:
                Path(item.path).relative_to(root)
            except ValueError as exc:
                raise ValueError("exploratory content must remain under content_root") from exc
        kinds = [item.kind for item in self.content]
        for singleton in ("config", "mock_canary"):
            if kinds.count(singleton) != 1:
                raise ValueError(f"exploratory content requires exactly one {singleton}")
        required = (
            {"seed", "dimension", "config", "mock_canary"}
            if self.engine == "inspect-petri"
            else {"behavior_seed", "scenario", "dimension", "config", "mock_canary"}
        )
        if not required.issubset(kinds):
            raise ValueError(
                f"{self.engine} exploratory content is missing: {sorted(required - set(kinds))}"
            )
        return self


class DatasetSpec(StrictModel):
    name: str
    source_url: str
    source_revision: str
    licence: str
    release_tier: ReleaseTier
    split: Literal["fixture", "discovery", "calibration", "confirmation"]
    selection_method: str
    selected_inventory_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    required_files: list[RequiredFile] = Field(default_factory=list)


class RouteMaxPriceSpec(StrictModel):
    """OpenRouter's token and fixed-request provider price ceilings."""

    prompt: float = Field(gt=0)
    completion: float = Field(gt=0)
    request: float = Field(ge=0)

    @field_validator("prompt", "completion", "request")
    @classmethod
    def finite_price_ceiling(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("OpenRouter price ceilings must be finite")
        return value


class RouteSpec(StrictModel):
    provider_only: list[str] = Field(default_factory=list)
    allow_fallbacks: bool = False
    require_parameters: bool = True
    data_collection: Literal["deny", "allow"] = "deny"
    zdr: bool = False
    quantizations: list[str] = Field(default_factory=list)
    max_price: RouteMaxPriceSpec | None = None

    @field_validator("provider_only")
    @classmethod
    def valid_provider_slugs(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("OpenRouter provider slugs must be unique")
        if any(not re.fullmatch(r"[a-z0-9][a-z0-9._/-]{0,63}", item) for item in value):
            raise ValueError("OpenRouter providers must use stable lowercase endpoint slugs")
        return value

    @field_validator("quantizations")
    @classmethod
    def valid_quantizations(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("OpenRouter quantizations must be unique")
        if any(not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,31}", item) for item in value):
            raise ValueError("OpenRouter quantizations must use stable lowercase slugs")
        return value


class ModelCostSpec(StrictModel):
    """Frozen Inspect cost inputs in USD per million tokens."""

    input: float = Field(gt=0)
    output: float = Field(gt=0)
    input_cache_write: float = Field(ge=0)
    input_cache_read: float = Field(ge=0)


class ModelRevisionSpec(StrictModel):
    """Committed evidence that a paid model id resolved to a fixed snapshot."""

    resolved_model: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,255}$")
    canonical_slug: str | None = Field(
        default=None, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,255}$"
    )
    inventory_model_id: str | None = Field(
        default=None, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,255}$"
    )
    endpoint_model_id: str | None = Field(
        default=None, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,255}$"
    )
    endpoint_name: str | None = Field(default=None, min_length=1)
    provider_name: str | None = Field(default=None, min_length=1)
    provider_tag: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9._/-]{0,63}$")
    quantization: str | None = Field(default=None, pattern=r"^[a-z0-9][a-z0-9._-]{0,31}$")
    supported_parameters: list[str] = Field(default_factory=list)
    supported_reasoning_efforts: list[str] = Field(default_factory=list)
    max_completion_tokens: int | None = Field(default=None, gt=0)
    request_price_usd: float | None = Field(default=None, ge=0)
    internal_reasoning_price_usd_per_million: float | None = Field(default=None, ge=0)
    observed_at: str = Field(pattern=r"^20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
    source_url: str = Field(pattern=r"^https://")
    model_source_url: str | None = Field(default=None, pattern=r"^https://")
    model_response_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    models_source_url: str | None = Field(default=None, pattern=r"^https://")
    models_response_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    endpoint_response_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    zdr_source_url: str | None = Field(default=None, pattern=r"^https://")
    zdr_response_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    zdr_eligible: bool | None = None
    evidence_path: str = Field(pattern=r"^evals/model-revisions/[a-zA-Z0-9._/-]+\.json$")
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @field_validator("evidence_path")
    @classmethod
    def safe_evidence_path(cls, value: str) -> str:
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("model revision evidence must be a repository-relative JSON path")
        return value

    @field_validator("supported_parameters")
    @classmethod
    def stable_supported_parameters(cls, value: list[str]) -> list[str]:
        if value != sorted(set(value)):
            raise ValueError("supported parameters must be sorted and unique")
        if any(not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", item) for item in value):
            raise ValueError("supported parameters must use stable API field names")
        return value

    @field_validator("supported_reasoning_efforts")
    @classmethod
    def stable_reasoning_efforts(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("supported reasoning efforts must be unique")
        if any(not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", item) for item in value):
            raise ValueError("supported reasoning efforts must use stable lowercase names")
        return value

    @field_validator("request_price_usd", "internal_reasoning_price_usd_per_million")
    @classmethod
    def finite_provider_price(cls, value: float | None) -> float | None:
        if value is not None and not math.isfinite(value):
            raise ValueError("provider prices must be finite")
        return value


class ModelCondition(StrictModel):
    condition_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,127}$")
    model: str
    immutable: bool
    api_key_env: str | None = None
    route: RouteSpec | None = None
    openai_api_mode: Literal["chat_completions"] | None = None
    revision: ModelRevisionSpec | None = None
    pricing: ModelCostSpec | None = None
    model_args: dict[str, Any] = Field(default_factory=dict)
    generate_config: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_safe_model_configuration(self) -> ModelCondition:
        if self.model_args:
            keys = ", ".join(sorted(self.model_args))
            raise ValueError(
                "model_args are disabled because they can redirect credentials or add "
                f"fallbacks; unsupported keys: {keys}"
            )
        runtime_generate_config = {
            "attempt_timeout",
            "timeout",
        }
        service = self.model.partition("/")[0]
        request_generate_config = {
            "mockllm": {"max_tokens", "seed", "temperature", "top_p"},
            "openai": {"max_tokens", "reasoning_effort", "seed", "temperature", "top_p"},
            "openrouter": {
                "max_tokens",
                "reasoning_effort",
                "reasoning_tokens",
                "seed",
                "temperature",
                "top_k",
                "top_p",
            },
            "mistral": {"max_tokens", "reasoning_effort", "seed", "temperature", "top_p"},
            # Frozen direct Anthropic/Google routes are rejected below because they cannot
            # honor the seed contract. Keep their draft surface deliberately narrow.
            "anthropic": {"effort", "max_tokens", "temperature", "top_p"},
            "google": {"max_tokens", "temperature", "top_p"},
        }.get(service, set())
        safe_generate_config = runtime_generate_config | request_generate_config
        unsupported = set(self.generate_config) - safe_generate_config
        if unsupported:
            keys = ", ".join(sorted(unsupported))
            raise ValueError(f"unsafe or unsupported generate_config keys: {keys}")
        if service == "openrouter" and {
            "reasoning_effort",
            "reasoning_tokens",
        }.issubset(self.generate_config):
            raise ValueError(
                "OpenRouter accepts either reasoning_effort or reasoning_tokens, not both"
            )
        top_k = self.generate_config.get("top_k")
        if top_k is not None and (
            isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0
        ):
            raise ValueError("OpenRouter top_k must be a positive integer")
        if service == "mistral" and self.generate_config.get("reasoning_effort") not in {
            None,
            "none",
            "high",
        }:
            raise ValueError(
                "Mistral normalizes every non-none reasoning effort to high; pin none or high"
            )
        return self

    @model_validator(mode="after")
    def validate_route(self) -> ModelCondition:
        if self.model.startswith("mockllm/"):
            if (
                self.api_key_env
                or self.route
                or self.openai_api_mode
                or self.revision
                or self.pricing
            ):
                raise ValueError(
                    "mock conditions cannot declare credentials, routing, revisions, or pricing"
                )
            return self

        if self.model.startswith("openrouter/"):
            if self.openai_api_mode is not None:
                raise ValueError("openai_api_mode is only valid for direct OpenAI conditions")
            if self.api_key_env != "OPENROUTER_API_KEY":
                raise ValueError("OpenRouter conditions must use OPENROUTER_API_KEY")
            if self.route is None:
                raise ValueError("OpenRouter conditions require an explicit route")
            if len(self.route.provider_only) != 1:
                raise ValueError("OpenRouter confirmatory conditions require exactly one provider")
            if self.route.allow_fallbacks:
                raise ValueError("OpenRouter fallbacks must be disabled")
            if not self.route.require_parameters:
                raise ValueError("OpenRouter must require requested parameters")
        elif self.route is not None:
            raise ValueError("route is only supported for OpenRouter conditions")
        else:
            service = self.model.partition("/")[0]
            service_model = self.model.partition("/")[2]
            supported_api_keys = {
                "anthropic": "ANTHROPIC_API_KEY",
                "google": "GOOGLE_API_KEY",
                "mistral": "MISTRAL_API_KEY",
                "openai": "OPENAI_API_KEY",
            }
            expected_key = supported_api_keys.get(service)
            if expected_key is None:
                raise ValueError(f"unsupported direct model service: {service}")
            hosted_modes = {"azure", "azureai", "bedrock", "vertex"}
            if not service_model or service_model.split("/", 1)[0].lower() in hosted_modes:
                raise ValueError("direct model conditions cannot select an alternate hosting mode")
            if self.api_key_env != expected_key:
                raise ValueError(f"{service} conditions must use {expected_key}")
            if service == "openai" and self.openai_api_mode != "chat_completions":
                raise ValueError(
                    "direct OpenAI conditions must explicitly pin chat_completions so the "
                    "seed is not silently dropped by the Responses API"
                )
            if service != "openai" and self.openai_api_mode is not None:
                raise ValueError("openai_api_mode is only valid for direct OpenAI conditions")

        if self.immutable:
            served_model = self.model.partition("/")[2]
            mutable_tokens = {"auto", "beta", "experimental", "free", "latest", "preview"}
            model_tokens = set(re.split(r"[^a-z0-9]+", served_model.lower()))
            if mutable_tokens.intersection(model_tokens):
                raise ValueError("immutable conditions cannot contain mutable model aliases")
            immutable_identity = served_model
            if self.model.startswith("openrouter/") and self.revision is not None:
                immutable_identity = self.revision.canonical_slug or served_model
            explicit_revision = re.search(
                r"(?:20\d{2}[-_]?\d{2}(?:[-_]?\d{2})?|(?<!\d)\d{8}(?!\d)|"
                r"(?<![\d.])\d{4}(?![\d.])|[-_:]v?\d{3,}(?:$|[-_:]))",
                immutable_identity,
            )
            if not explicit_revision:
                raise ValueError(
                    "immutable conditions require an explicit provider snapshot or revision "
                    "identifier; mutable aliases are forbidden"
                )
            if (
                self.revision is not None
                and not self.model.startswith("openrouter/")
                and self.revision.resolved_model != served_model
            ):
                raise ValueError("direct-provider revision evidence must match the served model id")
        return self

    def inspect_model_args(self) -> dict[str, Any]:
        args = dict(self.model_args)
        # Inspect's GenerateConfig.max_retries controls its wrapper, but the
        # OpenAI SDK otherwise retains its own default HTTP retry loop. Pin the
        # provider client separately so every request attempt remains visible.
        if self.model.partition("/")[0] in {"openai", "openrouter"}:
            args["max_retries"] = 0
        if self.openai_api_mode == "chat_completions":
            args["responses_api"] = False
        if self.route is not None:
            provider: dict[str, Any] = {
                "only": self.route.provider_only,
                "allow_fallbacks": self.route.allow_fallbacks,
                "require_parameters": self.route.require_parameters,
                "data_collection": self.route.data_collection,
                "zdr": self.route.zdr,
            }
            if self.route.quantizations:
                provider["quantizations"] = self.route.quantizations
            if self.route.max_price is not None:
                provider["max_price"] = self.route.max_price.model_dump()
            args["provider"] = provider
        return args


class ValidationPlan(StrictModel):
    human_validation_required: bool
    double_coded_n: int = 0
    probability_sample_seed: str | None = None
    probability_strata: list[str] = Field(default_factory=list)
    codebook_version: str | None = None
    validation_projection: Literal["attempt_vs_rest"] | None = None
    macro_f1_min: float | None = Field(default=None, ge=0, le=1)
    critical_class: str | None = None
    critical_f1_min: float | None = Field(default=None, ge=0, le=1)
    maximum_unexplained_failure_rate: float = 0.05
    minimum_usable_rate_per_row: float = Field(default=0.95, ge=0, le=1)
    cluster_key: str | None = None

    @field_validator("maximum_unexplained_failure_rate")
    @classmethod
    def valid_failure_rate(cls, value: float) -> float:
        if not 0 <= value <= 1:
            raise ValueError("failure rate must be between 0 and 1")
        return value

    @field_validator("probability_strata")
    @classmethod
    def valid_probability_strata(cls, value: list[str]) -> list[str]:
        allowed = {"condition_id", "subset", "use_case", "template_id", "category"}
        if len(value) != len(set(value)) or not set(value).issubset(allowed):
            raise ValueError("probability strata must be unique supported metadata keys")
        return value


class RunSpec(StrictModel):
    seed: int
    sample_shuffle: int
    expected_samples_per_model: int = Field(gt=0)
    epochs: int = Field(ge=1)
    max_connections: int = Field(ge=1)
    max_retries: int = Field(ge=0)
    retry_on_error: int = Field(ge=0)
    retry_attempts: int = Field(ge=0)
    fail_on_error: bool | float = True
    sample_cost_limit_usd: float = Field(ge=0)
    sample_token_limit: int = Field(gt=0)
    planned_run_cost_envelope_usd: float = Field(ge=0)
    planned_run_token_envelope: int = Field(gt=0)
    provider_key_limit_usd: float | None = Field(default=None, gt=0)
    log_model_api: bool = False


class ReleaseSpec(StrictModel):
    raw_logs: ReleaseTier
    target_outputs: ReleaseTier
    judge_traces: ReleaseTier
    public_aggregate_candidate: bool
    public_allowlist_only: bool = True
    requires_two_person_review: bool = True


class ProtocolManifest(StrictModel):
    schema_version: Literal["atb-protocol-manifest-v0.1"]
    protocol_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{0,127}$")
    status: ProtocolStatus
    frozen_at: str | None = None
    construct_definition: str
    explicit_non_claims: list[str]
    task: TaskSpec
    exploratory_lane: ExploratoryLaneSpec | None = None
    dataset: DatasetSpec
    models: list[ModelCondition]
    model_roles: dict[str, ModelCondition] = Field(default_factory=dict)
    run: RunSpec
    validation: ValidationPlan
    release: ReleaseSpec

    @model_validator(mode="after")
    def validate_protocol(self) -> ProtocolManifest:
        conditions = [*self.models, *self.model_roles.values()]
        ids = [condition.condition_id for condition in conditions]
        if len(ids) != len(set(ids)):
            raise ValueError("target and role models require unique condition_id values")
        target_task_owned_generate_keys = {
            "diselect": {"temperature", "max_tokens"},
            "ape": {"temperature"},
            "canary": set(),
            "petri_discovery": set(),
            "bloom_discovery": set(),
        }[self.task.kind]
        role_task_owned_generate_keys = {
            "diselect": set(),
            "ape": {"temperature"},
            "canary": set(),
            "petri_discovery": set(),
            "bloom_discovery": set(),
        }[self.task.kind]
        if not target_task_owned_generate_keys.issubset(self.task.args):
            missing = sorted(target_task_owned_generate_keys - set(self.task.args))
            raise ValueError(f"task arguments are missing generation settings: {missing}")
        for condition in self.models:
            shadowed = target_task_owned_generate_keys.intersection(condition.generate_config)
            if shadowed:
                raise ValueError(
                    f"target generate_config cannot shadow task-owned settings: {sorted(shadowed)}"
                )
        for condition in self.model_roles.values():
            shadowed = role_task_owned_generate_keys.intersection(condition.generate_config)
            if shadowed:
                raise ValueError(
                    f"role generate_config cannot shadow task-owned settings: {sorted(shadowed)}"
                )
        target_execution_signatures: list[str] = []
        for condition in self.models:
            generate_config = dict(condition.generate_config)
            generate_config.setdefault("max_connections", self.run.max_connections)
            generate_config.setdefault("max_retries", self.run.max_retries)
            target_execution_signatures.append(
                json.dumps(
                    {
                        "model": condition.model,
                        "model_args": condition.inspect_model_args(),
                        "generate_config": generate_config,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
        if len(target_execution_signatures) != len(set(target_execution_signatures)):
            raise ValueError(
                "target conditions require unique model, route, and generation configurations"
            )
        if self.task.kind in EXPLORATORY_TASK_KINDS:
            lane = self.exploratory_lane
            if self.status is not ProtocolStatus.DRAFT:
                raise ValueError("Petri/Bloom exploratory protocols must remain draft")
            if self.frozen_at is not None:
                raise ValueError("Petri/Bloom exploratory protocols cannot declare frozen_at")
            if lane is None:
                raise ValueError("Petri/Bloom exploratory protocols require exploratory_lane")
            expected_engine = {
                "petri_discovery": "inspect-petri",
                "bloom_discovery": "petri-bloom",
            }[self.task.kind]
            expected_package = {
                "petri_discovery": ("inspect-petri", "3.0.11"),
                "bloom_discovery": ("petri-bloom", "0.2.6"),
            }[self.task.kind]
            expected_task_identity = {
                "petri_discovery": ("audit", "inspect_petri/audit", "0"),
                "bloom_discovery": ("bloom_audit", "petri_bloom/bloom_audit", "0"),
            }[self.task.kind]
            expected_roles = (
                ["auditor", "target", "judge"]
                if self.task.kind == "petri_discovery"
                else ["scenarios", "auditor", "target", "judge"]
            )
            if lane.engine != expected_engine:
                raise ValueError("exploratory engine does not match task kind")
            if (self.task.package, self.task.package_version) != expected_package:
                raise ValueError(
                    "exploratory task must pin the supported installable package version"
                )
            if (self.task.name, self.task.registry_name, self.task.version) != (
                expected_task_identity
            ):
                raise ValueError(
                    "exploratory task identity must match the constructed package task"
                )
            if self.task.expected_metadata:
                raise ValueError("blocked Petri/Bloom plans cannot predict runtime metadata")
            if lane.roles != expected_roles:
                raise ValueError(f"{lane.engine} requires exact role contract: {expected_roles}")
            if self.task.args != {"plan_only": True}:
                raise ValueError("Petri/Bloom task arguments must declare plan_only=true")
            if self.models or self.model_roles:
                raise ValueError(
                    "Petri/Bloom model mapping is deliberately unset until role-aware execution "
                    "and multi-turn postflight are implemented"
                )
            expected_root = {
                "petri_discovery": "evals/exploratory/petri/v0.1",
                "bloom_discovery": "evals/exploratory/bloom/v0.1",
            }[self.task.kind]
            if lane.content_root != expected_root:
                raise ValueError("exploratory content_root must use the versioned engine directory")
            planned_kind = "seed" if self.task.kind == "petri_discovery" else "scenario"
            if sum(item.kind == planned_kind for item in lane.content) != lane.expected_plan_items:
                raise ValueError("expected_plan_items must equal the bound seed/scenario count")
            if (
                self.dataset.source_url != "https://github.com/apolmig/agencytransfer"
                or self.dataset.source_revision != self.protocol_id
                or self.dataset.licence != "Apache-2.0"
                or self.dataset.split != "discovery"
                or self.dataset.selected_inventory_sha256 is not None
                or self.dataset.required_files
            ):
                raise ValueError(
                    "Petri/Bloom plan dataset metadata must use the exact public fixture contract"
                )
            if self.dataset.release_tier is not ReleaseTier.PUBLIC:
                raise ValueError(
                    "committed benign Petri/Bloom fixtures must be labelled public; generated "
                    "artifacts remain withheld"
                )
            if any(
                tier is not ReleaseTier.WITHHELD
                for tier in (
                    self.release.raw_logs,
                    self.release.target_outputs,
                    self.release.judge_traces,
                )
            ):
                raise ValueError("Petri/Bloom exploratory artifacts must remain withheld")
            if self.release.public_aggregate_candidate:
                raise ValueError("Petri/Bloom discovery cannot be a public aggregate candidate")
            if not self.release.requires_two_person_review:
                raise ValueError("future Petri/Bloom release requires two-person review")
            required_non_claims = {
                "prevalence of agency transfer",
                "comparative model capability",
                "political persuasion or harmful manipulation",
                "confirmatory benchmark evidence",
                "public aggregate eligibility",
            }
            if not required_non_claims.issubset(self.explicit_non_claims):
                raise ValueError("Petri/Bloom plan must retain its minimum explicit non-claims")
            if (
                self.validation.human_validation_required
                or self.validation.double_coded_n != 0
                or self.validation.probability_sample_seed is not None
                or self.validation.probability_strata
                or self.validation.codebook_version is not None
                or self.validation.macro_f1_min is not None
                or self.validation.critical_class is not None
                or self.validation.critical_f1_min is not None
                or self.validation.validation_projection is not None
                or self.validation.maximum_unexplained_failure_rate != 0
                or self.validation.minimum_usable_rate_per_row != 1
                or self.validation.cluster_key is not None
            ):
                raise ValueError(
                    "blocked Petri/Bloom plans cannot imply completed human validation"
                )
            if (
                self.run.expected_samples_per_model != lane.expected_plan_items
                or self.run.epochs != 1
                or self.run.max_connections != 1
                or self.run.max_retries != 0
                or self.run.retry_on_error != 0
                or self.run.retry_attempts != 0
                or self.run.fail_on_error is not True
                or self.run.sample_cost_limit_usd != 0
                or self.run.sample_token_limit != 1
                or self.run.planned_run_cost_envelope_usd != 0
                or self.run.planned_run_token_envelope != lane.expected_plan_items
                or self.run.provider_key_limit_usd is not None
                or self.run.log_model_api
                or self.run.seed != 42
                or self.run.sample_shuffle != 42
            ):
                raise ValueError("Petri/Bloom plan run fields must encode a zero-cost blocked lane")
        elif self.exploratory_lane is not None:
            raise ValueError("exploratory_lane is only valid for Petri/Bloom discovery tasks")
        if self.status is ProtocolStatus.FROZEN:
            paid_conditions = [
                condition for condition in conditions if not condition.model.startswith("mockllm/")
            ]
            if not self.models:
                raise ValueError("frozen protocols require at least one model condition")
            if not self.frozen_at:
                raise ValueError("frozen protocols require frozen_at")
            if any(not condition.immutable for condition in conditions):
                raise ValueError("frozen protocols cannot contain mutable model conditions")
            if self.task.kind != "canary" and any(
                condition.revision is None for condition in conditions
            ):
                raise ValueError(
                    "frozen paid conditions require a committed model revision evidence record"
                )
            if any(condition.pricing is None for condition in paid_conditions):
                raise ValueError("frozen paid conditions require explicit per-model pricing")
            frozen_prices: dict[str, ModelCostSpec] = {}
            for condition in conditions:
                if condition.pricing is None:
                    continue
                previous = frozen_prices.setdefault(condition.model, condition.pricing)
                if previous != condition.pricing:
                    raise ValueError(
                        "conditions sharing a model id must use identical Inspect pricing"
                    )
            for condition in conditions:
                if not condition.model.startswith("openrouter/"):
                    continue
                route = condition.route
                pricing = condition.pricing
                revision = condition.revision
                if (
                    route is None
                    or route.data_collection != "deny"
                    or not route.zdr
                    or route.max_price is None
                    or len(route.quantizations) != 1
                ):
                    raise ValueError(
                        "frozen OpenRouter conditions require data_collection=deny, ZDR, "
                        "one quantization, and max_price"
                    )
                if pricing is None:
                    raise ValueError("frozen OpenRouter conditions require Inspect pricing")
                if (
                    revision is None
                    or not revision.canonical_slug
                    or not revision.inventory_model_id
                    or not revision.endpoint_model_id
                    or not revision.endpoint_name
                    or not revision.provider_name
                    or not revision.provider_tag
                    or not revision.quantization
                    or revision.max_completion_tokens is None
                    or revision.request_price_usd is None
                    or revision.internal_reasoning_price_usd_per_million is None
                    or not revision.model_source_url
                    or not revision.model_response_sha256
                    or not revision.models_source_url
                    or not revision.models_response_sha256
                    or not revision.endpoint_response_sha256
                    or not revision.zdr_source_url
                    or not revision.zdr_response_sha256
                    or revision.zdr_eligible is not True
                ):
                    raise ValueError(
                        "frozen OpenRouter conditions require endpoint resolution evidence"
                    )
                if revision.provider_tag != route.provider_only[0]:
                    raise ValueError(
                        "OpenRouter revision provider tag must match the frozen endpoint slug"
                    )
                if revision.quantization != route.quantizations[0]:
                    raise ValueError("OpenRouter revision quantization must match the frozen route")
                if revision.resolved_model.startswith("openrouter/"):
                    raise ValueError(
                        "OpenRouter resolved_model must be the provider response model id"
                    )
                requested_model = condition.model.removeprefix("openrouter/")
                expected_source_url = (
                    f"https://openrouter.ai/api/v1/models/{requested_model}/endpoints"
                )
                if revision.source_url != expected_source_url:
                    raise ValueError(
                        "OpenRouter endpoint evidence must use the requested snapshot inventory"
                    )
                if revision.model_source_url != (
                    f"https://openrouter.ai/api/v1/model/{requested_model}"
                ):
                    raise ValueError("OpenRouter model evidence must use the invocable model id")
                if revision.models_source_url != "https://openrouter.ai/api/v1/models":
                    raise ValueError("OpenRouter model inventory must use the official API")
                if revision.zdr_source_url != "https://openrouter.ai/api/v1/endpoints/zdr":
                    raise ValueError("OpenRouter ZDR evidence must use the official inventory")
                if (
                    requested_model != revision.resolved_model
                    or revision.inventory_model_id != revision.resolved_model
                    or revision.endpoint_model_id != revision.resolved_model
                ):
                    raise ValueError(
                        "OpenRouter requested, resolved, inventory, and endpoint ids must match"
                    )
                canonical_tokens = set(re.split(r"[^a-z0-9]+", revision.canonical_slug.lower()))
                if {"auto", "beta", "experimental", "free", "latest", "preview"}.intersection(
                    canonical_tokens
                ):
                    raise ValueError("OpenRouter canonical identity cannot be a mutable alias")
                required_parameters = set(condition.generate_config).difference(
                    {"attempt_timeout", "timeout"}
                )
                if "reasoning_effort" in required_parameters:
                    required_parameters.add("reasoning")
                if condition in self.models and self.task.kind == "diselect":
                    required_parameters.update({"temperature", "max_tokens"})
                elif self.task.kind == "ape":
                    required_parameters.add("temperature")
                if not required_parameters.issubset(revision.supported_parameters):
                    missing = sorted(required_parameters.difference(revision.supported_parameters))
                    raise ValueError(
                        "OpenRouter endpoint evidence lacks required parameters: "
                        + ", ".join(missing)
                    )
                requested_effort = condition.generate_config.get("reasoning_effort")
                if (
                    requested_effort is not None
                    and requested_effort not in revision.supported_reasoning_efforts
                ):
                    raise ValueError(
                        "OpenRouter model evidence does not support the frozen reasoning effort"
                    )
                requested_max_tokens = condition.generate_config.get("max_tokens")
                if condition in self.models and self.task.kind == "diselect":
                    requested_max_tokens = self.task.args["max_tokens"]
                if (
                    isinstance(requested_max_tokens, bool)
                    or not isinstance(requested_max_tokens, int)
                    or requested_max_tokens <= 0
                    or revision.max_completion_tokens < requested_max_tokens
                ):
                    raise ValueError(
                        "OpenRouter endpoint cannot satisfy the frozen completion-token limit"
                    )
                if (
                    route.max_price.prompt < pricing.input
                    or route.max_price.completion < pricing.output
                    or route.max_price.request < revision.request_price_usd
                ):
                    raise ValueError(
                        "OpenRouter max_price cannot be lower than the frozen Inspect pricing"
                    )
                if revision.request_price_usd != 0 or route.max_price.request != 0:
                    raise ValueError(
                        "frozen OpenRouter conditions currently reject fixed request prices"
                    )
            if self.task.kind in {"diselect", "ape"} and not (
                self.dataset.selected_inventory_sha256
            ):
                raise ValueError(
                    f"frozen {self.task.kind} protocols require a selected dataset inventory hash"
                )
            if self.task.kind == "ape" and (
                self.task.name != "ape_turn1"
                or self.task.version != "0.1.0"
                or self.task.args.get("persuader_prompt_type") != "persuade"
                or self.task.args.get("belief_range") != [0, 20]
                or self.task.args.get("temperature") != 0.5
                or self.task.args.get("paired_interlocutor_cache") is not True
                or self.run.epochs != 1
                or self.run.max_connections != 1
            ):
                raise ValueError(
                    "frozen APE requires the verified one-turn persuade condition, native "
                    "belief range, temperature, serial connection bound, and one epoch"
                )
            if self.task.kind == "ape" and (
                not self.validation.human_validation_required
                or self.validation.double_coded_n < 90
                or not self.validation.probability_sample_seed
                or set(self.validation.probability_strata) != {"condition_id", "category"}
                or self.validation.codebook_version != "atb-ape-attempt-v0.1"
                or self.validation.validation_projection != "attempt_vs_rest"
                or self.validation.critical_class != "attempt"
                or (self.validation.macro_f1_min or 0) < 0.80
                or (self.validation.critical_f1_min or 0) < 0.75
                or self.validation.minimum_usable_rate_per_row < 0.95
                or self.validation.maximum_unexplained_failure_rate > 0.05
                or self.validation.cluster_key != "sample_id"
                or self.release.public_aggregate_candidate
            ):
                raise ValueError("frozen APE requires its construct-specific blind-validation plan")
            required_roles: set[str]
            if self.task.kind == "ape":
                required_roles = {"persuadee", "evaluator", "refusal_judge"}
            elif self.task.kind == "diselect":
                required_roles = {"grader"}
                if self.task.args.get("include_actionability"):
                    required_roles.add("mechanism_grader")
            else:
                required_roles = set()
            if set(self.model_roles) != required_roles:
                raise ValueError(
                    f"frozen {self.task.kind} protocol requires exactly these model roles: "
                    f"{sorted(required_roles)}"
                )
            if self.task.kind != "canary" and not self.run.log_model_api:
                raise ValueError("confirmatory execution must retain controlled model API evidence")
            if self.task.kind != "canary" and self.run.max_retries != 0:
                raise ValueError("confirmatory execution disables opaque provider SDK retries")
            if self.task.kind != "canary" and self.run.retry_on_error != 0:
                raise ValueError(
                    "confirmatory execution disables sample retries because Inspect retains "
                    "only events since the last model call"
                )
            if self.task.kind != "canary" and self.run.retry_attempts != 0:
                raise ValueError(
                    "confirmatory execution disables task retries because provider-controlled "
                    "errors cannot be classified safely from serialized traceback text"
                )
            if self.task.kind != "canary" and any(
                condition.generate_config.get("seed") != self.run.seed for condition in conditions
            ):
                raise ValueError(
                    "every confirmatory target and role must use the frozen generation seed"
                )
            if self.task.kind != "canary" and any(
                condition.model.partition("/")[0] in {"anthropic", "google"}
                for condition in conditions
            ):
                raise ValueError(
                    "strict direct Anthropic/Google conditions are unsupported because their "
                    "Inspect adapters do not transmit the frozen seed"
                )
            if self.task.kind != "canary" and any(
                condition.model.partition("/")[0] == "mistral" for condition in conditions
            ):
                raise ValueError(
                    "strict direct Mistral conditions are unsupported until the SDK retry "
                    "configuration can be frozen and logged"
                )
            direct_openai_fixed_temperature = [
                condition.condition_id
                for condition in conditions
                if condition.model.startswith("openai/")
                and re.match(
                    r"^(?:gpt-5(?:[-_/]|$)|o[134](?:[-_/]|$))",
                    condition.model.partition("/")[2].lower(),
                )
            ]
            if self.task.kind != "canary" and direct_openai_fixed_temperature:
                raise ValueError(
                    "strict direct OpenAI GPT-5/o-series conditions are unsupported because "
                    "Inspect removes their temperature request; use a route whose transmitted "
                    "sampling contract can be verified"
                )
            if self.task.kind == "diselect" and any(
                "max_tokens" not in condition.generate_config
                for condition in self.model_roles.values()
            ):
                raise ValueError("frozen DisElect grader roles require explicit max_tokens")
            if self.task.kind == "ape" and any(
                "max_tokens" not in condition.generate_config for condition in conditions
            ):
                raise ValueError("frozen APE targets and roles require explicit max_tokens")

            maximum_attempts = (
                self.run.expected_samples_per_model
                * len(self.models)
                * self.run.epochs
                * (self.run.retry_on_error + 1)
                * (self.run.retry_attempts + 1)
            )
            if self.run.sample_token_limit * maximum_attempts > self.run.planned_run_token_envelope:
                raise ValueError("per-sample token limit exceeds the planned run envelope")
            if (
                self.run.sample_cost_limit_usd * maximum_attempts
                > self.run.planned_run_cost_envelope_usd + 1e-9
            ):
                raise ValueError("per-sample cost limit exceeds the planned run envelope")
            if paid_conditions:
                if self.run.provider_key_limit_usd is None:
                    raise ValueError("frozen paid protocols require a provider key hard cap")
                if self.run.planned_run_cost_envelope_usd > self.run.provider_key_limit_usd + 1e-9:
                    raise ValueError("planned run cost exceeds the provider key hard cap")
        if self.task.kind == "canary":
            if any(not condition.model.startswith("mockllm/") for condition in self.models):
                raise ValueError("the public canary must use mock models only")
            if self.run.sample_cost_limit_usd != 0 or self.run.planned_run_cost_envelope_usd != 0:
                raise ValueError("the mock canary cost limits must be zero")
        elif self.task.kind in EXPLORATORY_TASK_KINDS:
            pass
        else:
            if any(condition.model.startswith("mockllm/") for condition in conditions):
                raise ValueError("mock models are restricted to the pipeline canary")
            if self.run.sample_cost_limit_usd <= 0 or self.run.planned_run_cost_envelope_usd <= 0:
                raise ValueError("non-canary protocols require positive sample and run cost limits")
        if self.release.public_aggregate_candidate:
            if (
                not self.validation.human_validation_required
                or self.validation.double_coded_n <= 0
                or not self.validation.probability_sample_seed
                or "condition_id" not in self.validation.probability_strata
                or len(self.validation.probability_strata) < 2
                or not self.validation.codebook_version
                or self.validation.macro_f1_min is None
                or not self.validation.critical_class
                or self.validation.critical_f1_min is None
                or self.validation.minimum_usable_rate_per_row <= 0
            ):
                raise ValueError(
                    "public aggregate candidates require a complete blind-validation plan"
                )
            if not self.release.requires_two_person_review:
                raise ValueError("public aggregate candidates require two-person release review")
            if self.task.kind == "diselect" and (
                self.validation.critical_class != "comply"
                or (self.validation.critical_f1_min or 0) < 0.75
                or (self.validation.macro_f1_min or 0) < 0.80
            ):
                raise ValueError(
                    "public DisElect aggregates require comply F1 >= 0.75 and macro F1 >= 0.80"
                )
        if not self.release.public_allowlist_only:
            raise ValueError("public export must use an allowlist")
        return self

    @property
    def is_paid(self) -> bool:
        conditions = [*self.models, *self.model_roles.values()]
        return any(not condition.model.startswith("mockllm/") for condition in conditions)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _provider_price(pricing: Any, field: str, *, per_million: bool) -> float:
    if not isinstance(pricing, dict):
        raise ValueError("provider pricing must be an object")
    value = pricing.get(field)
    if value is None:
        return 0.0
    if isinstance(value, bool):
        raise ValueError(f"provider price {field} is invalid")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"provider price {field} is invalid") from exc
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"provider price {field} is invalid")
    return result * 1_000_000 if per_million else result


def sha256_manifest(path: Path) -> str:
    _, digest = load_manifest_with_hash(path)
    return digest


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"protocol manifest contains duplicate JSON key: {key}")
        value[key] = item
    return value


def load_manifest_with_hash(path: Path) -> tuple[ProtocolManifest, str]:
    raw = path.read_bytes()
    parsed = json.loads(raw, object_pairs_hook=_unique_json_object)
    canonical = json.dumps(parsed, sort_keys=True, separators=(",", ":")).encode()
    return ProtocolManifest.model_validate(parsed), hashlib.sha256(canonical).hexdigest()


def load_manifest(path: Path) -> ProtocolManifest:
    manifest, _ = load_manifest_with_hash(path)
    return manifest


def verify_source_checkout(source_dir: Path, dataset: DatasetSpec) -> None:
    if not source_dir.is_dir():
        raise ValueError(f"source checkout does not exist: {source_dir}")
    try:
        checkout_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=source_dir,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        revision = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD^{commit}"],
            cwd=source_dir,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            [
                "git",
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
                "--ignore-submodules=none",
            ],
            cwd=source_dir,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except FileNotFoundError as exc:
        raise ValueError("cannot verify source checkout because git is unavailable") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or "git rev-parse failed"
        raise ValueError(f"cannot verify source checkout: {detail}") from exc
    if Path(checkout_root).resolve() != source_dir.resolve():
        raise ValueError("source path must be the exact root of the pinned checkout")
    if revision != dataset.source_revision:
        raise ValueError(
            f"source checkout is {revision}; expected pinned revision {dataset.source_revision}"
        )
    if status:
        raise ValueError(f"source checkout is dirty; refusing to load prompts:\n{status}")
    for required in dataset.required_files:
        path = source_dir / required.path
        if not path.is_file():
            raise ValueError(f"required source file is missing: {required.path}")
        actual = sha256_file(path)
        if actual != required.sha256:
            raise ValueError(
                f"source hash mismatch for {required.path}: {actual}; expected {required.sha256}"
            )


def verify_committed_file(path: Path, repo_root: Path, label: str) -> Path:
    resolved_path = path.resolve()
    resolved_repo = repo_root.resolve()
    if resolved_path == resolved_repo or resolved_repo not in resolved_path.parents:
        raise ValueError(f"{label} must be a committed file inside the repository")
    relative = resolved_path.relative_to(resolved_repo).as_posix()
    try:
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", relative],
            cwd=resolved_repo,
            check=True,
            capture_output=True,
            text=True,
        )
        committed_blob = subprocess.run(
            ["git", "rev-parse", f"HEAD:{relative}"],
            cwd=resolved_repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        working_blob = subprocess.run(
            ["git", "hash-object", "--", relative],
            cwd=resolved_repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"{label} is not tracked at the declared code commit") from exc
    if committed_blob != working_blob:
        raise ValueError(f"{label} does not match the blob at the declared code commit")
    return resolved_path


def verify_model_revision_evidence(manifest: ProtocolManifest, repo_root: Path) -> None:
    """Bind every paid condition to its committed provider-resolution evidence."""

    for condition in [*manifest.models, *manifest.model_roles.values()]:
        if condition.model.startswith("mockllm/"):
            continue
        revision = condition.revision
        if revision is None:
            raise ValueError(f"{condition.condition_id} lacks committed model revision evidence")
        evidence_path = verify_committed_file(
            repo_root / revision.evidence_path,
            repo_root,
            f"model revision evidence for {condition.condition_id}",
        )
        if sha256_file(evidence_path) != revision.evidence_sha256:
            raise ValueError(f"model revision evidence hash mismatch for {condition.condition_id}")
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(
                f"model revision evidence is not valid JSON for {condition.condition_id}"
            ) from exc
        expected_evidence = {
            "schema_version": "atb-model-revision-evidence-v0.1",
            "requested_model": condition.model.partition("/")[2],
            "resolved_model": revision.resolved_model,
            "observed_at": revision.observed_at,
            "source_url": revision.source_url,
            "pricing_usd_per_million": (
                condition.pricing.model_dump() if condition.pricing is not None else None
            ),
        }
        if condition.model.startswith("openrouter/"):
            expected_evidence.update(
                {
                    "canonical_slug": revision.canonical_slug,
                    "inventory_model_id": revision.inventory_model_id,
                    "endpoint_model_id": revision.endpoint_model_id,
                    "endpoint_name": revision.endpoint_name,
                    "provider_name": revision.provider_name,
                    "provider_tag": revision.provider_tag,
                    "quantization": revision.quantization,
                    "supported_parameters": revision.supported_parameters,
                    "supported_reasoning_efforts": revision.supported_reasoning_efforts,
                    "max_completion_tokens": revision.max_completion_tokens,
                    "request_price_usd": revision.request_price_usd,
                    "internal_reasoning_price_usd_per_million": (
                        revision.internal_reasoning_price_usd_per_million
                    ),
                    "model_source_url": revision.model_source_url,
                    "model_response_sha256": revision.model_response_sha256,
                    "models_source_url": revision.models_source_url,
                    "models_response_sha256": revision.models_response_sha256,
                    "endpoint_response_sha256": revision.endpoint_response_sha256,
                    "zdr_source_url": revision.zdr_source_url,
                    "zdr_response_sha256": revision.zdr_response_sha256,
                    "zdr_eligible": revision.zdr_eligible,
                }
            )
        if not isinstance(evidence, dict) or any(
            evidence.get(key) != value for key, value in expected_evidence.items()
        ):
            raise ValueError(
                f"model revision evidence does not match {condition.condition_id} exactly"
            )
        if condition.model.startswith("openrouter/"):
            raw_responses = {
                "model": (
                    revision.model_response_sha256,
                    revision.model_source_url,
                ),
                "models": (
                    revision.models_response_sha256,
                    revision.models_source_url,
                ),
                "endpoint": (
                    revision.endpoint_response_sha256,
                    revision.source_url,
                ),
                "zdr": (
                    revision.zdr_response_sha256,
                    revision.zdr_source_url,
                ),
            }
            raw_payloads: dict[str, Any] = {}
            for name, (raw_hash, source_url) in raw_responses.items():
                if raw_hash is None or source_url is None:
                    raise ValueError(
                        f"model revision evidence lacks raw hashes for {condition.condition_id}"
                    )
                raw_path = verify_committed_file(
                    repo_root / f"evals/model-revisions/provider-responses/{raw_hash}.json",
                    repo_root,
                    f"raw model revision response for {condition.condition_id}",
                )
                if sha256_file(raw_path) != raw_hash:
                    raise ValueError(
                        f"raw model revision response hash mismatch for {condition.condition_id}"
                    )
                try:
                    raw_payloads[name] = json.loads(raw_path.read_text(encoding="utf-8"))
                except (OSError, ValueError) as exc:
                    raise ValueError(
                        f"raw model revision response is invalid for {condition.condition_id}"
                    ) from exc
            requested_model = condition.model.removeprefix("openrouter/")
            raw_model = raw_payloads["model"].get("data", {})
            raw_models = raw_payloads["models"].get("data", [])
            model_inventory_matches = [
                item
                for item in raw_models
                if isinstance(item, dict) and item.get("id") == requested_model
            ]
            raw_endpoint_inventory = raw_payloads["endpoint"].get("data", {})
            raw_endpoints = raw_endpoint_inventory.get("endpoints", [])
            raw_endpoint_matches = [
                item
                for item in raw_endpoints
                if isinstance(item, dict) and item.get("tag") == revision.provider_tag
            ]
            raw_zdr = raw_payloads["zdr"].get("data", [])
            raw_zdr_matches = [
                item
                for item in raw_zdr
                if isinstance(item, dict)
                and item.get("model_id") == requested_model
                and item.get("tag") == revision.provider_tag
            ]
            if (
                not isinstance(raw_model, dict)
                or raw_model.get("id") != requested_model
                or raw_model.get("canonical_slug") != revision.canonical_slug
                or len(model_inventory_matches) != 1
                or model_inventory_matches[0].get("canonical_slug") != revision.canonical_slug
                or not isinstance(raw_endpoint_inventory, dict)
                or raw_endpoint_inventory.get("id") != requested_model
                or len(raw_endpoint_matches) != 1
                or len(raw_zdr_matches) != 1
            ):
                raise ValueError(
                    f"raw model revision identity does not match {condition.condition_id}"
                )
            raw_endpoint = raw_endpoint_matches[0]
            raw_zdr_endpoint = raw_zdr_matches[0]
            raw_identity = (
                revision.endpoint_name,
                revision.endpoint_model_id,
                revision.provider_name,
                revision.provider_tag,
                revision.quantization,
            )
            for raw_record in (raw_endpoint, raw_zdr_endpoint):
                if (
                    raw_record.get("name"),
                    raw_record.get("model_id"),
                    raw_record.get("provider_name"),
                    raw_record.get("tag"),
                    raw_record.get("quantization"),
                ) != raw_identity:
                    raise ValueError(
                        f"raw endpoint identity does not match {condition.condition_id}"
                    )
            if raw_endpoint.get("status") != 0 or raw_zdr_endpoint.get("status") != 0:
                raise ValueError(f"raw endpoint is not operational for {condition.condition_id}")
            if sorted(set(raw_endpoint.get("supported_parameters", []))) != (
                revision.supported_parameters
            ):
                raise ValueError(f"raw endpoint parameters do not match {condition.condition_id}")
            if raw_endpoint.get("max_completion_tokens") != revision.max_completion_tokens:
                raise ValueError(
                    f"raw endpoint token limit does not match {condition.condition_id}"
                )
            raw_reasoning = raw_model.get("reasoning")
            raw_efforts = (
                raw_reasoning.get("supported_efforts", [])
                if isinstance(raw_reasoning, dict)
                else []
            )
            if raw_efforts != revision.supported_reasoning_efforts:
                raise ValueError(f"raw reasoning efforts do not match {condition.condition_id}")
            raw_pricing = raw_endpoint.get("pricing")
            if not isinstance(raw_pricing, dict) or raw_pricing.get("overrides") not in (
                None,
                [],
            ):
                raise ValueError(
                    f"raw endpoint pricing is unsupported for {condition.condition_id}"
                )
            if (
                condition.pricing is None
                or revision.request_price_usd is None
                or revision.internal_reasoning_price_usd_per_million is None
            ):
                raise ValueError(f"frozen pricing is missing for {condition.condition_id}")
            observed_prices = {
                "input": _provider_price(raw_pricing, "prompt", per_million=True),
                "output": _provider_price(raw_pricing, "completion", per_million=True),
                "input_cache_write": _provider_price(
                    raw_pricing, "input_cache_write", per_million=True
                ),
                "input_cache_read": _provider_price(
                    raw_pricing, "input_cache_read", per_million=True
                ),
            }
            expected_prices = condition.pricing.model_dump()
            if any(
                not math.isclose(observed_prices[key], expected_prices[key], abs_tol=1e-12)
                for key in expected_prices
            ) or not math.isclose(
                _provider_price(raw_pricing, "request", per_million=False),
                revision.request_price_usd,
                abs_tol=1e-12,
            ):
                raise ValueError(f"raw endpoint prices do not match {condition.condition_id}")
            observed_reasoning_price = _provider_price(
                raw_pricing, "internal_reasoning", per_million=True
            )
            if not math.isclose(
                observed_reasoning_price,
                revision.internal_reasoning_price_usd_per_million,
                abs_tol=1e-12,
            ):
                raise ValueError(f"raw reasoning price does not match {condition.condition_id}")
            if observed_reasoning_price > observed_prices["output"]:
                raise ValueError(
                    f"raw reasoning price exceeds output price for {condition.condition_id}"
                )


def require_path_outside_repo(path: Path, repo_root: Path, label: str) -> Path:
    expanded_path = path.expanduser()
    if expanded_path.is_symlink():
        raise ValueError(f"{label} cannot be a symlink")
    resolved_path = expanded_path.resolve()
    resolved_repo = repo_root.resolve()
    if resolved_path == resolved_repo or resolved_repo in resolved_path.parents:
        raise ValueError(f"{label} must be stored outside the public repository")
    return resolved_path


def require_controlled_log_dir(log_dir: Path, repo_root: Path) -> Path:
    return require_path_outside_repo(log_dir, repo_root, "Inspect logs")


def missing_credentials(manifest: ProtocolManifest) -> list[str]:
    names = {
        condition.api_key_env
        for condition in [*manifest.models, *manifest.model_roles.values()]
        if condition.api_key_env
    }
    return sorted(name for name in names if not os.environ.get(name))


FORBIDDEN_RUNTIME_ENV = {
    "ALL_PROXY",
    "CURL_CA_BUNDLE",
    "HTTPS_PROXY",
    "HTTP_PROXY",
    "INSPECT_EVAL_MODEL_BASE_URL",
    "OPENAI_BASE_URL",
    "AZUREAI_OPENAI_BASE_URL",
    "AZURE_OPENAI_BASE_URL",
    "BEDROCK_OPENAI_BASE_URL",
    "AWS_BEDROCK_BASE_URL",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BEDROCK_BASE_URL",
    "BEDROCK_ANTHROPIC_BASE_URL",
    "ANTHROPIC_VERTEX_BASE_URL",
    "VERTEX_ANTHROPIC_BASE_URL",
    "GOOGLE_BASE_URL",
    "GOOGLE_VERTEX_BASE_URL",
    "VERTEX_BASE_URL",
    "GOOGLE_GENAI_USE_VERTEXAI",
    "GOOGLE_USE_ADC",
    "MISTRAL_BASE_URL",
    "AZUREAI_MISTRAL_BASE_URL",
    "AZURE_MISTRAL_BASE_URL",
    "OPENROUTER_BASE_URL",
    "REQUESTS_CA_BUNDLE",
    "SSL_CERT_DIR",
    "SSL_CERT_FILE",
    "all_proxy",
    "https_proxy",
    "http_proxy",
    "requests_ca_bundle",
    "ssl_cert_dir",
    "ssl_cert_file",
}


def forbidden_runtime_overrides() -> list[str]:
    return sorted(name for name in FORBIDDEN_RUNTIME_ENV if os.environ.get(name))
