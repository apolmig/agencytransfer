"""The recommendation layer must not silently upgrade the evidence layer."""
import csv
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from release_config import VERSION


class ComparativeReleaseTests(unittest.TestCase):
    def test_complete_unique_membership(self):
        release = ROOT / 'release' / VERSION
        with (release / 'data' / 'derived' / 'atlas.csv').open(newline='', encoding='utf-8') as handle:
            atlas = list(csv.DictReader(handle))
        self.assertEqual(len(atlas), 118)
        self.assertEqual(len({row['implementation_id'] for row in atlas}), 118)
        self.assertEqual(Counter(row['comparative_group'] for row in atlas), {'A': 5, 'B': 41, 'C': 31, 'D': 16, 'E': 19, 'F': 6})
        self.assertTrue(all(row['comparative_classification_status'] == 'provisional_author_synthesis' for row in atlas))
        self.assertEqual(sum(row['effect_claim_checked'] == 'true' for row in atlas), 6)
        by_id = {row['implementation_id']: row for row in atlas}
        self.assertEqual(by_id['I-067']['publication_claim_class'], 'Open question')
        self.assertEqual(by_id['I-087']['comparative_group'], 'E')
        manifest = json.loads((release / 'manifests' / 'release.json').read_text(encoding='utf-8'))
        self.assertFalse(manifest['stable_release_ready'])
        self.assertEqual(manifest['counts']['control_effectiveness_claims_checked'], 6)
        self.assertEqual(manifest['counts']['comparatively_classified_implementations'], 118)


if __name__ == '__main__':
    unittest.main()
