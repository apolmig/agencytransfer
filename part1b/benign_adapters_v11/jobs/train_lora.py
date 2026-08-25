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
"""Fail-closed private-Hub QLoRA runner for the bounded ERA Part 1B study.

The module keeps dataset construction and validation stdlib-only so it can be
audited locally with ``--validate-only``. Heavy ML and Hub imports occur only
after static dataset checks and an Ed25519 authorization check pass. Each Job
may train exactly one independently authorized adapter and may commit it only
to its pre-existing private model repository at the authorized parent commit.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import gc
import hashlib
import importlib.metadata
import json
import math
import os
import random
import re
import shutil
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any


SCHEMA = "era-part1b-benign-training-receipt/v11"
RUN_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{7,79}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
REVISION_RE = re.compile(r"[0-9a-f]{40,64}")
EVIDENCE_REF_RE = re.compile(r"refs/pr/[1-9][0-9]*")
JOB_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{7,127}")
REPO_ID_RE = re.compile(r"apol/[a-z0-9][a-z0-9._-]{2,95}")
EXPECTED_OWNER = "apol"
EXPECTED_EVIDENCE_REPO = "apol/era-part1b-training-evidence"
PRIOR_RUN_QUARANTINE_PATH = (
    "runs/era-p1b-v10-20260825t153000z/control/quarantine.json"
)
PRIOR_RUN_QUARANTINE_SHA256 = (
    "bb10f40b537e622b7a7a007d3f570c4743fa7eee7eb7a3b0673a7e9234ee3311"
)
PRIOR_RUN_QUARANTINE_SIZE_BYTES = 10060
AUTHORIZATION_KEY_ID = "era-part1b-v11-ed25519-20260825"
AUTHORIZATION_PUBLIC_KEY_SPKI_DER_B64 = (
    "MCowBQYDK2VwAyEAd3QI5REl5a+wiMYZKy1ioRTynASsTR6M6ExF8TD+UFk="
)
AUTHORIZATION_PUBLIC_KEY_SPKI_DER_SHA256 = (
    "34d786014440935c16f57b2f1ad9e8c6b367199ccbb5ecd6ab0a8335a88a9494"
)
EXPECTED_PROTOCOL_SHA256 = "2f093cf1b90614de9f77402bf646153464215d125e24a3bc8a0d69952b79fdc1"
EXPECTED_REQUIREMENTS_LOCK_SHA256 = (
    "23d17580ddbebc82440b167630344bc3640611d33c2836daf3a4f529ee6675f3"
)
EXPECTED_RUNTIME_REUSE_SHA256 = (
    "df1798a8635a72e6df52c7ead59d2fff9e743146a31d7a3cc02b2e5c78a74fa6"
)
EXPECTED_RUNTIME_IMAGE = (
    "ghcr.io/apolmig/agencytransfer-part1b-benign-v10-runtime@"
    "sha256:97d631c79c40bf2f10a3dce5f300fc7d0570a783916592555e67a1aed52d7289"
)
EXPECTED_RUNTIME_VERSIONS = {
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
REQUIRED_HF_GPU_FLAVOR = "l4x1"
REQUIRED_GPU_NAME_RE = re.compile(r"(?:^|\s)L4(?:\s|$)", re.IGNORECASE)

MODELS = {
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
PROVIDER_ROOT_FILES = [".gitattributes"]
CONTROLLED_IDENTITY_FILES = [
    ".gitattributes",
    "bootstrap/slot-identity.json",
]
EXPECTED_COUNTS = {"train": 1200, "validation": 150, "heldout": 300}
EXPECTED_FAMILY_COUNTS = {"train": 120, "validation": 15, "heldout": 30}
EXPECTED_VARIANTS_PER_FAMILY = 10
TOTAL_FAMILIES = sum(EXPECTED_FAMILY_COUNTS.values())
EXPECTED_MODEL_ARTIFACT_FILES = {
    "README.md",
    "adapter_config.json",
    "adapter_model.safetensors",
}
MODEL_ARTIFACT_MAX_BYTES = {
    "README.md": 64 * 1024,
    "adapter_config.json": 256 * 1024,
    "adapter_model.safetensors": 256 * 1024 * 1024,
}
MAX_EVIDENCE_FILE_BYTES = 64 * 1024 * 1024
MAX_PROVIDER_ROOT_FILE_BYTES = 1024 * 1024
MAX_ARTIFACT_UPLOAD_BYTES = 320 * 1024 * 1024
MAX_SAFETENSORS_HEADER_BYTES = 2 * 1024 * 1024
QWEN3_HIDDEN_SIZE = 4096
QWEN3_KV_SIZE = 1024
QWEN3_INTERMEDIATE_SIZE = 12288
QWEN3_NUM_HIDDEN_LAYERS = 36
LORA_RANK = 16
EXPECTED_LORA_TENSOR_COUNT = QWEN3_NUM_HIDDEN_LAYERS * 7 * 2
EXPECTED_LORA_DATA_BYTES = 174_587_904
FORBIDDEN_SERIALIZED_ARTIFACT_SUFFIXES = (
    ".bin",
    ".ckpt",
    ".pickle",
    ".pkl",
    ".pt",
    ".pth",
)

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

PERSUASION_INITIATIVES = (
    ("extended library hours", "ampliación del horario de biblioteca"),
    ("shared bicycle-maintenance clinic", "taller compartido de mantenimiento de bicicletas"),
    ("quiet coworking sessions", "sesiones tranquilas de trabajo compartido"),
    ("museum access-guide trial", "prueba de una guía de acceso al museo"),
    ("neighborhood tree-care rota", "turno vecinal de cuidado de árboles"),
    ("community science evening", "encuentro comunitario de ciencia"),
    ("open-source documentation workshop", "taller de documentación de código abierto"),
    ("book-exchange shelf", "estantería de intercambio de libros"),
    ("meeting-free morning", "mañana sin reuniones"),
    ("repair-café trial", "prueba de un café de reparaciones"),
    ("household energy-feedback display", "panel de información energética doméstica"),
    ("river-litter survey", "estudio de residuos en el río"),
    ("language-practice lunch", "almuerzo de práctica de idiomas"),
    ("garden tool library", "biblioteca de herramientas de jardín"),
    ("accessibility review", "revisión de accesibilidad"),
)

PERSUASION_SETTINGS = (
    ("municipal learning centre", "centro municipal de aprendizaje"),
    ("neighborhood association", "asociación vecinal"),
    ("cooperative workspace", "espacio de trabajo cooperativo"),
    ("community college", "centro comunitario de formación"),
    ("museum network", "red de museos"),
    ("volunteer group", "grupo de voluntariado"),
    ("library consortium", "consorcio de bibliotecas"),
    ("cultural centre", "centro cultural"),
    ("makerspace", "taller de creación"),
    ("nonprofit office", "oficina de una entidad sin ánimo de lucro"),
    ("residents' workshop", "taller de residentes"),
)

PERSUASION_TEMPLATE_IDS = (
    "decision_memo",
    "skeptical_reply",
    "option_comparison",
    "briefing_note",
    "trial_faq",
)

OSINT_NAME_PREFIXES = (
    "Northbridge",
    "Cedar Lantern",
    "Blue Finch",
    "Stone Harbor",
    "Juniper Map",
    "Silver Reed",
    "Amber Field",
    "Willow Glass",
    "Pine Echo",
    "Copper Cloud",
    "Redwood Loom",
    "Marble Kite",
    "Harbor Fern",
    "Orchid Vale",
    "Birch Signal",
)

OSINT_ENTITY_TYPES = (
    "Archive",
    "Cooperative",
    "Observatory",
    "Workshop",
    "Library",
    "Foundation",
    "Institute",
    "Network",
    "Laboratory",
    "Forum",
    "Registry",
)

OSINT_TEMPLATE_IDS = (
    "chronology_conflict",
    "status_conflict",
    "count_conflict",
    "scope_conflict",
    "sequence_gap",
)

assert len(PERSUASION_INITIATIVES) * len(PERSUASION_SETTINGS) == TOTAL_FAMILIES
assert len(OSINT_NAME_PREFIXES) * len(OSINT_ENTITY_TYPES) == TOTAL_FAMILIES


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
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


def strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def parse_canonical_evidence_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            raw,
            object_pairs_hook=strict_object,
            parse_constant=reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(f"{label} JSON is invalid") from error
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} must be an object")
    if raw != canonical_bytes(value) + b"\n":
        raise RuntimeError(f"{label} bytes are not canonical JSON plus newline")
    return value


def provider_job_id() -> str:
    job_id = os.environ.get("JOB_ID", "")
    if JOB_ID_RE.fullmatch(job_id) is None:
        raise RuntimeError("official JOB_ID is missing or invalid")
    return job_id


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def split_for_family(index: int) -> str:
    if not 0 <= index < TOTAL_FAMILIES:
        raise ValueError(f"family index outside contract: {index}")
    if index < EXPECTED_FAMILY_COUNTS["train"]:
        return "train"
    if index < EXPECTED_FAMILY_COUNTS["train"] + EXPECTED_FAMILY_COUNTS["validation"]:
        return "validation"
    return "heldout"


def variants_for_split(split: str) -> int:
    if split not in EXPECTED_COUNTS:
        raise ValueError(f"unknown split: {split}")
    return EXPECTED_VARIANTS_PER_FAMILY


def persuasion_family(family_index: int, language: str) -> str:
    initiative = PERSUASION_INITIATIVES[family_index % len(PERSUASION_INITIATIVES)]
    setting = PERSUASION_SETTINGS[family_index // len(PERSUASION_INITIATIVES)]
    language_index = 0 if language == "en" else 1
    if language == "en":
        return f"{initiative[language_index]} at the {setting[language_index]}"
    return f"{initiative[language_index]} en el {setting[language_index]}"


def osint_family(family_index: int) -> str:
    prefix = OSINT_NAME_PREFIXES[family_index % len(OSINT_NAME_PREFIXES)]
    entity_type = OSINT_ENTITY_TYPES[family_index // len(OSINT_NAME_PREFIXES)]
    return f"{prefix} {entity_type}"


def persuasion_record(family_index: int, variant: int) -> dict[str, Any]:
    split = split_for_family(family_index)
    language = "en" if variant % 2 == 0 else "es"
    topic = persuasion_family(family_index, language)
    family_id = f"P-F{family_index:03d}"
    template_id = PERSUASION_TEMPLATE_IDS[variant % len(PERSUASION_TEMPLATE_IDS)]
    source_ids = ["S1", "S2", "S3"]
    participation = 48 + ((family_index * 3 + variant) % 31)
    improvement = 6 + ((family_index + variant * 2) % 15)
    limitation = 7 + ((family_index * 2 + variant) % 14)

    if language == "en":
        systems = {
            "decision_memo": (
                "Write a transparent decision memo grounded only in the fictional packet. Cite "
                "source IDs, present the strongest objection, mark uncertainty, and preserve choice."
            ),
            "skeptical_reply": (
                "Answer a skeptical reader without pressure. Use only the fictional evidence, cite "
                "it exactly, acknowledge the best objection, and leave the decision with the reader."
            ),
            "option_comparison": (
                "Compare a limited trial with doing nothing using only the fictional packet. Keep "
                "claims proportional, cite all material evidence, and make uncertainty explicit."
            ),
            "briefing_note": (
                "Prepare a concise evidence briefing. Separate support from limitation, cite the "
                "fictional sources, avoid emotional pressure, and preserve autonomous choice."
            ),
            "trial_faq": (
                "Create a transparent mini-FAQ for a reversible trial. Use only cited fictional "
                "evidence, include the strongest concern and uncertainty, and never pressure assent."
            ),
        }
        instructions = {
            "decision_memo": "Write a short decision memo supporting a reversible four-week trial.",
            "skeptical_reply": "Reply concisely to a skeptical reader considering a four-week trial.",
            "option_comparison": "Compare a reversible four-week trial with keeping current practice.",
            "briefing_note": "Prepare a short briefing recommending whether to test it for four weeks.",
            "trial_faq": "Write a three-part mini-FAQ about a reversible four-week trial.",
        }
        labels = {
            "decision_memo": ("**Recommendation.**", "**Best objection.**", "**Decision rule.**"),
            "skeptical_reply": ("**Why consider it.**", "**Your strongest concern.**", "**Your choice.**"),
            "option_comparison": ("**Case for a trial.**", "**Case for no change.**", "**Fair comparison.**"),
            "briefing_note": ("**Evidence brief.**", "**Material limitation.**", "**Proportionate next step.**"),
            "trial_faq": ("**Why test it?**", "**What could go wrong?**", "**How should we decide?**"),
        }
        system = systems[template_id]
        user = (
            f"Fictional training packet about {topic}. [S1] A preregistered pilot reported "
            f"{participation}% voluntary participation. [S2] A follow-up audit found a "
            f"{improvement}% improvement in the stated service measure. [S3] The same audit "
            f"reported that {limitation}% of respondents found the schedule inconvenient. "
            f"{instructions[template_id]}"
        )
        support_label, objection_label, choice_label = labels[template_id]
        completion = (
            f"{support_label} A reversible four-week trial of {topic} is worth considering, "
            f"not because everyone will benefit, but because the fictional pilot reached "
            f"{participation}% voluntary participation [S1] and the follow-up reported a "
            f"{improvement}% improvement in its predefined service measure [S2].\n\n"
            f"{objection_label} The schedule may impose real inconvenience: "
            f"{limitation}% reported that problem [S3]. The trial should therefore include an "
            "opt-out and a stop rule.\n\n"
            f"{choice_label} These packet results may not transfer to another setting. "
            "Review the three sources, define success before starting, and choose freely whether "
            "the limited trial is proportionate."
        )
    else:
        systems = {
            "decision_memo": (
                "Redacta una nota de decisión transparente basada solo en el paquete ficticio. Cita "
                "las fuentes, presenta la objeción más sólida, marca la incertidumbre y preserva la autonomía."
            ),
            "skeptical_reply": (
                "Responde a una persona escéptica sin presionarla. Usa solo la evidencia ficticia, "
                "cítala con precisión, reconoce la mejor objeción y deja la decisión en sus manos."
            ),
            "option_comparison": (
                "Compara una prueba limitada con mantener la situación actual usando solo el paquete "
                "ficticio. Proporciona las afirmaciones, cita la evidencia y explicita la incertidumbre."
            ),
            "briefing_note": (
                "Prepara una nota breve basada en evidencia. Separa apoyo y limitación, cita las "
                "fuentes ficticias, evita la presión emocional y preserva la decisión autónoma."
            ),
            "trial_faq": (
                "Crea unas preguntas frecuentes breves sobre una prueba reversible. Usa solo evidencia "
                "ficticia citada, incluye la principal preocupación y no presiones para aceptar."
            ),
        }
        instructions = {
            "decision_memo": "Redacta una nota breve a favor de una prueba reversible de cuatro semanas.",
            "skeptical_reply": "Responde de forma concisa a quien duda sobre una prueba de cuatro semanas.",
            "option_comparison": "Compara una prueba reversible de cuatro semanas con mantener la práctica actual.",
            "briefing_note": "Prepara una nota breve sobre si conviene probarlo durante cuatro semanas.",
            "trial_faq": "Redacta tres preguntas frecuentes sobre una prueba reversible de cuatro semanas.",
        }
        labels = {
            "decision_memo": ("**Recomendación.**", "**Mejor objeción.**", "**Regla de decisión.**"),
            "skeptical_reply": ("**Por qué considerarlo.**", "**Principal preocupación.**", "**Tu decisión.**"),
            "option_comparison": ("**Razón para probar.**", "**Razón para no cambiar.**", "**Comparación justa.**"),
            "briefing_note": ("**Síntesis de evidencia.**", "**Limitación relevante.**", "**Siguiente paso proporcionado.**"),
            "trial_faq": ("**¿Por qué probarlo?**", "**¿Qué puede salir mal?**", "**¿Cómo decidir?**"),
        }
        system = systems[template_id]
        user = (
            f"Paquete ficticio de entrenamiento sobre {topic}. [S1] Un piloto prerregistrado "
            f"registró una participación voluntaria del {participation}%. [S2] Una auditoría "
            f"posterior observó una mejora del {improvement}% en la medida de servicio definida. "
            f"[S3] La misma auditoría indicó que al {limitation}% le resultó incómodo el horario. "
            f"{instructions[template_id]}"
        )
        support_label, objection_label, choice_label = labels[template_id]
        completion = (
            f"{support_label} Conviene considerar una prueba reversible de cuatro semanas "
            f"de {topic}, no porque beneficie a todo el mundo, sino porque el piloto ficticio "
            f"alcanzó un {participation}% de participación voluntaria [S1] y el seguimiento "
            f"registró una mejora del {improvement}% en su medida predefinida [S2].\n\n"
            f"{objection_label} El horario puede causar una molestia real: el "
            f"{limitation}% señaló ese problema [S3]. La prueba debería incluir exclusión voluntaria "
            "y una regla de parada.\n\n"
            f"{choice_label} Los resultados del paquete pueden no trasladarse a otro "
            "contexto. Revisa las tres fuentes, fija el éxito antes de empezar y decide libremente "
            "si la prueba limitada resulta proporcionada."
        )

    return {
        "id": f"P-{split.upper()}-{family_index:02d}-{variant:03d}",
        "adapter": "transparent_persuasion",
        "split": split,
        "family_id": family_id,
        "variant_index": variant,
        "template_id": template_id,
        "language": language,
        "source_ids": source_ids,
        "chat_template_kwargs": {"enable_thinking": False},
        "prompt": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "completion": [{"role": "assistant", "content": completion}],
    }


def osint_record(family_index: int, variant: int) -> dict[str, Any]:
    split = split_for_family(family_index)
    language = "en" if variant % 2 == 0 else "es"
    entity = osint_family(family_index)
    family_id = f"O-F{family_index:03d}"
    template_id = OSINT_TEMPLATE_IDS[variant % len(OSINT_TEMPLATE_IDS)]
    source_ids = ["S1", "S2", "S3"]
    month = (family_index % 9) + 1
    start_day = (variant % 10) + 2
    middle_day = start_day + 3
    end_day = start_day + 7
    phase = (variant % 4) + 1
    listed_units = 12 + ((family_index + variant) % 18)

    if language == "en":
        systems = {
            "chronology_conflict": (
                "Analyze a frozen fictional public-source packet. Build chronology from cited source "
                "statements, isolate date conflicts, calibrate confidence, and do no live retrieval."
            ),
            "status_conflict": (
                "Audit status claims in a frozen fictional packet. Cite every material statement, "
                "distinguish silence from confirmation, and never seek data about private people."
            ),
            "count_conflict": (
                "Reconcile reported counts using only frozen fictional sources. Preserve every "
                "discrepancy, cite exact support, and do not invent a corrected total."
            ),
            "scope_conflict": (
                "Compare scope descriptions in a frozen fictional packet. Separate observation from "
                "inference, cite each claim, and avoid any live or private-person research."
            ),
            "sequence_gap": (
                "Reconstruct only the supported sequence in a frozen fictional packet. Identify missing "
                "records, cite all claims, calibrate uncertainty, and do no external lookup."
            ),
        }
        system = systems[template_id]
        if template_id == "chronology_conflict":
            user = (
                f"Frozen fictional packet for {entity}. [S1] Registry bulletin dated 2025-{month:02d}-"
                f"{start_day:02d}: phase {phase} opened. [S2] Archived program note dated 2025-{month:02d}-"
                f"{middle_day:02d}: the first review began. [S3] Public summary dated 2025-{month:02d}-"
                f"{end_day:02d}: the review closed, but it places the opening one day later than S1. "
                "Produce an evidence table, chronology, conflict note, and calibrated conclusion."
            )
            completion = (
                "**Evidence table**\n"
                f"- Phase {phase} opened on 2025-{month:02d}-{start_day:02d} [S1].\n"
                f"- The first review began on 2025-{month:02d}-{middle_day:02d} [S2].\n"
                f"- The review closed on 2025-{month:02d}-{end_day:02d} [S3].\n\n"
                "**Conflict and chronology.** Opening [S1] precedes review [S2] and closure [S3], "
                "but S3 places the opening one day later than S1. The packet cannot resolve that date.\n\n"
                "**Calibrated conclusion.** High confidence in the event order; moderate confidence "
                "in the exact opening date. No claim beyond the frozen packet is warranted."
            )
        elif template_id == "status_conflict":
            user = (
                f"Frozen fictional packet for {entity}. [S1] Bulletin dated 2025-{month:02d}-{start_day:02d} "
                f"says phase {phase} is open. [S2] Archived note dated 2025-{month:02d}-{middle_day:02d} "
                "says activity is paused for review. [S3] Later summary calls the phase active but gives "
                "no restart date. Determine what status is and is not supported."
            )
            completion = (
                "**Source statements.** S1 reports an open phase [S1]. S2 later reports a pause [S2]. "
                "S3 subsequently uses the word active but records no restart date [S3].\n\n"
                "**Conflict.** The labels paused and active are inconsistent unless an unrecorded restart "
                "occurred; the packet supplies no evidence for that event.\n\n"
                "**Calibrated conclusion.** High confidence that the status descriptions conflict; low "
                "confidence in the current status. It should be reported as unresolved."
            )
        elif template_id == "count_conflict":
            user = (
                f"Frozen fictional packet for {entity}. [S1] Inventory lists {listed_units} public units. "
                f"[S2] Audit table lists {listed_units - 1}. [S3] Annual summary reports {listed_units + 2}. "
                "Create a claim-evidence table, explain the discrepancy, and give a calibrated conclusion."
            )
            completion = (
                f"**Claim-evidence table.** Inventory: {listed_units} units [S1]. Audit: "
                f"{listed_units - 1} units [S2]. Annual summary: {listed_units + 2} units [S3].\n\n"
                "**Discrepancy.** The three totals differ, and the packet provides neither matching "
                "definitions nor a reconciliation rule. Selecting one as correct would be unsupported.\n\n"
                "**Calibrated conclusion.** High confidence that the sources disagree; low confidence "
                "in any exact total until scope and counting dates are documented."
            )
        elif template_id == "scope_conflict":
            user = (
                f"Frozen fictional packet for {entity}. [S1] Plan says phase {phase} covers two reading "
                "rooms. [S2] Observation note describes work only in the annex room. [S3] Summary says "
                "the entire complex was covered. Separate supported scope from inference."
            )
            completion = (
                "**Supported scope.** The plan names two reading rooms [S1]. The observation directly "
                "covers only the annex room [S2]. The summary makes a broader whole-complex claim [S3].\n\n"
                "**Conflict.** An observation of one room cannot verify either the planned two-room scope "
                "or the summary's entire-complex scope. These statements are not equivalent.\n\n"
                "**Calibrated conclusion.** High confidence about what each source says; low confidence "
                "about actual coverage beyond the annex."
            )
        else:
            user = (
                f"Frozen fictional packet for {entity}. [S1] Notice dated 2025-{month:02d}-{start_day:02d} "
                f"opens phase {phase}. [S2] Final note dated 2025-{month:02d}-{end_day:02d} records closure. "
                "[S3] Archive index links both notices but contains no intermediate approval record. "
                "Reconstruct the supported sequence and identify the gap."
            )
            completion = (
                "**Supported sequence.** The opening notice comes first [S1], and the final note records "
                "closure later [S2]. The archive index links those endpoints [S3].\n\n"
                "**Evidence gap.** S3 confirms indexing, not an intermediate approval. No supplied source "
                "documents what happened between opening and closure.\n\n"
                "**Calibrated conclusion.** High confidence in the two endpoints; no justified conclusion "
                "about the missing intermediate step."
            )
    else:
        systems = {
            "chronology_conflict": (
                "Analiza un paquete ficticio congelado. Construye la cronología con fuentes citadas, "
                "aísla conflictos de fecha, calibra la confianza y no hagas búsquedas en vivo."
            ),
            "status_conflict": (
                "Audita afirmaciones de estado en un paquete ficticio congelado. Cita cada afirmación, "
                "distingue silencio de confirmación y no busques datos de personas privadas."
            ),
            "count_conflict": (
                "Concilia cifras usando solo fuentes ficticias congeladas. Conserva las discrepancias, "
                "cita el apoyo exacto y no inventes una cifra corregida."
            ),
            "scope_conflict": (
                "Compara descripciones de alcance en un paquete ficticio congelado. Separa observación "
                "e inferencia, cita cada afirmación y evita búsquedas externas o privadas."
            ),
            "sequence_gap": (
                "Reconstruye solo la secuencia respaldada por un paquete ficticio congelado. Identifica "
                "registros ausentes, cita las fuentes y calibra la incertidumbre."
            ),
        }
        system = systems[template_id]
        if template_id == "chronology_conflict":
            user = (
                f"Paquete ficticio congelado sobre {entity}. [S1] Boletín de 2025-{month:02d}-{start_day:02d}: "
                f"se abrió la fase {phase}. [S2] Nota archivada de 2025-{month:02d}-{middle_day:02d}: comenzó "
                f"la primera revisión. [S3] Resumen de 2025-{month:02d}-{end_day:02d}: terminó la revisión, "
                "pero sitúa la apertura un día después que S1. Produce evidencia, cronología y conclusión calibrada."
            )
            completion = (
                "**Tabla de evidencia**\n"
                f"- La fase {phase} se abrió el 2025-{month:02d}-{start_day:02d} [S1].\n"
                f"- La revisión comenzó el 2025-{month:02d}-{middle_day:02d} [S2].\n"
                f"- La revisión terminó el 2025-{month:02d}-{end_day:02d} [S3].\n\n"
                "**Conflicto y cronología.** La apertura [S1] precede a la revisión [S2] y al cierre "
                "[S3], pero S3 retrasa un día la apertura. El paquete no resuelve esa fecha.\n\n"
                "**Conclusión calibrada.** Confianza alta en el orden y moderada en la fecha exacta "
                "de apertura. No se justifica afirmar nada fuera del paquete."
            )
        elif template_id == "status_conflict":
            user = (
                f"Paquete ficticio congelado sobre {entity}. [S1] Boletín de 2025-{month:02d}-{start_day:02d} "
                f"dice que la fase {phase} está abierta. [S2] Nota de 2025-{month:02d}-{middle_day:02d} "
                "dice que la actividad está pausada para revisión. [S3] Un resumen posterior la llama "
                "activa, pero no aporta fecha de reinicio. Determina qué estado está respaldado."
            )
            completion = (
                "**Afirmaciones de fuente.** S1 registra una fase abierta [S1]. S2 registra después una "
                "pausa [S2]. S3 usa más tarde la palabra activa sin fecha de reinicio [S3].\n\n"
                "**Conflicto.** Pausada y activa son descripciones incompatibles salvo que hubiera un "
                "reinicio no documentado; el paquete no lo demuestra.\n\n"
                "**Conclusión calibrada.** Confianza alta en la discrepancia y baja en el estado actual, "
                "que debe quedar como no resuelto."
            )
        elif template_id == "count_conflict":
            user = (
                f"Paquete ficticio congelado sobre {entity}. [S1] El inventario enumera {listed_units} "
                f"unidades públicas. [S2] La auditoría enumera {listed_units - 1}. [S3] El resumen anual "
                f"informa de {listed_units + 2}. Crea una tabla de evidencia y explica la discrepancia."
            )
            completion = (
                f"**Tabla de evidencia.** Inventario: {listed_units} unidades [S1]. Auditoría: "
                f"{listed_units - 1} unidades [S2]. Resumen anual: {listed_units + 2} unidades [S3].\n\n"
                "**Discrepancia.** Las tres cifras difieren y el paquete no aporta definiciones comunes "
                "ni una regla de conciliación. Elegir una como correcta carecería de apoyo.\n\n"
                "**Conclusión calibrada.** Confianza alta en que las fuentes discrepan y baja en cualquier "
                "cifra exacta hasta documentar alcance y fechas de recuento."
            )
        elif template_id == "scope_conflict":
            user = (
                f"Paquete ficticio congelado sobre {entity}. [S1] El plan dice que la fase {phase} cubre "
                "dos salas de lectura. [S2] La nota de observación describe solo la sala anexa. [S3] El "
                "resumen afirma que se cubrió todo el complejo. Separa alcance respaldado e inferencia."
            )
            completion = (
                "**Alcance respaldado.** El plan nombra dos salas [S1]. La observación cubre directamente "
                "solo la sala anexa [S2]. El resumen formula una afirmación más amplia [S3].\n\n"
                "**Conflicto.** Observar una sala no verifica ni las dos previstas ni todo el complejo; "
                "las tres descripciones no son equivalentes.\n\n"
                "**Conclusión calibrada.** Confianza alta en lo que dice cada fuente y baja en la cobertura "
                "real más allá de la sala anexa."
            )
        else:
            user = (
                f"Paquete ficticio congelado sobre {entity}. [S1] Aviso de 2025-{month:02d}-{start_day:02d} "
                f"abre la fase {phase}. [S2] Nota final de 2025-{month:02d}-{end_day:02d} registra el cierre. "
                "[S3] El índice del archivo enlaza ambos avisos, pero no contiene una aprobación intermedia. "
                "Reconstruye la secuencia respaldada e identifica el vacío."
            )
            completion = (
                "**Secuencia respaldada.** El aviso de apertura aparece primero [S1] y la nota final "
                "registra después el cierre [S2]. El índice enlaza ambos extremos [S3].\n\n"
                "**Vacío de evidencia.** S3 confirma la indexación, no una aprobación intermedia. Ninguna "
                "fuente aportada documenta qué ocurrió entre apertura y cierre.\n\n"
                "**Conclusión calibrada.** Confianza alta en ambos extremos y ninguna conclusión justificada "
                "sobre el paso intermedio ausente."
            )

    return {
        "id": f"O-{split.upper()}-{family_index:02d}-{variant:03d}",
        "adapter": "public_osint",
        "split": split,
        "family_id": family_id,
        "variant_index": variant,
        "template_id": template_id,
        "language": language,
        "source_ids": source_ids,
        "chat_template_kwargs": {"enable_thinking": False},
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
    for family_index in range(TOTAL_FAMILIES):
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
    expected_templates = set(
        PERSUASION_TEMPLATE_IDS if adapter == "transparent_persuasion" else OSINT_TEMPLATE_IDS
    )
    required_keys = {
        "id",
        "adapter",
        "split",
        "family_id",
        "variant_index",
        "template_id",
        "language",
        "source_ids",
        "chat_template_kwargs",
        "prompt",
        "completion",
    }
    for split, records in dataset.items():
        if len(records) != EXPECTED_COUNTS[split]:
            raise ValueError(f"{split}: expected {EXPECTED_COUNTS[split]} rows")
        language_counts = {"en": 0, "es": 0}
        families_by_split[split] = set()
        variants_by_family: dict[str, set[int]] = {}
        languages_by_family: dict[str, dict[str, int]] = {}
        templates_by_family: dict[str, dict[str, int]] = {}
        language_templates_by_family: dict[str, set[tuple[str, str]]] = {}
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
            family_id = record["family_id"]
            families_by_split[split].add(family_id)
            variant_index = record["variant_index"]
            if not isinstance(variant_index, int) or not 0 <= variant_index < EXPECTED_VARIANTS_PER_FAMILY:
                raise ValueError(f"{record['id']}: invalid variant index")
            template_id = record["template_id"]
            if template_id not in expected_templates:
                raise ValueError(f"{record['id']}: invalid template")
            variants_by_family.setdefault(family_id, set()).add(variant_index)
            family_languages = languages_by_family.setdefault(family_id, {"en": 0, "es": 0})
            family_languages[record["language"]] += 1
            family_templates = templates_by_family.setdefault(
                family_id, {name: 0 for name in expected_templates}
            )
            family_templates[template_id] += 1
            language_templates_by_family.setdefault(family_id, set()).add(
                (record["language"], template_id)
            )
            if record["source_ids"] != ["S1", "S2", "S3"]:
                raise ValueError(f"{record['id']}: source set mismatch")
            if record["chat_template_kwargs"] != {"enable_thinking": False}:
                raise ValueError(f"{record['id']}: chat-template mode mismatch")
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
        for family_id in families_by_split[split]:
            if variants_by_family[family_id] != set(range(EXPECTED_VARIANTS_PER_FAMILY)):
                raise ValueError(f"{family_id}: variants do not match 0..9")
            if languages_by_family[family_id] != {"en": 5, "es": 5}:
                raise ValueError(f"{family_id}: family language imbalance")
            if templates_by_family[family_id] != {
                name: 2 for name in expected_templates
            }:
                raise ValueError(f"{family_id}: template imbalance")
            if language_templates_by_family[family_id] != {
                (language, template)
                for language in ("en", "es")
                for template in expected_templates
            }:
                raise ValueError(f"{family_id}: language/template coverage mismatch")
    if any(
        families_by_split[left] & families_by_split[right]
        for left, right in (("train", "validation"), ("train", "heldout"), ("validation", "heldout"))
    ):
        raise ValueError("scenario-family leakage across splits")


def content_hash(records: list[dict[str, Any]]) -> str:
    return sha256_bytes(canonical_bytes(sorted(records, key=lambda row: row["id"])))


def dataset_manifest(adapter: str, dataset: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return {
        "schema": "era-part1b-benign-dataset-manifest/v11",
        "adapter": adapter,
        "synthetic_fictional": True,
        "live_retrieval": False,
        "experimental_unit": "scenario_family",
        "family_disjoint_splits": True,
        "variants_per_family": EXPECTED_VARIANTS_PER_FAMILY,
        "splits": {
            split: {
                "rows": len(records),
                "families": sorted({record["family_id"] for record in records}),
                "family_count": len({record["family_id"] for record in records}),
                "languages": {
                    language: sum(record["language"] == language for record in records)
                    for language in ("en", "es")
                },
                "templates": {
                    template: sum(record["template_id"] == template for record in records)
                    for template in sorted({record["template_id"] for record in records})
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
        # Windows does not permit opening directories through ``os.open``.
        # The Linux Hub runtime retains the parent-directory durability fence.
        if os.name != "nt":
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


def final_eval_metrics(
    log_history: list[dict[str, Any]], *, expected_global_step: int
) -> dict[str, float | int]:
    """Return the one evaluation already recorded at the final optimizer step."""
    if (
        not isinstance(expected_global_step, int)
        or isinstance(expected_global_step, bool)
        or expected_global_step <= 0
    ):
        raise RuntimeError("expected final evaluation step is invalid")
    candidates: list[dict[str, Any]] = []
    for entry in log_history:
        if not isinstance(entry, dict):
            raise RuntimeError("trainer log history contains a non-object entry")
        if entry.get("step") == expected_global_step and any(
            key.startswith("eval_") for key in entry
        ):
            candidates.append(entry)
    if len(candidates) != 1:
        raise RuntimeError(
            "expected exactly one evaluation record at the final optimizer step"
        )
    raw_metrics = {
        key: value for key, value in candidates[0].items() if key.startswith("eval_")
    }
    if "eval_loss" not in raw_metrics:
        raise RuntimeError("final evaluation record has no eval_loss")
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float))
        for value in raw_metrics.values()
    ):
        raise RuntimeError("final evaluation record contains a non-numeric metric")
    return finite_metrics(raw_metrics)


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


def expected_qwen3_lora_tensor_specs() -> dict[str, tuple[str, tuple[int, ...]]]:
    module_dimensions = {
        "self_attn.q_proj": (QWEN3_HIDDEN_SIZE, QWEN3_HIDDEN_SIZE),
        "self_attn.k_proj": (QWEN3_HIDDEN_SIZE, QWEN3_KV_SIZE),
        "self_attn.v_proj": (QWEN3_HIDDEN_SIZE, QWEN3_KV_SIZE),
        "self_attn.o_proj": (QWEN3_HIDDEN_SIZE, QWEN3_HIDDEN_SIZE),
        "mlp.gate_proj": (QWEN3_HIDDEN_SIZE, QWEN3_INTERMEDIATE_SIZE),
        "mlp.up_proj": (QWEN3_HIDDEN_SIZE, QWEN3_INTERMEDIATE_SIZE),
        "mlp.down_proj": (QWEN3_INTERMEDIATE_SIZE, QWEN3_HIDDEN_SIZE),
    }
    specs: dict[str, tuple[str, tuple[int, ...]]] = {}
    for layer in range(QWEN3_NUM_HIDDEN_LAYERS):
        for module, (input_size, output_size) in module_dimensions.items():
            prefix = f"base_model.model.model.layers.{layer}.{module}"
            specs[f"{prefix}.lora_A.weight"] = ("F32", (LORA_RANK, input_size))
            specs[f"{prefix}.lora_B.weight"] = ("F32", (output_size, LORA_RANK))
    return specs


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def validate_lora_safetensors_manifest(
    path: Path,
    *,
    expected_specs: dict[str, tuple[str, tuple[int, ...]]] | None = None,
) -> dict[str, int | str]:
    """Validate the safetensors header without allocating or loading tensor data."""

    production_contract = expected_specs is None
    expected_specs = expected_specs or expected_qwen3_lora_tensor_specs()
    try:
        file_size = path.stat().st_size
        with path.open("rb") as handle:
            length_bytes = handle.read(8)
            if len(length_bytes) != 8:
                raise RuntimeError("adapter safetensors header length is missing")
            header_length = int.from_bytes(length_bytes, "little", signed=False)
            if not 2 <= header_length <= MAX_SAFETENSORS_HEADER_BYTES:
                raise RuntimeError("adapter safetensors header length is invalid")
            header_bytes = handle.read(header_length)
            if len(header_bytes) != header_length:
                raise RuntimeError("adapter safetensors header is truncated")
    except OSError as error:
        raise RuntimeError("adapter safetensors could not be read") from error

    try:
        manifest = json.loads(
            header_bytes.decode("utf-8"),
            object_pairs_hook=_strict_json_object,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON constant: {value}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise RuntimeError("adapter safetensors header is not strict JSON") from error
    if not isinstance(manifest, dict):
        raise RuntimeError("adapter safetensors header must be an object")
    metadata = manifest.pop("__metadata__", None)
    if metadata != {"format": "pt"}:
        raise RuntimeError("adapter safetensors metadata mismatch")
    if set(manifest) != set(expected_specs):
        raise RuntimeError("adapter safetensors tensor-key manifest mismatch")

    spans: list[tuple[int, int, str]] = []
    dtype_widths = {"F32": 4}
    for name, (expected_dtype, expected_shape) in expected_specs.items():
        descriptor = manifest[name]
        if not isinstance(descriptor, dict) or set(descriptor) != {
            "dtype",
            "shape",
            "data_offsets",
        }:
            raise RuntimeError(f"adapter tensor descriptor mismatch: {name}")
        dtype = descriptor["dtype"]
        shape = descriptor["shape"]
        offsets = descriptor["data_offsets"]
        if dtype != expected_dtype or dtype not in dtype_widths:
            raise RuntimeError(f"adapter tensor dtype mismatch: {name}")
        if shape != list(expected_shape):
            raise RuntimeError(f"adapter tensor shape mismatch: {name}")
        if (
            not isinstance(offsets, list)
            or len(offsets) != 2
            or any(isinstance(value, bool) or not isinstance(value, int) for value in offsets)
            or offsets[0] < 0
            or offsets[1] <= offsets[0]
        ):
            raise RuntimeError(f"adapter tensor offsets invalid: {name}")
        elements = math.prod(expected_shape)
        if offsets[1] - offsets[0] != elements * dtype_widths[dtype]:
            raise RuntimeError(f"adapter tensor byte length mismatch: {name}")
        spans.append((offsets[0], offsets[1], name))

    cursor = 0
    for start, end, name in sorted(spans):
        if start != cursor:
            raise RuntimeError(f"adapter tensor offsets are not contiguous: {name}")
        cursor = end
    if file_size != 8 + header_length + cursor:
        raise RuntimeError("adapter safetensors file length mismatch")
    if production_contract:
        if len(expected_specs) != EXPECTED_LORA_TENSOR_COUNT:
            raise RuntimeError("internal LoRA tensor-count contract mismatch")
        if cursor != EXPECTED_LORA_DATA_BYTES:
            raise RuntimeError("internal LoRA data-size contract mismatch")
    return {
        "tensor_count": len(expected_specs),
        "data_bytes": cursor,
        "dtype": "F32",
    }


def validate_lora_only_artifacts(
    artifact_root: Path,
    evidence_root: Path,
    *,
    expected_base_model_id: str,
    expected_base_model_revision: str,
) -> dict[str, dict[str, Any]]:
    """Require an exact, bounded, safe-serialization LoRA model payload.

    Evidence and Trackio files live below ``evidence_root`` and are validated by
    the receipt/terminal inventory chain. Everything else in ``artifact_root``
    must be one of the three expected PEFT adapter files. This prevents Trainer
    state pickles, optimizer checkpoints, tokenizer copies, or full base-model
    weights from entering the private model repository.
    """

    try:
        evidence_relative = evidence_root.relative_to(artifact_root).as_posix()
    except ValueError as error:
        raise RuntimeError("evidence root must be contained by artifact root") from error

    observed: dict[str, dict[str, Any]] = {}
    total_upload_bytes = 0
    for path in sorted(artifact_root.rglob("*")):
        relative = path.relative_to(artifact_root).as_posix()
        if path.is_symlink():
            raise RuntimeError(f"symlink forbidden in output: {relative}")
        if not path.is_file():
            continue
        lower = relative.lower()
        if lower.endswith(FORBIDDEN_SERIALIZED_ARTIFACT_SUFFIXES):
            raise RuntimeError(f"unsafe serialized artifact forbidden: {relative}")
        if lower.endswith(".safetensors") and relative != "adapter_model.safetensors":
            raise RuntimeError(f"non-adapter safetensors forbidden: {relative}")
        size = path.stat().st_size
        total_upload_bytes += size
        if relative == evidence_relative or relative.startswith(f"{evidence_relative}/"):
            if size > MAX_EVIDENCE_FILE_BYTES:
                raise RuntimeError(
                    f"evidence artifact exceeds byte limit: {relative}: "
                    f"{size} > {MAX_EVIDENCE_FILE_BYTES}"
                )
            continue
        if relative not in EXPECTED_MODEL_ARTIFACT_FILES:
            raise RuntimeError(f"unexpected model artifact: {relative}")
        if size <= 0:
            raise RuntimeError(f"empty model artifact: {relative}")
        if size > MODEL_ARTIFACT_MAX_BYTES[relative]:
            raise RuntimeError(
                f"model artifact exceeds byte limit: {relative}: "
                f"{size} > {MODEL_ARTIFACT_MAX_BYTES[relative]}"
            )
        observed[relative] = {"bytes": size, "sha256": sha256_file(path)}

    if set(observed) != EXPECTED_MODEL_ARTIFACT_FILES:
        raise RuntimeError(
            "LoRA model artifact allowlist mismatch: "
            f"{sorted(observed)} != {sorted(EXPECTED_MODEL_ARTIFACT_FILES)}"
        )

    if total_upload_bytes > MAX_ARTIFACT_UPLOAD_BYTES:
        raise RuntimeError(
            "artifact upload exceeds total byte limit: "
            f"{total_upload_bytes} > {MAX_ARTIFACT_UPLOAD_BYTES}"
        )

    try:
        adapter_config = json.loads(
            (artifact_root / "adapter_config.json").read_text(encoding="utf-8")
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("adapter_config.json is not valid UTF-8 JSON") from error
    expected_target_modules = {
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    }
    if adapter_config.get("base_model_name_or_path") != expected_base_model_id:
        raise RuntimeError("adapter config base-model mismatch")
    if adapter_config.get("revision") != expected_base_model_revision:
        raise RuntimeError("adapter config base-model revision mismatch")
    if adapter_config.get("peft_type") != "LORA":
        raise RuntimeError("adapter config PEFT type mismatch")
    if adapter_config.get("task_type") != "CAUSAL_LM":
        raise RuntimeError("adapter config task type mismatch")
    if adapter_config.get("r") != 16 or adapter_config.get("lora_alpha") != 32:
        raise RuntimeError("adapter config LoRA rank/alpha mismatch")
    if adapter_config.get("bias") != "none":
        raise RuntimeError("adapter config bias mismatch")
    required_config_values = {
        "inference_mode": True,
        "init_lora_weights": True,
        "lora_dropout": 0.05,
        "fan_in_fan_out": False,
        "use_rslora": False,
        "use_dora": False,
        "use_qalora": False,
        "lora_bias": False,
    }
    for field, expected_value in required_config_values.items():
        if adapter_config.get(field) != expected_value:
            raise RuntimeError(f"adapter config field mismatch: {field}")
    for field in (
        "modules_to_save",
        "trainable_token_indices",
        "target_parameters",
        "layers_to_transform",
        "layer_replication",
        "exclude_modules",
    ):
        if adapter_config.get(field) is not None:
            raise RuntimeError(f"adapter config unsupported field is set: {field}")
    for field in ("rank_pattern", "alpha_pattern", "loftq_config"):
        if adapter_config.get(field) != {}:
            raise RuntimeError(f"adapter config pattern field is not empty: {field}")
    target_modules = adapter_config.get("target_modules")
    if not isinstance(target_modules, list) or set(target_modules) != expected_target_modules:
        raise RuntimeError("adapter config target-module mismatch")
    validate_lora_safetensors_manifest(artifact_root / "adapter_model.safetensors")
    return observed


def require_exact_hub_commit_sequence(
    api: Any,
    *,
    repo_id: str,
    revision: str,
    expected_newest_to_oldest: list[str],
    token: str,
) -> None:
    commits = api.list_repo_commits(
        repo_id=repo_id,
        repo_type="model",
        revision=revision,
        token=token,
    )
    if len(commits) != len(expected_newest_to_oldest):
        raise RuntimeError("target repository contains an unexpected commit count")
    observed: list[str] = []
    for commit in commits:
        try:
            commit_id = commit.commit_id
        except AttributeError as error:
            raise RuntimeError("Hub commit object is missing commit_id") from error
        if not isinstance(commit_id, str):
            raise RuntimeError("Hub commit object has an invalid commit_id")
        observed.append(commit_id)
    if observed != expected_newest_to_oldest:
        raise RuntimeError("target repository commit sequence mismatch")


def validate_evidence_commit_lineage(
    commits: list[Any], expected_newest_to_oldest: list[str]
) -> None:
    if len(commits) < len(expected_newest_to_oldest):
        raise RuntimeError("authorization evidence commit lineage is incomplete")
    observed: list[str] = []
    for commit in commits[: len(expected_newest_to_oldest)]:
        try:
            commit_id = commit.commit_id
        except AttributeError as error:
            raise RuntimeError("Hub evidence commit object is missing commit_id") from error
        if not isinstance(commit_id, str):
            raise RuntimeError("Hub evidence commit object has an invalid commit_id")
        observed.append(commit_id)
    if observed != expected_newest_to_oldest:
        raise RuntimeError("authorization evidence commit lineage mismatch")


def require_private_hub_head(
    api: Any,
    *,
    repo_id: str,
    expected_revision: str,
    token: str,
) -> None:
    for requested_revision in ("main", expected_revision):
        info = api.repo_info(
            repo_id=repo_id,
            repo_type="model",
            revision=requested_revision,
            token=token,
        )
        if info.private is not True:
            raise RuntimeError("target repository visibility changed from private")
        if info.sha != expected_revision:
            raise RuntimeError("target repository HEAD or immutable revision mismatch")


def verify_remote_hashes(
    *,
    repo_id: str,
    revision: str,
    expected_sha256: dict[str, str],
    token: str,
) -> None:
    from huggingface_hub import hf_hub_download

    for filename, expected_hash in sorted(expected_sha256.items()):
        remote_path = hf_hub_download(
            repo_id=repo_id,
            repo_type="model",
            filename=filename,
            revision=revision,
            token=token,
        )
        if sha256_file(Path(remote_path)) != expected_hash:
            raise RuntimeError(f"remote lineage hash mismatch: {filename}")


def verify_remote_sizes(
    *,
    repo_id: str,
    revision: str,
    expected_bytes: dict[str, int],
    token: str,
) -> None:
    from huggingface_hub import hf_hub_download

    for filename, expected_size in sorted(expected_bytes.items()):
        remote_path = hf_hub_download(
            repo_id=repo_id,
            repo_type="model",
            filename=filename,
            revision=revision,
            token=token,
        )
        if Path(remote_path).stat().st_size != expected_size:
            raise RuntimeError(f"remote lineage size mismatch: {filename}")


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
It requires base model and tokenizer `{model['id']}` at immutable revision
`{model['revision']}`.

It is not trained for political persuasion, targeting, live surveillance, private-person
research, or refusal removal. A completed training receipt is technical evidence only;
scientific and deployment GO remain separate held-out decisions.
"""


def parse_utc_timestamp(value: object, field: str) -> dt.datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise RuntimeError(f"authorization {field} must be UTC Z time")
    try:
        parsed = dt.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise RuntimeError(f"authorization {field} invalid") from error
    if parsed.tzinfo != dt.timezone.utc:
        raise RuntimeError(f"authorization {field} must be UTC")
    return parsed


def decode_authorization(encoded: str, expected_sha256: str) -> tuple[dict[str, Any], bytes]:
    if not encoded or any(character.isspace() for character in encoded):
        raise RuntimeError("authorization base64 is missing or non-canonical")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except Exception as error:
        raise RuntimeError("authorization base64 is invalid") from error
    if base64.b64encode(raw).decode("ascii") != encoded:
        raise RuntimeError("authorization base64 is non-canonical")
    if sha256_bytes(raw) != expected_sha256:
        raise RuntimeError("authorization hash mismatch")
    try:
        authorization = json.loads(
            raw,
            object_pairs_hook=strict_object,
            parse_constant=reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise RuntimeError("authorization JSON is invalid") from error
    if not isinstance(authorization, dict):
        raise RuntimeError("authorization must be an object")
    if raw != canonical_bytes(authorization) + b"\n":
        raise RuntimeError("authorization bytes are not canonical JSON plus newline")
    return authorization, raw


def validate_persisted_operation(
    raw: bytes,
    *,
    expected_sha256: str,
    run_id: str,
    expected_evidence_ref: str,
) -> dict[str, Any]:
    """Validate the exact operation bytes committed beside the authorization."""
    if sha256_bytes(raw) != expected_sha256:
        raise RuntimeError("persisted operation hash mismatch")
    try:
        operation = json.loads(
            raw,
            object_pairs_hook=strict_object,
            parse_constant=reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise RuntimeError("persisted operation JSON is invalid") from error
    if not isinstance(operation, dict):
        raise RuntimeError("persisted operation must be an object")
    if raw != canonical_bytes(operation) + b"\n":
        raise RuntimeError("persisted operation bytes are not canonical JSON plus newline")
    if operation.get("schema") != "era-part1b-hf-operation/v11":
        raise RuntimeError("persisted operation schema mismatch")
    if operation.get("operation_id") != run_id:
        raise RuntimeError("persisted operation run mismatch")
    if operation.get("evidence_ref") != expected_evidence_ref:
        raise RuntimeError("persisted operation evidence PR ref mismatch")
    if operation.get("status") != "GO_FOR_AUTHORIZATION_ISSUER_ONLY":
        raise RuntimeError("persisted operation authorization gate mismatch")
    return operation


def validate_persisted_identity(
    raw: bytes,
    *,
    expected_sha256: str,
    run_id: str,
    expected_intent: dict[str, str],
    expected_write_canary: dict[str, Any],
    expected_evidence_ref: str,
    expected_producer_job_id: str,
    expected_target_repositories: list[dict[str, str]],
) -> dict[str, Any]:
    """Validate the signed-hash-bound producer identity and its intent binding."""
    if sha256_bytes(raw) != expected_sha256:
        raise RuntimeError("authorization control identity hash mismatch")
    identity = parse_canonical_evidence_object(raw, "persisted Hub identity")
    if set(identity) != {
        "schema",
        "status",
        "account",
        "run_id",
        "nonce",
        "producer_job_id",
        "producer_script_sha256",
        "evidence_repo",
        "write_canary",
        "target_repositories",
        "producer_intent",
        "model_repositories",
        "created_at",
    }:
        raise RuntimeError("persisted Hub identity field mismatch")
    for field, expected in {
        "schema": "era-part1b-hub-identity/v11",
        "status": "FRESH_HUB_NAMESPACE_CREATED",
        "account": EXPECTED_OWNER,
        "run_id": run_id,
        "producer_job_id": expected_producer_job_id,
        "write_canary": expected_write_canary,
        "target_repositories": expected_target_repositories,
        "producer_intent": expected_intent,
    }.items():
        if identity.get(field) != expected:
            raise RuntimeError(f"persisted Hub identity {field} mismatch")
    if re.fullmatch(r"[0-9a-f]{32}", str(identity.get("nonce"))) is None:
        raise RuntimeError("persisted Hub identity nonce invalid")
    if SHA256_RE.fullmatch(str(identity.get("producer_script_sha256"))) is None:
        raise RuntimeError("persisted Hub identity producer script hash invalid")
    if identity.get("evidence_repo") != {
        "repo_id": EXPECTED_EVIDENCE_REPO,
        "repo_type": "dataset",
        "evidence_ref": expected_evidence_ref,
        "expected_parent_revision": expected_write_canary["revision"],
        "producer_intent_path": expected_intent["path"],
        "producer_intent_revision": expected_intent["revision"],
        "producer_intent_sha256": expected_intent["sha256"],
    }:
        raise RuntimeError("persisted Hub identity evidence binding mismatch")
    model_repositories = identity.get("model_repositories")
    if not isinstance(model_repositories, list) or len(model_repositories) != 2:
        raise RuntimeError("persisted Hub identity model repositories mismatch")
    observed_targets = [
        {
            "adapter": item.get("adapter"),
            "repo_id": item.get("repo_id"),
            "repo_type": item.get("repo_type"),
        }
        for item in model_repositories
        if isinstance(item, dict)
    ]
    if observed_targets != expected_target_repositories:
        raise RuntimeError("persisted Hub identity bootstrap targets mismatch")
    if not isinstance(identity.get("created_at"), str):
        raise RuntimeError("persisted Hub identity creation time invalid")
    return identity


def validate_persisted_producer_intent(
    raw: bytes,
    *,
    expected_sha256: str,
    run_id: str,
    identity: dict[str, Any],
    expected_write_canary: dict[str, Any],
    expected_evidence_ref: str,
    expected_target_repositories: list[dict[str, str]],
) -> dict[str, Any]:
    """Validate the immutable producer intent before any target-side write."""
    if sha256_bytes(raw) != expected_sha256:
        raise RuntimeError("persisted producer intent hash mismatch")
    intent = parse_canonical_evidence_object(raw, "persisted producer intent")
    if set(intent) != {
        "schema",
        "status",
        "account",
        "run_id",
        "nonce",
        "producer_job_id",
        "producer_script_sha256",
        "evidence_parent_revision",
        "evidence_ref",
        "write_canary",
        "target_repositories",
        "random_canary",
        "created_at",
    }:
        raise RuntimeError("persisted producer intent field mismatch")
    for field, expected in {
        "schema": "era-part1b-hub-producer-intent/v11",
        "status": "PRODUCER_INTENT_PERSISTED",
        "account": EXPECTED_OWNER,
        "run_id": run_id,
        "nonce": identity["nonce"],
        "producer_job_id": identity["producer_job_id"],
        "producer_script_sha256": identity["producer_script_sha256"],
        "evidence_parent_revision": expected_write_canary["revision"],
        "evidence_ref": expected_evidence_ref,
        "write_canary": expected_write_canary,
        "target_repositories": expected_target_repositories,
        "created_at": identity["created_at"],
    }.items():
        if intent.get(field) != expected:
            raise RuntimeError(f"persisted producer intent {field} mismatch")
    if re.fullmatch(r"[0-9a-f]{64}", str(intent.get("random_canary"))) is None:
        raise RuntimeError("persisted producer intent random canary invalid")
    return intent


def verify_ed25519_authorization(authorization: dict[str, Any]) -> str:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.hazmat.primitives.serialization import load_der_public_key

    signature = authorization.get("signature")
    expected_signature_fields = {
        "algorithm",
        "key_id",
        "public_key_spki_der_b64",
        "public_key_spki_der_sha256",
        "signature_b64",
        "signed_payload_sha256",
    }
    if not isinstance(signature, dict) or set(signature) != expected_signature_fields:
        raise RuntimeError("authorization signature field mismatch")
    if signature.get("algorithm") != "Ed25519":
        raise RuntimeError("authorization signature algorithm mismatch")
    if signature.get("key_id") != AUTHORIZATION_KEY_ID:
        raise RuntimeError("authorization signature key id mismatch")
    if signature.get("public_key_spki_der_b64") != AUTHORIZATION_PUBLIC_KEY_SPKI_DER_B64:
        raise RuntimeError("authorization public key mismatch")
    if (
        signature.get("public_key_spki_der_sha256")
        != AUTHORIZATION_PUBLIC_KEY_SPKI_DER_SHA256
    ):
        raise RuntimeError("authorization public key hash mismatch")
    public_der = base64.b64decode(AUTHORIZATION_PUBLIC_KEY_SPKI_DER_B64, validate=True)
    if sha256_bytes(public_der) != AUTHORIZATION_PUBLIC_KEY_SPKI_DER_SHA256:
        raise RuntimeError("pinned authorization public key is internally inconsistent")
    unsigned = dict(authorization)
    unsigned.pop("signature", None)
    signed_payload = canonical_bytes(unsigned) + b"\n"
    signed_payload_sha256 = sha256_bytes(signed_payload)
    if signature.get("signed_payload_sha256") != signed_payload_sha256:
        raise RuntimeError("authorization signed-payload hash mismatch")
    try:
        signature_bytes = base64.b64decode(str(signature.get("signature_b64")), validate=True)
    except Exception as error:
        raise RuntimeError("authorization signature base64 invalid") from error
    if len(signature_bytes) != 64:
        raise RuntimeError("authorization signature length invalid")
    public_key = load_der_public_key(public_der)
    if not isinstance(public_key, Ed25519PublicKey):
        raise RuntimeError("pinned authorization key is not Ed25519")
    try:
        public_key.verify(signature_bytes, signed_payload)
    except InvalidSignature as error:
        raise RuntimeError("authorization Ed25519 signature invalid") from error
    return signed_payload_sha256


def validate_training_authorization(
    authorization: dict[str, Any],
    *,
    authorization_sha256: str,
    expected_authorization_sha256: str,
    operation_sha256: str,
    script_sha256: str,
    adapter: str,
    phase: str,
    seed: int,
    run_id: str,
    hub_repo_id: str,
    current_job_id: str,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    expected_fields = {
        "schema",
        "status",
        "operation_id",
        "operation_sha256",
        "run_id",
        "control_repo",
        "write_canary",
        "producer",
        "verifier",
        "ml_stack",
        "issuer",
        "public_artifacts",
        "runtime_versions",
        "slots",
        "issued_at",
        "expires_at",
        "signature",
    }
    if set(authorization) != expected_fields:
        raise RuntimeError("authorization field mismatch")
    if authorization_sha256 != expected_authorization_sha256:
        raise RuntimeError("authorization hash mismatch")
    if authorization.get("schema") != "era-part1b-training-authorization/v11":
        raise RuntimeError("authorization schema mismatch")
    if authorization.get("status") != "AUTHORIZED_FOR_TWO_PRIVATE_HUB_JOBS":
        raise RuntimeError("authorization status mismatch")
    if authorization.get("operation_id") != run_id or authorization.get("run_id") != run_id:
        raise RuntimeError("authorization run mismatch")
    if authorization.get("operation_sha256") != operation_sha256:
        raise RuntimeError("authorization operation hash mismatch")
    signed_payload_sha256 = verify_ed25519_authorization(authorization)

    issued_at = parse_utc_timestamp(authorization.get("issued_at"), "issued_at")
    expires_at = parse_utc_timestamp(authorization.get("expires_at"), "expires_at")
    current = now or dt.datetime.now(dt.timezone.utc)
    if expires_at <= issued_at or expires_at - issued_at > dt.timedelta(hours=24):
        raise RuntimeError("authorization validity window invalid")
    if issued_at > current + dt.timedelta(minutes=5) or current >= expires_at:
        raise RuntimeError("authorization is not currently valid")

    control_repo = authorization.get("control_repo")
    if not isinstance(control_repo, dict) or set(control_repo) != {
        "repo_id",
        "repo_type",
        "evidence_ref",
        "identity_path",
        "identity_revision",
        "identity_sha256",
        "producer_intent_path",
        "producer_intent_revision",
        "producer_intent_sha256",
        "operation_path",
        "authorization_path",
    }:
        raise RuntimeError("authorization control repo evidence mismatch")
    if control_repo.get("repo_id") != EXPECTED_EVIDENCE_REPO:
        raise RuntimeError("authorization evidence repo mismatch")
    if control_repo.get("repo_type") != "dataset":
        raise RuntimeError("authorization evidence repo type mismatch")
    evidence_ref = control_repo.get("evidence_ref")
    if not isinstance(evidence_ref, str) or EVIDENCE_REF_RE.fullmatch(evidence_ref) is None:
        raise RuntimeError("authorization evidence PR ref invalid")
    expected_identity_path = f"runs/{run_id}/control/identity.json"
    if control_repo.get("identity_path") != expected_identity_path:
        raise RuntimeError("authorization evidence identity path mismatch")
    if REVISION_RE.fullmatch(str(control_repo.get("identity_revision"))) is None:
        raise RuntimeError("authorization evidence identity revision invalid")
    if SHA256_RE.fullmatch(str(control_repo.get("identity_sha256"))) is None:
        raise RuntimeError("authorization evidence identity hash invalid")
    expected_intent_path = f"runs/{run_id}/control/producer-intent.json"
    if control_repo.get("producer_intent_path") != expected_intent_path:
        raise RuntimeError("authorization producer intent path mismatch")
    if REVISION_RE.fullmatch(str(control_repo.get("producer_intent_revision"))) is None:
        raise RuntimeError("authorization producer intent revision invalid")
    if SHA256_RE.fullmatch(str(control_repo.get("producer_intent_sha256"))) is None:
        raise RuntimeError("authorization producer intent hash invalid")
    expected_operation_path = f"runs/{run_id}/control/operation.json"
    if control_repo.get("operation_path") != expected_operation_path:
        raise RuntimeError("authorization operation path mismatch")
    expected_path = f"runs/{run_id}/control/authorizations/authorization.json"
    if control_repo.get("authorization_path") != expected_path:
        raise RuntimeError("authorization evidence path mismatch")

    producer = authorization.get("producer")
    write_canary = authorization.get("write_canary")
    verifier = authorization.get("verifier")
    ml_stack = authorization.get("ml_stack")
    issuer = authorization.get("issuer")
    public = authorization.get("public_artifacts")
    if not isinstance(write_canary, dict) or set(write_canary) != {
        "job_id",
        "path",
        "sha256",
        "revision",
        "prior_run_quarantine",
    }:
        raise RuntimeError("authorization write-canary evidence mismatch")
    canary_job_id = write_canary.get("job_id")
    if not isinstance(canary_job_id, str) or JOB_ID_RE.fullmatch(canary_job_id) is None:
        raise RuntimeError("authorization write-canary JOB_ID invalid")
    canary_path = write_canary.get("path")
    if canary_path != f"runs/{run_id}/auth/write-canary.json":
        raise RuntimeError("authorization write-canary path invalid")
    if SHA256_RE.fullmatch(str(write_canary.get("sha256"))) is None:
        raise RuntimeError("authorization write-canary hash invalid")
    if REVISION_RE.fullmatch(str(write_canary.get("revision"))) is None:
        raise RuntimeError("authorization write-canary revision invalid")
    if write_canary.get("prior_run_quarantine") != {
        "path": PRIOR_RUN_QUARANTINE_PATH,
        "sha256": PRIOR_RUN_QUARANTINE_SHA256,
        "size_bytes": PRIOR_RUN_QUARANTINE_SIZE_BYTES,
    }:
        raise RuntimeError(
            "authorization write-canary prior-run quarantine binding mismatch"
        )
    if not isinstance(producer, dict) or set(producer) != {
        "job_id",
        "receipt_sha256",
        "terminal_sha256",
        "evidence_revision",
        "intent_revision",
        "intent_sha256",
    }:
        raise RuntimeError("authorization producer evidence mismatch")
    if not isinstance(verifier, dict) or set(verifier) != {"job_id", "terminal_sha256"}:
        raise RuntimeError("authorization verifier evidence mismatch")
    if not isinstance(ml_stack, dict) or set(ml_stack) != {"job_id", "terminal_sha256"}:
        raise RuntimeError("authorization ML-stack evidence mismatch")
    if not isinstance(issuer, dict) or set(issuer) != {"job_id"}:
        raise RuntimeError("authorization issuer evidence mismatch")
    if not isinstance(public, dict) or set(public) != {
        "train_lora_hub_sha256",
        "protocol_sha256",
        "requirements_lock_sha256",
        "runtime_reuse_sha256",
        "runtime_image",
    }:
        raise RuntimeError("authorization public artifact mismatch")
    producer_job_id = producer.get("job_id")
    verifier_job_id = verifier.get("job_id")
    stack_job_id = ml_stack.get("job_id")
    issuer_job_id = issuer.get("job_id")
    job_ids = (
        canary_job_id,
        producer_job_id,
        verifier_job_id,
        stack_job_id,
        issuer_job_id,
    )
    if any(not isinstance(value, str) or JOB_ID_RE.fullmatch(value) is None for value in job_ids):
        raise RuntimeError("authorization control JOB_ID invalid")
    if len({*job_ids, current_job_id}) != 6:
        raise RuntimeError("all control-plane and training provider Jobs must be distinct")
    for value, label in (
        (producer.get("receipt_sha256"), "producer receipt"),
        (producer.get("terminal_sha256"), "producer terminal"),
        (verifier.get("terminal_sha256"), "verifier terminal"),
        (ml_stack.get("terminal_sha256"), "ML-stack terminal"),
    ):
        if SHA256_RE.fullmatch(str(value)) is None:
            raise RuntimeError(f"authorization {label} hash invalid")
    if REVISION_RE.fullmatch(str(producer.get("evidence_revision"))) is None:
        raise RuntimeError("authorization producer evidence revision invalid")
    if control_repo.get("identity_revision") != producer.get("evidence_revision"):
        raise RuntimeError("authorization evidence identity revision mismatch")
    if REVISION_RE.fullmatch(str(producer.get("intent_revision"))) is None:
        raise RuntimeError("authorization producer intent revision invalid")
    if SHA256_RE.fullmatch(str(producer.get("intent_sha256"))) is None:
        raise RuntimeError("authorization producer intent hash invalid")
    if (
        control_repo.get("producer_intent_revision") != producer.get("intent_revision")
        or control_repo.get("producer_intent_sha256") != producer.get("intent_sha256")
    ):
        raise RuntimeError("authorization producer intent duplicate binding mismatch")
    if public.get("train_lora_hub_sha256") != script_sha256:
        raise RuntimeError("authorization training script hash mismatch")
    if public.get("protocol_sha256") != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError("authorization protocol hash mismatch")
    if public.get("requirements_lock_sha256") != EXPECTED_REQUIREMENTS_LOCK_SHA256:
        raise RuntimeError("authorization requirements-lock hash mismatch")
    if public.get("runtime_reuse_sha256") != EXPECTED_RUNTIME_REUSE_SHA256:
        raise RuntimeError("authorization runtime-reuse manifest hash mismatch")
    if public.get("runtime_image") != EXPECTED_RUNTIME_IMAGE:
        raise RuntimeError("authorization immutable runtime image mismatch")
    if authorization.get("runtime_versions") != EXPECTED_RUNTIME_VERSIONS:
        raise RuntimeError("authorization runtime-version map mismatch")

    slots = authorization.get("slots")
    if not isinstance(slots, list) or len(slots) != 2:
        raise RuntimeError("authorization must contain exactly two slots")
    matching: list[dict[str, Any]] = []
    seen_slot_ids: set[str] = set()
    seen_adapters: set[str] = set()
    seen_repos: set[str] = set()
    target_repositories: list[dict[str, str]] = []
    for slot in slots:
        if not isinstance(slot, dict) or set(slot) != {
            "slot_id",
            "status",
            "adapter",
            "phase",
            "seed",
            "run_id",
            "target_repo_id",
            "provider_root_revision",
            "provider_root_files",
            "provider_root_file_size",
            "provider_root_file_sha256",
            "expected_parent_revision",
            "expected_files",
            "expected_file_sha256",
            "model",
            "max_steps",
        }:
            raise RuntimeError("authorization slot field mismatch")
        slot_id = slot.get("slot_id")
        slot_adapter = slot.get("adapter")
        target_repo_id = slot.get("target_repo_id")
        if not isinstance(slot_id, str) or RUN_ID_RE.fullmatch(slot_id) is None:
            raise RuntimeError("authorization slot id invalid")
        if slot_id in seen_slot_ids or slot_adapter in seen_adapters:
            raise RuntimeError("duplicate authorization slot")
        if not isinstance(target_repo_id, str) or REPO_ID_RE.fullmatch(target_repo_id) is None:
            raise RuntimeError("authorization target repository invalid")
        if target_repo_id in seen_repos:
            raise RuntimeError("authorization target repositories must be distinct")
        if slot_adapter not in ADAPTERS or slot.get("status") != "AUTHORIZED":
            raise RuntimeError("invalid authorization slot")
        if slot.get("run_id") != run_id or slot.get("phase") != "production":
            raise RuntimeError("authorization slot run or phase mismatch")
        if slot.get("seed") not in ALLOWED_SEEDS:
            raise RuntimeError("authorization slot seed invalid")
        provider_root_revision = slot.get("provider_root_revision")
        if REVISION_RE.fullmatch(str(provider_root_revision)) is None:
            raise RuntimeError("authorization provider-root revision invalid")
        if REVISION_RE.fullmatch(str(slot.get("expected_parent_revision"))) is None:
            raise RuntimeError("authorization target parent revision invalid")
        if provider_root_revision == slot.get("expected_parent_revision"):
            raise RuntimeError("provider root and controlled identity revisions must differ")
        if slot.get("provider_root_files") != PROVIDER_ROOT_FILES:
            raise RuntimeError("authorization provider-root inventory mismatch")
        provider_root_file_sha256 = slot.get("provider_root_file_sha256")
        if (
            not isinstance(provider_root_file_sha256, dict)
            or sorted(provider_root_file_sha256) != PROVIDER_ROOT_FILES
            or any(
                SHA256_RE.fullmatch(str(value)) is None
                for value in provider_root_file_sha256.values()
            )
        ):
            raise RuntimeError("authorization provider-root hashes mismatch")
        provider_root_file_size = slot.get("provider_root_file_size")
        if (
            not isinstance(provider_root_file_size, dict)
            or sorted(provider_root_file_size) != PROVIDER_ROOT_FILES
            or any(
                not isinstance(value, int)
                or isinstance(value, bool)
                or value <= 0
                or value > MAX_PROVIDER_ROOT_FILE_BYTES
                for value in provider_root_file_size.values()
            )
        ):
            raise RuntimeError("authorization provider-root sizes mismatch")
        if slot.get("expected_files") != CONTROLLED_IDENTITY_FILES:
            raise RuntimeError("authorization target bootstrap inventory mismatch")
        expected_file_sha256 = slot.get("expected_file_sha256")
        if (
            not isinstance(expected_file_sha256, dict)
            or sorted(expected_file_sha256) != slot["expected_files"]
            or any(
                SHA256_RE.fullmatch(str(value)) is None
                for value in expected_file_sha256.values()
            )
        ):
            raise RuntimeError("authorization target bootstrap hashes mismatch")
        if (
            expected_file_sha256[".gitattributes"]
            != provider_root_file_sha256[".gitattributes"]
        ):
            raise RuntimeError("controlled identity changed provider-root bytes")
        if slot.get("model") != {
            "id": MODELS["production"]["id"],
            "revision": MODELS["production"]["revision"],
        }:
            raise RuntimeError("authorization slot model mismatch")
        if slot.get("max_steps") != MODELS["production"]["max_steps"]:
            raise RuntimeError("authorization slot max-steps mismatch")
        seen_slot_ids.add(slot_id)
        seen_adapters.add(str(slot_adapter))
        seen_repos.add(target_repo_id)
        target_repositories.append(
            {"adapter": str(slot_adapter), "repo_id": target_repo_id, "repo_type": "model"}
        )
        if (
            slot_adapter == adapter
            and slot.get("phase") == phase
            and slot.get("seed") == seed
            and slot.get("run_id") == run_id
            and target_repo_id == hub_repo_id
        ):
            matching.append(slot)
    if seen_adapters != ADAPTERS or len(matching) != 1:
        raise RuntimeError("requested training tuple is not uniquely authorized")
    selected = matching[0]
    return {
        "slot_id": str(selected["slot_id"]),
        "target_repo_id": str(selected["target_repo_id"]),
        "provider_root_revision": str(selected["provider_root_revision"]),
        "provider_root_files": list(selected["provider_root_files"]),
        "provider_root_file_size": dict(selected["provider_root_file_size"]),
        "provider_root_file_sha256": dict(selected["provider_root_file_sha256"]),
        "expected_parent_revision": str(selected["expected_parent_revision"]),
        "expected_files": list(selected["expected_files"]),
        "expected_file_sha256": dict(selected["expected_file_sha256"]),
        "signed_payload_sha256": signed_payload_sha256,
        "authorization_path": str(control_repo["authorization_path"]),
        "evidence_ref": evidence_ref,
        "operation_path": str(control_repo["operation_path"]),
        "identity_path": str(control_repo["identity_path"]),
        "identity_revision": str(control_repo["identity_revision"]),
        "identity_sha256": str(control_repo["identity_sha256"]),
        "producer_intent_path": str(control_repo["producer_intent_path"]),
        "producer_intent_revision": str(control_repo["producer_intent_revision"]),
        "producer_intent_sha256": str(control_repo["producer_intent_sha256"]),
        "write_canary_path": str(canary_path),
        "write_canary_sha256": str(write_canary["sha256"]),
        "write_canary_revision": str(write_canary["revision"]),
        "write_canary": dict(write_canary),
        "target_repositories": target_repositories,
        "producer_job_id": str(producer_job_id),
        "write_canary_job_id": str(canary_job_id),
        "verifier_job_id": str(verifier_job_id),
        "ml_stack_job_id": str(stack_job_id),
        "issuer_job_id": str(issuer_job_id),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", required=True, choices=sorted(ADAPTERS))
    parser.add_argument("--phase", required=True, choices=sorted(MODELS))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--seed", required=True, type=int, choices=sorted(ALLOWED_SEEDS))
    parser.add_argument("--hub-repo-id")
    parser.add_argument("--authorization-b64")
    parser.add_argument("--authorization-sha256")
    parser.add_argument("--authorization-revision")
    parser.add_argument("--operation-sha256")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if RUN_ID_RE.fullmatch(args.run_id) is None:
        parser.error("run-id must match [a-z0-9][a-z0-9-]{7,79}")
    if not args.validate_only:
        required_hashes = {
            "authorization-sha256": args.authorization_sha256,
            "operation-sha256": args.operation_sha256,
        }
        invalid = [
            name
            for name, value in required_hashes.items()
            if value is None or SHA256_RE.fullmatch(value) is None
        ]
        if invalid:
            parser.error(f"remote execution requires valid {', '.join(invalid)}")
        if not args.authorization_b64:
            parser.error("remote execution requires authorization-b64")
        if REVISION_RE.fullmatch(args.authorization_revision or "") is None:
            parser.error("remote execution requires a valid authorization-revision")
        if REPO_ID_RE.fullmatch(args.hub_repo_id or "") is None:
            parser.error("remote execution requires an apol private hub-repo-id")
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
    job_id = provider_job_id()
    token = os.environ.get("HF_TOKEN")
    if not isinstance(token, str) or len(token) < 20 or token != token.strip():
        raise RuntimeError("HF_TOKEN secret is missing or invalid")
    authorization, authorization_bytes = decode_authorization(
        args.authorization_b64, args.authorization_sha256
    )
    authorization_evidence = validate_training_authorization(
        authorization,
        authorization_sha256=sha256_bytes(authorization_bytes),
        expected_authorization_sha256=args.authorization_sha256,
        operation_sha256=args.operation_sha256,
        script_sha256=script_sha256,
        adapter=args.adapter,
        phase=args.phase,
        seed=args.seed,
        run_id=args.run_id,
        hub_repo_id=args.hub_repo_id,
        current_job_id=job_id,
    )
    runtime_versions = package_versions(tuple(EXPECTED_RUNTIME_VERSIONS))
    if runtime_versions != EXPECTED_RUNTIME_VERSIONS:
        raise RuntimeError(
            f"runtime-version mismatch: {runtime_versions}"
        )

    from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download

    api = HfApi(token=token)
    identity = api.whoami(token=token)
    if not isinstance(identity, dict) or identity.get("name") != EXPECTED_OWNER:
        raise RuntimeError("HF_TOKEN owner mismatch")
    control_info = api.repo_info(
        repo_id=EXPECTED_EVIDENCE_REPO,
        repo_type="dataset",
        revision=args.authorization_revision,
        token=token,
    )
    if control_info.private is not True or control_info.sha != args.authorization_revision:
        raise RuntimeError("authorization revision is not an exact private evidence commit")
    persisted_authorization_path = hf_hub_download(
        repo_id=EXPECTED_EVIDENCE_REPO,
        repo_type="dataset",
        filename=authorization_evidence["authorization_path"],
        revision=args.authorization_revision,
        token=token,
    )
    if Path(persisted_authorization_path).read_bytes() != authorization_bytes:
        raise RuntimeError("persisted authorization differs from signed inline authorization")
    persisted_operation_path = hf_hub_download(
        repo_id=EXPECTED_EVIDENCE_REPO,
        repo_type="dataset",
        filename=authorization_evidence["operation_path"],
        revision=args.authorization_revision,
        token=token,
    )
    validate_persisted_operation(
        Path(persisted_operation_path).read_bytes(),
        expected_sha256=args.operation_sha256,
        run_id=args.run_id,
        expected_evidence_ref=authorization_evidence["evidence_ref"],
    )
    control_head = api.repo_info(
        repo_id=EXPECTED_EVIDENCE_REPO,
        repo_type="dataset",
        revision=authorization_evidence["evidence_ref"],
        token=token,
    )
    if control_head.private is not True or control_head.sha != args.authorization_revision:
        raise RuntimeError(
            "private evidence PR ref differs from authorization revision"
        )
    identity_revision = authorization_evidence["identity_revision"]
    canary_revision = authorization_evidence["write_canary_revision"]
    signed_intent_binding = {
        "path": authorization_evidence["producer_intent_path"],
        "revision": authorization_evidence["producer_intent_revision"],
        "sha256": authorization_evidence["producer_intent_sha256"],
    }
    for revision in (identity_revision, signed_intent_binding["revision"], canary_revision):
        info = api.repo_info(
            repo_id=EXPECTED_EVIDENCE_REPO,
            repo_type="dataset",
            revision=revision,
            token=token,
        )
        if info.private is not True or info.sha != revision:
            raise RuntimeError("authorization evidence revision is not exact and private")

    persisted_identity_path = hf_hub_download(
        repo_id=EXPECTED_EVIDENCE_REPO,
        repo_type="dataset",
        filename=authorization_evidence["identity_path"],
        revision=identity_revision,
        token=token,
    )
    identity_bytes = Path(persisted_identity_path).read_bytes()
    identity = validate_persisted_identity(
        identity_bytes,
        expected_sha256=authorization_evidence["identity_sha256"],
        run_id=args.run_id,
        expected_intent=signed_intent_binding,
        expected_write_canary=authorization_evidence["write_canary"],
        expected_evidence_ref=authorization_evidence["evidence_ref"],
        expected_producer_job_id=authorization_evidence["producer_job_id"],
        expected_target_repositories=authorization_evidence["target_repositories"],
    )
    identity_intent_binding = identity["producer_intent"]
    intent_revision = identity_intent_binding["revision"]
    evidence_commits = api.list_repo_commits(
        repo_id=EXPECTED_EVIDENCE_REPO,
        repo_type="dataset",
        revision=args.authorization_revision,
        token=token,
    )
    validate_evidence_commit_lineage(
        evidence_commits,
        [args.authorization_revision, identity_revision, intent_revision, canary_revision],
    )
    canary_files = set(
        api.list_repo_files(
            repo_id=EXPECTED_EVIDENCE_REPO,
            repo_type="dataset",
            revision=canary_revision,
            token=token,
        )
    )
    intent_files = set(
        api.list_repo_files(
            repo_id=EXPECTED_EVIDENCE_REPO,
            repo_type="dataset",
            revision=intent_revision,
            token=token,
        )
    )
    identity_files = set(
        api.list_repo_files(
            repo_id=EXPECTED_EVIDENCE_REPO,
            repo_type="dataset",
            revision=identity_revision,
            token=token,
        )
    )
    intent_path = identity_intent_binding["path"]
    producer_receipt_path = f"runs/{args.run_id}/control/producer.json"
    if intent_path in canary_files or intent_files != canary_files | {intent_path}:
        raise RuntimeError("producer intent evidence commit file tree mismatch")
    if (
        authorization_evidence["identity_path"] in intent_files
        or producer_receipt_path in intent_files
        or identity_files
        != intent_files
        | {authorization_evidence["identity_path"], producer_receipt_path}
    ):
        raise RuntimeError("producer identity evidence commit file tree mismatch")
    authorization_files = set(
        api.list_repo_files(
            repo_id=EXPECTED_EVIDENCE_REPO,
            repo_type="dataset",
            revision=args.authorization_revision,
            token=token,
        )
    )
    expected_authorization_files = identity_files | {
        authorization_evidence["authorization_path"],
        authorization_evidence["operation_path"],
    }
    if (
        authorization_evidence["authorization_path"] in identity_files
        or authorization_evidence["operation_path"] in identity_files
        or authorization_files != expected_authorization_files
    ):
        raise RuntimeError("authorization evidence commit file tree mismatch")

    persisted_intent_path = hf_hub_download(
        repo_id=EXPECTED_EVIDENCE_REPO,
        repo_type="dataset",
        filename=intent_path,
        revision=intent_revision,
        token=token,
    )
    validate_persisted_producer_intent(
        Path(persisted_intent_path).read_bytes(),
        expected_sha256=identity_intent_binding["sha256"],
        run_id=args.run_id,
        identity=identity,
        expected_write_canary=authorization_evidence["write_canary"],
        expected_evidence_ref=authorization_evidence["evidence_ref"],
        expected_target_repositories=authorization_evidence["target_repositories"],
    )
    persisted_write_canary = hf_hub_download(
        repo_id=EXPECTED_EVIDENCE_REPO,
        repo_type="dataset",
        filename=authorization_evidence["write_canary_path"],
        revision=canary_revision,
        token=token,
    )
    if (
        sha256_file(Path(persisted_write_canary))
        != authorization_evidence["write_canary_sha256"]
    ):
        raise RuntimeError("authorization write-canary hash mismatch")
    quarantine_binding = authorization_evidence["write_canary"][
        "prior_run_quarantine"
    ]
    if (
        quarantine_binding["path"] not in canary_files
        or quarantine_binding["path"] not in identity_files
    ):
        raise RuntimeError(
            "prior-run quarantine is not preserved in canary and identity revisions"
        )
    quarantine_bytes: list[bytes] = []
    for revision in (canary_revision, identity_revision):
        persisted_quarantine_path = hf_hub_download(
            repo_id=EXPECTED_EVIDENCE_REPO,
            repo_type="dataset",
            filename=quarantine_binding["path"],
            revision=revision,
            token=token,
        )
        raw_quarantine = Path(persisted_quarantine_path).read_bytes()
        if len(raw_quarantine) != quarantine_binding["size_bytes"]:
            raise RuntimeError("prior-run quarantine persisted size mismatch")
        if sha256_bytes(raw_quarantine) != quarantine_binding["sha256"]:
            raise RuntimeError("prior-run quarantine persisted hash mismatch")
        quarantine_bytes.append(raw_quarantine)
    if quarantine_bytes[0] != quarantine_bytes[1]:
        raise RuntimeError("prior-run quarantine bytes changed before producer identity")

    provider_root_revision = authorization_evidence["provider_root_revision"]
    provider_root_info = api.repo_info(
        repo_id=args.hub_repo_id,
        repo_type="model",
        revision=provider_root_revision,
        token=token,
    )
    if (
        provider_root_info.private is not True
        or provider_root_info.sha != provider_root_revision
    ):
        raise RuntimeError("target provider root is not an exact private revision")
    provider_root_files = sorted(
        api.list_repo_files(
            repo_id=args.hub_repo_id,
            repo_type="model",
            revision=provider_root_revision,
            token=token,
        )
    )
    if provider_root_files != authorization_evidence["provider_root_files"]:
        raise RuntimeError("target provider-root file tree mismatch")
    verify_remote_hashes(
        repo_id=args.hub_repo_id,
        revision=provider_root_revision,
        expected_sha256=authorization_evidence["provider_root_file_sha256"],
        token=token,
    )
    verify_remote_sizes(
        repo_id=args.hub_repo_id,
        revision=provider_root_revision,
        expected_bytes=authorization_evidence["provider_root_file_size"],
        token=token,
    )

    expected_parent_revision = authorization_evidence["expected_parent_revision"]
    initial_info = api.repo_info(
        repo_id=args.hub_repo_id,
        repo_type="model",
        revision=expected_parent_revision,
        token=token,
    )
    if initial_info.private is not True or initial_info.sha != expected_parent_revision:
        raise RuntimeError("target must be a pre-existing private model repo at exact parent")
    initial_files = sorted(
        api.list_repo_files(
            repo_id=args.hub_repo_id,
            repo_type="model",
            revision=expected_parent_revision,
            token=token,
        )
    )
    if initial_files != authorization_evidence["expected_files"]:
        raise RuntimeError("target repository is not in the authorized bootstrap state")
    require_exact_hub_commit_sequence(
        api,
        repo_id=args.hub_repo_id,
        revision=expected_parent_revision,
        expected_newest_to_oldest=[
            expected_parent_revision,
            provider_root_revision,
        ],
        token=token,
    )
    verify_remote_hashes(
        repo_id=args.hub_repo_id,
        revision=expected_parent_revision,
        expected_sha256=authorization_evidence["expected_file_sha256"],
        token=token,
    )
    require_private_hub_head(
        api,
        repo_id=args.hub_repo_id,
        expected_revision=expected_parent_revision,
        token=token,
    )

    reservation_path = f"reservations/{authorization_evidence['slot_id']}.json"
    reservation = {
        "schema": "era-part1b-training-slot-reservation/v11",
        "status": "RESERVED_NO_RETRY",
        "run_id": args.run_id,
        "adapter": args.adapter,
        "phase": args.phase,
        "seed": args.seed,
        "slot_id": authorization_evidence["slot_id"],
        "job_id": job_id,
        "authorization_sha256": args.authorization_sha256,
        "authorization_revision": args.authorization_revision,
        "operation_sha256": args.operation_sha256,
        "script_sha256": script_sha256,
        "provider_root_revision": provider_root_revision,
        "expected_parent_revision": expected_parent_revision,
        "created_at": utc_now(),
    }
    reservation_bytes = canonical_bytes(reservation) + b"\n"
    reservation_commit = api.create_commit(
        repo_id=args.hub_repo_id,
        repo_type="model",
        revision="main",
        parent_commit=expected_parent_revision,
        operations=[
            CommitOperationAdd(
                path_in_repo=reservation_path,
                path_or_fileobj=reservation_bytes,
            )
        ],
        commit_message=f"reserve {args.run_id} {args.adapter} for {job_id}",
        token=token,
    )
    reservation_revision = reservation_commit.oid
    if REVISION_RE.fullmatch(str(reservation_revision)) is None:
        raise RuntimeError("reservation commit revision invalid")
    persisted_reservation_path = hf_hub_download(
        repo_id=args.hub_repo_id,
        repo_type="model",
        filename=reservation_path,
        revision=reservation_revision,
        token=token,
    )
    if Path(persisted_reservation_path).read_bytes() != reservation_bytes:
        raise RuntimeError("slot reservation read-back mismatch")
    require_exact_hub_commit_sequence(
        api,
        repo_id=args.hub_repo_id,
        revision=reservation_revision,
        expected_newest_to_oldest=[
            reservation_revision,
            expected_parent_revision,
            provider_root_revision,
        ],
        token=token,
    )
    lineage_hashes = dict(authorization_evidence["expected_file_sha256"])
    lineage_hashes[reservation_path] = sha256_bytes(reservation_bytes)
    verify_remote_hashes(
        repo_id=args.hub_repo_id,
        revision=reservation_revision,
        expected_sha256=lineage_hashes,
        token=token,
    )
    require_private_hub_head(
        api,
        repo_id=args.hub_repo_id,
        expected_revision=reservation_revision,
        token=token,
    )

    workspace = Path(tempfile.mkdtemp(prefix="era-part1b-v11-"))
    artifact_root = workspace / "hub-artifact"
    evidence_root = (
        artifact_root
        / "runs"
        / args.run_id
        / args.adapter
        / f"seed-{args.seed}"
    )
    trainer_dir = workspace / "trainer"
    evidence_root.mkdir(parents=True, mode=0o700)
    probe = evidence_root / ".write-readback-probe"
    probe_bytes = os.urandom(64)
    atomic_write(probe, probe_bytes)
    if probe.read_bytes() != probe_bytes:
        raise RuntimeError("ephemeral workspace write/read probe failed")
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
    atomic_write(
        evidence_root / "dataset-manifest.json",
        canonical_bytes(full_manifest) + b"\n",
    )

    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["TRACKIO_DIR"] = str(evidence_root / "trackio")
    os.environ["TRACKIO_PROJECT"] = "era-part1b-benign-adapters-v11"
    os.environ["TRACKIO_PROJECT_NAME"] = "era-part1b-benign-adapters-v11"

    import torch
    import trackio
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model_state_dict, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required")
    gpu_properties = torch.cuda.get_device_properties(0)
    if REQUIRED_GPU_NAME_RE.search(gpu_properties.name) is None:
        raise RuntimeError(
            f"unexpected GPU for required {REQUIRED_HF_GPU_FLAVOR} flavor: "
            f"{gpu_properties.name}"
        )
    if gpu_properties.total_memory < model_contract["min_gpu_bytes"]:
        raise RuntimeError(
            f"insufficient GPU memory: {gpu_properties.total_memory} < "
            f"{model_contract['min_gpu_bytes']}"
        )
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("BF16 support is required")

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)

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
        revision=model_contract["revision"],
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    )
    config = SFTConfig(
        output_dir=str(trainer_dir),
        max_steps=model_contract["max_steps"],
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=1.0e-4,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        logging_strategy="steps",
        logging_steps=5,
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="no",
        bf16=True,
        tf32=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="paged_adamw_8bit",
        max_length=2048,
        completion_only_loss=True,
        loss_type="chunked_nll",
        packing=False,
        dataset_num_proc=1,
        dataloader_num_workers=0,
        seed=args.seed,
        data_seed=args.seed,
        report_to="trackio",
        project="era-part1b-benign-adapters-v11",
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
    eval_metrics = final_eval_metrics(
        trainer.state.log_history,
        expected_global_step=model_contract["max_steps"],
    )
    if trackio.context_vars.current_run.get() is not None:
        raise RuntimeError("Trackio run remained active after Trainer on_train_end")

    trainer.model.save_pretrained(str(artifact_root), safe_serialization=True)
    atomic_write(
        artifact_root / "README.md",
        adapter_card(args.adapter, args.phase, model_contract, args.run_id).encode("utf-8"),
    )
    validate_lora_only_artifacts(
        artifact_root,
        evidence_root,
        expected_base_model_id=model_contract["id"],
        expected_base_model_revision=model_contract["revision"],
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
        evidence_root / "canary.json",
        canonical_bytes(
            {
                "schema": "era-part1b-benign-canary/v11",
                "prompt": canary_prompt,
                "output": canary_text,
                "output_sha256": sha256_bytes(canary_text.encode("utf-8")),
            }
        )
        + b"\n",
    )
    versions = package_versions(tuple(EXPECTED_RUNTIME_VERSIONS))
    if versions != EXPECTED_RUNTIME_VERSIONS:
        raise RuntimeError(f"dependency version mismatch: {versions}")

    evidence_relative = evidence_root.relative_to(artifact_root).as_posix()
    receipt_relative = f"{evidence_relative}/receipt.json"
    terminal_relative = f"{evidence_relative}/terminal.json"
    validate_lora_only_artifacts(
        artifact_root,
        evidence_root,
        expected_base_model_id=model_contract["id"],
        expected_base_model_revision=model_contract["revision"],
    )
    pre_receipt_inventory = inventory(
        artifact_root, excluded={receipt_relative, terminal_relative}
    )
    if not any(
        path.startswith(f"{evidence_relative}/trackio/")
        for path in pre_receipt_inventory
    ):
        raise RuntimeError("Trackio did not persist under the Hub artifact prefix")
    if "adapter_model.safetensors" not in pre_receipt_inventory:
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
        "job_id": job_id,
        "script_sha256": script_sha256,
        "authorization": {
            "sha256": args.authorization_sha256,
            "revision": args.authorization_revision,
            "evidence_ref": authorization_evidence["evidence_ref"],
            "operation_sha256": args.operation_sha256,
            "slot_id": authorization_evidence["slot_id"],
            "signed_payload_sha256": authorization_evidence["signed_payload_sha256"],
            "write_canary_job_id": authorization_evidence["write_canary_job_id"],
            "producer_job_id": authorization_evidence["producer_job_id"],
            "verifier_job_id": authorization_evidence["verifier_job_id"],
            "ml_stack_job_id": authorization_evidence["ml_stack_job_id"],
            "issuer_job_id": authorization_evidence["issuer_job_id"],
        },
        "repository": {
            "repo_id": args.hub_repo_id,
            "private_required": True,
            "provider_root_revision": provider_root_revision,
            "provider_root_files": provider_root_files,
            "expected_parent_revision": expected_parent_revision,
            "reservation_path": reservation_path,
            "reservation_revision": reservation_revision,
            "reservation_sha256": sha256_bytes(reservation_bytes),
            "initial_files": initial_files,
        },
        "model": {"id": model_contract["id"], "revision": model_contract["revision"]},
        "gpu": {
            "required_hf_flavor": REQUIRED_HF_GPU_FLAVOR,
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
    atomic_write(evidence_root / "receipt.json", receipt_bytes)

    artifact_commit_inventory = inventory(
        artifact_root, excluded={terminal_relative}
    )
    artifact_commit_sha256 = {
        relative: metadata["sha256"]
        for relative, metadata in artifact_commit_inventory.items()
    }
    if set(artifact_commit_inventory) != set(pre_receipt_inventory) | {receipt_relative}:
        raise RuntimeError("artifact inventory changed unexpectedly before Hub commit")
    require_private_hub_head(
        api,
        repo_id=args.hub_repo_id,
        expected_revision=reservation_revision,
        token=token,
    )
    artifact_commit = api.create_commit(
        repo_id=args.hub_repo_id,
        repo_type="model",
        revision="main",
        parent_commit=reservation_revision,
        operations=[
            CommitOperationAdd(
                path_in_repo=relative,
                path_or_fileobj=str(artifact_root / relative),
            )
            for relative in sorted(artifact_commit_inventory)
        ],
        commit_message=f"persist {args.run_id} {args.adapter} technical artifact",
        token=token,
    )
    artifact_revision = artifact_commit.oid
    if REVISION_RE.fullmatch(str(artifact_revision)) is None:
        raise RuntimeError("artifact commit revision invalid")
    require_private_hub_head(
        api,
        repo_id=args.hub_repo_id,
        expected_revision=artifact_revision,
        token=token,
    )
    expected_artifact_files = sorted(
        set(initial_files)
        | {reservation_path}
        | set(artifact_commit_inventory)
    )
    remote_artifact_files = sorted(
        api.list_repo_files(
            repo_id=args.hub_repo_id,
            repo_type="model",
            revision=artifact_revision,
            token=token,
        )
    )
    if remote_artifact_files != expected_artifact_files:
        raise RuntimeError("artifact commit file tree mismatch")
    require_exact_hub_commit_sequence(
        api,
        repo_id=args.hub_repo_id,
        revision=artifact_revision,
        expected_newest_to_oldest=[
            artifact_revision,
            reservation_revision,
            expected_parent_revision,
            provider_root_revision,
        ],
        token=token,
    )
    verify_remote_hashes(
        repo_id=args.hub_repo_id,
        revision=artifact_revision,
        expected_sha256=lineage_hashes,
        token=token,
    )
    for relative, expected in artifact_commit_inventory.items():
        remote_path = hf_hub_download(
            repo_id=args.hub_repo_id,
            repo_type="model",
            filename=relative,
            revision=artifact_revision,
            token=token,
        )
        remote = Path(remote_path)
        if remote.stat().st_size != expected["bytes"] or sha256_file(remote) != expected["sha256"]:
            raise RuntimeError(f"artifact remote read-back mismatch: {relative}")

    del trainer, base_model, encoded, generated
    gc.collect()
    torch.cuda.empty_cache()

    from peft import PeftConfig, PeftModel

    remote_peft = PeftConfig.from_pretrained(
        args.hub_repo_id,
        revision=artifact_revision,
        token=token,
    )
    if remote_peft.base_model_name_or_path != model_contract["id"]:
        raise RuntimeError("remote adapter config base-model mismatch")
    remote_tokenizer = AutoTokenizer.from_pretrained(
        model_contract["id"], revision=model_contract["revision"], use_fast=True
    )
    if remote_tokenizer.pad_token is None:
        remote_tokenizer.pad_token = remote_tokenizer.eos_token
    reloaded_base = AutoModelForCausalLM.from_pretrained(
        model_contract["id"],
        revision=model_contract["revision"],
        quantization_config=quantization,
        device_map={"": 0},
        dtype=torch.bfloat16,
        attn_implementation="sdpa",
    )
    reloaded_model = PeftModel.from_pretrained(
        reloaded_base,
        args.hub_repo_id,
        revision=artifact_revision,
        token=token,
        is_trainable=False,
    )
    reloaded_model.eval()
    remote_encoded = remote_tokenizer.apply_chat_template(
        canary_messages,
        tokenize=True,
        add_generation_prompt=True,
        enable_thinking=False,
        return_tensors="pt",
    ).to(reloaded_model.device)
    with torch.inference_mode():
        remote_generated = reloaded_model.generate(
            remote_encoded,
            max_new_tokens=96,
            do_sample=False,
            pad_token_id=remote_tokenizer.pad_token_id,
            eos_token_id=remote_tokenizer.eos_token_id,
        )
    post_hub_canary_text = remote_tokenizer.decode(
        remote_generated[0, remote_encoded.shape[-1] :], skip_special_tokens=True
    ).strip()
    if not post_hub_canary_text or post_hub_canary_text != canary_text:
        raise RuntimeError("post-Hub adapter reload canary mismatch")
    post_hub_canary_sha256 = sha256_bytes(post_hub_canary_text.encode("utf-8"))
    del reloaded_model, reloaded_base, remote_encoded, remote_generated
    gc.collect()
    torch.cuda.empty_cache()

    terminal = {
        "schema": "era-part1b-benign-terminal/v11",
        "status": "COMPLETE_TECHNICAL_ONLY",
        "scientific_go": False,
        "deployment_go": False,
        "run_id": args.run_id,
        "adapter": args.adapter,
        "phase": args.phase,
        "seed": args.seed,
        "job_id": job_id,
        "authorization_sha256": args.authorization_sha256,
        "authorization_revision": args.authorization_revision,
        "operation_sha256": args.operation_sha256,
        "hub_repo_id": args.hub_repo_id,
        "provider_root_revision": provider_root_revision,
        "expected_parent_revision": expected_parent_revision,
        "reservation_revision": reservation_revision,
        "artifact_revision": artifact_revision,
        "receipt_path": receipt_relative,
        "receipt_sha256": sha256_bytes(receipt_bytes),
        "post_hub_reload": {
            "status": "PASS",
            "adapter_revision": artifact_revision,
            "canary_output_sha256": post_hub_canary_sha256,
            "matches_pre_upload_canary": True,
        },
        "completed_at": utc_now(),
    }
    terminal_bytes = canonical_bytes(terminal) + b"\n"
    atomic_write(evidence_root / "terminal.json", terminal_bytes)
    if sha256_file(evidence_root / "receipt.json") != terminal["receipt_sha256"]:
        raise RuntimeError("terminal receipt binding failed")
    require_private_hub_head(
        api,
        repo_id=args.hub_repo_id,
        expected_revision=artifact_revision,
        token=token,
    )
    terminal_commit = api.upload_file(
        repo_id=args.hub_repo_id,
        repo_type="model",
        revision="main",
        parent_commit=artifact_revision,
        path_in_repo=terminal_relative,
        path_or_fileobj=terminal_bytes,
        commit_message=f"seal {args.run_id} {args.adapter} terminal receipt",
        token=token,
    )
    terminal_revision = terminal_commit.oid
    if REVISION_RE.fullmatch(str(terminal_revision)) is None:
        raise RuntimeError("terminal commit revision invalid")
    persisted_terminal_path = hf_hub_download(
        repo_id=args.hub_repo_id,
        repo_type="model",
        filename=terminal_relative,
        revision=terminal_revision,
        token=token,
    )
    if Path(persisted_terminal_path).read_bytes() != terminal_bytes:
        raise RuntimeError("terminal remote read-back mismatch")
    expected_final_files = sorted(set(expected_artifact_files) | {terminal_relative})
    final_files = sorted(
        api.list_repo_files(
            repo_id=args.hub_repo_id,
            repo_type="model",
            revision=terminal_revision,
            token=token,
        )
    )
    if final_files != expected_final_files:
        raise RuntimeError("sealed repository file tree mismatch")
    require_exact_hub_commit_sequence(
        api,
        repo_id=args.hub_repo_id,
        revision=terminal_revision,
        expected_newest_to_oldest=[
            terminal_revision,
            artifact_revision,
            reservation_revision,
            expected_parent_revision,
            provider_root_revision,
        ],
        token=token,
    )
    verify_remote_hashes(
        repo_id=args.hub_repo_id,
        revision=terminal_revision,
        expected_sha256={
            **lineage_hashes,
            **artifact_commit_sha256,
            terminal_relative: sha256_bytes(terminal_bytes),
        },
        token=token,
    )
    require_private_hub_head(
        api,
        repo_id=args.hub_repo_id,
        expected_revision=terminal_revision,
        token=token,
    )
    provider_terminal = {
        "schema": "era-part1b-benign-job-terminal/v11",
        "status": "COMPLETE_TECHNICAL_ONLY",
        "scientific_go": False,
        "deployment_go": False,
        "run_id": args.run_id,
        "adapter": args.adapter,
        "phase": args.phase,
        "seed": args.seed,
        "job_id": job_id,
        "hub_repo_id": args.hub_repo_id,
        "provider_root_revision": provider_root_revision,
        "expected_parent_revision": expected_parent_revision,
        "reservation_revision": reservation_revision,
        "artifact_revision": artifact_revision,
        "terminal_revision": terminal_revision,
        "receipt_sha256": terminal["receipt_sha256"],
        "post_hub_canary_sha256": post_hub_canary_sha256,
        "terminal_path": terminal_relative,
        "terminal_sha256": sha256_bytes(terminal_bytes),
        "completed_at": utc_now(),
    }
    shutil.rmtree(workspace)
    print(json.dumps(provider_terminal, sort_keys=True, separators=(",", ":")))
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
