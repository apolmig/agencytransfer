from __future__ import annotations

import ast
import copy
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "jobs" / "train_lora.py"
ML_PREFLIGHT = ROOT / "jobs" / "ml_stack_preflight.py"
SPEC = importlib.util.spec_from_file_location("era_part1b_train_lora", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

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


class DatasetContractTest(unittest.TestCase):
    def test_frozen_counts_families_languages_and_hashes(self) -> None:
        for adapter, expected_hashes in EXPECTED_HASHES.items():
            dataset = MODULE.build_dataset(adapter)
            manifest = MODULE.dataset_manifest(adapter, dataset)
            self.assertEqual(manifest["experimental_unit"], "scenario_family")
            self.assertTrue(manifest["family_disjoint_splits"])
            self.assertEqual(
                manifest["variants_per_family"], MODULE.EXPECTED_VARIANTS_PER_FAMILY
            )
            for split, expected_count in MODULE.EXPECTED_COUNTS.items():
                split_manifest = manifest["splits"][split]
                self.assertEqual(split_manifest["rows"], expected_count)
                self.assertEqual(split_manifest["content_sha256"], expected_hashes[split])
                self.assertEqual(
                    split_manifest["family_count"], MODULE.EXPECTED_FAMILY_COUNTS[split]
                )
                self.assertEqual(
                    len(split_manifest["families"]), MODULE.EXPECTED_FAMILY_COUNTS[split]
                )
                self.assertEqual(
                    split_manifest["languages"],
                    {"en": expected_count // 2, "es": expected_count // 2},
                )

    def test_scenario_families_are_group_disjoint(self) -> None:
        for adapter in MODULE.ADAPTERS:
            dataset = MODULE.build_dataset(adapter)
            families = {
                split: {row["family_id"] for row in records}
                for split, records in dataset.items()
            }
            self.assertFalse(families["train"] & families["validation"])
            self.assertFalse(families["train"] & families["heldout"])
            self.assertFalse(families["validation"] & families["heldout"])

    def test_qwen_thinking_mode_is_disabled_for_every_row(self) -> None:
        for adapter in MODULE.ADAPTERS:
            dataset = MODULE.build_dataset(adapter)
            for records in dataset.values():
                self.assertTrue(
                    all(
                        row["chat_template_kwargs"] == {"enable_thinking": False}
                        for row in records
                    )
                )

    def test_chat_template_mode_tampering_is_rejected(self) -> None:
        dataset = MODULE.build_dataset("public_osint")
        tampered = copy.deepcopy(dataset)
        tampered["train"][0]["chat_template_kwargs"]["enable_thinking"] = True
        with self.assertRaisesRegex(ValueError, "chat-template mode mismatch"):
            MODULE.validate_dataset("public_osint", tampered)

    def test_each_family_has_ten_balanced_diverse_variants(self) -> None:
        for adapter in MODULE.ADAPTERS:
            dataset = MODULE.build_dataset(adapter)
            for records in dataset.values():
                by_family: dict[str, list[dict[str, object]]] = {}
                for record in records:
                    by_family.setdefault(record["family_id"], []).append(record)
                for family_records in by_family.values():
                    self.assertEqual(len(family_records), 10)
                    self.assertEqual(
                        {record["variant_index"] for record in family_records}, set(range(10))
                    )
                    self.assertEqual(
                        sum(record["language"] == "en" for record in family_records), 5
                    )
                    self.assertEqual(
                        sum(record["language"] == "es" for record in family_records), 5
                    )
                    self.assertEqual(len({record["template_id"] for record in family_records}), 5)
                    self.assertEqual(
                        len(
                            {
                                (record["language"], record["template_id"])
                                for record in family_records
                            }
                        ),
                        10,
                    )

    def test_family_variant_contract_rejects_pseudoreplication_regression(self) -> None:
        dataset = MODULE.build_dataset("transparent_persuasion")
        tampered = copy.deepcopy(dataset)
        tampered["train"][10]["family_id"] = tampered["train"][0]["family_id"]
        with self.assertRaisesRegex(
            ValueError,
            "family count mismatch|variants do not match|family language imbalance",
        ):
            MODULE.validate_dataset("transparent_persuasion", tampered)

    def test_protocol_binds_family_design_and_dataset_hashes(self) -> None:
        protocol_dataset = json.loads(
            (ROOT / "protocol.json").read_text(encoding="utf-8")
        )["dataset"]
        self.assertEqual(protocol_dataset["family_counts"], MODULE.EXPECTED_FAMILY_COUNTS)
        self.assertEqual(
            protocol_dataset["variants_per_family"], MODULE.EXPECTED_VARIANTS_PER_FAMILY
        )
        self.assertTrue(protocol_dataset["family_disjoint_splits"])
        self.assertEqual(protocol_dataset["content_sha256"], EXPECTED_HASHES)

    def test_political_or_electoral_content_is_rejected(self) -> None:
        dataset = MODULE.build_dataset("transparent_persuasion")
        tampered = copy.deepcopy(dataset)
        tampered["train"][0]["prompt"][1]["content"] += " Target a voter in an election."
        with self.assertRaisesRegex(ValueError, "excluded-domain"):
            MODULE.validate_dataset("transparent_persuasion", tampered)

    def test_live_url_and_identifier_are_rejected(self) -> None:
        dataset = MODULE.build_dataset("public_osint")
        tampered = copy.deepcopy(dataset)
        tampered["train"][0]["prompt"][1]["content"] += " https://example.test person@test.test"
        with self.assertRaisesRegex(ValueError, "excluded-domain"):
            MODULE.validate_dataset("public_osint", tampered)

    def test_citation_outside_packet_is_rejected(self) -> None:
        dataset = MODULE.build_dataset("public_osint")
        tampered = copy.deepcopy(dataset)
        tampered["train"][0]["completion"][0]["content"] += " Unsupported [S4]."
        with self.assertRaisesRegex(ValueError, "citation outside packet"):
            MODULE.validate_dataset("public_osint", tampered)

    def test_heldout_is_never_counted_as_training_input(self) -> None:
        for phase, contract in MODULE.MODELS.items():
            self.assertLessEqual(contract["train_examples"], MODULE.EXPECTED_COUNTS["train"])
            self.assertLessEqual(
                contract["validation_examples"], MODULE.EXPECTED_COUNTS["validation"]
            )
            self.assertNotIn("heldout_examples", contract)


class ControlContractTest(unittest.TestCase):
    def test_remote_args_require_bucket_identity(self) -> None:
        with self.assertRaises(SystemExit):
            MODULE.parse_args(
                [
                    "--adapter",
                    "public_osint",
                    "--phase",
                    "production",
                    "--run-id",
                    "valid-run-id",
                    "--seed",
                    "17",
                ]
            )

    def test_validate_only_does_not_require_bucket_identity(self) -> None:
        args = MODULE.parse_args(
            [
                "--adapter",
                "transparent_persuasion",
                "--phase",
                "production",
                "--run-id",
                "valid-run-id",
                "--seed",
                "17",
                "--validate-only",
            ]
        )
        self.assertTrue(args.validate_only)

    def test_remote_args_require_authorization_and_operation_hashes(self) -> None:
        args = MODULE.parse_args(
            [
                "--adapter",
                "public_osint",
                "--phase",
                "production",
                "--run-id",
                "valid-run-id",
                "--seed",
                "17",
                "--bucket-identity-sha256",
                "a" * 64,
                "--authorization-sha256",
                "b" * 64,
                "--operation-sha256",
                "c" * 64,
            ]
        )
        self.assertEqual(args.authorization_sha256, "b" * 64)

    def test_authorization_is_tuple_and_provider_job_bound(self) -> None:
        authorization = {
            "schema": "era-part1b-training-authorization/v2",
            "status": "AUTHORIZED_FOR_TWO_TECHNICAL_TRAINING_JOBS",
            "operation_id": "valid-run-id",
            "operation_sha256": "c" * 64,
            "run_id": "valid-run-id",
            "bucket_identity_sha256": "a" * 64,
            "producer": {"job_id": "producer01", "receipt_sha256": "d" * 64},
            "verifier": {"job_id": "verifier01", "terminal_sha256": "e" * 64},
            "ml_stack": {"job_id": "mlstack001", "terminal_sha256": "1" * 64},
            "issuer": {"job_id": "issuer001"},
            "public_artifacts": {
                "train_lora_sha256": "f" * 64,
                "protocol_sha256": MODULE.EXPECTED_PROTOCOL_SHA256,
            },
            "slots": [
                {
                    "slot_id": "persuasion-slot",
                    "status": "AUTHORIZED",
                    "adapter": "transparent_persuasion",
                    "phase": "production",
                    "seed": 17,
                    "run_id": "valid-run-id",
                },
                {
                    "slot_id": "public-osint-slot",
                    "status": "AUTHORIZED",
                    "adapter": "public_osint",
                    "phase": "production",
                    "seed": 17,
                    "run_id": "valid-run-id",
                },
            ],
            "issued_at": "2026-08-14T00:00:00Z",
        }
        evidence = MODULE.validate_training_authorization(
            authorization,
            authorization_sha256="b" * 64,
            expected_authorization_sha256="b" * 64,
            operation_sha256="c" * 64,
            marker_sha256="a" * 64,
            script_sha256="f" * 64,
            adapter="public_osint",
            phase="production",
            seed=17,
            run_id="valid-run-id",
            current_job_id="training01",
        )
        self.assertEqual(evidence["slot_id"], "public-osint-slot")
        with self.assertRaisesRegex(RuntimeError, "distinct"):
            MODULE.validate_training_authorization(
                authorization,
                authorization_sha256="b" * 64,
                expected_authorization_sha256="b" * 64,
                operation_sha256="c" * 64,
                marker_sha256="a" * 64,
                script_sha256="f" * 64,
                adapter="public_osint",
                phase="production",
                seed=17,
                run_id="valid-run-id",
                current_job_id="producer01",
            )

    def test_atomic_write_is_exact_and_exclusive_by_fresh_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            MODULE.atomic_write(path, b'{"ok":true}\n')
            self.assertEqual(path.read_bytes(), b'{"ok":true}\n')

    def test_protocol_is_diagnostic_only_for_refusal_direction(self) -> None:
        protocol = json.loads((ROOT / "protocol.json").read_text(encoding="utf-8"))
        self.assertEqual(protocol["status"], "READY_FOR_TECHNICAL_EXECUTION")
        self.assertEqual(
            protocol["refusal_direction_arm"]["status"],
            "DIAGNOSTIC_NO_GO_FOR_DEPLOYMENT",
        )
        self.assertFalse(protocol["refusal_direction_arm"]["public_vector_or_delta"])
        self.assertFalse(protocol["refusal_direction_arm"]["public_raw_harmful_outputs"])

    def test_dependency_lock_matches_pep_723(self) -> None:
        locked = {
            line.strip() for line in (ROOT / "requirements.lock").read_text().splitlines() if line
        }
        script = SCRIPT.read_text(encoding="utf-8")
        for requirement in locked:
            self.assertIn(f'"{requirement}"', script)

    def test_ml_preflight_uses_the_identical_dependency_lock(self) -> None:
        locked = {
            line.strip() for line in (ROOT / "requirements.lock").read_text().splitlines() if line
        }
        preflight = ML_PREFLIGHT.read_text(encoding="utf-8")
        for requirement in locked:
            self.assertIn(f'"{requirement}"', preflight)

    def test_official_job_id_is_required(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "official JOB_ID"):
                MODULE.provider_job_id()
        with mock.patch.dict(os.environ, {"JOB_ID": "job-valid-123"}, clear=True):
            self.assertEqual(MODULE.provider_job_id(), "job-valid-123")


class MLCompatibilityContractTest(unittest.TestCase):
    @staticmethod
    def _calls(function_name: str) -> list[ast.Call]:
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        calls = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id == function_name:
                calls.append(node)
            elif isinstance(node.func, ast.Attribute) and node.func.attr == function_name:
                calls.append(node)
        return calls

    @staticmethod
    def _keyword_literal(call: ast.Call, name: str) -> object:
        for keyword in call.keywords:
            if keyword.arg == name:
                return ast.literal_eval(keyword.value)
        raise AssertionError(f"missing keyword {name}")

    def test_lora_targets_qwen_projections_but_not_lm_head(self) -> None:
        calls = self._calls("LoraConfig")
        self.assertEqual(len(calls), 1)
        targets = self._keyword_literal(calls[0], "target_modules")
        self.assertEqual(
            targets,
            [
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ],
        )
        self.assertNotIn("lm_head", targets)

    def test_sft_uses_completion_mask_and_chunked_loss(self) -> None:
        calls = self._calls("SFTConfig")
        self.assertEqual(len(calls), 1)
        self.assertIs(self._keyword_literal(calls[0], "completion_only_loss"), True)
        self.assertEqual(self._keyword_literal(calls[0], "loss_type"), "chunked_nll")
        self.assertEqual(self._keyword_literal(calls[0], "max_length"), 2048)
        self.assertIs(self._keyword_literal(calls[0], "packing"), False)
        self.assertEqual(
            self._keyword_literal(calls[0], "gradient_checkpointing_kwargs"),
            {"use_reentrant": False},
        )

    def test_qlora_is_nf4_bfloat16_double_quant_and_prepared(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('bnb_4bit_quant_type="nf4"', source)
        self.assertIn("bnb_4bit_compute_dtype=torch.bfloat16", source)
        self.assertIn("bnb_4bit_use_double_quant=True", source)
        self.assertIn("view(torch.uint8)", source)
        self.assertLess(
            source.index("prepare_model_for_kbit_training("),
            source.index("trainer = SFTTrainer("),
        )

    def test_l4_flavor_is_fail_closed_and_rejects_t4_name(self) -> None:
        self.assertEqual(MODULE.REQUIRED_HF_GPU_FLAVOR, "l4x1")
        self.assertIsNotNone(MODULE.REQUIRED_GPU_NAME_RE.search("NVIDIA L4"))
        self.assertIsNone(MODULE.REQUIRED_GPU_NAME_RE.search("Tesla T4"))
        self.assertGreaterEqual(MODULE.MODELS["production"]["min_gpu_bytes"], 22_000_000_000)

    def test_tensor_hash_supports_bfloat16_when_torch_is_available(self) -> None:
        try:
            import torch
        except ImportError:
            self.skipTest("torch is exercised by the remote ML-stack preflight")
        state = {"adapter.weight": torch.arange(8, dtype=torch.bfloat16).reshape(2, 4)}
        first = MODULE.tensor_state_hash(state)
        self.assertRegex(first, r"^[0-9a-f]{64}$")
        self.assertEqual(first, MODULE.tensor_state_hash(state))
        changed = {"adapter.weight": state["adapter.weight"].clone()}
        changed["adapter.weight"][0, 0] = 99
        self.assertNotEqual(first, MODULE.tensor_state_hash(changed))

    def test_preflight_is_weight_free_and_checks_both_revisions(self) -> None:
        source = ML_PREFLIGHT.read_text(encoding="utf-8")
        self.assertNotIn("AutoModelForCausalLM", source)
        self.assertNotIn("SFTTrainer", source)
        self.assertIn("AutoConfig.from_pretrained", source)
        self.assertIn("AutoTokenizer.from_pretrained", source)
        self.assertIn("enable_thinking=False", source)
        for contract in MODULE.MODELS.values():
            self.assertIn(contract["id"], source)
            self.assertIn(contract["revision"], source)

    def test_preflight_terminal_contract_is_exact_v2(self) -> None:
        tree = ast.parse(ML_PREFLIGHT.read_text(encoding="utf-8"))
        terminal_dicts = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "terminal"
                for target in node.targets
            )
            and isinstance(node.value, ast.Dict)
        ]
        self.assertEqual(len(terminal_dicts), 1)
        keys = {ast.literal_eval(key) for key in terminal_dicts[0].keys}
        self.assertEqual(
            keys,
            {
                "schema",
                "status",
                "operation_id",
                "run_id",
                "job_id",
                "train_lora_sha256",
                "protocol_sha256",
                "models",
                "dependencies",
                "completed_at",
            },
        )
        source = ML_PREFLIGHT.read_text(encoding="utf-8")
        self.assertIn('SCHEMA = "era-part1b-ml-stack-preflight/v2"', source)
        for flag in ("--run-id", "--train-lora-sha256", "--protocol-sha256"):
            self.assertIn(flag, source)


if __name__ == "__main__":
    unittest.main()
