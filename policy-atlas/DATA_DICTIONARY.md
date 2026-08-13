# Data dictionary

## Core tables

| File | Primary key | Purpose |
|---|---|---|
| intervention_families.csv | control_family_id | Groups related implementations |
| implementations.csv | implementation_id | Concrete policy or operational controls |
| claims.csv | claim_id | Atomic legal, mechanism, and effect claims |
| sources.csv | source_id | Canonical source metadata and verification |
| mechanisms.csv | mechanism_id | Causal mechanisms and failure points |
| legal_instruments.csv | legal_id | Scope-correct legal instruments |
| case_index.csv | entity_id | Incidents, contexts, counterexamples, and studies |
| research_gaps.csv | gap_id | Evidence and construct gaps |
| policy_packages.csv | package_id | Decision-oriented bundles |
| decision_gates.csv | criterion_code | Non-compensable gates |
| priority_claim_reviews.csv | claim_id | Publication treatment for six priority effect claims |

## Relation tables

| File | Links |
|---|---|
| implementation_claims.csv | implementation ↔ claim |
| claim_sources.csv | claim ↔ source |
| implementation_mechanisms.csv | implementation ↔ mechanism |
| implementation_cases.csv | implementation ↔ case/context |
| implementation_gaps.csv | implementation ↔ research gap |
| implementation_findings.csv | implementation ↔ Parts 1–3 finding |

The source policy-packages table retains semicolon-separated implementation IDs
from the working register. The release builder normalizes these into
package_implementations.csv.

Every public table is available as CSV and Parquet. In Parquet, ID collections
in the derived atlas are typed lists and review flags are typed booleans.

## Important semantic boundaries

- legal_force describes normative force, not effectiveness.
- legal_status describes application stage, not effectiveness.
- mechanism_evidence_tier describes evidence for the risk or causal mechanism,
  not the control.
- intervention_effect_evidence describes evidence for the control itself.
- epistemic_status belongs to a bounded claim and must be read with its
  endpoint.
- decision_tier is a posture, not an ordinal score.
- verification_level states how deeply a source–claim relation was checked.
