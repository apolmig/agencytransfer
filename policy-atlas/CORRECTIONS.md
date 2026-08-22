# Corrections, withdrawals, and tombstones

The Atlas is a living evidence map, but published releases are historical
records. Errors are corrected in a new version; immutable tags and archived
objects are never silently replaced.

## Reporting an error

Open a GitHub issue or pull request and include, where possible:

- affected release, file, and stable IDs;
- the statement believed to be wrong;
- proposed correction;
- primary source or reproducible evidence;
- likely impact on related claims, implementations, packages, gates, or
  rankings; and
- relevant conflicts of interest.

Do not post personal data, embargoed information, or sensitive security details
in a public issue. Contact route for sensitive corrections:
**TODO — establish a private channel before stable release.**

## Triage

Corrections are classified by their effect on the research record:

| Class | Examples | Expected release treatment |
|---|---|---|
| Editorial | Typo or link formatting with no change in meaning | Patch or next scheduled release |
| Metadata | Wrong date, jurisdiction label, identifier, or source metadata | Patch; revalidate affected relations |
| Evidentiary | Source does not support the claim, endpoint is overstated, or uncertainty is missing | Prompt new release; recode all downstream uses |
| Legal | Force, scope, applicability, or effective date is wrong or has changed | Prompt review by a human legal reviewer |
| Structural | Broken ID, foreign key, schema, manifest, checksum, or derived-view parity | Block publication until repaired |
| Withdrawal | Unlawful, unsafe, fabricated, irreparably flawed, or non-consensual material | Remove from current distribution where necessary and publish a non-sensitive tombstone |

No fixed response time is promised during the beta. Material errors affecting
public conclusions should be labelled as soon as confirmed and block further
release until dispositioned.

## Review and propagation

An identified human reviewer must confirm the correction. Evidence and legal
corrections require the corresponding domain reviewer. The review must examine
all downstream objects, including:

- claim-source relations;
- implementation classifications;
- packages and decision bands;
- gate assessments;
- figures, summaries, and documentation; and
- manifests, citations, and external mirrors.

Automation may identify affected records but cannot provide the human sign-off.
If reviewers disagree materially, the disagreement is recorded and the item
remains uncertain, excluded, or release-blocking.

## Tombstones

Withdrawn, superseded, merged, duplicated, or deprecated records retain their
stable ID in a tombstone. At minimum it records:

```yaml
id: <stable ID>
status: withdrawn | superseded | merged | duplicate | deprecated
effective_date: YYYY-MM-DD
reason: <bounded public explanation>
replacement_id: <stable ID or null>
affected_versions: []
evidence: []
reviewed_by: <human name>
decision_date: YYYY-MM-DD
```

IDs are never reused. If privacy, safety, or law prevents retaining the
original value, the tombstone preserves only the minimum non-sensitive audit
record.

## Versioning and notices

- Corrections follow the Semantic Versioning policy in
  [GOVERNANCE.md](GOVERNANCE.md).
- Every material correction appears in the changelog and release notes.
- A corrected release links backward to affected versions and forward from any
  maintained landing page.
- Checksums and manifests are regenerated; old checksums remain associated only
  with the old immutable release.
- If a future DOI version contains an error, deposit a corrected version and
  link the records. Do not mutate the archived DOI object.
- Retraction of a DOI version does not erase its metadata; the public notice
  must state why it should not be used.

The current beta has no DOI.
