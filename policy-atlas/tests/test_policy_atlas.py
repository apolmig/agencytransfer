import subprocess
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

from importlib.util import module_from_spec, spec_from_file_location


ROOT = Path(__file__).resolve().parents[1]
CONFIG_SPEC = spec_from_file_location(
    "release_config", ROOT / "scripts" / "release_config.py"
)
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
        with tempfile.TemporaryDirectory() as temporary:
            tampered = Path(temporary) / "huggingface"
            shutil.copytree(staged, tampered)
            atlas = tampered / "data" / "derived" / "atlas.csv"
            atlas.write_bytes(atlas.read_bytes() + b"\n")
            with self.assertRaises(SystemExit):
                validate_staged_release(tampered)

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
            all(row["publication_epistemic_status"] == "Unverified candidate" for row in unchecked_established)
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
        self.assertTrue(all(row["effect_claim_reviewed"] == "true" for row in established_effect_rows))
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
        self.assertTrue(all(row["mechanism_claim_checked"] == "false" for row in project_mechanism_rows))
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
                row["publication_claim_class"]
                == "Provisional — legal status not claim-checked"
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


if __name__ == "__main__":
    unittest.main()
