import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pyarrow.parquet as parquet
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_SPEC = spec_from_file_location("release_config", ROOT / "scripts" / "release_config.py")
CONFIG = module_from_spec(CONFIG_SPEC)
assert CONFIG_SPEC.loader is not None
CONFIG_SPEC.loader.exec_module(CONFIG)


class PolicyAtlasReleaseTest(unittest.TestCase):
    def test_build_and_validate(self) -> None:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build_release.py")],
            check=True,
        )
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_release.py")],
            check=True,
        )
        subprocess.run(
            ["node", str(ROOT / "scripts" / "build_parquet.cjs")],
            check=True,
        )
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_release.py")],
            check=True,
        )
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "prepare_hf_release.py")],
            check=True,
        )

        sys.path.insert(0, str(ROOT / "scripts"))
        from publish_hf import validate_staged_release

        staged = ROOT / "dist" / "huggingface"
        validate_staged_release(staged)
        card_text = (staged / "README.md").read_text(encoding="utf-8")
        metadata = yaml.safe_load(card_text.split("---", 2)[1])
        configured_paths = {
            data_file["path"]
            for config in metadata["configs"]
            for data_file in config["data_files"]
        }
        manifest = json.loads((staged / "manifests" / "release.json").read_text(encoding="utf-8"))
        expected_parquet = {
            relative for relative in manifest["files"] if relative.endswith(".parquet")
        }
        self.assertEqual(configured_paths, expected_parquet)
        self.assertEqual(len(metadata["configs"]), len(expected_parquet))
        for relative in sorted(configured_paths):
            with self.subTest(viewer_config=relative):
                table = parquet.read_table(staged / relative)
                self.assertGreaterEqual(table.num_rows, 1)
        with tempfile.TemporaryDirectory() as temporary:
            tampered = Path(temporary) / "huggingface"
            shutil.copytree(staged, tampered)
            atlas = tampered / "data" / "derived" / "atlas.csv"
            atlas.write_bytes(atlas.read_bytes() + b"\n")
            with self.assertRaises(SystemExit):
                validate_staged_release(tampered)

        with tempfile.TemporaryDirectory() as temporary:
            duplicate_checksum = Path(temporary) / "huggingface"
            shutil.copytree(staged, duplicate_checksum)
            checksums = duplicate_checksum / "manifests" / "checksums.sha256"
            first_line = checksums.read_text(encoding="utf-8").splitlines()[0]
            checksums.write_text(
                checksums.read_text(encoding="utf-8") + first_line + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SystemExit, "Duplicate checksum"):
                validate_staged_release(duplicate_checksum)

        with tempfile.TemporaryDirectory() as temporary:
            fake_stable = Path(temporary) / "huggingface"
            shutil.copytree(staged, fake_stable)
            manifest_path = fake_stable / "manifests" / "release.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.update(
                {
                    "release_stage": "stable",
                    "stable_release_ready": True,
                    "stable_release_blockers": [],
                }
            )
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SystemExit, "blocked research-preview"):
                validate_staged_release(fake_stable)

        with tempfile.TemporaryDirectory() as temporary:
            nested_doi = Path(temporary) / "huggingface"
            shutil.copytree(staged, nested_doi)
            manifest_path = nested_doi / "manifests" / "release.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["identifiers"] = [{"type": "doi", "value": "10.5281/zenodo.9999999"}]
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SystemExit, "must not contain DOI metadata"):
                validate_staged_release(nested_doi)

    def test_publisher_parses_cff_and_requires_final_release_metadata(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from publish_hf import (
            file_contains_credential,
            load_and_validate_citation,
            validate_publication_changelog,
        )

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            citation = directory / "CITATION.cff"
            citation.write_text(
                (ROOT / "CITATION.cff").read_text(encoding="utf-8")
                + '\n"DOI": "10.5281/zenodo.9999999"\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SystemExit, "must not contain DOI metadata"):
                load_and_validate_citation(citation)

            binary = directory / "metadata.parquet"
            binary.write_bytes(b"PAR1\xff\x00publisher_secret=hf_" + b"A" * 24 + b"\x00PAR1")
            self.assertTrue(file_contains_credential(binary))

            citation.write_text(
                (ROOT / "CITATION.cff").read_text(encoding="utf-8")
                + "\nidentifiers:\n  - type: doi\n"
                + "    value: 10.5281/zenodo.9999999\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SystemExit, "must not contain DOI metadata"):
                load_and_validate_citation(citation)

            changelog = directory / "CHANGELOG.md"
            changelog.write_text(
                f"# Changelog\n\n## {CONFIG.VERSION} — 2026-08-15 (unreleased candidate)\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SystemExit, "must exactly match"):
                validate_publication_changelog(changelog, required_release_date="2026-08-15")

    def test_publication_downgrades_and_priority_review(self) -> None:
        import csv

        release = ROOT / "release" / CONFIG.VERSION / "data"
        with (release / "core" / "claims.csv").open(newline="", encoding="utf-8") as handle:
            claims = list(csv.DictReader(handle))
        unchecked_established = [
            row
            for row in claims
            if row["epistemic_status"] == "Established evidence"
            and row["publication_verification_status"] != "claim_checked"
        ]
        self.assertTrue(unchecked_established)
        self.assertTrue(
            all(
                row["publication_epistemic_status"] == "Unverified candidate"
                for row in unchecked_established
            )
        )

        with (release / "derived" / "atlas.csv").open(newline="", encoding="utf-8") as handle:
            atlas = list(csv.DictReader(handle))
        established_effect_rows = [
            row for row in atlas if row["claim_class"] == "Established — component effect"
        ]
        self.assertEqual(
            {row["implementation_id"] for row in established_effect_rows},
            {"I-068"},
        )
        self.assertTrue(
            all(row["effect_claim_reviewed"] == "true" for row in established_effect_rows)
        )
        self.assertTrue(
            all(
                row["publication_claim_class"] == "Established — component effect"
                for row in established_effect_rows
            )
        )

        priority_rows = [row for row in atlas if row["effect_claim_reviewed"] == "true"]
        self.assertEqual(
            {row["implementation_id"] for row in priority_rows},
            {"I-008", "I-044", "I-067", "I-068", "I-086", "I-087"},
        )
        self.assertTrue(all(row["effect_claim_checked"] == "true" for row in priority_rows))
        self.assertEqual(
            {row["implementation_id"]: row["publication_claim_class"] for row in priority_rows},
            {
                "I-008": "Strong inference",
                "I-044": "Strong inference",
                "I-067": "Open question",
                "I-068": "Established — component effect",
                "I-086": "Strong inference",
                "I-087": "Open question",
            },
        )

        project_mechanism_rows = [
            row for row in atlas if row["claim_class"] == "Established — project mechanism"
        ]
        self.assertEqual(len(project_mechanism_rows), 2)
        self.assertTrue(
            all(row["mechanism_claim_checked"] == "false" for row in project_mechanism_rows)
        )
        self.assertTrue(
            all(
                row["publication_claim_class"]
                == "Provisional — project mechanism not claim-checked"
                for row in project_mechanism_rows
            )
        )

        established_legal_rows = [
            row for row in atlas if row["claim_class"] == "Established — legal status"
        ]
        unchecked_legal_rows = [
            row for row in established_legal_rows if row["legal_claim_checked"] == "false"
        ]
        self.assertTrue(established_legal_rows)
        self.assertTrue(unchecked_legal_rows)
        self.assertTrue(
            all(
                row["publication_claim_class"] == "Provisional — legal status not claim-checked"
                for row in unchecked_legal_rows
            )
        )

        atlas_by_id = {row["implementation_id"]: row for row in atlas}
        for implementation_id in ("I-098", "I-106"):
            self.assertEqual(atlas_by_id[implementation_id]["legal_claim_checked"], "true")
            self.assertEqual(
                atlas_by_id[implementation_id]["publication_claim_class"],
                "Established — legal status",
            )
        self.assertEqual(
            atlas_by_id["I-105"]["legal_force"],
            "Planned / no legal force",
        )

    def test_stable_core_foundation_is_provisional_and_unranked(self) -> None:
        import csv

        release = ROOT / "release" / CONFIG.VERSION / "data"

        def rows(relative: str) -> list[dict[str, str]]:
            with (release / relative).open(newline="", encoding="utf-8") as handle:
                return list(csv.DictReader(handle))

        atlas = rows("derived/atlas.csv")
        core = rows("derived/stable_core_candidates.csv")
        registry = rows("derived/candidate_registry.csv")
        stable_gates = rows("core/stable_release_gates.csv")
        public_implementations = rows("core/implementations.csv")
        public_packages = rows("core/policy_packages.csv")
        public_families = rows("core/intervention_families.csv")

        core_ids = {row["implementation_id"] for row in core}
        registry_ids = {row["implementation_id"] for row in registry}
        atlas_ids = {row["implementation_id"] for row in atlas}

        self.assertEqual(len(core), 30)
        self.assertEqual(len(registry), 88)
        self.assertFalse(core_ids & registry_ids)
        self.assertEqual(core_ids | registry_ids, atlas_ids)
        self.assertTrue(all(row["inclusion_status"] == "proposed_core_candidate" for row in core))
        self.assertTrue(
            all(
                row["stable_core_admission_status"] == "blocked_pending_verification"
                and row["ranking_ready"] == "false"
                and row["rank_eligibility"].startswith("not_eligible_now__")
                for row in core
            )
        )
        self.assertTrue(
            all(
                row["stable_core_ready"] == "false"
                and row["ranking_ready"] == "false"
                and row["publication_decision_posture"] == "not_assessed"
                and "decision_tier" not in row
                and "working_register_decision_tier" not in row
                for row in atlas
            )
        )
        self.assertTrue(
            all(
                row["publication_decision_posture"] == "not_assessed"
                and row["working_register_decision_tier"]
                and "decision_tier" not in row
                for row in public_implementations + public_packages
            )
        )
        self.assertTrue(
            all(
                row["publication_decision_posture"] == "not_assessed"
                and row["working_register_decision_posture"]
                and "decision_posture" not in row
                for row in public_families
            )
        )
        self.assertEqual(len(stable_gates), 13)
        self.assertNotIn("satisfied", {row["status"] for row in stable_gates})
        self.assertFalse((release / "derived" / "rank_results.csv").exists())


if __name__ == "__main__":
    unittest.main()
