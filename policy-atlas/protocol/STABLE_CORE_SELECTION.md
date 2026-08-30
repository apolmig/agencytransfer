# Retrospective stable-core verification-wave selection record

**Protocol:** `stable-core-selection-v0.1`

**Source release:** `v0.1.0-beta.2`

**Selection status:** provisional; not a stable release

**Selection design:** `retrospective_editorial_selection`

**Preregistration status:** `not_preregistered`
**Selection date:** 2026-08-14

## Purpose

This protocol defines a decision-useful subset of the Policy Atlas for intensive verification. It selects **30 proposed core candidates from 118 implementations**. Selection does not establish legal accuracy, causal effectiveness, readiness for adoption, or rank eligibility.

The remaining 88 implementations stay in the candidate registry. Non-selection means “outside this verification wave,” not “ineffective” or “rejected.”

## Unit and rule

The unit is an implementation, not an intervention family. A candidate is included only when it satisfies the electoral-relevance and auditability rules and contributes material portfolio coverage.

1. **Electoral decision relevance.** The implementation directly interrupts an election-influence pathway or supplies an essential enabling condition for doing so.
2. **Causal-chain coverage.** The portfolio covers capability and release, operator access, data and personalisation, authenticity, distribution and reach, independent evidence, preparedness and response, resilience, remedy, and pluralism.
3. **Jurisdiction and actor coverage.** The portfolio includes materially different legal and operational arrangements and assigns a plausible accountable actor. EU, Brazil, UK, US, global-standard and cross-jurisdictional examples are represented.
4. **Auditability.** The implementation has an observable duty, artefact, event, decision or outcome. `high` means the core obligation can normally be checked from records or tests; `medium` means important scope, attribution or outcome judgments remain.
5. **Non-duplication.** Similar controls are retained together only when they are a cross-jurisdiction comparator or act at a different layer in the same chain.

The selection ledger records that effect direction, current decision tier and
whether a finding was positive were not selection criteria. The
machine-readable file expresses this process declaration as
`effect_direction_used_for_selection=false` for every included row. It is not
evidence of blinded selection: the editorial selection occurred after beta.2
was available and no complete row-level screening/exclusion ledger was
created for all 118 implementations.

`display_order` is a non-ordinal presentation field: it follows ascending
`implementation_id` and carries no priority, quality, readiness, or rank
meaning.

## Portfolio strata

| Stratum | Proposed candidates | Purpose |
|---|---:|---|
| Upstream model assurance and release | 4 | Test safeguards and make release reasoning inspectable before exposure |
| Operator and agent accountability | 3 | Attribute high-risk access, constrain consequential agent actions and address relational impersonation |
| Authoritative election information | 1 | Reduce avoidable false administrative guidance |
| Data, profiling and personalisation | 4 | Limit vulnerability inference, targeting and persistent behavioural profiles |
| Authenticity and source disclosure | 5 | Compare provenance, disclosure, imprint, consent and prohibition controls |
| Distribution, advertising and reach | 4 | Address amplification, paid influence and private-channel virality |
| Independent evidence and assurance | 2 | Enable external measurement and recurring audit |
| Preparedness and incident response | 3 | Exercise, escalate and coordinate before and during incidents |
| Cognitive resilience | 1 | Test a pre-exposure, user-facing intervention |
| Remedy, electoral lifecycle and pluralism | 3 | Add complaint, high-risk lifecycle and structural information-environment controls |
| **Total** | **30** | |

The strata are analytical labels, not mutually exclusive ontologies. Each implementation is assigned one primary stratum to permit reproducible coverage checks.

## Rank eligibility

No selected implementation is rank-eligible in this version. Initial values have three meanings:

- `not_eligible_now__comparison_class_possible`: a later within-context comparison may be defensible after full claim verification, endpoint harmonisation and a predeclared comparator set.
- `not_eligible_now__contextual_assessment_only`: the control is a system condition or legal/institutional component that should be assessed by context and decision gates, not placed in a universal ordinal list.
- `not_eligible_now__pilot_evidence_required`: the implementation is sufficiently prospective that implementation evidence is needed before even defining a defensible comparison class.

A later ranking must use the unit `implementation × jurisdiction × threat × population × comparator × endpoint × horizon`. Missing evidence is never scored as zero. Rights, legality, proportionality, remedy and reversibility remain non-compensable decision gates rather than weighted score components.

## Verification required before stable-core admission

`proposed_core_candidate` may be changed to a stable-core status only after:

- legal status and scope are checked against a primary legal or official source;
- mechanism and effect claims receive an explicit disposition: supported, mixed/indirect, no eligible evidence found, or excluded;
- intervention, comparator, population, endpoint, design, uncertainty and limitations are extracted for every effect claim;
- decision gates and the relevant implementation-to-legal-instrument bridge are assessed;
- a second reviewer checks all high-impact judgments and double-codes a predeclared sample;
- identifiers, relations, CSV/Parquet parity, checksums and reproducible builds pass validation.

## Coverage and limitations

The 30 candidates span 25 intervention families, seven atlas layers and eight instrument classes. Baseline maturity in beta.2 is 22 operational, four pilot, two design-ready, one partial/uneven and one not yet applicable. These values describe the source release; they are not validation outcomes.

EU implementations are deliberately prominent because the current registry contains a comparatively dense, operative regulatory architecture. This is **not** geographic representativeness. Evidence from low- and middle-income democracies, non-European platforms, private messaging and resource-constrained electoral authorities remains thin. Brazil is retained as the principal election-specific comparator; UK, US and global controls prevent the core from becoming an EU-only legal inventory.

The proposed core is also intentionally tilted toward implementation-ready
objects: 22 of 30 candidates are coded operational, compared with 40 of 88 in
the candidate registry. That makes it a practical verification workload, not
a representative sample of the full register.

The authoritative authoring ledger is
[`stable_core_selection.csv`](https://github.com/apolmig/agencytransfer/blob/main/policy-atlas/data/curation-v0.5/stable_core_selection.csv).
Its IDs and copied metadata are checked against the immutable beta.2 release
at Git commit `f4b6472b2fe1faf98b05f958b016e057ce27b60c`; the frozen release
manifest SHA-256 is
`26fc870523b1a2482b505dbb590d7504507b034fca4726442c2d343eb184e926`.
The public joined view is `data/derived/stable_core_candidates.csv`; no
beta.2 row is modified by this record.
