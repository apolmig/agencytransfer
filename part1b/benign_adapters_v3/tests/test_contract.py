from __future__ import annotations

import ast
import base64
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "jobs" / "train_lora.py"
ML_PREFLIGHT = ROOT / "jobs" / "ml_stack_preflight.py"
SPEC = importlib.util.spec_from_file_location("era_part1b_v3_train_lora", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

RUN_ID = "era-p1b-v3-20260814t010317z"
PERSUASION_REPO = (
    "apol/era-p1b-v3-20260814t010317z-transparent-persuasion-qwen3-8b-lora"
)
OSINT_REPO = "apol/era-p1b-v3-20260814t010317z-public-osint-qwen3-8b-lora"
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
        "schema": "era-part1b-training-authorization/v3",
        "status": "AUTHORIZED_FOR_TWO_PRIVATE_HUB_JOBS",
        "operation_id": RUN_ID,
        "operation_sha256": "1" * 64,
        "run_id": RUN_ID,
        "control_repo": {
            "repo_id": MODULE.EXPECTED_EVIDENCE_REPO,
            "repo_type": "dataset",
            "identity_path": f"runs/{RUN_ID}/control/identity.json",
            "identity_revision": "8" * 40,
            "identity_sha256": "3" * 64,
            "operation_path": f"runs/{RUN_ID}/control/operation.json",
            "authorization_path": f"runs/{RUN_ID}/control/authorizations/authorization.json",
        },
        "write_canary": {
            "job_id": "canary-job-001",
            "path": f"runs/{RUN_ID}/auth/write-canary.json",
            "sha256": "4" * 64,
            "revision": "5" * 40,
        },
        "producer": {
            "job_id": "producer-job-001",
            "receipt_sha256": "6" * 64,
            "terminal_sha256": "7" * 64,
            "evidence_revision": "8" * 40,
        },
        "verifier": {"job_id": "verifier-job-001", "terminal_sha256": "9" * 64},
        "ml_stack": {"job_id": "ml-stack-job-001", "terminal_sha256": "a" * 64},
        "issuer": {"job_id": "issuer-job-001"},
        "public_artifacts": {
            "train_lora_hub_sha256": "b" * 64,
            "protocol_sha256": MODULE.EXPECTED_PROTOCOL_SHA256,
        },
        "runtime_versions": dict(MODULE.EXPECTED_RUNTIME_VERSIONS),
        "slots": [
            {
                "slot_id": "persuasion-slot-v3",
                "status": "AUTHORIZED",
                "adapter": "transparent_persuasion",
                "phase": "production",
                "seed": 17,
                "run_id": RUN_ID,
                "target_repo_id": PERSUASION_REPO,
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
                "slot_id": "public-osint-slot-v3",
                "status": "AUTHORIZED",
                "adapter": "public_osint",
                "phase": "production",
                "seed": 17,
                "run_id": RUN_ID,
                "target_repo_id": OSINT_REPO,
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


class DatasetContractTest(unittest.TestCase):
    def test_frozen_counts_families_languages_and_hashes(self) -> None:
        for adapter, expected_hashes in EXPECTED_HASHES.items():
            dataset = MODULE.build_dataset(adapter)
            manifest = MODULE.dataset_manifest(adapter, dataset)
            self.assertEqual(manifest["schema"], "era-part1b-benign-dataset-manifest/v3")
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
            self.assertEqual(evidence["write_canary_job_id"], "canary-job-001")
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
            "schema": "era-part1b-hf-operation/v3",
            "operation_id": RUN_ID,
            "status": "GO_FOR_AUTHORIZATION_ISSUER_ONLY",
        }
        raw = MODULE.canonical_bytes(operation) + b"\n"
        expected = hashlib.sha256(raw).hexdigest()
        self.assertEqual(
            MODULE.validate_persisted_operation(
                raw, expected_sha256=expected, run_id=RUN_ID
            ),
            operation,
        )
        with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
            MODULE.validate_persisted_operation(
                raw, expected_sha256="0" * 64, run_id=RUN_ID
            )
        noncanonical = b'{"status":"GO_FOR_AUTHORIZATION_ISSUER_ONLY", "schema":"era-part1b-hf-operation/v3","operation_id":"' + RUN_ID.encode() + b'"}\n'
        with self.assertRaisesRegex(RuntimeError, "canonical"):
            MODULE.validate_persisted_operation(
                noncanonical,
                expected_sha256=hashlib.sha256(noncanonical).hexdigest(),
                run_id=RUN_ID,
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
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('bnb_4bit_quant_type="nf4"', source)
        self.assertIn("bnb_4bit_compute_dtype=torch.bfloat16", source)
        self.assertIn("bnb_4bit_use_double_quant=True", source)
        self.assertIn('"max_steps": 300', source)

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

    def test_private_repo_exact_tree_lineage_readback_and_remote_reload(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for required in (
            "initial_info.private",
            "initial_info.sha != expected_parent_revision",
            "initial_files != authorization_evidence",
            "require_linear_hub_history(",
            "verify_remote_hashes(",
            "require_private_hub_head(",
            "PeftModel.from_pretrained(",
            "post-Hub adapter reload canary mismatch",
        ):
            self.assertIn(required, source)
        self.assertGreaterEqual(source.count("require_private_hub_head("), 7)

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
            protocol["refusal_direction_arm"]["status"],
            "DIAGNOSTIC_NO_GO_FOR_DEPLOYMENT",
        )

    def test_protocol_hash_and_identical_dependency_locks(self) -> None:
        protocol_hash = hashlib.sha256((ROOT / "protocol.json").read_bytes()).hexdigest()
        self.assertEqual(protocol_hash, MODULE.EXPECTED_PROTOCOL_SHA256)
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

    def test_preflight_is_weight_free_and_checks_crypto_hub_and_only_8b(self) -> None:
        source = ML_PREFLIGHT.read_text(encoding="utf-8")
        self.assertNotIn("AutoModelForCausalLM", source)
        self.assertNotIn("SFTTrainer", source)
        self.assertNotIn("Qwen3-1.7B", source)
        self.assertIn("Qwen/Qwen3-8B", source)
        self.assertIn("load_der_public_key", source)
        self.assertIn("HfApi.create_commit", source)
        self.assertIn('"writes_performed": False', source)

    def test_linear_history_helper_rejects_extra_or_wrong_parent(self) -> None:
        class FakeApi:
            def __init__(self, commits: list[object]) -> None:
                self.commits = commits

            def list_repo_commits(self, **_: object) -> list[object]:
                return self.commits

        good = [
            types.SimpleNamespace(commit_id="a" * 40, parents=["b" * 40]),
            types.SimpleNamespace(commit_id="b" * 40, parents=[]),
        ]
        MODULE.require_linear_hub_history(
            FakeApi(good),
            repo_id=PERSUASION_REPO,
            revision="a" * 40,
            expected_newest_to_oldest=["a" * 40, "b" * 40],
            token="not-a-real-token",
        )
        bad = good + [types.SimpleNamespace(commit_id="c" * 40, parents=[])]
        with self.assertRaisesRegex(RuntimeError, "commit count"):
            MODULE.require_linear_hub_history(
                FakeApi(bad),
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
