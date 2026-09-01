# Data dictionary

This dictionary describes the generated public release, not every table in the frozen working-register snapshot.

## Public core tables

| File | Primary key | Purpose |
|---|---|---|
| intervention_families.csv | control_family_id | Groups related implementations |
| implementations.csv | implementation_id | Concrete policy or operational controls; retains source coding |
| claims.csv | claim_id | Atomic legal, mechanism, and effect claims |
| sources.csv | source_id | Canonical source metadata and source-record verification |
| mechanisms.csv | mechanism_id | Causal mechanisms and failure points |
| legal_instruments.csv | legal_id | Scope-correct legal instruments |
| context_entities.csv | entity_id | Incidents, contexts, counterexamples, and studies |
| research_gaps.csv | gap_id | Evidence and construct gaps |
| policy_packages.csv | package_id | Candidate decision-oriented bundles |
| decision_gates.csv | criterion_code | Non-compensable gates |
| priority_claim_reviews.csv | claim_id | Designs, endpoints, limitations and treatment of six checked effect claims |
| evidence_groups.csv | group_id | Six provisional recommendation postures, source descriptions, membership and claim ceilings |

## Public relation tables

| File | Links |
|---|---|
| implementation_claims.csv | implementation ↔ claim |
| claim_sources.csv | claim ↔ source, including relation-specific verification |
| implementation_mechanisms.csv | implementation ↔ mechanism |
| implementation_contexts.csv | implementation ↔ case/context |
| implementation_gaps.csv | implementation ↔ research gap |
| package_implementations.csv | policy package ↔ implementation |
| implementation_evidence_groups.csv | Each of the 118 implementations ↔ exactly one provisional group |

## Public derived table

`atlas.csv` has one row per implementation. It is generated from the normalized tables and exposes publication-safe evidence fields alongside historical source coding. The new comparative fields are additive:

| Field | Meaning |
|---|---|
| comparative_group | A–F identifier, not an ordinal efficacy score |
| comparative_group_label | Working-register posture label |
| comparative_recommended_posture | Proposed policy action, not a demonstrated effect |
| comparative_rationale | Source-authored group-level rationale, not independent evidence |
| comparative_claim_ceiling | Group-level boundary; the source-specific claim may be narrower |
| comparative_classification_status | `provisional_author_synthesis` |
| comparative_classification_date | Date of classification, not a new empirical evidence cutoff |
| comparative_evidence_note | Explicit distinction between classification coverage and verification |

`evidence_groups.implementation_count` counts membership, not independent studies. The six memberships total 118. `implementation_ids` lists stable existing identifiers, including historical gaps in numbering. No identifiers are renumbered.

The source snapshot also contains provenance-only working tables such as `implementation_findings.csv`, `verification_log.csv`, and `changelog.csv`; these are not public release configurations. Package membership is normalized into `package_implementations.csv`.

Every public table has CSV and Parquet companions. ID collections are typed lists in Parquet and boolean review flags are typed booleans. The viewer's `train` split is only a display container.

## Semantic boundaries

- Legal force and application stage are not effectiveness.
- Mechanism evidence concerns the risk or causal mechanism, not necessarily the intervention.
- Intervention-effect and epistemic grades belong to bounded endpoints.
- `claim_role` is a relation type, not an evidence grade; `decision_tier` is a posture, not a score.
- The authoritative claim-specific source status is `claim_sources.verification_level`, not source-record review alone.
- Use `effect_claim_checked`, `publication_claim_class` and `publication_epistemic_status` for publication judgments. Fields without the publication prefix preserve source provenance.
- `comparative_*` fields never override those evidence fields. All 118 rows are classified, but only six effect claims have checked empirical relations in the retained core.

The release manifest separately records empirical curation, comparative classification, source provenance, counts and checksums.
