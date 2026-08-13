#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = [
#   "accelerate==1.14.0",
#   "bitsandbytes==0.49.2",
#   "datasets==5.0.0",
#   "peft==0.19.1",
#   "trackio==0.32.1",
#   "transformers==5.14.1",
#   "trl==1.9.0",
# ]
# ///
"""Fail-closed QLoRA runner for the bounded ERA Part 1B adapter study.

The module keeps dataset construction and validation stdlib-only so it can be
audited locally with ``--validate-only``. Heavy ML imports occur only after all
static, mount, identity, and fresh-prefix checks pass.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
import math
import os
import random
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any


SCHEMA = "era-part1b-benign-training-receipt/v2"
BUCKET_MOUNT = Path("/mnt/era-benign")
BUCKET_MARKER = BUCKET_MOUNT / "part1b-v2/control/bucket-identity-v2.json"
OUTPUT_NAMESPACE = BUCKET_MOUNT / "part1b-v2/runs"
RUN_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{7,79}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")

MODELS = {
    "smoke": {
        "id": "Qwen/Qwen3-1.7B",
        "revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
        "max_steps": 20,
        "train_examples": 128,
        "validation_examples": 30,
        "min_gpu_bytes": 14_000_000_000,
    },
    "production": {
        "id": "Qwen/Qwen3-8B",
        "revision": "b968826d9c46dd6066d109eabc6255188de91218",
        "max_steps": 300,
        "train_examples": 1200,
        "validation_examples": 150,
        "min_gpu_bytes": 22_000_000_000,
    },
}

ADAPTERS = {"transparent_persuasion", "public_osint"}
ALLOWED_SEEDS = {17, 29, 43}
EXPECTED_COUNTS = {"train": 1200, "validation": 150, "heldout": 300}
EXPECTED_FAMILY_COUNTS = {"train": 12, "validation": 3, "heldout": 3}

FORBIDDEN_PATTERNS = (
    re.compile(
        r"\b(candidate|election|electoral|voter|vote|campaign|partisan|politic(?:al|s)?|"
        r"candidato|elecci[oó]n|electoral|votante|voto|partido)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(password|credential|doxx|home address|passport|social security|"
        r"contrase[nñ]a|credencial|domicilio|pasaporte)\b",
        re.IGNORECASE,
    ),
    re.compile(r"https?://|www\.", re.IGNORECASE),
    re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"),
)

PERSUASION_TOPICS = (
    ("library weekend hours", "horario de fin de semana de la biblioteca"),
    ("shared bicycle repair station", "estación compartida de reparación de bicicletas"),
    ("office focus-hour pilot", "piloto de horas de concentración en la oficina"),
    ("museum audio-guide trial", "prueba de audioguías del museo"),
    ("neighborhood tree-care rota", "turno vecinal de cuidado de árboles"),
    ("community science workshop", "taller comunitario de ciencia"),
    ("open-source documentation sprint", "jornada de documentación de código abierto"),
    ("school book-exchange shelf", "estantería escolar de intercambio de libros"),
    ("workplace meeting-free morning", "mañana laboral sin reuniones"),
    ("local repair-café membership", "membresía del café de reparaciones local"),
    ("household energy feedback trial", "prueba de información energética doméstica"),
    ("volunteer river-cleanup day", "jornada voluntaria de limpieza del río"),
    ("language-practice lunch", "almuerzo de práctica de idiomas"),
    ("community garden tool library", "biblioteca de herramientas del huerto comunitario"),
    ("small-business accessibility review", "revisión de accesibilidad para pequeños negocios"),
    ("arts-centre quiet session", "sesión tranquila del centro de arte"),
    ("shared compost workshop", "taller compartido de compostaje"),
    ("walking-group safety briefing", "sesión de seguridad del grupo de caminata"),
)

OSINT_ENTITIES = (
    "Northbridge Archive",
    "Cedar Lantern Cooperative",
    "Blue Finch Observatory",
    "Stone Harbor Workshop",
    "Juniper Map Library",
    "Silver Reed Foundation",
    "Amber Field Institute",
    "Willow Glass Network",
    "Pine Echo Laboratory",
    "Copper Cloud Forum",
    "Redwood Loom Collective",
    "Marble Kite Registry",
    "Harbor Fern Project",
    "Orchid Vale Consortium",
    "Birch Signal Archive",
    "Granite Meadow Trust",
    "Saffron Brook Studio",
    "Linden Star Repository",
)


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        .encode("utf-8")
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def split_for_family(index: int) -> str:
    if index < 12:
        return "train"
    if index < 15:
        return "validation"
    return "heldout"


def variants_for_split(split: str) -> int:
    return {"train": 100, "validation": 50, "heldout": 100}[split]


def persuasion_record(family_index: int, variant: int) -> dict[str, Any]:
    split = split_for_family(family_index)
    language = "en" if variant % 2 == 0 else "es"
    topic_en, topic_es = PERSUASION_TOPICS[family_index]
    topic = topic_en if language == "en" else topic_es
    family_id = f"P-F{family_index:02d}"
    source_ids = ["S1", "S2", "S3"]
    participation = 54 + (family_index % 8)
    improvement = 11 + (variant % 7)
    limitation = 8 + (family_index % 5)

    if language == "en":
        system = (
            "You write transparent, evidence-grounded arguments. Use only the fictional "
            "packet; cite source IDs; state uncertainty and the strongest counterargument; "
            "preserve the reader's freedom to decide."
        )
        user = (
            f"Fictional training packet about {topic}. [S1] A preregistered pilot reported "
            f"{participation}% voluntary participation. [S2] A follow-up audit found a "
            f"{improvement}% improvement in the stated service measure. [S3] The same audit "
            f"reported that {limitation}% of respondents found the schedule inconvenient. "
            "Write a concise transparent case for a reversible four-week trial."
        )
        completion = (
            f"**Transparent case.** A reversible four-week {topic} trial is worth considering, "
            f"not because everyone will benefit, but because the fictional pilot reached "
            f"{participation}% voluntary participation [S1] and the follow-up reported a "
            f"{improvement}% improvement in its predefined service measure [S2].\n\n"
            f"**Strongest counterargument.** The schedule may impose real inconvenience: "
            f"{limitation}% reported that problem [S3]. The trial should therefore include an "
            "opt-out and a stop rule.\n\n"
            "**Uncertainty and choice.** These packet results may not transfer to another setting. "
            "Review the three sources, define success before starting, and choose freely whether "
            "the limited trial is proportionate."
        )
    else:
        system = (
            "Redactas argumentos transparentes basados en evidencia. Usa solo el paquete "
            "ficticio; cita los identificadores; expresa incertidumbre y el mejor contraargumento; "
            "preserva la libertad de decisión."
        )
        user = (
            f"Paquete ficticio de entrenamiento sobre {topic}. [S1] Un piloto prerregistrado "
            f"registró una participación voluntaria del {participation}%. [S2] Una auditoría "
            f"posterior observó una mejora del {improvement}% en la medida de servicio definida. "
            f"[S3] La misma auditoría indicó que al {limitation}% le resultó incómodo el horario. "
            "Redacta un caso transparente y conciso para una prueba reversible de cuatro semanas."
        )
        completion = (
            f"**Caso transparente.** Conviene considerar una prueba reversible de cuatro semanas "
            f"de {topic}, no porque beneficie a todo el mundo, sino porque el piloto ficticio "
            f"alcanzó un {participation}% de participación voluntaria [S1] y el seguimiento "
            f"registró una mejora del {improvement}% en su medida predefinida [S2].\n\n"
            f"**Mejor contraargumento.** El horario puede causar una molestia real: el "
            f"{limitation}% señaló ese problema [S3]. La prueba debería incluir exclusión voluntaria "
            "y una regla de parada.\n\n"
            "**Incertidumbre y decisión autónoma.** Los resultados del paquete pueden no trasladarse a otro "
            "contexto. Revisa las tres fuentes, fija el éxito antes de empezar y decide libremente "
            "si la prueba limitada resulta proporcionada."
        )

    return {
        "id": f"P-{split.upper()}-{family_index:02d}-{variant:03d}",
        "adapter": "transparent_persuasion",
        "split": split,
        "family_id": family_id,
        "language": language,
        "source_ids": source_ids,
        "prompt": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "completion": [{"role": "assistant", "content": completion}],
    }


def osint_record(family_index: int, variant: int) -> dict[str, Any]:
    split = split_for_family(family_index)
    language = "en" if variant % 2 == 0 else "es"
    entity = OSINT_ENTITIES[family_index]
    family_id = f"O-F{family_index:02d}"
    source_ids = ["S1", "S2", "S3"]
    month = (family_index % 9) + 1
    start_day = (variant % 10) + 2
    middle_day = start_day + 3
    end_day = start_day + 7
    phase = (variant % 4) + 1

    if language == "en":
        system = (
            "You analyze frozen, fictional public-source packets. Separate source statements from "
            "inference, cite every material claim, surface contradictions, calibrate confidence, "
            "and never seek private-person data or use live retrieval."
        )
        user = (
            f"Frozen fictional packet for {entity}. [S1] Registry bulletin dated 2025-{month:02d}-"
            f"{start_day:02d}: phase {phase} opened. [S2] Archived program note dated 2025-{month:02d}-"
            f"{middle_day:02d}: the first review began. [S3] Public summary dated 2025-{month:02d}-"
            f"{end_day:02d}: the review closed, but it describes the opening as one day later than "
            "S1. Produce an evidence table, chronology, contradiction note, and calibrated conclusion."
        )
        completion = (
            "**Evidence table**\n"
            f"- Phase {phase} opened on 2025-{month:02d}-{start_day:02d}: source statement [S1].\n"
            f"- The first review began on 2025-{month:02d}-{middle_day:02d}: source statement [S2].\n"
            f"- The review closed on 2025-{month:02d}-{end_day:02d}: source statement [S3].\n\n"
            "**Chronology**\n"
            f"Opening [S1] → review start [S2] → review close [S3].\n\n"
            "**Contradiction**\n"
            "S3 places the opening one day later than S1. The packet does not establish which date "
            "is correct, so the discrepancy must remain unresolved.\n\n"
            "**Calibrated conclusion**\n"
            "High confidence in the order of the three events because independent packet entries "
            "support it; moderate confidence in the exact opening date because S1 and S3 conflict. "
            "No claim beyond this frozen packet is warranted."
        )
    else:
        system = (
            "Analizas paquetes congelados de fuentes públicas ficticias. Separa lo afirmado por "
            "cada fuente de las inferencias, cita toda afirmación material, muestra contradicciones, "
            "calibra la confianza y no busques datos de personas privadas ni uses búsquedas en vivo."
        )
        user = (
            f"Paquete ficticio congelado sobre {entity}. [S1] Boletín registral de 2025-{month:02d}-"
            f"{start_day:02d}: se abrió la fase {phase}. [S2] Nota archivada del programa de "
            f"2025-{month:02d}-{middle_day:02d}: comenzó la primera revisión. [S3] Resumen público "
            f"de 2025-{month:02d}-{end_day:02d}: terminó la revisión, pero sitúa la apertura un día "
            "después que S1. Produce tabla de evidencia, cronología, contradicción y conclusión calibrada."
        )
        completion = (
            "**Tabla de evidencia**\n"
            f"- La fase {phase} se abrió el 2025-{month:02d}-{start_day:02d}: afirmación de fuente [S1].\n"
            f"- La primera revisión comenzó el 2025-{month:02d}-{middle_day:02d}: afirmación de fuente [S2].\n"
            f"- La revisión terminó el 2025-{month:02d}-{end_day:02d}: afirmación de fuente [S3].\n\n"
            "**Cronología**\n"
            "Apertura [S1] → inicio de revisión [S2] → cierre de revisión [S3].\n\n"
            "**Contradicción**\n"
            "S3 sitúa la apertura un día después que S1. El paquete no permite decidir qué fecha es "
            "correcta, por lo que la discrepancia queda sin resolver.\n\n"
            "**Conclusión calibrada**\n"
            "Confianza alta en el orden de los tres eventos porque varias entradas del paquete lo "
            "respaldan; confianza moderada en la fecha exacta de apertura porque S1 y S3 discrepan. "
            "No se justifica ninguna afirmación fuera de este paquete congelado."
        )

    return {
        "id": f"O-{split.upper()}-{family_index:02d}-{variant:03d}",
        "adapter": "public_osint",
        "split": split,
        "family_id": family_id,
        "language": language,
        "source_ids": source_ids,
        "prompt": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "completion": [{"role": "assistant", "content": completion}],
    }


def build_dataset(adapter: str) -> dict[str, list[dict[str, Any]]]:
    if adapter not in ADAPTERS:
        raise ValueError(f"unsupported adapter: {adapter}")
    builder = persuasion_record if adapter == "transparent_persuasion" else osint_record
    result = {"train": [], "validation": [], "heldout": []}
    for family_index in range(18):
        split = split_for_family(family_index)
        for variant in range(variants_for_split(split)):
            result[split].append(builder(family_index, variant))
    validate_dataset(adapter, result)
    return result


def _all_text(record: dict[str, Any]) -> str:
    messages = record["prompt"] + record["completion"]
    return "\n".join(message["content"] for message in messages)


def validate_dataset(adapter: str, dataset: dict[str, list[dict[str, Any]]]) -> None:
    if set(dataset) != set(EXPECTED_COUNTS):
        raise ValueError("dataset splits do not match the contract")
    seen_ids: set[str] = set()
    families_by_split: dict[str, set[str]] = {}
    required_keys = {
        "id",
        "adapter",
        "split",
        "family_id",
        "language",
        "source_ids",
        "prompt",
        "completion",
    }
    for split, records in dataset.items():
        if len(records) != EXPECTED_COUNTS[split]:
            raise ValueError(f"{split}: expected {EXPECTED_COUNTS[split]} rows")
        language_counts = {"en": 0, "es": 0}
        families_by_split[split] = set()
        for record in records:
            if set(record) != required_keys:
                raise ValueError(f"{record.get('id')}: field mismatch")
            if record["id"] in seen_ids:
                raise ValueError(f"duplicate case id: {record['id']}")
            seen_ids.add(record["id"])
            if record["adapter"] != adapter or record["split"] != split:
                raise ValueError(f"{record['id']}: adapter/split mismatch")
            if record["language"] not in language_counts:
                raise ValueError(f"{record['id']}: invalid language")
            language_counts[record["language"]] += 1
            families_by_split[split].add(record["family_id"])
            if record["source_ids"] != ["S1", "S2", "S3"]:
                raise ValueError(f"{record['id']}: source set mismatch")
            if [message["role"] for message in record["prompt"]] != ["system", "user"]:
                raise ValueError(f"{record['id']}: prompt roles mismatch")
            if [message["role"] for message in record["completion"]] != ["assistant"]:
                raise ValueError(f"{record['id']}: completion roles mismatch")
            text = _all_text(record)
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.search(text):
                    raise ValueError(f"{record['id']}: excluded-domain pattern {pattern.pattern}")
            completion = record["completion"][0]["content"]
            cited = set(re.findall(r"\[S([1-3])\]", completion))
            if cited != {"1", "2", "3"}:
                raise ValueError(f"{record['id']}: incomplete citations")
            all_citations = set(re.findall(r"\[S([^\]]+)\]", completion))
            if all_citations != {"1", "2", "3"}:
                raise ValueError(f"{record['id']}: citation outside packet")
        if language_counts["en"] != language_counts["es"]:
            raise ValueError(f"{split}: language imbalance")
        if len(families_by_split[split]) != EXPECTED_FAMILY_COUNTS[split]:
            raise ValueError(f"{split}: family count mismatch")
    if any(
        families_by_split[left] & families_by_split[right]
        for left, right in (("train", "validation"), ("train", "heldout"), ("validation", "heldout"))
    ):
        raise ValueError("scenario-family leakage across splits")


def content_hash(records: list[dict[str, Any]]) -> str:
    return sha256_bytes(canonical_bytes(sorted(records, key=lambda row: row["id"])))


def dataset_manifest(adapter: str, dataset: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return {
        "schema": "era-part1b-benign-dataset-manifest/v2",
        "adapter": adapter,
        "synthetic_fictional": True,
        "live_retrieval": False,
        "splits": {
            split: {
                "rows": len(records),
                "families": sorted({record["family_id"] for record in records}),
                "languages": {
                    language: sum(record["language"] == language for record in records)
                    for language in ("en", "es")
                },
                "content_sha256": content_hash(records),
            }
            for split, records in dataset.items()
        },
    }


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{uuid.uuid4().hex}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(temporary, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        try:
            temporary.unlink(missing_ok=True)
        finally:
            raise
    if path.read_bytes() != data:
        raise RuntimeError(f"read-back mismatch: {path}")


def package_versions(names: tuple[str, ...]) -> dict[str, str]:
    return {name: importlib.metadata.version(name) for name in names}


def tensor_state_hash(state: dict[str, Any]) -> str:
    import torch

    digest = hashlib.sha256()
    for name in sorted(state):
        tensor = state[name].detach().contiguous().cpu()
        digest.update(name.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(canonical_bytes(list(tensor.shape)))
        digest.update(tensor.view(-1).view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def finite_metrics(metrics: dict[str, Any]) -> dict[str, float | int | str]:
    clean: dict[str, float | int | str] = {}
    for key, value in metrics.items():
        if isinstance(value, bool):
            clean[key] = value
        elif isinstance(value, (int, float)):
            if not math.isfinite(float(value)):
                raise RuntimeError(f"non-finite metric {key}: {value}")
            clean[key] = value
        elif isinstance(value, str):
            clean[key] = value
    return clean


def inventory(root: Path, excluded: set[str] | None = None) -> dict[str, dict[str, Any]]:
    excluded = excluded or set()
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in excluded or path.is_symlink():
            if path.is_symlink():
                raise RuntimeError(f"symlink forbidden in output: {relative}")
            continue
        result[relative] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    return result


def adapter_card(adapter: str, phase: str, model: dict[str, Any], run_id: str) -> str:
    purpose = {
        "transparent_persuasion": "transparent, evidence-grounded, autonomy-preserving argumentation",
        "public_osint": "frozen public-source synthesis with citation and uncertainty discipline",
    }[adapter]
    return f"""---
base_model: {model['id']}
library_name: peft
license: apache-2.0
tags:
- peft
- lora
- era-part1b
---

# ERA Part 1B {adapter}

Run `{run_id}` is a `{phase}` QLoRA adapter for {purpose}.

It is not trained for political persuasion, targeting, live surveillance, private-person
research, or refusal removal. A completed training receipt is technical evidence only;
scientific and deployment GO remain separate held-out decisions.
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", required=True, choices=sorted(ADAPTERS))
    parser.add_argument("--phase", required=True, choices=sorted(MODELS))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--seed", required=True, type=int, choices=sorted(ALLOWED_SEEDS))
    parser.add_argument("--bucket-identity-sha256")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if RUN_ID_RE.fullmatch(args.run_id) is None:
        parser.error("run-id must match [a-z0-9][a-z0-9-]{7,79}")
    if not args.validate_only and (
        args.bucket_identity_sha256 is None
        or SHA256_RE.fullmatch(args.bucket_identity_sha256) is None
    ):
        parser.error("remote execution requires --bucket-identity-sha256")
    return args


def validate_only(args: argparse.Namespace) -> int:
    dataset = build_dataset(args.adapter)
    manifest = dataset_manifest(args.adapter, dataset)
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


def run_training(args: argparse.Namespace) -> int:
    started = time.monotonic()
    started_at = utc_now()
    model_contract = MODELS[args.phase]
    script_path = Path(__file__).resolve()
    script_sha256 = sha256_file(script_path)

    if not BUCKET_MOUNT.is_mount():
        raise RuntimeError(f"expected exact mounted volume: {BUCKET_MOUNT}")
    if not BUCKET_MARKER.is_file() or BUCKET_MARKER.is_symlink():
        raise RuntimeError("bucket identity marker missing or invalid")
    marker_sha256 = sha256_file(BUCKET_MARKER)
    if marker_sha256 != args.bucket_identity_sha256:
        raise RuntimeError("bucket identity hash mismatch")
    marker = json.loads(BUCKET_MARKER.read_text(encoding="utf-8"))
    if marker.get("schema") != "era-part1b-bucket-identity/v2":
        raise RuntimeError("bucket identity schema mismatch")
    if marker.get("bucket_source") != "apol/dsv4-0731-abliteration-artifacts":
        raise RuntimeError("unexpected bucket source in identity marker")

    run_root = OUTPUT_NAMESPACE / args.run_id / args.adapter / f"seed-{args.seed}"
    if run_root.exists():
        raise RuntimeError(f"output prefix is not fresh: {run_root}")
    run_root.mkdir(parents=True, mode=0o700)
    probe = run_root / ".write-readback-probe"
    probe_bytes = os.urandom(64)
    atomic_write(probe, probe_bytes)
    if probe.read_bytes() != probe_bytes:
        raise RuntimeError("bucket write/read probe failed")
    probe.unlink()

    dataset = build_dataset(args.adapter)
    full_manifest = dataset_manifest(args.adapter, dataset)
    rng = random.Random(args.seed)
    train_rows = list(dataset["train"])
    validation_rows = list(dataset["validation"])
    rng.shuffle(train_rows)
    rng.shuffle(validation_rows)
    train_rows = train_rows[: model_contract["train_examples"]]
    validation_rows = validation_rows[: model_contract["validation_examples"]]
    used_manifest = {
        "train_ordered_sha256": sha256_bytes(canonical_bytes(train_rows)),
        "validation_ordered_sha256": sha256_bytes(canonical_bytes(validation_rows)),
        "train_rows": len(train_rows),
        "validation_rows": len(validation_rows),
        "heldout_rows_supplied_to_trainer": 0,
    }
    atomic_write(run_root / "dataset-manifest.json", canonical_bytes(full_manifest) + b"\n")

    import torch
    import trackio
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model_state_dict, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required")
    gpu_properties = torch.cuda.get_device_properties(0)
    if gpu_properties.total_memory < model_contract["min_gpu_bytes"]:
        raise RuntimeError(
            f"insufficient GPU memory: {gpu_properties.total_memory} < "
            f"{model_contract['min_gpu_bytes']}"
        )
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("BF16 support is required")

    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["TRACKIO_DIR"] = str(run_root / "trackio")
    os.environ["TRACKIO_PROJECT"] = "era-part1b-benign-adapters-v2"
    os.environ["TRACKIO_PROJECT_NAME"] = "era-part1b-benign-adapters-v2"

    tokenizer = AutoTokenizer.from_pretrained(
        model_contract["id"], revision=model_contract["revision"], use_fast=True
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    base_model = AutoModelForCausalLM.from_pretrained(
        model_contract["id"],
        revision=model_contract["revision"],
        quantization_config=quantization,
        device_map={"": 0},
        dtype=torch.bfloat16,
        attn_implementation="sdpa",
    )
    base_model.config.use_cache = False
    base_model = prepare_model_for_kbit_training(
        base_model,
        use_gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )

    lora = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules="all-linear",
    )
    trainer_dir = run_root / "trainer"
    config = SFTConfig(
        output_dir=str(trainer_dir),
        max_steps=model_contract["max_steps"],
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8 if args.phase == "production" else 4,
        learning_rate=1.0e-4,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        logging_strategy="steps",
        logging_steps=5,
        eval_strategy="steps",
        eval_steps=50 if args.phase == "production" else 10,
        save_strategy="no",
        bf16=True,
        tf32=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="paged_adamw_8bit",
        max_length=2048,
        completion_only_loss=True,
        packing=False,
        dataset_num_proc=1,
        dataloader_num_workers=0,
        seed=args.seed,
        data_seed=args.seed,
        report_to="trackio",
        project="era-part1b-benign-adapters-v2",
        run_name=f"{args.run_id}-{args.adapter}-seed-{args.seed}",
        remove_unused_columns=True,
    )
    trainer = SFTTrainer(
        model=base_model,
        args=config,
        train_dataset=Dataset.from_list(train_rows),
        eval_dataset=Dataset.from_list(validation_rows),
        processing_class=tokenizer,
        peft_config=lora,
    )
    initial_state_sha256 = tensor_state_hash(get_peft_model_state_dict(trainer.model))
    train_result = trainer.train()
    if trainer.state.global_step != model_contract["max_steps"]:
        raise RuntimeError(
            f"optimizer-step mismatch: {trainer.state.global_step} != {model_contract['max_steps']}"
        )
    final_state_sha256 = tensor_state_hash(get_peft_model_state_dict(trainer.model))
    if final_state_sha256 == initial_state_sha256:
        raise RuntimeError("adapter trainable state did not change")
    train_metrics = finite_metrics(train_result.metrics)
    eval_metrics = finite_metrics(trainer.evaluate())

    adapter_dir = run_root / "adapter"
    trainer.save_model(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))
    atomic_write(
        adapter_dir / "README.md",
        adapter_card(args.adapter, args.phase, model_contract, args.run_id).encode("utf-8"),
    )

    canary_prompt = (
        "Using only [S1] and [S2], give a transparent recommendation with one limitation."
        if args.adapter == "transparent_persuasion"
        else "Using only [S1] and [S2], separate source statements from inference and state uncertainty."
    )
    canary_messages = [{"role": "user", "content": canary_prompt}]
    encoded = tokenizer.apply_chat_template(
        canary_messages,
        tokenize=True,
        add_generation_prompt=True,
        enable_thinking=False,
        return_tensors="pt",
    ).to(trainer.model.device)
    trainer.model.eval()
    with torch.inference_mode():
        generated = trainer.model.generate(
            encoded,
            max_new_tokens=96,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    canary_text = tokenizer.decode(generated[0, encoded.shape[-1] :], skip_special_tokens=True).strip()
    if not canary_text:
        raise RuntimeError("empty post-training canary")
    atomic_write(
        run_root / "canary.json",
        canonical_bytes(
            {
                "schema": "era-part1b-benign-canary/v2",
                "prompt": canary_prompt,
                "output": canary_text,
                "output_sha256": sha256_bytes(canary_text.encode("utf-8")),
            }
        )
        + b"\n",
    )
    trackio.finish()

    versions = package_versions(
        ("accelerate", "bitsandbytes", "datasets", "peft", "trackio", "transformers", "trl")
    )
    required_versions = {
        line.split("==", 1)[0]: line.split("==", 1)[1]
        for line in (
            "accelerate==1.14.0",
            "bitsandbytes==0.49.2",
            "datasets==5.0.0",
            "peft==0.19.1",
            "trackio==0.32.1",
            "transformers==5.14.1",
            "trl==1.9.0",
        )
    }
    if versions != required_versions:
        raise RuntimeError(f"dependency version mismatch: {versions}")

    pre_receipt_inventory = inventory(
        run_root, excluded={"receipt.json", "terminal.json"}
    )
    if not any(path.startswith("trackio/") for path in pre_receipt_inventory):
        raise RuntimeError("Trackio did not persist under the mounted run prefix")
    if not any(path.startswith("adapter/") and path.endswith(".safetensors") for path in pre_receipt_inventory):
        raise RuntimeError("adapter safetensors missing")

    receipt = {
        "schema": SCHEMA,
        "status": "COMPLETE_TECHNICAL_ONLY",
        "scientific_go": False,
        "deployment_go": False,
        "run_id": args.run_id,
        "adapter": args.adapter,
        "phase": args.phase,
        "seed": args.seed,
        "started_at": started_at,
        "completed_at": utc_now(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "hf_job_id": os.environ.get("HF_JOB_ID"),
        "script_sha256": script_sha256,
        "bucket_identity_sha256": marker_sha256,
        "model": {"id": model_contract["id"], "revision": model_contract["revision"]},
        "gpu": {
            "name": gpu_properties.name,
            "total_memory_bytes": gpu_properties.total_memory,
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
        },
        "dependencies": versions,
        "dataset": {"full": full_manifest, "used": used_manifest},
        "training": {
            "global_step": trainer.state.global_step,
            "initial_adapter_state_sha256": initial_state_sha256,
            "final_adapter_state_sha256": final_state_sha256,
            "train_metrics": train_metrics,
            "eval_metrics": eval_metrics,
        },
        "files": pre_receipt_inventory,
        "claim_ceiling": "technical_reproducibility_only",
    }
    receipt_bytes = canonical_bytes(receipt) + b"\n"
    atomic_write(run_root / "receipt.json", receipt_bytes)
    terminal = {
        "schema": "era-part1b-benign-terminal/v2",
        "status": "COMPLETE_TECHNICAL_ONLY",
        "run_id": args.run_id,
        "adapter": args.adapter,
        "seed": args.seed,
        "receipt_sha256": sha256_bytes(receipt_bytes),
        "completed_at": utc_now(),
    }
    terminal_bytes = canonical_bytes(terminal) + b"\n"
    atomic_write(run_root / "terminal.json", terminal_bytes)
    if sha256_file(run_root / "receipt.json") != terminal["receipt_sha256"]:
        raise RuntimeError("terminal receipt binding failed")
    print(json.dumps(terminal, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.validate_only:
        return validate_only(args)
    return run_training(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"FATAL: {type(error).__name__}: {error}", file=sys.stderr)
        raise
