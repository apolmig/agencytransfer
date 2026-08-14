---
pretty_name: Agency Transfer Policy Atlas
license: cc-by-4.0
language:
  - en
size_categories:
  - 1K<n<10K
tags:
  - tabular
  - ai-safety
  - ai-governance
  - public-policy
  - harmful-manipulation
  - election-integrity
  - agency-transfer
  - policy-interventions
  - legal-analysis
  - evidence-mapping
configs:
  - config_name: atlas
    default: true
    data_files:
      - split: train
        path: data/derived/atlas.parquet
  - config_name: intervention_families
    data_files:
      - split: train
        path: data/core/intervention_families.parquet
  - config_name: implementations
    data_files:
      - split: train
        path: data/core/implementations.parquet
  - config_name: claims
    data_files:
      - split: train
        path: data/core/claims.parquet
  - config_name: sources
    data_files:
      - split: train
        path: data/core/sources.parquet
  - config_name: mechanisms
    data_files:
      - split: train
        path: data/core/mechanisms.parquet
  - config_name: legal_instruments
    data_files:
      - split: train
        path: data/core/legal_instruments.parquet
  - config_name: context_entities
    data_files:
      - split: train
        path: data/core/context_entities.parquet
  - config_name: research_gaps
    data_files:
      - split: train
        path: data/core/research_gaps.parquet
  - config_name: policy_packages
    data_files:
      - split: train
        path: data/core/policy_packages.parquet
  - config_name: decision_gates
    data_files:
      - split: train
        path: data/core/decision_gates.parquet
  - config_name: priority_claim_reviews
    data_files:
      - split: train
        path: data/core/priority_claim_reviews.parquet
  - config_name: stable_release_gates
    data_files:
      - split: train
        path: data/core/stable_release_gates.parquet
  - config_name: claim_sources
    data_files:
      - split: train
        path: data/relations/claim_sources.parquet
  - config_name: implementation_claims
    data_files:
      - split: train
        path: data/relations/implementation_claims.parquet
  - config_name: implementation_mechanisms
    data_files:
      - split: train
        path: data/relations/implementation_mechanisms.parquet
  - config_name: implementation_contexts
    data_files:
      - split: train
        path: data/relations/implementation_contexts.parquet
  - config_name: implementation_gaps
    data_files:
      - split: train
        path: data/relations/implementation_gaps.parquet
  - config_name: package_implementations
    data_files:
      - split: train
        path: data/relations/package_implementations.parquet
  - config_name: stable_core_candidates
    data_files:
      - split: train
        path: data/derived/stable_core_candidates.parquet
  - config_name: candidate_registry
    data_files:
      - split: train
        path: data/derived/candidate_registry.parquet
---

# Agency Transfer Policy Atlas

A causal evidence map of interventions against AI-mediated manipulation.

This is the Part 4 artifact of *From Persuasion to Agency Transfer*. It maps
where an intervention could interrupt the chain from AI capability and control
to concentrated influence and democratic harm, who could implement it, and
what is known about its legal status, mechanism, effect evidence, failure
modes, rights risks, maturity, and evaluability.

## Status

`v0.2.0-beta.1` is a **research preview**, not a validated policy benchmark.
The `train` split name is only the Hugging Face Dataset Viewer container; these
records are not intended as model-training examples.

The release has 68 control families, 118 implementations, 320 atomic claims,
123 sources, 16 mechanisms, 15 candidate policy packages, and 24
non-compensable decision gates. It has no composite effectiveness score or
leaderboard.

This version records 30 **proposed** stable-core candidates for intensive
verification and retains the other 88 implementations in a candidate
registry. The editorial selection was retrospective and not preregistered; its
ledger records that apparent effect direction was not used, but no complete
118-row screening ledger exists. Every selected row remains blocked from
stable admission and ranking; no rank results are published.

## Critical evidence boundary

The existence of a law, the plausibility of a mechanism, and evidence that an
intervention works are different claims. In this preview:

- 20 of 123 source records participate in at least one type-eligible, fully
  supporting, checked claim–source relation; the other 103 remain candidate
  source records;
- 38 of 144 unique claim–source edges meet that public support rule; 10 other
  source-checked edges use a verification type that is not eligible for the
  linked claim type;
- 56 duplicate claim–source rows are removed from the generated release;
- 6 of 118 control-effect claims have a checked empirical source and a bounded
  observed endpoint; the other 112 remain unchecked;
- of the six priority implementations, three are now strong inference, two
  are open questions, and only technique-recognition prebunking retains an
  established component-effect classification;
- established legal-status rows without a checked legal claim are also exposed
  as provisional in the default atlas view; 25 of 53 currently have a checked
  primary-legal claim;
- the two project-mechanism rows are provisional until their mechanism claims
  receive claim-specific source verification.
- 3 of 118 mechanism claims currently have a fully supporting checked
  empirical relation; a legal-source check does not establish a mechanism.
- source-register action tiers appear only in normalized provenance fields;
  the default atlas omits them. Every implementation, family, and package has
  authoritative `publication_decision_posture=not_assessed`, because gate
  assessments are incomplete.

The dataset therefore supports mapping, audit, and research-priority setting.
It does not support claims that the listed controls reduce democratic harm.

## Configurations

`atlas` is the default denormalized view, one row per implementation. The other
configurations expose the normalized objects and bridge tables. Parquet keeps
multi-value ID fields as typed lists. CSV companions remain in the repository
for transparent diffs.

## Responsible use

Use the Atlas to compare intervention points, trace claims to sources, identify
coverage gaps, and design bounded evaluations. Do not treat a working-register
tier as a recommendation or effectiveness estimate. Do not infer vote effects
from reach, virality, or case linkage. The dataset contains no
participant-level or sensitive personal data, targeting profiles,
current-campaign playbooks, safeguard-bypass prompts, or raw harmful model
outputs. Public bibliographic and contributor names remain where required for
attribution.

## Licensing and citation

CC BY 4.0 covers project-authored taxonomy, annotations, relations, and
metadata. It does not relicense linked statutes, papers, reports, or other
third-party material. No DOI is minted for this beta. Cite the repository and
version using `CITATION.cff` until a stable, independently reviewed release.
Zenodo is the sole planned DOI archive; Hugging Face remains the Viewer and
distribution mirror.

Immutable source version:
https://github.com/apolmig/agencytransfer/tree/v0.2.0-beta.1/policy-atlas

Living source repository:
https://github.com/apolmig/agencytransfer/tree/main/policy-atlas

Immutable dataset version:
https://huggingface.co/datasets/apol/agency-transfer-policy-atlas/tree/v0.2.0-beta.1
