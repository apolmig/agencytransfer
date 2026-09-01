"""Keep the dated website companion traceable without upgrading Atlas evidence."""

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "policy-atlas/review/source-linked-20260901/review.json"


class SourceLinkedReviewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.review = json.loads(REVIEW.read_text(encoding="utf-8"))

    def test_coverage_and_source_references(self) -> None:
        review = self.review
        self.assertEqual(review["status"], "working_draft")
        self.assertEqual(len(set(review["implementation_ids"])), 118)
        self.assertEqual(review["coverage"]["implementations"], 118)
        source_ids = {source["id"] for source in review["sources"]}
        self.assertEqual(len(source_ids), 69)
        self.assertEqual(len(review["sources"]), 69)
        self.assertEqual(sum(review["evidence_modes"].values()), 118)
        self.assertEqual(len(review["new_substantive_checks"]), 8)
        self.assertTrue(set(review["new_substantive_checks"]) <= source_ids)

    def test_original_source_files_are_preserved(self) -> None:
        for source in self.review["source_files"]:
            with self.subTest(path=source["path"]):
                path = (ROOT / source["path"]).resolve()
                self.assertTrue(path.is_relative_to(ROOT))
                raw = path.read_bytes()
                self.assertEqual(len(raw), source["bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), source["sha256"])

    def test_review_does_not_upgrade_empirical_claim_flags(self) -> None:
        dataset = self.review["production_dataset"]
        self.assertEqual(dataset["release"], "v0.1.0-beta.3")
        self.assertFalse(dataset["empirical_claim_flags_changed"])
        self.assertTrue(dataset["historical_A_F_assignments_preserved"])
        self.assertEqual(self.review["manuscript"]["parts_i_iii_evidence_freeze"], "2026-08-28")
        self.assertEqual(self.review["manuscript"]["part_iv_review_date"], "2026-09-01")


if __name__ == "__main__":
    unittest.main()
