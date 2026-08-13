import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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
            ["npm", "--prefix", str(ROOT), "run", "build:parquet"],
            check=True,
        )
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_release.py")],
            check=True,
        )

    def test_publication_downgrades_and_priority_review(self) -> None:
        import csv

        release = ROOT / "release" / "v0.1.0-beta.1" / "data"
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
        self.assertEqual(len(established_effect_rows), 6)
        self.assertTrue(all(row["effect_claim_reviewed"] == "true" for row in established_effect_rows))
        self.assertTrue(
            all(
                row["publication_claim_class"]
                == "Provisional — effect evidence not claim-checked"
                for row in established_effect_rows
            )
        )


if __name__ == "__main__":
    unittest.main()
