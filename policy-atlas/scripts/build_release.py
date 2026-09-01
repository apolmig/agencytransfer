#!/usr/bin/env python3
"""Build the existing evidence release, then join provisional policy postures."""
from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from build_core_release import *  # Preserve the existing builder's public API.
from build_core_release import main as build_core

OVERLAY = ROOT / 'data' / 'comparative-v0.4' / 'groups.json'


def add_comparative_layer(release: Path, source: Path = OVERLAY) -> dict:
    config = json.loads(source.read_text(encoding='utf-8'))
    groups = config['groups']
    if len(groups) != 6 or {g['group_id'] for g in groups} != set('ABCDEF'):
        raise ValueError('Expected exactly the six source-defined postures A-F')
    membership = {}
    for group in groups:
        if len(group['implementation_ids']) != group['implementation_count']:
            raise ValueError(f"Source count mismatch: {group['group_id']}")
        for identifier in group['implementation_ids']:
            if identifier in membership:
                raise ValueError(f'Duplicate group membership: {identifier}')
            membership[identifier] = group
    atlas_path = release / 'data' / 'derived' / 'atlas.csv'
    atlas = read_csv(atlas_path)
    identifiers = [row['implementation_id'] for row in atlas]
    if len(identifiers) != 118 or len(set(identifiers)) != 118 or set(identifiers) != set(membership):
        raise ValueError('Comparative membership must exactly match all 118 existing implementations')
    baseline = [dict(row) for row in atlas]
    relations = []
    for row in atlas:
        group = membership[row['implementation_id']]
        additions = {
            'comparative_group': group['group_id'],
            'comparative_group_label': group['label'],
            'comparative_recommended_posture': group['recommended_posture'],
            'comparative_rationale': group['source_rationale'],
            'comparative_claim_ceiling': group['claim_ceiling'],
            'comparative_classification_status': config['classification_status'],
            'comparative_classification_date': config['classification_date'],
            'comparative_evidence_note': config['epistemic_note'],
        }
        row.update(additions)
        relations.append({'implementation_id': row['implementation_id'], **additions})
    for old, new in zip(baseline, atlas):
        if any(new[key] != value for key, value in old.items()):
            raise ValueError('The comparative overlay changed an existing evidence field')
    write_csv(atlas_path, atlas)
    write_csv(release / 'data' / 'relations' / 'implementation_evidence_groups.csv', relations)
    group_rows = []
    for group in groups:
        group_rows.append({
            **{key: value for key, value in group.items() if key != 'implementation_ids'},
            'implementation_ids': '; '.join(group['implementation_ids']),
            'classification_status': config['classification_status'],
            'classification_date': config['classification_date'],
            'epistemic_note': config['epistemic_note'],
        })
    write_csv(release / 'data' / 'core' / 'evidence_groups.csv', group_rows)
    manifest_path = release / 'manifests' / 'release.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['release_prepared_on'] = config['classification_date']
    manifest['comparative_classification'] = {key: value for key, value in config.items() if key != 'groups'}
    manifest['counts']['comparatively_classified_implementations'] = len(relations)
    manifest['counts']['comparative_groups'] = len(groups)
    manifest['comparative_group_counts'] = dict(sorted(Counter(row['comparative_group'] for row in relations).items()))
    manifest['stable_release_blockers'].append('Comparative policy postures are provisional author synthesis; no new claim-source adjudications accompany this overlay')
    manifest['claim_boundary'] = config['epistemic_note']
    files = sorted(path for path in (release / 'data').rglob('*') if path.is_file())
    manifest['files'] = {path.relative_to(release).as_posix(): {'sha256': sha256(path), 'bytes': path.stat().st_size} for path in files}
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (release / 'manifests' / 'checksums.sha256').write_text(''.join(f'{sha256(path)}  {path.relative_to(release).as_posix()}\n' for path in files + [manifest_path]), encoding='utf-8')
    return manifest


def main() -> None:
    build_core()
    manifest = add_comparative_layer(RELEASE)
    print(json.dumps({'comparative_group_counts': manifest['comparative_group_counts'], 'empirical_claims_checked_unchanged': manifest['counts']['control_effectiveness_claims_checked']}, indent=2))


if __name__ == '__main__':
    main()
