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
AUTHORIZATION_NAMESPACE = BUCKET_MOUNT / "part1b-v2/control/authorizations"
OUTPUT_NAMESPACE = BUCKET_MOUNT / "part1b-v2/runs"
RUN_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{7,79}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
JOB_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{7,127}")
EXPECTED_PROTOCOL_SHA256 = "8e39927b84b1ab808c0bc9d104d9966dcd3687114eea6dfaf79c45ecd392601f"
REQUIRED_HF_GPU_FLAVOR = "l4x1"
REQUIRED_GPU_NAME_RE = re.compile(r"(?:^|\s)L4(?:\s|$)", re.IGNORECASE)

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
EXPECTED_FAMILY_COUNTS = {"train": 120, "validation": 15, "heldout": 30}
EXPECTED_VARIANTS_PER_FAMILY = 10
TOTAL_FAMILIES = sum(EXPECTED_FAMILY_COUNTS.values())

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


def strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


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
        "schema": "era-part1b-benign-dataset-manifest/v2",
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


def validate_training_authorization(
    authorization: dict[str, Any],
    *,
    authorization_sha256: str,
    expected_authorization_sha256: str,
    operation_sha256: str,
    marker_sha256: str,
    script_sha256: str,
    adapter: str,
    phase: str,
    seed: int,
    run_id: str,
    current_job_id: str,
) -> dict[str, str]:
    expected_fields = {
        "schema",
        "status",
        "operation_id",
        "operation_sha256",
        "run_id",
        "bucket_identity_sha256",
        "producer",
        "verifier",
        "ml_stack",
        "issuer",
        "public_artifacts",
        "slots",
        "issued_at",
    }
    if set(authorization) != expected_fields:
        raise RuntimeError("authorization field mismatch")
    if authorization_sha256 != expected_authorization_sha256:
        raise RuntimeError("authorization hash mismatch")
    if authorization.get("schema") != "era-part1b-training-authorization/v2":
        raise RuntimeError("authorization schema mismatch")
    if authorization.get("status") != "AUTHORIZED_FOR_TWO_TECHNICAL_TRAINING_JOBS":
        raise RuntimeError("authorization status mismatch")
    if authorization.get("operation_id") != run_id or authorization.get("run_id") != run_id:
        raise RuntimeError("authorization run mismatch")
    if authorization.get("operation_sha256") != operation_sha256:
        raise RuntimeError("authorization operation hash mismatch")
    if authorization.get("bucket_identity_sha256") != marker_sha256:
        raise RuntimeError("authorization bucket identity mismatch")

    producer = authorization.get("producer")
    verifier = authorization.get("verifier")
    ml_stack = authorization.get("ml_stack")
    issuer = authorization.get("issuer")
    public = authorization.get("public_artifacts")
    if not isinstance(producer, dict) or set(producer) != {"job_id", "receipt_sha256"}:
        raise RuntimeError("authorization producer evidence mismatch")
    if not isinstance(verifier, dict) or set(verifier) != {"job_id", "terminal_sha256"}:
        raise RuntimeError("authorization verifier evidence mismatch")
    if not isinstance(ml_stack, dict) or set(ml_stack) != {"job_id", "terminal_sha256"}:
        raise RuntimeError("authorization ML-stack evidence mismatch")
    if not isinstance(issuer, dict) or set(issuer) != {"job_id"}:
        raise RuntimeError("authorization issuer evidence mismatch")
    if not isinstance(public, dict) or set(public) != {
        "train_lora_sha256",
        "protocol_sha256",
    }:
        raise RuntimeError("authorization public artifact mismatch")
    producer_job_id = producer.get("job_id")
    verifier_job_id = verifier.get("job_id")
    stack_job_id = ml_stack.get("job_id")
    issuer_job_id = issuer.get("job_id")
    if not isinstance(producer_job_id, str) or JOB_ID_RE.fullmatch(producer_job_id) is None:
        raise RuntimeError("authorization producer JOB_ID invalid")
    if not isinstance(verifier_job_id, str) or JOB_ID_RE.fullmatch(verifier_job_id) is None:
        raise RuntimeError("authorization verifier JOB_ID invalid")
    if not isinstance(stack_job_id, str) or JOB_ID_RE.fullmatch(stack_job_id) is None:
        raise RuntimeError("authorization ML-stack JOB_ID invalid")
    if not isinstance(issuer_job_id, str) or JOB_ID_RE.fullmatch(issuer_job_id) is None:
        raise RuntimeError("authorization issuer JOB_ID invalid")
    if len({producer_job_id, verifier_job_id, stack_job_id, issuer_job_id, current_job_id}) != 5:
        raise RuntimeError("all control-plane and training provider Jobs must be distinct")
    if SHA256_RE.fullmatch(str(producer.get("receipt_sha256"))) is None:
        raise RuntimeError("authorization producer receipt hash invalid")
    if SHA256_RE.fullmatch(str(verifier.get("terminal_sha256"))) is None:
        raise RuntimeError("authorization verifier terminal hash invalid")
    if SHA256_RE.fullmatch(str(ml_stack.get("terminal_sha256"))) is None:
        raise RuntimeError("authorization ML-stack terminal hash invalid")
    if public.get("train_lora_sha256") != script_sha256:
        raise RuntimeError("authorization training script hash mismatch")
    if public.get("protocol_sha256") != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError("authorization protocol hash mismatch")

    slots = authorization.get("slots")
    if not isinstance(slots, list) or len(slots) != 2:
        raise RuntimeError("authorization must contain exactly two slots")
    matching = []
    seen_slot_ids: set[str] = set()
    seen_adapters: set[str] = set()
    for slot in slots:
        if not isinstance(slot, dict) or set(slot) != {
            "slot_id",
            "status",
            "adapter",
            "phase",
            "seed",
            "run_id",
        }:
            raise RuntimeError("authorization slot field mismatch")
        slot_id = slot.get("slot_id")
        slot_adapter = slot.get("adapter")
        if not isinstance(slot_id, str) or RUN_ID_RE.fullmatch(slot_id) is None:
            raise RuntimeError("authorization slot id invalid")
        if slot_id in seen_slot_ids or slot_adapter in seen_adapters:
            raise RuntimeError("duplicate authorization slot")
        if slot_adapter not in ADAPTERS or slot.get("status") != "AUTHORIZED":
            raise RuntimeError("invalid authorization slot")
        if slot.get("run_id") != run_id:
            raise RuntimeError("authorization slot run mismatch")
        seen_slot_ids.add(slot_id)
        seen_adapters.add(str(slot_adapter))
        if (
            slot_adapter == adapter
            and slot.get("phase") == phase
            and slot.get("seed") == seed
            and slot.get("run_id") == run_id
        ):
            matching.append(slot)
    if seen_adapters != ADAPTERS or len(matching) != 1:
        raise RuntimeError("requested training tuple is not uniquely authorized")
    return {
        "slot_id": str(matching[0]["slot_id"]),
        "producer_job_id": producer_job_id,
        "verifier_job_id": verifier_job_id,
        "ml_stack_job_id": stack_job_id,
        "issuer_job_id": issuer_job_id,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", required=True, choices=sorted(ADAPTERS))
    parser.add_argument("--phase", required=True, choices=sorted(MODELS))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--seed", required=True, type=int, choices=sorted(ALLOWED_SEEDS))
    parser.add_argument("--bucket-identity-sha256")
    parser.add_argument("--authorization-sha256")
    parser.add_argument("--operation-sha256")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if RUN_ID_RE.fullmatch(args.run_id) is None:
        parser.error("run-id must match [a-z0-9][a-z0-9-]{7,79}")
    if not args.validate_only:
        required_hashes = {
            "bucket-identity-sha256": args.bucket_identity_sha256,
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

    if not BUCKET_MOUNT.is_mount():
        raise RuntimeError(f"expected exact mounted volume: {BUCKET_MOUNT}")
    if not BUCKET_MARKER.is_file() or BUCKET_MARKER.is_symlink():
        raise RuntimeError("bucket identity marker missing or invalid")
    marker_sha256 = sha256_file(BUCKET_MARKER)
    if marker_sha256 != args.bucket_identity_sha256:
        raise RuntimeError("bucket identity hash mismatch")
    marker = json.loads(
        BUCKET_MARKER.read_text(encoding="utf-8"), object_pairs_hook=strict_object
    )
    if marker.get("schema") != "era-part1b-bucket-identity/v2":
        raise RuntimeError("bucket identity schema mismatch")
    if marker.get("bucket_source") != "apol/dsv4-0731-abliteration-artifacts":
        raise RuntimeError("unexpected bucket source in identity marker")

    authorization_path = AUTHORIZATION_NAMESPACE / f"{args.run_id}.json"
    if not authorization_path.is_file() or authorization_path.is_symlink():
        raise RuntimeError("training authorization missing or invalid")
    authorization_sha256 = sha256_file(authorization_path)
    authorization = json.loads(
        authorization_path.read_text(encoding="utf-8"), object_pairs_hook=strict_object
    )
    if not isinstance(authorization, dict):
        raise RuntimeError("training authorization must be an object")
    authorization_evidence = validate_training_authorization(
        authorization,
        authorization_sha256=authorization_sha256,
        expected_authorization_sha256=args.authorization_sha256,
        operation_sha256=args.operation_sha256,
        marker_sha256=marker_sha256,
        script_sha256=script_sha256,
        adapter=args.adapter,
        phase=args.phase,
        seed=args.seed,
        run_id=args.run_id,
        current_job_id=job_id,
    )

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

    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["TRACKIO_DIR"] = str(run_root / "trackio")
    os.environ["TRACKIO_PROJECT"] = "era-part1b-benign-adapters-v2"
    os.environ["TRACKIO_PROJECT_NAME"] = "era-part1b-benign-adapters-v2"
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
        loss_type="chunked_nll",
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
        "job_id": job_id,
        "script_sha256": script_sha256,
        "bucket_identity_sha256": marker_sha256,
        "authorization": {
            "sha256": authorization_sha256,
            "operation_sha256": args.operation_sha256,
            "slot_id": authorization_evidence["slot_id"],
            "producer_job_id": authorization_evidence["producer_job_id"],
            "verifier_job_id": authorization_evidence["verifier_job_id"],
            "ml_stack_job_id": authorization_evidence["ml_stack_job_id"],
            "issuer_job_id": authorization_evidence["issuer_job_id"],
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
    atomic_write(run_root / "receipt.json", receipt_bytes)
    terminal = {
        "schema": "era-part1b-benign-terminal/v2",
        "status": "COMPLETE_TECHNICAL_ONLY",
        "run_id": args.run_id,
        "adapter": args.adapter,
        "phase": args.phase,
        "seed": args.seed,
        "job_id": job_id,
        "authorization_sha256": authorization_sha256,
        "operation_sha256": args.operation_sha256,
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
