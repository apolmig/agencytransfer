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
  - config_name: evidence_groups
    data_files:
      - split: train
        path: data/core/evidence_groups.parquet
  - config_name: implementation_evidence_groups
    data_files:
      - split: train
        path: data/relations/implementation_evidence_groups.parquet
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

**Comparative policy recommendations, not six effective policies.**

This Part IV research artifact maps how interventions could interrupt AI-enabled agency transfer, who can implement them, and what the evidence supports. The democratic concern is concentrated control over people's information, choices, dependencies, and institutional decisions, not misinformation alone.

## Current release

`v0.1.0-beta.3` incorporates the working register's **v0.4 comparative classification** into the actual dataset: the default `atlas` has group fields for all **118 implementations**, with normalized `evidence_groups` and `implementation_evidence_groups` tables. The 68 control families, 320 atomic claims, and 123 source records retain their existing identifiers and evidence coding.

This is a **research preview and provisional author synthesis**, not a validated policy benchmark or a completed full-text systematic review. The `train` split is a viewer container, not a recommendation to train a model on these records.

## Comparative recommendation groups

| Group | Implementations | Working policy posture | Examples |
|---|---:|---|---|
| A | 5 | Prioritize bounded component controls, subject to source-specific limits | Choice architecture, forwarding friction, technique-based prebunking, official-source grounding, data minimisation |
| B | 41 | Build control and observability infrastructure; measure its effects | Least privilege, confirmations, traces, independent access, incident response |
| C | 31 | Enforce legal and operational baselines where applicable | Platform duties, targeting and data rules, audits, complaints and remedies |
| D | 16 | Use authenticity and disclosure as auxiliary controls | Provenance, labels, caller authentication, detection and ad repositories |
| E | 19 | Pilot frontier-specific and structural controls | Purpose and workflow controls, memory/dependency safeguards, loyalty audits, functional portability |
| F | 6 | Research before using general triggers as automatic gates | Unvalidated capability/reach thresholds and broad release triggers |

These groups combine evidence relevance, mechanism, maturity and decision posture. **They are not an ordinal ranking of efficacy, legal force, effect size, cost-effectiveness or democratic importance.** An intervention in E may be more structurally important than one in A. A does not mean that five implemented policies have directly demonstrated beneficial effects.

## What is verified, and what is not

**118/118 is classification coverage, not empirical verification coverage.** This release adds no new claim-source adjudications. Existing `effect_claim_checked`, `publication_claim_class`, source links and bounded endpoints remain authoritative and are not overwritten by group membership.

The retained wave-1 record contains six checked empirical effect claims, not six proven policies. At implementation level, it supports one established bounded component effect, three strong inferences and two open questions. Immediate recognition of taught manipulation techniques is the retained established component effect. In particular, forwarding limits and functional portability must not be represented as directly proven effective on the basis of that audit; portability remains in E.

The other 112 effect claims still lack a checked empirical claim-source relation in the reproducible core. This does **not** mean that no relevant literature exists or that those interventions fail. Twenty-two of 123 source records participate in at least one checked claim-source relation; the other 101 remain candidate source records. The comparative grouping does not close these verification gaps.

The raw `implementations` table preserves historical source coding. Use the default `atlas` and its `publication_*` fields for current publication-safe evidence classifications. A law's existence, compliance, a technical mechanism and a democratic effect are distinct propositions. Legal applicability must be verified for the relevant jurisdiction and date.

## Provenance and reproducibility

The empirical curation remains `curation-v0.4-wave1`. The separately versioned recommendation layer is `comparative-v0.4-20260901`, sourced from the working register's `v0.4 Evidence Groups` sheet. Its source workbook hash and provenance are recorded in `manifests/release.json`.

Group descriptions are author synthesis, not independent empirical sources. The builder checks complete, unique 118-row membership and preserves every pre-existing evidence field. CSV and typed Parquet companions, checksums and the immutable release tag make the published state inspectable. Previous tags are retained rather than moved.

## Responsible use

Use this Atlas to prioritize bounded controls, assemble complementary safeguards, inspect claims and design evaluations. Do not infer reduced agency transfer, preserved turnout or democratic integrity from labels, logs, consent clicks or message reach. Controls should preserve reflective agency, contestability, rights and meaningful exit; a stronger recommendation is not permission to bypass those conditions.

No targeting profiles, campaign playbooks, safeguard-bypass prompts, personal data or raw harmful model outputs are included. No DOI is minted for this beta. CC BY 4.0 covers project-authored annotations and metadata, not third-party sources.

[Canonical source and methods](https://github.com/apolmig/agencytransfer/tree/main/policy-atlas) · [Immutable dataset version](https://huggingface.co/datasets/apol/agency-transfer-policy-atlas/tree/v0.1.0-beta.3) · [Programme and working paper](https://miguelguerrero.eu/agencytransfer/paper/)
