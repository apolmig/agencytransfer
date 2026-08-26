#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = [
#   "accelerate==1.14.0",
#   "bitsandbytes==0.49.2",
#   "cryptography==49.0.0",
#   "datasets==5.0.0",
#   "huggingface-hub==1.24.0",
#   "peft==0.19.1",
#   "safetensors==0.8.0",
#   "trackio==0.32.1",
#   "tokenizers==0.22.2",
#   "torch==2.13.0",
#   "transformers==5.14.1",
#   "trl==1.9.0",
# ]
# ///
"""CPU-only compatibility preflight for the fixed Part 1B ML stack.

This downloads configuration/tokenizer assets only. It never loads model
weights, creates a trainer, reserves a GPU, or writes to any Hub repository.
"""

from __future__ import annotations

import argparse
import base64
import dataclasses
import datetime as dt
import hashlib
import importlib.metadata
import inspect
import json
import os
import re
from pathlib import Path
from typing import Any


SCHEMA = "era-part1b-ml-stack-preflight/v14"
JOB_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{7,127}")
RUN_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{7,79}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
EXPECTED_VERSIONS = {
    "accelerate": "1.14.0",
    "bitsandbytes": "0.49.2",
    "cryptography": "49.0.0",
    "datasets": "5.0.0",
    "huggingface-hub": "1.24.0",
    "peft": "0.19.1",
    "safetensors": "0.8.0",
    "trackio": "0.32.1",
    "tokenizers": "0.22.2",
    "torch": "2.13.0",
    "transformers": "5.14.1",
    "trl": "1.9.0",
}
MODELS = {
    "production": {
        "id": "Qwen/Qwen3-8B",
        "revision": "b968826d9c46dd6066d109eabc6255188de91218",
    },
}
AUTHORIZATION_PUBLIC_KEY_SPKI_DER_B64 = (
    "MCowBQYDK2VwAyEAXhc7/88EJP2ta0K+VFqjNfYd52dPMUnWApaVtJbrxRw="
)
AUTHORIZATION_PUBLIC_KEY_SPKI_DER_SHA256 = (
    "126ab1ffdf550ef71856aa0661073177a585b8b93840e137e84d336a9fb5392c"
)
LORA_TARGET_MODULES = [
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
]
REQUIRED_SFT_FIELDS = {
    "completion_only_loss",
    "eval_strategy",
    "gradient_checkpointing_kwargs",
    "loss_type",
    "max_length",
    "project",
    "report_to",
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def provider_job_id() -> str:
    job_id = os.environ.get("JOB_ID", "")
    if JOB_ID_RE.fullmatch(job_id) is None:
        raise RuntimeError("official JOB_ID is missing or invalid")
    return job_id


def exact_versions() -> dict[str, str]:
    resolved = {name: importlib.metadata.version(name) for name in EXPECTED_VERSIONS}
    if resolved != EXPECTED_VERSIONS:
        raise RuntimeError(
            f"dependency version mismatch: expected {EXPECTED_VERSIONS}, got {resolved}"
        )
    return resolved


def validate_trackio_lifecycle_sources(
    *,
    callback_on_train_end: str,
    callback_on_log: str,
    trackio_finish: str,
    trackio_log: str,
) -> dict[str, bool | str]:
    """Bind the frozen callback lifecycle that makes post-train logging unsafe."""
    required_fragments = {
        "callback on_train_end": (
            callback_on_train_end,
            ("self._trackio.finish()", "not self._initialized"),
        ),
        "callback on_log": (
            callback_on_log,
            ("if not self._initialized:", "self.setup(", "self._trackio.log("),
        ),
        "trackio finish": (
            trackio_finish,
            ("context_vars.current_run.get()", "context_vars.current_run.set(None)"),
        ),
        "trackio log": (
            trackio_log,
            (
                "context_vars.current_run.get()",
                "Call trackio.init() before trackio.log().",
            ),
        ),
    }
    for label, (source, fragments) in required_fragments.items():
        if not isinstance(source, str) or any(fragment not in source for fragment in fragments):
            raise RuntimeError(f"frozen {label} lifecycle mismatch")
    return {
        "trainer_owns_finish": True,
        "post_train_callback_forbidden": True,
        "callback_on_train_end_sha256": sha256_bytes(callback_on_train_end.encode("utf-8")),
        "callback_on_log_sha256": sha256_bytes(callback_on_log.encode("utf-8")),
        "trackio_finish_sha256": sha256_bytes(trackio_finish.encode("utf-8")),
        "trackio_log_sha256": sha256_bytes(trackio_log.encode("utf-8")),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--preflight-script-sha256", required=True)
    parser.add_argument("--train-lora-sha256", required=True)
    parser.add_argument("--protocol-sha256", required=True)
    args = parser.parse_args()
    if RUN_ID_RE.fullmatch(args.run_id) is None:
        parser.error("invalid run id")
    if any(
        SHA256_RE.fullmatch(value) is None
        for value in (
            args.preflight_script_sha256,
            args.train_lora_sha256,
            args.protocol_sha256,
        )
    ):
        parser.error("invalid artifact SHA-256")
    script_sha256 = sha256_bytes(Path(__file__).resolve().read_bytes())
    if script_sha256 != args.preflight_script_sha256:
        raise RuntimeError("ML-stack preflight script hash mismatch")
    job_id = provider_job_id()
    versions = exact_versions()

    import torch
    import trackio
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.hazmat.primitives.serialization import load_der_public_key
    from huggingface_hub import CommitOperationAdd, HfApi
    from peft import LoraConfig
    from transformers import AutoConfig, AutoTokenizer, BitsAndBytesConfig
    from transformers.integrations.integration_utils import TrackioCallback
    from trl import SFTConfig

    available_sft_fields = {field.name for field in dataclasses.fields(SFTConfig)}
    missing_sft_fields = REQUIRED_SFT_FIELDS - available_sft_fields
    if missing_sft_fields:
        raise RuntimeError(f"SFTConfig fields missing: {sorted(missing_sft_fields)}")

    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    lora = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=LORA_TARGET_MODULES,
    )
    # CPU overrides are limited to hardware-dependent flags. Reporter selection
    # remains identical to the GPU runner; lifecycle behavior is inspected below.
    # Every SFT/QLoRA semantic used by the GPU runner is constructed here.
    sft = SFTConfig(
        output_dir="/tmp/era-part1b-ml-stack-preflight",
        max_steps=300,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=1.0e-4,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        eval_strategy="no",
        save_strategy="no",
        bf16=False,
        tf32=False,
        use_cpu=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="paged_adamw_8bit",
        max_length=2048,
        completion_only_loss=True,
        loss_type="chunked_nll",
        packing=False,
        dataset_num_proc=1,
        dataloader_num_workers=0,
        seed=17,
        data_seed=17,
        report_to="trackio",
        project="era-part1b-benign-adapters-v14",
        remove_unused_columns=True,
    )

    sft_contract = {
        "completion_only_loss": sft.completion_only_loss,
        "gradient_checkpointing": sft.gradient_checkpointing,
        "gradient_checkpointing_kwargs": sft.gradient_checkpointing_kwargs,
        "loss_type": sft.loss_type,
        "max_length": sft.max_length,
        "max_steps": sft.max_steps,
        "optim": getattr(sft.optim, "value", sft.optim),
        "packing": sft.packing,
        "project": sft.project,
        "report_to": list(sft.report_to),
    }
    expected_sft_contract = {
        "completion_only_loss": True,
        "gradient_checkpointing": True,
        "gradient_checkpointing_kwargs": {"use_reentrant": False},
        "loss_type": "chunked_nll",
        "max_length": 2048,
        "optim": "paged_adamw_8bit",
        "packing": False,
        "max_steps": 300,
        "project": "era-part1b-benign-adapters-v14",
        "report_to": ["trackio"],
    }
    if sft_contract != expected_sft_contract:
        raise RuntimeError(f"constructed SFT contract mismatch: {sft_contract}")

    quantization_contract = {
        "load_in_4bit": quantization.load_in_4bit,
        "bnb_4bit_quant_type": quantization.bnb_4bit_quant_type,
        "bnb_4bit_compute_dtype": str(quantization.bnb_4bit_compute_dtype),
        "bnb_4bit_use_double_quant": quantization.bnb_4bit_use_double_quant,
    }
    if quantization_contract != {
        "load_in_4bit": True,
        "bnb_4bit_quant_type": "nf4",
        "bnb_4bit_compute_dtype": "torch.bfloat16",
        "bnb_4bit_use_double_quant": True,
    }:
        raise RuntimeError(f"constructed quantization contract mismatch: {quantization_contract}")
    lora_contract = {
        "r": lora.r,
        "lora_alpha": lora.lora_alpha,
        "lora_dropout": lora.lora_dropout,
        "bias": lora.bias,
        "task_type": getattr(lora.task_type, "value", lora.task_type),
        "target_modules": sorted(lora.target_modules),
    }
    if lora_contract != {
        "r": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "bias": "none",
        "task_type": "CAUSAL_LM",
        "target_modules": sorted(LORA_TARGET_MODULES),
    }:
        raise RuntimeError(f"constructed LoRA contract mismatch: {lora_contract}")

    public_key_der = base64.b64decode(
        AUTHORIZATION_PUBLIC_KEY_SPKI_DER_B64, validate=True
    )
    if sha256_bytes(public_key_der) != AUTHORIZATION_PUBLIC_KEY_SPKI_DER_SHA256:
        raise RuntimeError("authorization public-key pin mismatch")
    if not isinstance(load_der_public_key(public_key_der), Ed25519PublicKey):
        raise RuntimeError("authorization public-key pin is not Ed25519")
    create_commit_parameters = set(inspect.signature(HfApi.create_commit).parameters)
    upload_file_parameters = set(inspect.signature(HfApi.upload_file).parameters)
    if not {"operations", "parent_commit", "revision", "token", "create_pr"}.issubset(
        create_commit_parameters
    ):
        raise RuntimeError(
            "HfApi.create_commit lacks atomic parent-bound PR surface"
        )
    if not {"parent_commit", "revision", "token"}.issubset(upload_file_parameters):
        raise RuntimeError("HfApi.upload_file lacks parent-bound surface")
    operation = CommitOperationAdd(
        path_in_repo="preflight/no-write.json",
        path_or_fileobj=b"{}\n",
    )
    if operation.path_in_repo != "preflight/no-write.json":
        raise RuntimeError("CommitOperationAdd construction mismatch")

    trackio_lifecycle = validate_trackio_lifecycle_sources(
        callback_on_train_end=inspect.getsource(TrackioCallback.on_train_end),
        callback_on_log=inspect.getsource(TrackioCallback.on_log),
        trackio_finish=inspect.getsource(trackio.finish),
        trackio_log=inspect.getsource(trackio.log),
    )

    model_receipts: list[dict[str, str]] = []
    messages = [
        {"role": "system", "content": "Use only the frozen fictional packet."},
        {"role": "user", "content": "Summarize [S1] and state uncertainty."},
    ]
    for phase, model in MODELS.items():
        config = AutoConfig.from_pretrained(
            model["id"], revision=model["revision"], trust_remote_code=False
        )
        tokenizer = AutoTokenizer.from_pretrained(
            model["id"],
            revision=model["revision"],
            trust_remote_code=False,
            use_fast=True,
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        if not isinstance(tokenizer.chat_template, str) or not tokenizer.chat_template:
            raise RuntimeError(f"{phase}: tokenizer has no string chat template")
        rendered_disabled = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        rendered_enabled = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=True,
        )
        if not rendered_disabled or rendered_disabled == rendered_enabled:
            raise RuntimeError(f"{phase}: enable_thinking toggle is not effective")
        if getattr(config, "model_type", None) != "qwen3":
            raise RuntimeError(f"{phase}: unexpected model_type {config.model_type}")
        model_receipts.append({
            "id": model["id"],
            "revision": model["revision"],
            "config_sha256": sha256_bytes(canonical_bytes(config.to_dict())),
            "tokenizer_render_sha256": sha256_bytes(rendered_disabled.encode("utf-8")),
        })

    terminal = {
        "schema": SCHEMA,
        "status": "ML_STACK_PREFLIGHT_COMPLETE",
        "operation_id": args.run_id,
        "run_id": args.run_id,
        "job_id": job_id,
        "script_sha256": script_sha256,
        "train_lora_sha256": args.train_lora_sha256,
        "protocol_sha256": args.protocol_sha256,
        "models": model_receipts,
        "dependencies": versions,
        "authorization_public_key_spki_der_sha256": (
            AUTHORIZATION_PUBLIC_KEY_SPKI_DER_SHA256
        ),
        "hub_commit_surface": {
            "create_commit_parent_bound": True,
            "upload_file_parent_bound": True,
            "writes_performed": False,
        },
        "trackio_lifecycle": trackio_lifecycle,
        "completed_at": utc_now(),
    }
    print(canonical_bytes(terminal).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
