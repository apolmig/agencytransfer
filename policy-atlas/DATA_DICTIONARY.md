# Data dictionary

This dictionary describes the generated public release, not every table in the
frozen working-register snapshot.

## Public core tables

| File | Primary key | Purpose |
|---|---|---|
| intervention_families.csv | control_family_id | Groups related implementations |
| implementations.csv | implementation_id | Concrete policy or operational controls |
| claims.csv | claim_id | Atomic legal, mechanism, and effect claims |
| sources.csv | source_id | Canonical source metadata and source-record verification |
| mechanisms.csv | mechanism_id | Causal mechanisms and failure points |
| legal_instruments.csv | legal_id | Scope-correct legal instruments |
| context_entities.csv | entity_id | Incidents, contexts, counterexamples, and studies |
| research_gaps.csv | gap_id | Evidence and construct gaps |
| policy_packages.csv | package_id | Candidate decision-oriented bundles |
| decision_gates.csv | criterion_code | Non-compensable gates |
| priority_claim_reviews.csv | claim_id | Designs, endpoints, limitations, and publication treatment for six priority effect claims |

## Public relation tables

| File | Links |
|---|---|
| implementation_claims.csv | implementation ↔ claim |
| claim_sources.csv | claim ↔ source, including relation-specific verification |
| implementation_mechanisms.csv | implementation ↔ mechanism |
| implementation_contexts.csv | implementation ↔ case/context |
| implementation_gaps.csv | implementation ↔ research gap |
| package_implementations.csv | policy package ↔ implementation |

## Public derived table

| File | Unit | Purpose |
|---|---|---|
| atlas.csv | implementation_id | One-row-per-implementation policy-facing view generated from the normalized tables |

The source snapshot also contains provenance-only working tables such as
`implementation_findings.csv`, `verification_log.csv`, and `changelog.csv`.
They are not public release configurations. The source package table retains
semicolon-separated implementation IDs; the release builder normalizes them
into `package_implementations.csv`.

Every public table is available as CSV and Parquet. In Parquet, ID collections
in the derived atlas are typed lists and review flags are typed booleans.

## Important semantic boundaries

- `legal_force` describes normative force, not effectiveness.
- `legal_status` describes application stage, not effectiveness.
- `mechanism_evidence_tier` describes evidence for the risk or causal
  mechanism, not the control.
- `intervention_effect_evidence` describes evidence relevant to the control;
  its scope is constrained by the linked claim endpoint.
- `epistemic_status` belongs to a bounded claim and must be read with its
  endpoint.
- `claim_role` describes how a claim relates to an implementation; it is not an
  evidence grade.
- `decision_tier` is a posture, not an ordinal score.
- `sources.verification_level` records review of the source record; the
  authoritative claim-specific status is
  `claim_sources.verification_level` on each relation.
- Public consumers should filter on `publication_claim_class` and
  `publication_epistemic_status`. The corresponding fields without the
  `publication_` prefix preserve working-register provenance.
