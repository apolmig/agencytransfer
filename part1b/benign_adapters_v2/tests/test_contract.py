from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "jobs" / "train_lora.py"
SPEC = importlib.util.spec_from_file_location("era_part1b_train_lora", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

EXPECTED_HASHES = {
    "transparent_persuasion": {
        "train": "569863d288420c78427464e2faa0ccbb472f3c103ead328b797c20f688f62513",
        "validation": "4650aeb5df605322c2f6efb3f5e02e01e41af75e869f1eef516a5ff0f0c8dc45",
        "heldout": "02b0dca6e97b1dcdb1108b5da5674a8e3ee9e1521ce9afa23f013bfd6aac44d8",
    },
    "public_osint": {
        "train": "758d07e08178eb4fedea51dcfd795201d0d569132590b0989e384d4684f01dc6",
        "validation": "4c90f3cc516d2af440797cbae3696c93f5fd311c1c3c21b503eb0c65452d63fe",
        "heldout": "f22a3a1d3bc95239f9e9889e21d3a9e6121e2dbf9e0857b3d84ee0c6cb254384",
    },
}


class DatasetContractTest(unittest.TestCase):
    def test_frozen_counts_families_languages_and_hashes(self) -> None:
        for adapter, expected_hashes in EXPECTED_HASHES.items():
            dataset = MODULE.build_dataset(adapter)
            manifest = MODULE.dataset_manifest(adapter, dataset)
            for split, expected_count in MODULE.EXPECTED_COUNTS.items():
                split_manifest = manifest["splits"][split]
                self.assertEqual(split_manifest["rows"], expected_count)
                self.assertEqual(split_manifest["content_sha256"], expected_hashes[split])
                self.assertEqual(
                    len(split_manifest["families"]), MODULE.EXPECTED_FAMILY_COUNTS[split]
                )
                self.assertEqual(
                    split_manifest["languages"],
                    {"en": expected_count // 2, "es": expected_count // 2},
                )

    def test_scenario_families_are_group_disjoint(self) -> None:
        dataset = MODULE.build_dataset("public_osint")
        families = {
            split: {row["family_id"] for row in records}
            for split, records in dataset.items()
        }
        self.assertFalse(families["train"] & families["validation"])
        self.assertFalse(families["train"] & families["heldout"])
        self.assertFalse(families["validation"] & families["heldout"])

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


if __name__ == "__main__":
    unittest.main()
