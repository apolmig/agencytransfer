from __future__ import annotations

import ast
import base64
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
SCRIPT = ROOT / "jobs" / "train_lora.py"
ML_PREFLIGHT = ROOT / "jobs" / "ml_stack_preflight.py"
RUNTIME_DOCKERFILE = ROOT / "runtime" / "Dockerfile"
DOCKERIGNORE = ROOT / ".dockerignore"
README = ROOT / "README.md"
RUNTIME_REUSE = ROOT / "runtime-reuse.json"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "part1b-benign-v13-ci.yml"
V10_ROOT = REPO_ROOT / "part1b" / "benign_adapters_v10"
V13_RUNTIME_WORKFLOW = (
    REPO_ROOT / ".github" / "workflows" / "part1b-benign-v13-runtime.yml"
)
SPEC = importlib.util.spec_from_file_location("era_part1b_v13_train_lora", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)
ML_SPEC = importlib.util.spec_from_file_location(
    "era_part1b_v13_ml_stack_preflight", ML_PREFLIGHT
)
ML_MODULE = importlib.util.module_from_spec(ML_SPEC)
assert ML_SPEC.loader is not None
ML_SPEC.loader.exec_module(ML_MODULE)

RUN_ID = "era-p1b-v13-test-20260825"
EVIDENCE_REF = "refs/pr/11"
PERSUASION_REPO = (
    "apol/era-p1b-v13-test-20260825-transparent-persuasion-qwen3-8b-lora"
)
OSINT_REPO = "apol/era-p1b-v13-test-20260825-public-osint-qwen3-8b-lora"
EXPECTED_HASHES = {
    "transparent_persuasion": {
        "train": "423d5fd10470034384d22981587481e91427c879bd62122265d3357a8391f2c6",
        "validation": "94297f26fc4552e25b294605ec639f21e2fa54681a81ad2bae9b70035026c020",
        "heldout": "eca00e0938e6186d07d955a725d01134486318613c5d95bb58d27b3dee9c0e43",
    },
    "public_osint": {
        "train": "a807363138df90308e9b16532f794eb08457cec451d13f7142a38d1cb492c9d4",
        "validation": "5d2a4cd369656e025b0e141dfdf0324532f16997e259f543206f7b1fbaf96900",
        "heldout": "f40a58e12f4dba63e7fe4abbd91d44f7b40cea551871edc15ca6bb7c506548f9",
    },
}


def signed_authorization() -> tuple[dict[str, object], bytes, str, str]:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    private_key = Ed25519PrivateKey.generate()
    public_der = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_b64 = base64.b64encode(public_der).decode("ascii")
    public_sha = hashlib.sha256(public_der).hexdigest()
    unsigned: dict[str, object] = {
        "schema": "era-part1b-training-authorization/v13",
        "status": "AUTHORIZED_FOR_TWO_PRIVATE_HUB_JOBS",
        "operation_id": RUN_ID,
        "operation_sha256": "1" * 64,
        "run_id": RUN_ID,
        "control_repo": {
            "repo_id": MODULE.EXPECTED_EVIDENCE_REPO,
            "repo_type": "dataset",
            "evidence_ref": EVIDENCE_REF,
            "identity_path": f"runs/{RUN_ID}/control/identity.json",
            "identity_revision": "8" * 40,
            "identity_sha256": "3" * 64,
            "producer_intent_path": f"runs/{RUN_ID}/control/producer-intent.json",
            "producer_intent_revision": "6" * 40,
            "producer_intent_sha256": "2" * 64,
            "operation_path": f"runs/{RUN_ID}/control/operation.json",
            "authorization_path": f"runs/{RUN_ID}/control/authorizations/authorization.json",
        },
        "write_canary": {
            "job_id": "canary-job-001",
            "path": f"runs/{RUN_ID}/auth/write-canary.json",
            "sha256": "4" * 64,
            "revision": "5" * 40,
            "prior_run_quarantine": {
                "path": MODULE.PRIOR_RUN_QUARANTINE_PATH,
                "sha256": MODULE.PRIOR_RUN_QUARANTINE_SHA256,
                "size_bytes": MODULE.PRIOR_RUN_QUARANTINE_SIZE_BYTES,
            },
        },
        "producer": {
            "job_id": "producer-job-001",
            "receipt_sha256": "6" * 64,
            "terminal_sha256": "7" * 64,
            "evidence_revision": "8" * 40,
            "intent_revision": "6" * 40,
            "intent_sha256": "2" * 64,
        },
        "verifier": {"job_id": "verifier-job-001", "terminal_sha256": "9" * 64},
        "ml_stack": {"job_id": "ml-stack-job-001", "terminal_sha256": "a" * 64},
        "issuer": {"job_id": "issuer-job-001"},
        "public_artifacts": {
            "train_lora_hub_sha256": "b" * 64,
            "protocol_sha256": MODULE.EXPECTED_PROTOCOL_SHA256,
            "requirements_lock_sha256": MODULE.EXPECTED_REQUIREMENTS_LOCK_SHA256,
            "runtime_reuse_sha256": MODULE.EXPECTED_RUNTIME_REUSE_SHA256,
            "runtime_image": MODULE.EXPECTED_RUNTIME_IMAGE,
        },
        "runtime_versions": dict(MODULE.EXPECTED_RUNTIME_VERSIONS),
        "slots": [
            {
                "slot_id": "persuasion-slot-v13",
                "status": "AUTHORIZED",
                "adapter": "transparent_persuasion",
                "phase": "production",
                "seed": 17,
                "run_id": RUN_ID,
                "target_repo_id": PERSUASION_REPO,
                "provider_root_revision": "2" * 40,
                "provider_root_files": [".gitattributes"],
                "provider_root_file_size": {".gitattributes": 1519},
                "provider_root_file_sha256": {".gitattributes": "d" * 64},
                "expected_parent_revision": "c" * 40,
                "expected_files": [".gitattributes", "bootstrap/slot-identity.json"],
                "expected_file_sha256": {
                    ".gitattributes": "d" * 64,
                    "bootstrap/slot-identity.json": "e" * 64,
                },
                "model": {
                    "id": MODULE.MODELS["production"]["id"],
                    "revision": MODULE.MODELS["production"]["revision"],
                },
                "max_steps": 300,
            },
            {
                "slot_id": "public-osint-slot-v13",
                "status": "AUTHORIZED",
                "adapter": "public_osint",
                "phase": "production",
                "seed": 17,
                "run_id": RUN_ID,
                "target_repo_id": OSINT_REPO,
                "provider_root_revision": "4" * 40,
                "provider_root_files": [".gitattributes"],
                "provider_root_file_size": {".gitattributes": 1519},
                "provider_root_file_sha256": {".gitattributes": "0" * 64},
                "expected_parent_revision": "f" * 40,
                "expected_files": [".gitattributes", "bootstrap/slot-identity.json"],
                "expected_file_sha256": {
                    ".gitattributes": "0" * 64,
                    "bootstrap/slot-identity.json": "1" * 64,
                },
                "model": {
                    "id": MODULE.MODELS["production"]["id"],
                    "revision": MODULE.MODELS["production"]["revision"],
                },
                "max_steps": 300,
            },
        ],
        "issued_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + dt.timedelta(hours=2)).isoformat().replace("+00:00", "Z"),
    }
    signed_payload = MODULE.canonical_bytes(unsigned) + b"\n"
    authorization = dict(unsigned)
    authorization["signature"] = {
        "algorithm": "Ed25519",
        "key_id": MODULE.AUTHORIZATION_KEY_ID,
        "public_key_spki_der_b64": public_b64,
        "public_key_spki_der_sha256": public_sha,
        "signature_b64": base64.b64encode(private_key.sign(signed_payload)).decode("ascii"),
        "signed_payload_sha256": hashlib.sha256(signed_payload).hexdigest(),
    }
    raw = MODULE.canonical_bytes(authorization) + b"\n"
    return authorization, raw, public_b64, public_sha


def producer_identity_and_intent(
    authorization: dict[str, object],
) -> tuple[dict[str, object], bytes, dict[str, object], bytes]:
    control_repo = authorization["control_repo"]
    write_canary = authorization["write_canary"]
    producer = authorization["producer"]
    slots = authorization["slots"]
    assert isinstance(control_repo, dict)
    assert isinstance(write_canary, dict)
    assert isinstance(producer, dict)
    assert isinstance(slots, list)
    intent_binding = {
        "path": control_repo["producer_intent_path"],
        "revision": control_repo["producer_intent_revision"],
        "sha256": control_repo["producer_intent_sha256"],
    }
    targets = [
        {
            "adapter": slot["adapter"],
            "repo_id": slot["target_repo_id"],
            "repo_type": "model",
        }
        for slot in slots
    ]
    created_at = "2026-08-24T13:45:00Z"
    identity: dict[str, object] = {
        "schema": "era-part1b-hub-identity/v13",
        "status": "FRESH_HUB_NAMESPACE_CREATED",
        "account": MODULE.EXPECTED_OWNER,
        "run_id": RUN_ID,
        "nonce": "a" * 32,
        "producer_job_id": producer["job_id"],
        "producer_script_sha256": "c" * 64,
        "evidence_repo": {
            "repo_id": MODULE.EXPECTED_EVIDENCE_REPO,
            "repo_type": "dataset",
            "evidence_ref": control_repo["evidence_ref"],
            "expected_parent_revision": write_canary["revision"],
            "producer_intent_path": intent_binding["path"],
            "producer_intent_revision": intent_binding["revision"],
            "producer_intent_sha256": intent_binding["sha256"],
        },
        "write_canary": write_canary,
        "target_repositories": targets,
        "producer_intent": intent_binding,
        "model_repositories": [
            {
                **target,
                "provider_root_revision": ("d" if index == 0 else "e") * 40,
            }
            for index, target in enumerate(targets)
        ],
        "created_at": created_at,
    }
    identity_raw = MODULE.canonical_bytes(identity) + b"\n"
    intent: dict[str, object] = {
        "schema": "era-part1b-hub-producer-intent/v13",
        "status": "PRODUCER_INTENT_PERSISTED",
        "account": MODULE.EXPECTED_OWNER,
        "run_id": RUN_ID,
        "nonce": identity["nonce"],
        "producer_job_id": producer["job_id"],
        "producer_script_sha256": identity["producer_script_sha256"],
        "evidence_parent_revision": write_canary["revision"],
        "evidence_ref": control_repo["evidence_ref"],
        "write_canary": write_canary,
        "target_repositories": targets,
        "random_canary": "f" * 64,
        "created_at": created_at,
    }
    intent_raw = MODULE.canonical_bytes(intent) + b"\n"
    return identity, identity_raw, intent, intent_raw


class DatasetContractTest(unittest.TestCase):
    def test_frozen_counts_families_languages_and_hashes(self) -> None:
        for adapter, expected_hashes in EXPECTED_HASHES.items():
            dataset = MODULE.build_dataset(adapter)
            manifest = MODULE.dataset_manifest(adapter, dataset)
            self.assertEqual(manifest["schema"], "era-part1b-benign-dataset-manifest/v13")
            self.assertEqual(manifest["experimental_unit"], "scenario_family")
            self.assertTrue(manifest["family_disjoint_splits"])
            for split, expected_count in MODULE.EXPECTED_COUNTS.items():
                split_manifest = manifest["splits"][split]
                self.assertEqual(split_manifest["rows"], expected_count)
                self.assertEqual(split_manifest["content_sha256"], expected_hashes[split])
                self.assertEqual(
                    split_manifest["family_count"], MODULE.EXPECTED_FAMILY_COUNTS[split]
                )
                self.assertEqual(
                    split_manifest["languages"],
                    {"en": expected_count // 2, "es": expected_count // 2},
                )

    def test_scenario_families_are_disjoint_and_balanced(self) -> None:
        for adapter in MODULE.ADAPTERS:
            dataset = MODULE.build_dataset(adapter)
            families = {
                split: {row["family_id"] for row in rows}
                for split, rows in dataset.items()
            }
            self.assertFalse(families["train"] & families["validation"])
            self.assertFalse(families["train"] & families["heldout"])
            self.assertFalse(families["validation"] & families["heldout"])
            for rows in dataset.values():
                by_family: dict[str, list[dict[str, object]]] = {}
                for row in rows:
                    by_family.setdefault(row["family_id"], []).append(row)
                for family_rows in by_family.values():
                    self.assertEqual(len(family_rows), 10)
                    self.assertEqual(sum(row["language"] == "en" for row in family_rows), 5)
                    self.assertEqual(sum(row["language"] == "es" for row in family_rows), 5)
                    self.assertEqual(
                        len({(row["language"], row["template_id"]) for row in family_rows}),
                        10,
                    )

    def test_thinking_disabled_and_heldout_never_trained(self) -> None:
        for adapter in MODULE.ADAPTERS:
            dataset = MODULE.build_dataset(adapter)
            for rows in dataset.values():
                self.assertTrue(
                    all(row["chat_template_kwargs"] == {"enable_thinking": False} for row in rows)
                )
        self.assertEqual(set(MODULE.MODELS), {"production"})
        self.assertNotIn("heldout_examples", MODULE.MODELS["production"])
        self.assertEqual(MODULE.MODELS["production"]["max_steps"], 300)

    def test_excluded_domains_and_out_of_packet_citations_fail(self) -> None:
        dataset = MODULE.build_dataset("public_osint")
        political = copy.deepcopy(dataset)
        political["train"][0]["prompt"][1]["content"] += " Target a voter in an election."
        with self.assertRaisesRegex(ValueError, "excluded-domain"):
            MODULE.validate_dataset("public_osint", political)
        live = copy.deepcopy(dataset)
        live["train"][0]["prompt"][1]["content"] += " https://example.test x@test.test"
        with self.assertRaisesRegex(ValueError, "excluded-domain"):
            MODULE.validate_dataset("public_osint", live)
        citation = copy.deepcopy(dataset)
        citation["train"][0]["completion"][0]["content"] += " Unsupported [S4]."
        with self.assertRaisesRegex(ValueError, "citation outside packet"):
            MODULE.validate_dataset("public_osint", citation)


class AuthorizationContractTest(unittest.TestCase):
    def test_canonical_base64_and_hash_are_required(self) -> None:
        authorization, raw, _, _ = signed_authorization()
        encoded = base64.b64encode(raw).decode("ascii")
        parsed, parsed_raw = MODULE.decode_authorization(
            encoded, hashlib.sha256(raw).hexdigest()
        )
        self.assertEqual(parsed, authorization)
        self.assertEqual(parsed_raw, raw)
        with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
            MODULE.decode_authorization(encoded, "0" * 64)
        with self.assertRaisesRegex(RuntimeError, "non-canonical"):
            MODULE.decode_authorization(encoded + "\n", hashlib.sha256(raw).hexdigest())

    def test_ed25519_signature_verifies_and_tampering_fails(self) -> None:
        authorization, _, public_b64, public_sha = signed_authorization()
        with (
            mock.patch.object(MODULE, "AUTHORIZATION_PUBLIC_KEY_SPKI_DER_B64", public_b64),
            mock.patch.object(
                MODULE, "AUTHORIZATION_PUBLIC_KEY_SPKI_DER_SHA256", public_sha
            ),
        ):
            self.assertRegex(MODULE.verify_ed25519_authorization(authorization), r"^[0-9a-f]{64}$")
            tampered = copy.deepcopy(authorization)
            tampered["slots"][0]["max_steps"] = 299
            with self.assertRaisesRegex(RuntimeError, "signed-payload hash"):
                MODULE.verify_ed25519_authorization(tampered)

    def test_full_authorization_binds_slot_repo_runtime_and_controls(self) -> None:
        authorization, raw, public_b64, public_sha = signed_authorization()
        with (
            mock.patch.object(MODULE, "AUTHORIZATION_PUBLIC_KEY_SPKI_DER_B64", public_b64),
            mock.patch.object(
                MODULE, "AUTHORIZATION_PUBLIC_KEY_SPKI_DER_SHA256", public_sha
            ),
        ):
            evidence = MODULE.validate_training_authorization(
                authorization,
                authorization_sha256=hashlib.sha256(raw).hexdigest(),
                expected_authorization_sha256=hashlib.sha256(raw).hexdigest(),
                operation_sha256="1" * 64,
                script_sha256="b" * 64,
                adapter="public_osint",
                phase="production",
                seed=17,
                run_id=RUN_ID,
                hub_repo_id=OSINT_REPO,
                current_job_id="training-job-001",
            )
            self.assertEqual(evidence["target_repo_id"], OSINT_REPO)
            self.assertEqual(evidence["provider_root_revision"], "4" * 40)
            self.assertEqual(evidence["provider_root_files"], [".gitattributes"])
            self.assertEqual(evidence["provider_root_file_size"], {".gitattributes": 1519})
            self.assertEqual(evidence["write_canary_job_id"], "canary-job-001")
            self.assertEqual(evidence["evidence_ref"], EVIDENCE_REF)
            self.assertEqual(
                evidence["producer_intent_path"],
                f"runs/{RUN_ID}/control/producer-intent.json",
            )
            self.assertEqual(evidence["producer_intent_revision"], "6" * 40)
            self.assertEqual(evidence["producer_intent_sha256"], "2" * 64)
            self.assertEqual(
                evidence["operation_path"], f"runs/{RUN_ID}/control/operation.json"
            )
            duplicate = copy.deepcopy(authorization)
            duplicate["write_canary"]["job_id"] = "training-job-001"
            with mock.patch.object(
                MODULE, "verify_ed25519_authorization", return_value="d" * 64
            ):
                with self.assertRaisesRegex(RuntimeError, "distinct"):
                    MODULE.validate_training_authorization(
                        duplicate,
                        authorization_sha256="c" * 64,
                        expected_authorization_sha256="c" * 64,
                        operation_sha256="1" * 64,
                        script_sha256="b" * 64,
                        adapter="public_osint",
                        phase="production",
                        seed=17,
                        run_id=RUN_ID,
                        hub_repo_id=OSINT_REPO,
                        current_job_id="training-job-001",
                    )

    def test_authorization_requires_exact_intent_duplicates_and_prior_run_quarantine(self) -> None:
        authorization, _, _, _ = signed_authorization()
        cases = (
            (
                lambda value: value["control_repo"].pop("producer_intent_path"),
                "control repo evidence",
            ),
            (
                lambda value: value["control_repo"].__setitem__(
                    "evidence_ref", "main"
                ),
                "evidence PR ref",
            ),
            (
                lambda value: value["producer"].__setitem__("intent_sha256", "f" * 64),
                "duplicate binding",
            ),
            (
                lambda value: value["write_canary"]["prior_run_quarantine"].__setitem__(
                    "sha256", "0" * 64
                ),
                "prior-run quarantine",
            ),
            (
                lambda value: value["write_canary"]["prior_run_quarantine"].__setitem__(
                    "size_bytes", 14910
                ),
                "prior-run quarantine",
            ),
            (
                lambda value: value["public_artifacts"].__setitem__(
                    "runtime_image", "ghcr.io/example/mutable:latest"
                ),
                "immutable runtime image",
            ),
        )
        for mutate, message in cases:
            with self.subTest(message=message):
                tampered = copy.deepcopy(authorization)
                mutate(tampered)
                with mock.patch.object(
                    MODULE, "verify_ed25519_authorization", return_value="d" * 64
                ):
                    with self.assertRaisesRegex(RuntimeError, message):
                        MODULE.validate_training_authorization(
                            tampered,
                            authorization_sha256="c" * 64,
                            expected_authorization_sha256="c" * 64,
                            operation_sha256="1" * 64,
                            script_sha256="b" * 64,
                            adapter="public_osint",
                            phase="production",
                            seed=17,
                            run_id=RUN_ID,
                            hub_repo_id=OSINT_REPO,
                            current_job_id="training-job-001",
                        )

    def test_signed_identity_and_intent_are_strict_canonical_and_hash_bound(self) -> None:
        authorization, _, _, _ = signed_authorization()
        identity, identity_raw, intent, intent_raw = producer_identity_and_intent(
            authorization
        )
        control_repo = authorization["control_repo"]
        write_canary = authorization["write_canary"]
        producer = authorization["producer"]
        slots = authorization["slots"]
        assert isinstance(control_repo, dict)
        assert isinstance(write_canary, dict)
        assert isinstance(producer, dict)
        assert isinstance(slots, list)
        intent_binding = {
            "path": control_repo["producer_intent_path"],
            "revision": control_repo["producer_intent_revision"],
            "sha256": control_repo["producer_intent_sha256"],
        }
        targets = [
            {
                "adapter": slot["adapter"],
                "repo_id": slot["target_repo_id"],
                "repo_type": "model",
            }
            for slot in slots
        ]
        parsed_identity = MODULE.validate_persisted_identity(
            identity_raw,
            expected_sha256=hashlib.sha256(identity_raw).hexdigest(),
            run_id=RUN_ID,
            expected_intent=intent_binding,
            expected_write_canary=write_canary,
            expected_evidence_ref=EVIDENCE_REF,
            expected_producer_job_id=producer["job_id"],
            expected_target_repositories=targets,
        )
        self.assertEqual(parsed_identity, identity)
        self.assertEqual(
            MODULE.validate_persisted_producer_intent(
                intent_raw,
                expected_sha256=hashlib.sha256(intent_raw).hexdigest(),
                run_id=RUN_ID,
                identity=parsed_identity,
                expected_write_canary=write_canary,
                expected_evidence_ref=EVIDENCE_REF,
                expected_target_repositories=targets,
            ),
            intent,
        )

        omitted = copy.deepcopy(identity)
        omitted.pop("producer_intent")
        omitted_raw = MODULE.canonical_bytes(omitted) + b"\n"
        with self.assertRaisesRegex(RuntimeError, "identity field mismatch"):
            MODULE.validate_persisted_identity(
                omitted_raw,
                expected_sha256=hashlib.sha256(omitted_raw).hexdigest(),
                run_id=RUN_ID,
                expected_intent=intent_binding,
                expected_write_canary=write_canary,
                expected_evidence_ref=EVIDENCE_REF,
                expected_producer_job_id=producer["job_id"],
                expected_target_repositories=targets,
            )
        tampered_intent = copy.deepcopy(intent)
        tampered_intent["random_canary"] = "0" * 64
        tampered_raw = MODULE.canonical_bytes(tampered_intent) + b"\n"
        with self.assertRaisesRegex(RuntimeError, "intent hash mismatch"):
            MODULE.validate_persisted_producer_intent(
                tampered_raw,
                expected_sha256=hashlib.sha256(intent_raw).hexdigest(),
                run_id=RUN_ID,
                identity=parsed_identity,
                expected_write_canary=write_canary,
                expected_evidence_ref=EVIDENCE_REF,
                expected_target_repositories=targets,
            )
        noncanonical_raw = json.dumps(intent, indent=2, sort_keys=True).encode() + b"\n"
        with self.assertRaisesRegex(RuntimeError, "not canonical"):
            MODULE.validate_persisted_producer_intent(
                noncanonical_raw,
                expected_sha256=hashlib.sha256(noncanonical_raw).hexdigest(),
                run_id=RUN_ID,
                identity=parsed_identity,
                expected_write_canary=write_canary,
                expected_evidence_ref=EVIDENCE_REF,
                expected_target_repositories=targets,
            )
        duplicate_key_raw = intent_raw.replace(
            b'{"account":', b'{"account":"apol","account":', 1
        )
        with self.assertRaisesRegex(RuntimeError, "JSON is invalid"):
            MODULE.validate_persisted_producer_intent(
                duplicate_key_raw,
                expected_sha256=hashlib.sha256(duplicate_key_raw).hexdigest(),
                run_id=RUN_ID,
                identity=parsed_identity,
                expected_write_canary=write_canary,
                expected_evidence_ref=EVIDENCE_REF,
                expected_target_repositories=targets,
            )

    def test_evidence_lineage_requires_intent_between_identity_and_canary(self) -> None:
        authorization_revision = "a" * 40
        identity_revision = "b" * 40
        intent_revision = "c" * 40
        canary_revision = "d" * 40
        expected = [
            authorization_revision,
            identity_revision,
            intent_revision,
            canary_revision,
        ]
        MODULE.validate_evidence_commit_lineage(
            [types.SimpleNamespace(commit_id=value) for value in expected], expected
        )
        chain_of_three = [
            types.SimpleNamespace(commit_id=value)
            for value in (authorization_revision, identity_revision, canary_revision)
        ]
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            MODULE.validate_evidence_commit_lineage(chain_of_three, expected)
        omitted_intent = [
            types.SimpleNamespace(commit_id=value)
            for value in (
                authorization_revision,
                identity_revision,
                canary_revision,
                "e" * 40,
            )
        ]
        with self.assertRaisesRegex(RuntimeError, "lineage mismatch"):
            MODULE.validate_evidence_commit_lineage(omitted_intent, expected)

    def test_authorization_binds_distinct_provider_root_and_unchanged_identity_base(self) -> None:
        authorization, _, _, _ = signed_authorization()
        cases = (
            (
                lambda value: value["slots"][1].__setitem__(
                    "provider_root_revision",
                    value["slots"][1]["expected_parent_revision"],
                ),
                "must differ",
            ),
            (
                lambda value: value["slots"][1].__setitem__(
                    "provider_root_files",
                    [".gitattributes", "README.md"],
                ),
                "provider-root inventory",
            ),
            (
                lambda value: value["slots"][1]["provider_root_file_sha256"].__setitem__(
                    ".gitattributes",
                    "9" * 64,
                ),
                "changed provider-root bytes",
            ),
            (
                lambda value: value["slots"][1]["provider_root_file_size"].__setitem__(
                    ".gitattributes",
                    0,
                ),
                "provider-root sizes",
            ),
        )
        for mutate, message in cases:
            with self.subTest(message=message):
                tampered = copy.deepcopy(authorization)
                mutate(tampered)
                with mock.patch.object(
                    MODULE, "verify_ed25519_authorization", return_value="d" * 64
                ):
                    with self.assertRaisesRegex(RuntimeError, message):
                        MODULE.validate_training_authorization(
                            tampered,
                            authorization_sha256="c" * 64,
                            expected_authorization_sha256="c" * 64,
                            operation_sha256="1" * 64,
                            script_sha256="b" * 64,
                            adapter="public_osint",
                            phase="production",
                            seed=17,
                            run_id=RUN_ID,
                            hub_repo_id=OSINT_REPO,
                            current_job_id="training-job-001",
                        )

    def test_runtime_version_or_repo_composition_tampering_is_rejected(self) -> None:
        authorization, raw, public_b64, public_sha = signed_authorization()
        with (
            mock.patch.object(MODULE, "AUTHORIZATION_PUBLIC_KEY_SPKI_DER_B64", public_b64),
            mock.patch.object(
                MODULE, "AUTHORIZATION_PUBLIC_KEY_SPKI_DER_SHA256", public_sha
            ),
        ):
            for mutate in ("runtime", "repo"):
                tampered = copy.deepcopy(authorization)
                if mutate == "runtime":
                    tampered["runtime_versions"]["torch"] = "0.0.0"
                else:
                    tampered["slots"][1]["target_repo_id"] = PERSUASION_REPO
                with self.assertRaises(RuntimeError):
                    MODULE.validate_training_authorization(
                        tampered,
                        authorization_sha256=hashlib.sha256(raw).hexdigest(),
                        expected_authorization_sha256=hashlib.sha256(raw).hexdigest(),
                        operation_sha256="1" * 64,
                        script_sha256="b" * 64,
                        adapter="public_osint",
                        phase="production",
                        seed=17,
                        run_id=RUN_ID,
                        hub_repo_id=OSINT_REPO,
                        current_job_id="training-job-001",
                    )

    def test_remote_args_and_official_job_id_fail_closed(self) -> None:
        with self.assertRaises(SystemExit):
            MODULE.parse_args(
                [
                    "--adapter", "public_osint", "--phase", "production",
                    "--run-id", RUN_ID, "--seed", "17",
                ]
            )
        args = MODULE.parse_args(
            [
                "--adapter", "public_osint", "--phase", "production",
                "--run-id", RUN_ID, "--seed", "17", "--validate-only",
            ]
        )
        self.assertTrue(args.validate_only)
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "official JOB_ID"):
                MODULE.provider_job_id()

    def test_persisted_operation_is_canonical_hash_bound_and_at_issuer_gate(self) -> None:
        operation = {
            "schema": "era-part1b-hf-operation/v13",
            "operation_id": RUN_ID,
            "evidence_ref": EVIDENCE_REF,
            "status": "GO_FOR_AUTHORIZATION_ISSUER_ONLY",
        }
        raw = MODULE.canonical_bytes(operation) + b"\n"
        expected = hashlib.sha256(raw).hexdigest()
        self.assertEqual(
            MODULE.validate_persisted_operation(
                raw,
                expected_sha256=expected,
                run_id=RUN_ID,
                expected_evidence_ref=EVIDENCE_REF,
            ),
            operation,
        )
        with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
            MODULE.validate_persisted_operation(
                raw,
                expected_sha256="0" * 64,
                run_id=RUN_ID,
                expected_evidence_ref=EVIDENCE_REF,
            )
        noncanonical = b'{"status":"GO_FOR_AUTHORIZATION_ISSUER_ONLY", "schema":"era-part1b-hf-operation/v13","operation_id":"' + RUN_ID.encode() + b'"}\n'
        with self.assertRaisesRegex(RuntimeError, "canonical"):
            MODULE.validate_persisted_operation(
                noncanonical,
                expected_sha256=hashlib.sha256(noncanonical).hexdigest(),
                run_id=RUN_ID,
                expected_evidence_ref=EVIDENCE_REF,
            )
        for constant in (b"NaN", b"Infinity", b"-Infinity"):
            nonfinite = (
                b'{"operation_id":"'
                + RUN_ID.encode()
                + b'","schema":"era-part1b-hf-operation/v13","status":"GO_FOR_AUTHORIZATION_ISSUER_ONLY","value":'
                + constant
                + b"}\n"
            )
            with self.assertRaisesRegex(RuntimeError, "invalid"):
                MODULE.validate_persisted_operation(
                    nonfinite,
                    expected_sha256=hashlib.sha256(nonfinite).hexdigest(),
                    run_id=RUN_ID,
                    expected_evidence_ref=EVIDENCE_REF,
                )


class PersistenceAndMLContractTest(unittest.TestCase):
    @staticmethod
    def calls(function_name: str) -> list[ast.Call]:
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        result = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id == function_name:
                result.append(node)
            elif isinstance(node.func, ast.Attribute) and node.func.attr == function_name:
                result.append(node)
        return result

    @staticmethod
    def keyword(call: ast.Call, name: str) -> object:
        for keyword in call.keywords:
            if keyword.arg == name:
                return ast.literal_eval(keyword.value)
        raise AssertionError(f"missing keyword {name}")

    def test_qlora_and_sft_contract_is_exact(self) -> None:
        lora = self.calls("LoraConfig")
        self.assertEqual(len(lora), 1)
        self.assertEqual(
            self.keyword(lora[0], "target_modules"),
            ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        )
        sft = self.calls("SFTConfig")
        self.assertEqual(len(sft), 1)
        self.assertEqual(self.keyword(sft[0], "max_length"), 2048)
        self.assertEqual(self.keyword(sft[0], "eval_strategy"), "steps")
        self.assertEqual(self.keyword(sft[0], "eval_steps"), 50)
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('bnb_4bit_quant_type="nf4"', source)
        self.assertIn("bnb_4bit_compute_dtype=torch.bfloat16", source)
        self.assertIn("bnb_4bit_use_double_quant=True", source)
        self.assertIn('"max_steps": 300', source)
        protocol = json.loads((ROOT / "protocol.json").read_text(encoding="utf-8"))
        training = protocol["training"]
        self.assertEqual(training["eval_strategy"], "steps")
        self.assertEqual(training["eval_steps"], 50)
        self.assertEqual(
            training["final_eval_source"], "trainer.state.log_history@max_steps"
        )
        self.assertFalse(training["post_train_evaluate"])
        self.assertTrue(training["trainer_callback_owns_trackio_finish"])

    def test_reservation_precedes_ml_and_artifacts_use_one_atomic_commit(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        run_training = source[source.index("def run_training") :]
        self.assertLess(
            run_training.index("reservation_commit = api.create_commit("),
            run_training.index("    import torch"),
        )
        self.assertLess(
            run_training.index("validate_persisted_operation("),
            run_training.index("reservation_commit = api.create_commit("),
        )
        self.assertLess(
            run_training.index("authorization evidence commit file tree mismatch"),
            run_training.index("reservation_commit = api.create_commit("),
        )
        self.assertIn('authorization_evidence["operation_path"]', run_training)
        self.assertNotIn("upload_folder(", source)
        self.assertIn("parent_commit=expected_parent_revision", source)
        self.assertIn("parent_commit=reservation_revision", source)
        self.assertIn("parent_commit=artifact_revision", source)
        self.assertIn("for relative in sorted(artifact_commit_inventory)", source)
        self.assertIn("RESERVED_NO_RETRY", source)

    def test_trackio_directory_is_bound_before_any_trackio_import(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        run_training = source[source.index("def run_training") :]
        self.assertLess(
            run_training.index('os.environ["TRACKIO_DIR"]'),
            run_training.index("    import trackio"),
        )
        self.assertLess(
            run_training.index('os.environ["TRACKIO_DIR"]'),
            run_training.index("    from trl import SFTConfig, SFTTrainer"),
        )
        self.assertIn("Trackio did not persist under the Hub artifact prefix", run_training)

    def test_post_train_metrics_do_not_reenter_a_finished_trackio_run(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        run_training = source[source.index("def run_training") :]
        after_train = run_training[run_training.index("train_result = trainer.train()") :]
        self.assertNotIn("trainer.evaluate()", after_train)
        self.assertNotIn("trackio.finish()", after_train)
        self.assertIn("eval_metrics = final_eval_metrics(", after_train)
        self.assertIn("trainer.state.log_history", after_train)
        self.assertIn("trackio.context_vars.current_run.get() is not None", after_train)

    def test_final_eval_metrics_requires_one_finite_final_step_record(self) -> None:
        history = [
            {"loss": 0.2, "step": 295},
            {
                "eval_loss": 0.1,
                "eval_runtime": 2.5,
                "eval_mean_token_accuracy": 0.9,
                "epoch": 2.0,
                "step": 300,
            },
            {"train_runtime": 10.0, "step": 300},
        ]
        self.assertEqual(
            MODULE.final_eval_metrics(history, expected_global_step=300),
            {
                "eval_loss": 0.1,
                "eval_runtime": 2.5,
                "eval_mean_token_accuracy": 0.9,
            },
        )
        invalid_cases = (
            (history, 299, "exactly one evaluation record"),
            (
                history + [{"eval_loss": 0.09, "step": 300}],
                300,
                "exactly one evaluation record",
            ),
            ([{"eval_runtime": 2.5, "step": 300}], 300, "no eval_loss"),
            ([{"eval_loss": float("nan"), "step": 300}], 300, "non-finite"),
            ([{"eval_loss": "0.1", "step": 300}], 300, "non-numeric"),
        )
        for candidate, expected_step, message in invalid_cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(RuntimeError, message):
                    MODULE.final_eval_metrics(
                        candidate, expected_global_step=expected_step
                    )

    def test_private_repo_exact_tree_lineage_readback_and_remote_reload(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for required in (
            "provider_root_info.private",
            "provider_root_files != authorization_evidence",
            "verify_remote_sizes(",
            "initial_info.private",
            "initial_info.sha != expected_parent_revision",
            "initial_files != authorization_evidence",
            "require_exact_hub_commit_sequence(",
            "verify_remote_hashes(",
            "require_private_hub_head(",
            "PeftModel.from_pretrained(",
            "post-Hub adapter reload canary mismatch",
        ):
            self.assertIn(required, source)
        self.assertGreaterEqual(source.count("require_private_hub_head("), 7)

    def test_physical_history_grows_from_two_to_exactly_five_commits(self) -> None:
        expected_sequences = [
            ["expected_parent_revision", "provider_root_revision"],
            ["reservation_revision", "expected_parent_revision", "provider_root_revision"],
            [
                "artifact_revision",
                "reservation_revision",
                "expected_parent_revision",
                "provider_root_revision",
            ],
            [
                "terminal_revision",
                "artifact_revision",
                "reservation_revision",
                "expected_parent_revision",
                "provider_root_revision",
            ],
        ]
        observed_sequences: list[list[str]] = []
        for call in self.calls("require_exact_hub_commit_sequence"):
            for keyword in call.keywords:
                if keyword.arg != "expected_newest_to_oldest":
                    continue
                self.assertIsInstance(keyword.value, ast.List)
                observed_sequences.append(
                    [
                        element.id
                        for element in keyword.value.elts
                        if isinstance(element, ast.Name)
                    ]
                )
        self.assertEqual(observed_sequences, expected_sequences)

    def test_terminal_head_rehashes_artifacts_and_rejects_byte_substitution(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        terminal_section = source[source.index("expected_final_files =") :]
        self.assertIn("**artifact_commit_sha256", terminal_section)
        with tempfile.TemporaryDirectory() as directory:
            tampered = Path(directory) / "adapter_model.safetensors"
            tampered.write_bytes(b"different adapter bytes")
            expected = hashlib.sha256(b"authorized adapter bytes").hexdigest()
            fake_hub = types.SimpleNamespace(
                hf_hub_download=lambda **_: str(tampered),
            )
            with mock.patch.dict(sys.modules, {"huggingface_hub": fake_hub}):
                with self.assertRaisesRegex(RuntimeError, "remote lineage hash mismatch"):
                    MODULE.verify_remote_hashes(
                        repo_id=PERSUASION_REPO,
                        revision="a" * 40,
                        expected_sha256={"adapter_model.safetensors": expected},
                        token="not-a-real-token",
                    )
                with self.assertRaisesRegex(RuntimeError, "remote lineage size mismatch"):
                    MODULE.verify_remote_sizes(
                        repo_id=PERSUASION_REPO,
                        revision="a" * 40,
                        expected_bytes={"adapter_model.safetensors": 1},
                        token="not-a-real-token",
                    )

    def test_no_bucket_combination_or_signing_secret_in_runner(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("/mnt/", source)
        self.assertNotIn("BUCKET_", source)
        self.assertNotIn("AUTH_PRIVATE", source)
        self.assertNotIn("HF_WRITE_TOKEN", source)
        self.assertIn('os.environ.get("HF_TOKEN")', source)
        protocol = json.loads((ROOT / "protocol.json").read_text(encoding="utf-8"))
        self.assertTrue(protocol["private_hub_persistence"]["one_adapter_per_repo"])
        self.assertFalse(protocol["private_hub_persistence"]["combined_adapter"])
        self.assertEqual(
            protocol["private_hub_persistence"]["provider_root_files"],
            MODULE.PROVIDER_ROOT_FILES,
        )
        self.assertTrue(
            protocol["private_hub_persistence"]["provider_root_file_size_required"]
        )
        self.assertEqual(
            protocol["private_hub_persistence"]["controlled_identity_files"],
            MODULE.CONTROLLED_IDENTITY_FILES,
        )
        self.assertEqual(
            protocol["private_hub_persistence"]["physical_commit_count_before_reservation"],
            2,
        )
        self.assertEqual(
            protocol["private_hub_persistence"]["physical_commit_count_after_terminal"],
            5,
        )
        self.assertEqual(
            set(protocol["private_hub_persistence"]["model_payload_exact_allowlist"]),
            MODULE.EXPECTED_MODEL_ARTIFACT_FILES,
        )
        self.assertEqual(
            protocol["private_hub_persistence"]["adapter_model_max_bytes"],
            MODULE.MODEL_ARTIFACT_MAX_BYTES["adapter_model.safetensors"],
        )
        self.assertEqual(
            protocol["private_hub_persistence"][
                "adapter_safetensors_expected_tensor_count"
            ],
            MODULE.EXPECTED_LORA_TENSOR_COUNT,
        )
        self.assertEqual(
            protocol["private_hub_persistence"][
                "adapter_safetensors_expected_dtype"
            ],
            "F32",
        )
        self.assertTrue(
            protocol["private_hub_persistence"][
                "adapter_safetensors_exact_qwen3_lora_manifest"
            ]
        )
        self.assertTrue(
            protocol["private_hub_persistence"][
                "adapter_config_requires_base_model_revision"
            ]
        )
        self.assertEqual(
            protocol["private_hub_persistence"]["total_artifact_upload_max_bytes"],
            MODULE.MAX_ARTIFACT_UPLOAD_BYTES,
        )
        self.assertTrue(
            protocol["private_hub_persistence"]["unsafe_serialized_artifacts_forbidden"]
        )
        self.assertTrue(
            protocol["private_hub_persistence"][
                "tokenizer_reloaded_from_pinned_base_revision"
            ]
        )
        self.assertEqual(
            protocol["refusal_direction_arm"]["status"],
            "DIAGNOSTIC_NO_GO_FOR_DEPLOYMENT",
        )

    def test_protocol_hash_and_identical_dependency_locks(self) -> None:
        protocol_hash = hashlib.sha256((ROOT / "protocol.json").read_bytes()).hexdigest()
        self.assertEqual(protocol_hash, MODULE.EXPECTED_PROTOCOL_SHA256)
        self.assertEqual(
            hashlib.sha256(RUNTIME_REUSE.read_bytes()).hexdigest(),
            MODULE.EXPECTED_RUNTIME_REUSE_SHA256,
        )
        for relative in ("requirements.lock", "runtime/Dockerfile", ".dockerignore"):
            self.assertEqual(
                (ROOT / relative).read_bytes(),
                (V10_ROOT / relative).read_bytes(),
                relative,
            )
        locked = {
            line for line in (ROOT / "requirements.lock").read_text().splitlines() if line
        }
        for path in (SCRIPT, ML_PREFLIGHT):
            source = path.read_text(encoding="utf-8")
            for requirement in locked:
                self.assertIn(f'"{requirement}"', source)
        self.assertEqual(
            locked,
            {f"{name}=={version}" for name, version in MODULE.EXPECTED_RUNTIME_VERSIONS.items()},
        )

    def test_documented_v13_identity_and_v12_quarantine_are_exact(self) -> None:
        source = README.read_text(encoding="utf-8")
        run_id = "era-p1b-v13-20260825t193000z"
        nonce = "f47eb8f766aae2a3365c2ef045664f01"
        quarantine = (
            '{"path":"runs/era-p1b-v12-20260825t182000z/control/quarantine.json",'
            '"sha256":"e2e5761d1e7d836c0dc13b2a961362a8e679a57683c0cc24a118611245664ada",'
            '"size_bytes":8609}'
        )
        self.assertIn(f"`{run_id}`", source)
        self.assertIn(f"`{nonce}`", source)
        self.assertIn(
            f"`apol/{run_id}-transparent-persuasion-qwen3-8b-lora`", source
        )
        self.assertIn(f"`apol/{run_id}-public-osint-qwen3-8b-lora`", source)
        self.assertIn(quarantine, source)
        self.assertNotIn(f"runs/{run_id}/control/quarantine.json", source)

    def test_public_v13_and_consumed_private_v13_schemas_are_exact(self) -> None:
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (SCRIPT, ML_PREFLIGHT, ROOT / "protocol.json")
        )
        public_schemas = {
            "era-part1b-benign-adapters-protocol/v13",
            "era-part1b-benign-canary/v13",
            "era-part1b-benign-dataset-manifest/v13",
            "era-part1b-benign-job-terminal/v13",
            "era-part1b-benign-terminal/v13",
            "era-part1b-benign-training-receipt/v13",
            "era-part1b-hf-operation/v13",
            "era-part1b-ml-stack-preflight/v13",
            "era-part1b-training-authorization/v13",
            "era-part1b-training-slot-reservation/v13",
        }
        private_schemas = {
            "era-part1b-hub-identity/v13",
            "era-part1b-hub-producer-intent/v13",
        }
        for schema in public_schemas | private_schemas:
            self.assertIn(schema, source)
        self.assertNotRegex(source, r"era-part1b-[a-z-]+/v[1-9](?:\D|$)")
        self.assertNotRegex(
            source,
            r"era-part1b-hub-(?:identity|producer-intent)/v[1-9](?:\D|$)",
        )
        self.assertNotIn("v6_quarantine", source)
        self.assertNotIn("v13_quarantine", source)
        self.assertNotIn("v8_quarantine", source)

    def test_authoritative_public_artifacts_are_utf8_lf(self) -> None:
        authoritative = (
            SCRIPT,
            ML_PREFLIGHT,
            DOCKERIGNORE,
            ROOT / "protocol.json",
            ROOT / "requirements.lock",
            RUNTIME_REUSE,
            RUNTIME_DOCKERFILE,
            Path(__file__).resolve(),
        )
        self.assertEqual(len(authoritative), 8)
        for path in authoritative:
            raw = path.read_bytes()
            self.assertNotIn(b"\r", raw, str(path))
            self.assertTrue(raw.endswith(b"\n"), str(path))
            self.assertEqual(raw.decode("utf-8").encode("utf-8"), raw, str(path))

    def test_runtime_is_content_addressed_dependency_only_and_launcher_compatible(self) -> None:
        source = RUNTIME_DOCKERFILE.read_text(encoding="utf-8")
        self.assertIn(
            "FROM ghcr.io/astral-sh/uv:python3.12-bookworm@sha256:"
            "9aa60c50016c0485636ab9a830246a6ef3399aa4a8bab3d17ef4a2358fba2ca7",
            source,
        )
        self.assertIn("uv venv --python python3.12 /opt/era-venv", source)
        self.assertIn("--python /opt/era-venv/bin/python", source)
        self.assertIn("/opt/era-venv/bin/python --version", source)
        for command in ("base64", "cut", "gzip", "sha256sum"):
            self.assertIn(f"command -v {command}", source)
        self.assertNotIn("COPY jobs", source)
        self.assertNotIn("train_lora.py", source)
        self.assertNotIn("ml_stack_preflight.py", source)
        self.assertIn("ENTRYPOINT []", source)
        self.assertIn('CMD ["/opt/era-venv/bin/python", "--version"]', source)
        self.assertEqual(
            DOCKERIGNORE.read_text(encoding="utf-8").splitlines(),
            ["**", "!requirements.lock", "!runtime/", "!runtime/Dockerfile"],
        )

    def test_runtime_reuse_is_exact_and_no_v13_image_workflow_exists(self) -> None:
        self.assertFalse(V13_RUNTIME_WORKFLOW.exists())
        reuse = json.loads(RUNTIME_REUSE.read_text(encoding="utf-8"))
        self.assertEqual(reuse["schema"], "era-part1b-runtime-reuse/v13")
        self.assertEqual(reuse["status"], "REUSE_AUTHORIZED")
        self.assertEqual(reuse["image"]["reference"], MODULE.EXPECTED_RUNTIME_IMAGE)
        self.assertTrue(reuse["image"]["dependency_only"])
        self.assertFalse(reuse["image"]["runner_embedded"])
        self.assertFalse(reuse["image"]["new_v13_build_required"])
        self.assertFalse(reuse["image"]["new_v13_smoke_authorized"])
        self.assertEqual(reuse["smoke"]["job_id"], "6a8dc027984507d9db4e435c")
        self.assertEqual(reuse["smoke"]["stage"], "COMPLETED")
        self.assertEqual(reuse["smoke"]["retry"], 0)
        ci_source = CI_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09",
            ci_source,
        )
        self.assertIn(
            "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
            ci_source,
        )
        protocol = json.loads((ROOT / "protocol.json").read_text(encoding="utf-8"))
        self.assertEqual(
            protocol["training"]["runtime"],
            {
                "image_repository": (
                    "ghcr.io/apolmig/agencytransfer-part1b-benign-v10-runtime"
                ),
                "image_reference": MODULE.EXPECTED_RUNTIME_IMAGE,
                "reuse_manifest_path": "part1b/benign_adapters_v13/runtime-reuse.json",
                "reuse_manifest_sha256": MODULE.EXPECTED_RUNTIME_REUSE_SHA256,
                "requirements_lock_sha256": MODULE.EXPECTED_REQUIREMENTS_LOCK_SHA256,
                "reused_from_public_commit": "c8c2ba081ea2e5043da820f3d633c2fcb9bca3c1",
                "new_v13_build_required": False,
                "new_v13_smoke_authorized": False,
                "manifest_digest_required": True,
                "dependency_only": True,
                "runner_embedded": False,
                "launcher_materializes_hash_bound_runner": True,
                "python_path": "/opt/era-venv/bin/python",
            },
        )
        self.assertEqual(protocol["training"]["raw_job_timeout_seconds"], 5400)
        self.assertEqual(
            protocol["private_evidence_persistence"][
                "initial_write_required_permissions"
            ],
            ["repo.write", "discussion.write"],
        )
        self.assertIn(
            "same_job_token_repo_write_and_discussion_write_pre_mutation_gate",
            protocol["technical_go"]["requires"],
        )
        budget = protocol["execution_budget"]
        self.assertEqual(
            budget,
            {
                "currency": "USD",
                "micro_usd_per_usd": 1000000,
                "program_cap_micro_usd": 6000000,
                "conservative_prior_micro_usd": 3224312,
                "prior_jobs": 27,
                "fresh_v13_allowance_micro_usd": 2435190,
                "worst_case_cumulative_micro_usd": 5659502,
                "remaining_margin_micro_usd": 340498,
                "cpu_control_jobs_max": 7,
                "cpu_timeout_minutes_each_max": 30,
                "cpu_billed_minute_micro_usd_max": 167,
                "l4x1_training_jobs_max": 2,
                "l4x1_timeout_minutes_each_max": 90,
                "l4x1_billed_minute_micro_usd_max": 13334,
                "retries": 0,
            },
        )
        self.assertEqual(
            budget["fresh_v13_allowance_micro_usd"],
            budget["cpu_control_jobs_max"]
            * budget["cpu_timeout_minutes_each_max"]
            * budget["cpu_billed_minute_micro_usd_max"]
            + budget["l4x1_training_jobs_max"]
            * budget["l4x1_timeout_minutes_each_max"]
            * budget["l4x1_billed_minute_micro_usd_max"],
        )
        self.assertEqual(
            budget["worst_case_cumulative_micro_usd"],
            budget["conservative_prior_micro_usd"]
            + budget["fresh_v13_allowance_micro_usd"],
        )
        self.assertEqual(
            budget["remaining_margin_micro_usd"],
            budget["program_cap_micro_usd"]
            - budget["worst_case_cumulative_micro_usd"],
        )

    def test_preflight_binds_trainer_owned_trackio_lifecycle(self) -> None:
        valid = ML_MODULE.validate_trackio_lifecycle_sources(
            callback_on_train_end=(
                "if not self._initialized:\n    return\nself._trackio.finish()"
            ),
            callback_on_log=(
                "if not self._initialized:\n    self.setup(args, state, model)\n"
                "self._trackio.log(logs)"
            ),
            trackio_finish=(
                "run = context_vars.current_run.get()\n"
                "context_vars.current_run.set(None)"
            ),
            trackio_log=(
                "run = context_vars.current_run.get()\n"
                'raise RuntimeError("Call trackio.init() before trackio.log().")'
            ),
        )
        self.assertTrue(valid["trainer_owns_finish"])
        self.assertTrue(valid["post_train_callback_forbidden"])
        with self.assertRaisesRegex(RuntimeError, "callback on_train_end"):
            ML_MODULE.validate_trackio_lifecycle_sources(
                callback_on_train_end="pass",
                callback_on_log=(
                    "if not self._initialized:\n    self.setup(args, state, model)\n"
                    "self._trackio.log(logs)"
                ),
                trackio_finish=(
                    "run = context_vars.current_run.get()\n"
                    "context_vars.current_run.set(None)"
                ),
                trackio_log=(
                    "run = context_vars.current_run.get()\n"
                    'raise RuntimeError("Call trackio.init() before trackio.log().")'
                ),
            )
        source = ML_PREFLIGHT.read_text(encoding="utf-8")
        self.assertIn('"trackio_lifecycle": trackio_lifecycle', source)
        self.assertIn('report_to="trackio"', source)
        self.assertNotIn('report_to="none"', source)

    def test_v13_signing_key_is_exact_and_has_no_old_key_fallback(self) -> None:
        expected_key_id = "era-part1b-v13-ed25519-20260825"
        expected_public_b64 = (
            "MCowBQYDK2VwAyEAukFGaCsN2p1AfHbYvX+hQfPUQbNFdoh2SjiajW3Xk0s="
        )
        expected_public_sha256 = (
            "6b4498671d5920c5129787b90a0e8cf0ca0af021fd69ac9fbdf9bdb1a6607158"
        )
        old_key_material = (
            "era-part1b-v3-ed25519-20260814",
            "MCowBQYDK2VwAyEAeW8JSPbwuS8bi70ezdax5XZu5kBqYM3G9KCTaTN8zjA=",
            "4329b50d6e1d4b093018f60e4bd6b1a571f01b4dc6260a31bd256d17573cdbce",
            "era-part1b-v4-ed25519-20260814",
            "MCowBQYDK2VwAyEAt6Z/Q+8pKbYCLbeLH+Ilw9D7V6k4iIKtgGhU4fl1hsg=",
            "09f6fe3693f80663d6cb603eb8acf6d74a18a52cf2f157775217a131a5ae0ecb",
            "era-part1b-v6-ed25519-20260824",
            "MCowBQYDK2VwAyEAgQ1+i9jyisHFNwYpoPh68e9swh1lPXcJRVzkSOqRoyg=",
            "630b86913170ffad4ce274d3f3f3958df150266821adea7b81a22bf6b2296dfa",
            "era-part1b-v7-ed25519-20260824",
            "MCowBQYDK2VwAyEADehmAFyNnRS6c941dMx8mDvec/E3y7YQuKIxnylIGhU=",
            "f650510b9e62da614293a43e5b5c5dfef563f8b5ba9a81e126de2a16b9914ff2",
            "era-part1b-v8-ed25519-20260825",
            "MCowBQYDK2VwAyEA/5pMybVkcePNUNSPw1VxgaAt3gqC5M4yzsMUMUKPv20=",
            "9f8c0030e95628ab81721fb92316ad27763fe1436b34b7b21d6eb4db697dfa5a",
            "era-part1b-v9-ed25519-20260825",
            "MCowBQYDK2VwAyEAC7ALZyf3RqIH5UP9M8pXryUjNq//Oo0rPb/5TjgC5QM=",
            "d1bf2104f07b00d1a7a64df630de88f7969a069edf0f8b56f36ed9dae2c64013",
            "era-part1b-v10-ed25519-20260825",
            "MCowBQYDK2VwAyEAoX+4MXP85kxoydzFZN3dk+qFcWTL+W6IE4HWI/yUZrE=",
            "83090f11d5822ca4f1b9a569824dfa377a8818cb80bb229427bd120c927615ec",
            "era-part1b-v11-ed25519-20260825",
            "MCowBQYDK2VwAyEAd3QI5REl5a+wiMYZKy1ioRTynASsTR6M6ExF8TD+UFk=",
            "34d786014440935c16f57b2f1ad9e8c6b367199ccbb5ecd6ab0a8335a88a9494",
            "era-part1b-v12-ed25519-20260825",
            "MCowBQYDK2VwAyEAO3Nwuaye+0lXfakOqpSjeNqGAnHvAJVqbr7hroUuLRY=",
            "0c31c7db1d655ea3a74b3bf1bd0026067611dd55072e69640e81b18643c9cd9e",
        )
        protocol = json.loads((ROOT / "protocol.json").read_text(encoding="utf-8"))
        self.assertEqual(MODULE.AUTHORIZATION_KEY_ID, expected_key_id)
        self.assertEqual(
            MODULE.AUTHORIZATION_PUBLIC_KEY_SPKI_DER_B64, expected_public_b64
        )
        self.assertEqual(
            MODULE.AUTHORIZATION_PUBLIC_KEY_SPKI_DER_SHA256,
            expected_public_sha256,
        )
        self.assertEqual(
            ML_MODULE.AUTHORIZATION_PUBLIC_KEY_SPKI_DER_B64, expected_public_b64
        )
        self.assertEqual(
            ML_MODULE.AUTHORIZATION_PUBLIC_KEY_SPKI_DER_SHA256,
            expected_public_sha256,
        )
        self.assertEqual(protocol["authorization"]["key_id"], expected_key_id)
        self.assertEqual(
            protocol["authorization"]["public_key_spki_der_b64"],
            expected_public_b64,
        )
        self.assertEqual(
            protocol["authorization"]["public_key_spki_der_sha256"],
            expected_public_sha256,
        )
        self.assertEqual(
            protocol["authorization"]["prior_run_quarantine"],
            {
                "path": MODULE.PRIOR_RUN_QUARANTINE_PATH,
                "sha256": MODULE.PRIOR_RUN_QUARANTINE_SHA256,
                "size_bytes": MODULE.PRIOR_RUN_QUARANTINE_SIZE_BYTES,
            },
        )
        public_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (SCRIPT, ML_PREFLIGHT, ROOT / "protocol.json")
        )
        for forbidden in old_key_material:
            self.assertNotIn(forbidden, public_source)

    def test_preflight_is_weight_free_and_checks_crypto_hub_and_only_8b(self) -> None:
        source = ML_PREFLIGHT.read_text(encoding="utf-8")
        self.assertNotIn("AutoModelForCausalLM", source)
        self.assertNotIn("SFTTrainer", source)
        self.assertNotIn("Qwen3-1.7B", source)
        self.assertIn("Qwen/Qwen3-8B", source)
        self.assertIn("load_der_public_key", source)
        self.assertIn("HfApi.create_commit", source)
        self.assertIn('"create_pr"', source)
        self.assertIn('"writes_performed": False', source)

    def test_lora_artifact_allowlist_rejects_pickles_full_weights_and_oversize(self) -> None:
        adapter_config = {
            "base_model_name_or_path": MODULE.MODELS["production"]["id"],
            "revision": MODULE.MODELS["production"]["revision"],
            "peft_type": "LORA",
            "task_type": "CAUSAL_LM",
            "r": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05,
            "bias": "none",
            "inference_mode": True,
            "init_lora_weights": True,
            "fan_in_fan_out": False,
            "use_rslora": False,
            "use_dora": False,
            "use_qalora": False,
            "lora_bias": False,
            "modules_to_save": None,
            "trainable_token_indices": None,
            "target_parameters": None,
            "layers_to_transform": None,
            "layer_replication": None,
            "exclude_modules": None,
            "rank_pattern": {},
            "alpha_pattern": {},
            "loftq_config": {},
            "target_modules": [
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ],
        }

        def valid_tree(root: Path) -> Path:
            evidence = root / "runs" / RUN_ID / "transparent_persuasion" / "seed-17"
            evidence.mkdir(parents=True)
            (evidence / "receipt.json").write_text("{}\n", encoding="utf-8")
            (root / "README.md").write_text("adapter card\n", encoding="utf-8")
            (root / "adapter_config.json").write_text(
                json.dumps(adapter_config), encoding="utf-8"
            )
            (root / "adapter_model.safetensors").write_bytes(b"safe-adapter")
            return evidence

        manifest_patch = mock.patch.object(
            MODULE,
            "validate_lora_safetensors_manifest",
            return_value={"tensor_count": 504, "data_bytes": 174_587_904, "dtype": "F32"},
        )
        manifest_patch.start()
        self.addCleanup(manifest_patch.stop)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = valid_tree(root)
            observed = MODULE.validate_lora_only_artifacts(
                root,
                evidence,
                expected_base_model_id=MODULE.MODELS["production"]["id"],
                expected_base_model_revision=MODULE.MODELS["production"]["revision"],
            )
            self.assertEqual(set(observed), MODULE.EXPECTED_MODEL_ARTIFACT_FILES)

            for forbidden in (
                "training_args.bin",
                "optimizer.pt",
                "model.safetensors",
                "pytorch_model-00001-of-00002.bin",
                "tokenizer.json",
                "chat_template.jinja",
            ):
                path = root / forbidden
                path.write_bytes(b"forbidden")
                with self.assertRaisesRegex(
                    RuntimeError, "forbidden|unexpected model artifact"
                ):
                    MODULE.validate_lora_only_artifacts(
                        root,
                        evidence,
                        expected_base_model_id=MODULE.MODELS["production"]["id"],
                        expected_base_model_revision=MODULE.MODELS["production"][
                            "revision"
                        ],
                    )
                path.unlink()

            checkpoint = root / "checkpoint-1" / "trainer_state.json"
            checkpoint.parent.mkdir()
            checkpoint.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "unexpected model artifact"):
                MODULE.validate_lora_only_artifacts(
                    root,
                    evidence,
                    expected_base_model_id=MODULE.MODELS["production"]["id"],
                    expected_base_model_revision=MODULE.MODELS["production"]["revision"],
                )
            checkpoint.unlink()

            config_path = root / "adapter_config.json"
            for field, drift_value, message in (
                ("revision", "main", "base-model revision"),
                ("inference_mode", False, "inference_mode"),
                ("modules_to_save", ["lm_head"], "modules_to_save"),
                ("rank_pattern", {"q_proj": 8}, "rank_pattern"),
            ):
                drifted = dict(adapter_config)
                drifted[field] = drift_value
                config_path.write_text(json.dumps(drifted), encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, message):
                    MODULE.validate_lora_only_artifacts(
                        root,
                        evidence,
                        expected_base_model_id=MODULE.MODELS["production"]["id"],
                        expected_base_model_revision=MODULE.MODELS["production"][
                            "revision"
                        ],
                    )
            config_path.write_text(json.dumps(adapter_config), encoding="utf-8")

            evidence_pickle = evidence / "trackio" / "state.pkl"
            evidence_pickle.parent.mkdir()
            evidence_pickle.write_bytes(b"forbidden")
            with self.assertRaisesRegex(RuntimeError, "unsafe serialized artifact"):
                MODULE.validate_lora_only_artifacts(
                    root,
                    evidence,
                    expected_base_model_id=MODULE.MODELS["production"]["id"],
                    expected_base_model_revision=MODULE.MODELS["production"]["revision"],
                )
            evidence_pickle.unlink()

            with mock.patch.dict(
                MODULE.MODEL_ARTIFACT_MAX_BYTES,
                {"adapter_model.safetensors": 4},
            ):
                with self.assertRaisesRegex(RuntimeError, "exceeds byte limit"):
                    MODULE.validate_lora_only_artifacts(
                        root,
                        evidence,
                        expected_base_model_id=MODULE.MODELS["production"]["id"],
                        expected_base_model_revision=MODULE.MODELS["production"][
                            "revision"
                        ],
                    )

    def test_qwen3_lora_safetensors_contract_is_exact(self) -> None:
        specs = MODULE.expected_qwen3_lora_tensor_specs()
        self.assertEqual(len(specs), MODULE.EXPECTED_LORA_TENSOR_COUNT)
        self.assertEqual(
            sum(math.prod(shape) * 4 for dtype, shape in specs.values()),
            MODULE.EXPECTED_LORA_DATA_BYTES,
        )
        self.assertEqual(
            specs[
                "base_model.model.model.layers.0.self_attn.k_proj.lora_B.weight"
            ],
            ("F32", (1024, 16)),
        )
        self.assertEqual(
            specs["base_model.model.model.layers.35.mlp.down_proj.lora_A.weight"],
            ("F32", (16, 12288)),
        )

    def test_safetensors_header_rejects_manifest_shape_dtype_and_metadata_drift(self) -> None:
        expected = {
            "adapter.layer.lora_A.weight": ("F32", (2, 3)),
            "adapter.layer.lora_B.weight": ("F32", (4, 2)),
        }

        def write_fixture(
            path: Path,
            specs: dict[str, tuple[str, tuple[int, ...]]],
            *,
            metadata: dict[str, str] | None = None,
        ) -> None:
            widths = {"F32": 4, "F16": 2}
            cursor = 0
            header: dict[str, object] = {"__metadata__": metadata or {"format": "pt"}}
            for name, (dtype, shape) in sorted(specs.items()):
                size = math.prod(shape) * widths[dtype]
                header[name] = {
                    "dtype": dtype,
                    "shape": list(shape),
                    "data_offsets": [cursor, cursor + size],
                }
                cursor += size
            header_bytes = json.dumps(
                header, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            header_bytes += b" " * (-len(header_bytes) % 8)
            path.write_bytes(
                len(header_bytes).to_bytes(8, "little")
                + header_bytes
                + b"\0" * cursor
            )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "adapter_model.safetensors"
            write_fixture(path, expected)
            summary = MODULE.validate_lora_safetensors_manifest(
                path, expected_specs=expected
            )
            self.assertEqual(summary["tensor_count"], 2)
            self.assertEqual(summary["data_bytes"], 56)

            drift_cases = (
                (
                    {**expected, "base_model.weight": ("F32", (1, 1))},
                    {"format": "pt"},
                    "tensor-key manifest",
                ),
                (
                    {"adapter.layer.lora_A.weight": ("F32", (2, 3))},
                    {"format": "pt"},
                    "tensor-key manifest",
                ),
                (
                    {
                        "adapter.layer.lora_A.weight": ("F16", (2, 3)),
                        "adapter.layer.lora_B.weight": ("F32", (4, 2)),
                    },
                    {"format": "pt"},
                    "dtype mismatch",
                ),
                (
                    {
                        "adapter.layer.lora_A.weight": ("F32", (3, 2)),
                        "adapter.layer.lora_B.weight": ("F32", (4, 2)),
                    },
                    {"format": "pt"},
                    "shape mismatch",
                ),
                (expected, {"format": "numpy"}, "metadata mismatch"),
            )
            for written_specs, metadata, message in drift_cases:
                write_fixture(path, written_specs, metadata=metadata)
                with self.assertRaisesRegex(RuntimeError, message):
                    MODULE.validate_lora_safetensors_manifest(
                        path, expected_specs=expected
                    )

    def test_training_uses_direct_peft_safe_save_and_pinned_base_tokenizer(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        run_training = source[source.index("def run_training") :]
        self.assertNotIn("trainer.save_model(", run_training)
        self.assertNotIn("tokenizer.save_pretrained(", run_training)
        self.assertIn(
            "trainer.model.save_pretrained(str(artifact_root), safe_serialization=True)",
            run_training,
        )
        self.assertGreaterEqual(run_training.count("validate_lora_only_artifacts("), 2)
        self.assertIn('model_contract["revision"], use_fast=True', run_training)
        self.assertIn('revision=model_contract["revision"]', run_training)
        card = MODULE.adapter_card(
            "public_osint", "production", MODULE.MODELS["production"], RUN_ID
        )
        self.assertIn(MODULE.MODELS["production"]["revision"], card)

    def test_exact_commit_sequence_helper_uses_real_hub124_surface_and_rejects_sequence_drift(self) -> None:
        from huggingface_hub.hf_api import GitCommitInfo

        class FakeApi:
            def __init__(self, commits: list[object]) -> None:
                self.commits = commits

            def list_repo_commits(self, **_: object) -> list[object]:
                return self.commits

        def commit(commit_id: str) -> GitCommitInfo:
            return GitCommitInfo(
                commit_id=commit_id,
                authors=["apol"],
                created_at=dt.datetime(2026, 8, 14, tzinfo=dt.timezone.utc),
                title="test",
                message="",
                formatted_title=None,
                formatted_message=None,
            )

        good = [commit("a" * 40), commit("b" * 40)]
        MODULE.require_exact_hub_commit_sequence(
            FakeApi(good),
            repo_id=PERSUASION_REPO,
            revision="a" * 40,
            expected_newest_to_oldest=["a" * 40, "b" * 40],
            token="not-a-real-token",
        )
        bad = good + [commit("c" * 40)]
        with self.assertRaisesRegex(RuntimeError, "commit count"):
            MODULE.require_exact_hub_commit_sequence(
                FakeApi(bad),
                repo_id=PERSUASION_REPO,
                revision="a" * 40,
                expected_newest_to_oldest=["a" * 40, "b" * 40],
                token="not-a-real-token",
            )
        with self.assertRaisesRegex(RuntimeError, "missing commit_id"):
            MODULE.require_exact_hub_commit_sequence(
                FakeApi([object(), commit("b" * 40)]),
                repo_id=PERSUASION_REPO,
                revision="a" * 40,
                expected_newest_to_oldest=["a" * 40, "b" * 40],
                token="not-a-real-token",
            )
        with self.assertRaisesRegex(RuntimeError, "sequence"):
            MODULE.require_exact_hub_commit_sequence(
                FakeApi(list(reversed(good))),
                repo_id=PERSUASION_REPO,
                revision="a" * 40,
                expected_newest_to_oldest=["a" * 40, "b" * 40],
                token="not-a-real-token",
            )

    def test_private_head_helper_rejects_visibility_flip_or_moved_head(self) -> None:
        class FakeApi:
            def __init__(self, private: bool, revision: str) -> None:
                self.info = types.SimpleNamespace(private=private, sha=revision)

            def repo_info(self, **_: object) -> object:
                return self.info

        expected = "a" * 40
        MODULE.require_private_hub_head(
            FakeApi(True, expected),
            repo_id=PERSUASION_REPO,
            expected_revision=expected,
            token="not-a-real-token",
        )
        with self.assertRaisesRegex(RuntimeError, "visibility"):
            MODULE.require_private_hub_head(
                FakeApi(False, expected),
                repo_id=PERSUASION_REPO,
                expected_revision=expected,
                token="not-a-real-token",
            )
        with self.assertRaisesRegex(RuntimeError, "HEAD"):
            MODULE.require_private_hub_head(
                FakeApi(True, "b" * 40),
                repo_id=PERSUASION_REPO,
                expected_revision=expected,
                token="not-a-real-token",
            )
        class FlipApi:
            def __init__(self) -> None:
                self.calls = 0

            def repo_info(self, **_: object) -> object:
                self.calls += 1
                return types.SimpleNamespace(
                    private=self.calls == 1,
                    sha=expected,
                )

        with self.assertRaisesRegex(RuntimeError, "visibility"):
            MODULE.require_private_hub_head(
                FlipApi(),
                repo_id=PERSUASION_REPO,
                expected_revision=expected,
                token="not-a-real-token",
            )

    def test_atomic_write_readback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            MODULE.atomic_write(path, b'{"ok":true}\n')
            self.assertEqual(path.read_bytes(), b'{"ok":true}\n')


if __name__ == "__main__":
    unittest.main()
