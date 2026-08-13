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
---

# Agency Transfer Policy Atlas

A causal evidence map of interventions against AI-mediated manipulation.

This is the Part 4 artifact of *From Persuasion to Agency Transfer*. It maps
where an intervention could interrupt the chain from AI capability and control
to concentrated influence and democratic harm, who could implement it, and
what is known about its legal status, mechanism, effect evidence, failure
modes, rights risks, maturity, and evaluability.

## Status

`v0.1.0-beta.1` is a **research preview**, not a validated policy benchmark.
The `train` split name is only the Hugging Face Dataset Viewer container; these
records are not intended as model-training examples.

The release has 68 control families, 118 implementations, 320 atomic claims,
114 sources, 16 mechanisms, 15 candidate policy packages, and 24
non-compensable decision gates. It has no composite effectiveness score or
leaderboard.

## Critical evidence boundary

The existence of a law, the plausibility of a mechanism, and evidence that an
intervention works are different claims. In this preview:

- 98 of 114 source records require claim-by-claim checking;
- 56 duplicate claim–source rows are removed from the generated release;
- none of 118 control-effect claims has a checked empirical source;
- all six claims formerly labelled established component effects are exposed
  as provisional, with their priority review in a separate configuration.

The dataset therefore supports mapping, audit, and research-priority setting.
It does not support claims that the listed controls reduce democratic harm.

## Configurations

`atlas` is the default denormalized view, one row per implementation. The other
configurations expose the normalized objects and bridge tables. Parquet keeps
multi-value ID fields as typed lists. CSV companions remain in the repository
for transparent diffs.

## Responsible use

Use the Atlas to compare intervention points, trace claims to sources, identify
coverage gaps, and design bounded evaluations. Do not use a decision tier as
an effectiveness estimate. Do not infer vote effects from reach, virality, or
case linkage. The dataset contains no targeting profiles, current-campaign
playbooks, safeguard-bypass prompts, personally identifiable data, or raw
harmful model outputs.

## Licensing and citation

CC BY 4.0 covers project-authored taxonomy, annotations, relations, and
metadata. It does not relicense linked statutes, papers, reports, or other
third-party material. No DOI is minted for this beta. Cite the repository and
version using `CITATION.cff` until a stable, independently reviewed release.

Canonical repository:
https://github.com/apolmig/agencytransfer/tree/main/policy-atlas
