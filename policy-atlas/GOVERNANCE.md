# Governance

## Current status

The Agency Transfer Policy Atlas is a public research beta. Its current release
is not a validated policy ranking, does not meet the stable-release gate, and
must not receive a DOI. Governance documents describe the process the project
will use; their existence is not evidence that every role or review has already
been completed.

The repository is the canonical working record. Immutable release tags and
their manifests are the canonical records of published versions.

## Principles

Project decisions follow five rules:

1. Evidence claims remain narrower than the sources that support them.
2. Legal status, mechanism plausibility, observed effect, and implementation
   readiness remain separate.
3. Missing evidence is recorded as missing, never converted into a zero or a
   negative finding.
4. Rights, legality, necessity, proportionality, remedy, contestability,
   oversight, and capture risks are non-compensable considerations.
5. Published history is corrected transparently, not silently rewritten.

## Roles and authority

The project requires humans in the following roles. Automation may prepare
evidence packets, run validation, or suggest edits, but it cannot supply a
required sign-off.

| Role | Authority | Required human responsibility |
|---|---|---|
| Lead maintainer | Sets scope; resolves routine disputes; approves beta releases | Confirms release scope, unresolved limitations, conflicts, and public wording |
| Evidence editor | Accepts or rejects claim-source relations | Reads the cited source and verifies the bounded claim, endpoint, design, and limitations |
| Legal reviewer | Reviews legal force, applicability, jurisdiction, and dates | Checks primary legal or official sources and records uncertainty |
| Methods reviewer | Reviews synthesis and ranking methods | Checks inclusion rules, bias assessment, missing-data treatment, weights, and sensitivity analysis |
| Release manager | Produces and verifies release artifacts | Confirms reproducibility, manifests, checksums, inventories, licensing, and version labels |
| Independent reviewer | Challenges central packages and conclusions | Reviews without having authored the item under review and records disagreements |

One person may hold more than one operational role in a beta release, but may
not act as the independent reviewer of their own work. Stable or ranked outputs
require the distinct human sign-offs specified below. Current assignments and
vacancies are recorded in [MAINTAINERS.md](MAINTAINERS.md).

## Decisions

Routine corrections and additions are proposed through a pull request with the
evidence and review record required by [CONTRIBUTING.md](CONTRIBUTING.md).

- The lead maintainer may merge routine beta changes after the relevant human
  domain review.
- A change to the ontology, stable-release gate, inclusion criteria, decision
  gates, or ranking method requires written rationale, methods review, and lead
  maintainer approval.
- A stable release requires evidence, legal, methods, release-management, and
  independent-review sign-offs from identified humans.
- A ranking release additionally requires a frozen prospective protocol,
  published sensitivity analysis, and documented treatment of disagreement and
  missing evidence.
- A DOI may be minted only for a frozen release that has passed its declared
  release gate. A DOI identifies an archived object; it does not certify that
  its findings are correct or peer reviewed.

Material unresolved disagreement is not settled by averaging views. It is
recorded in the review log and release limitations. The lead maintainer decides
whether the affected item is excluded, marked uncertain, or blocks release.

## Release classes and versioning

The Atlas uses Semantic Versioning for project releases:

- `0.y.z-beta.n`: research preview; schemas and conclusions may change.
- `0.y.z`: pre-stable development release without the beta suffix; not a stable
  scientific endorsement.
- `1.0.0`: first release satisfying the published stable-release gate.
- patch: corrections that do not intentionally change the public schema or
  interpretation of the portfolio;
- minor: backward-compatible additions or new reviewed coverage;
- major: incompatible schema, ontology, or decision-method changes.

Scientific meaning takes precedence over mechanical compatibility. A change
that materially alters a conclusion, eligibility rule, or ranking method must
be conspicuous in the changelog even if the file schema is unchanged.

Tags and archived releases are immutable. Corrections are issued in a new
version and linked to the affected version. Stable identifiers are never
reassigned.

## Stable-release gate

A stable release must, at minimum:

- define a bounded stable core and disposition every claim in that core;
- verify legal status and applicability against primary sources;
- verify every effect claim against an eligible empirical source and state the
  observed endpoint, population, comparator, design, horizon, and limitations;
- publish implementation-level gate assessments and their evidence;
- publish explicit implementation-to-legal-instrument relations;
- complete independent review of the central policy packages;
- document double-coding scope and agreement, including disagreements;
- verify source licensing and attribution;
- reproduce all derived views and pass schema, foreign-key, parity, checksum,
  and inventory checks; and
- publish authorship, CRediT roles, ORCIDs where available, funding, and
  conflicts of interest.

The current beta does not satisfy this gate.

## Ranking governance

The project will not publish a universal numerical league table of policies.
Any future comparison must state its unit as an implementation in a specified
jurisdiction, threat, population, comparator, endpoint, and time horizon.

Non-compensable gates are applied before comparative scoring. Ranking is
permitted only among meaningfully comparable alternatives and must report:

- eligibility and exclusion decisions;
- evidence certainty separately from estimated effect;
- missing values as `unrankable`, not zero;
- weights and their justification;
- uncertainty and sensitivity to weights and assumptions;
- reviewer disagreement; and
- the underlying data and reproducible method.

If these conditions are not met, the project may publish a descriptive
evidence map or decision band, but not an ordinal ranking.

## Deprecation, withdrawal, and tombstones

Records are not deleted merely because evidence changes. A withdrawn,
superseded, duplicated, legally expired, or irreparably flawed record receives
a tombstone that preserves:

- its stable ID and last valid public label;
- status and effective date;
- reason and supporting source;
- replacement ID, when one exists;
- affected releases; and
- the reviewing human and decision date.

Tombstoned IDs cannot be reused. Harmful personal data, unlawful material, or
content that cannot safely remain public may be removed from current files,
but the release history must retain a non-sensitive tombstone explaining the
removal. The correction process is defined in
[CORRECTIONS.md](CORRECTIONS.md).

## Independence, funding, and conflicts

Funding and institutional support do not confer editorial authority unless
explicitly disclosed in this file and [MAINTAINERS.md](MAINTAINERS.md).
Contributors and reviewers must disclose financial, professional,
institutional, political, litigation, and advocacy interests that a reasonable
reader could see as relevant to the item reviewed.

The following project-level fields are deliberately unresolved and must be
completed before a stable release:

- Funding statement: **TODO — not yet declared in this governance record.**
- Institutional sponsorship: **TODO — not yet declared.**
- Project-level conflicts of interest: **TODO — not yet declared.**
- Final CRediT contribution statement: **TODO — not yet approved.**
- Contributor ORCIDs: **TODO — collect and verify where available.**

An empty disclosure is not interpreted as “no conflicts.”
