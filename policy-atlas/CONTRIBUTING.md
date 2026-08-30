# Contributing

The Policy Atlas welcomes corrections, stronger sources, bounded claims, legal
updates, and reproducibility improvements. It is currently a beta research
artifact, not a policy recommendation service or a validated ranking.

## Before proposing a change

Open an issue or pull request that identifies the affected stable IDs and the
type of change. Do not include confidential information, personal targeting
data, operational manipulation playbooks, safeguard-bypass instructions, raw
harmful model outputs, or copyrighted source documents.

For a correction to published material, follow
[CORRECTIONS.md](CORRECTIONS.md).

## Evidence contributions

Each proposed claim must be atomic and distinguish among:

- legal force or applicability;
- mechanism evidence;
- intervention-effect evidence;
- implementation maturity; and
- contextual or background information.

A claim-source proposal must include:

1. affected claim and implementation IDs;
2. the exact bounded proposition being supported;
3. a canonical source URL or persistent identifier;
4. source type and publication or effective date;
5. for empirical claims: population, intervention, comparator, endpoint,
   design, sample, horizon, uncertainty, and material limitations;
6. for legal claims: instrument, provision, jurisdiction, legal force,
   application date, territorial and material scope, and primary official
   source;
7. whether the source supports, limits, contradicts, or merely contextualizes
   the claim; and
8. the contributor's relevant conflicts of interest.

Search results, snippets, secondary summaries, project-authored notes, and
language-model output do not by themselves verify a claim. Automated tools may
help locate or structure evidence, but an identified human reviewer must read
the source before a relation is marked checked.

Negative findings and failed implementations are welcome. “No eligible
evidence found” must state the search boundary and is not evidence of no
effect.

## Data and schema changes

- Preserve stable IDs. Never recycle an ID.
- Use a tombstone for withdrawal, supersession, duplication, or deprecation.
- Add controlled-vocabulary values only with definitions and migration impact.
- Keep source metadata separate from claim-level verification.
- Do not mutate frozen snapshots or immutable release tags.
- Update derived files only through the documented build path.
- Include tests or validation evidence for code and schema changes.

Material ontology, inclusion-rule, gate, or ranking-method changes require a
written rationale and the approvals in [GOVERNANCE.md](GOVERNANCE.md).

## Pull-request checklist

- [ ] Scope and affected IDs are stated.
- [ ] New or changed claims are atomic and bounded.
- [ ] Primary sources are used where required.
- [ ] Evidence details and limitations are recorded.
- [ ] Licensing and attribution have been checked.
- [ ] Stable IDs are preserved; removals use tombstones.
- [ ] Conflicts and relevant affiliations are disclosed.
- [ ] Human domain reviewer is identified or explicitly marked pending.
- [ ] Validation and tests pass, where applicable.
- [ ] Changelog impact and Semantic Versioning impact are stated.

Checking a box does not replace evidence in the pull request.

## Review and authorship

Merge authority does not equal scientific validation. Evidence claims require
human evidence-editor review; legal claims require human legal review. Stable
and ranked releases require the additional independent sign-offs described in
[GOVERNANCE.md](GOVERNANCE.md).

Authorship is based on contribution, not access or seniority. Before a stable
release, accepted contributors will be asked to confirm:

- preferred name and affiliation;
- ORCID, if available;
- CRediT roles;
- funding relevant to the contribution; and
- conflicts of interest.

Current project-level CRediT, ORCID, funding, and conflict records contain
explicit placeholders and must not be inferred from commit history.

## Licensing

By submitting project-authored data, annotations, taxonomy, relations, or
metadata for inclusion, you agree that the accepted contribution may be
released under CC BY 4.0 as described in [LICENSE](LICENSE). By submitting
code, tests, schemas, or build tooling, you agree that the accepted
contribution may be released under Apache-2.0 as described in
[LICENSES/CODE](LICENSES/CODE).

Do not submit third-party material unless its terms permit the proposed use.
Linking or describing a source does not transfer its copyright to this project.

## Conduct

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
