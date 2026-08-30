# Agency Transfer Policy Atlas

**A causal evidence map of interventions against AI-mediated manipulation.**

The Policy Atlas is the Part 4 research artifact of *From Persuasion to Agency
Transfer*. It asks a narrower question than a conventional policy catalogue:

> Which interventions could interrupt AI-enabled agency transfer, at what point
> in the causal chain, under whose authority, and with what evidence,
> trade-offs, and implementation readiness?

This directory contains the first reproducible snapshot of the working
register. It is deliberately labelled **beta**. Most source records still
require claim-by-claim verification, and no numeric policy ranking is provided.

## What is here

- 68 control families and 118 jurisdiction-specific or operational
  implementations;
- 320 atomic legal, mechanism, and control-effectiveness claims;
- 123 canonical sources and explicit claim-specific verification status;
- 16 mechanisms, 28 legal instruments, 15 policy packages, 24
  non-compensable decision gates, 9 cases or contexts, and 16 research gaps;
- bridge tables for implementation–claim, claim–source,
  implementation–mechanism/context/gap, and package–implementation relations;
- a retrospective, non-preregistered editorial selection of 30 **proposed**
  stable-core candidates and the complementary 88-row candidate registry;
- 13 machine-readable stable-release gates, all still blocked or in progress;
- a prospective ranking protocol and repo-only templates with no scores or
  results; and
- CSV for diff-friendly review and typed Parquet for Hugging Face/Data Studio.

The unit of analysis is a concrete **implementation**, not a broad idea such as
“transparency”. Families group related implementations without collapsing
legal scope, jurisdiction, actor, or evidentiary status.

## Core causal chain

AI capability → controller → influence vector → target → change → agency
transfer → concentration of power → democratic harm → intervention

An intervention is mapped to the point it targets. The existence of a law, the
plausibility of a mechanism, and evidence that a control works are separate
claims.

## Evidence discipline

The Atlas distinguishes established evidence, strong inference, plausible
hypothesis, and open question. It also separates:

1. legal force and application;
2. mechanism evidence;
3. intervention-effect evidence;
4. operational maturity; and
5. source-verification depth.

The curated preview contains 20 source records used in at least one
type-eligible, fully supporting, checked claim–source relation; the other 103
remain candidate source records. These
records are useful for research triage but must not be treated as
publication-ready support. The first evidence wave checked six priority
effect claims, rewrote each to its observed endpoint, and recoded five of the
six implementation-level effect classifications. See
[PUBLICATION_STATUS.md](PUBLICATION_STATUS.md) and
[review/PRIORITY_VERIFICATION.md](review/PRIORITY_VERIFICATION.md).

## Decision architecture

There is no composite “best policy” score. The release proposes
non-compensable gates for legality, rights, necessity, proportionality,
contestability, remedy, independent oversight, and anti-capture. Applying
those gates implementation by implementation remains a review task; this beta
does not publish gate-assessment results. Working-register action tiers—enforce
now, implement now, prepare, pilot, research or hold, and monitor or shape—are
therefore provenance-only author postures, not reproduced gate outcomes. The
generated public `implementations` and `policy_packages` tables preserve those
source labels only as explicitly named `working_register_decision_tier`
provenance; families use `working_register_decision_posture`. The default
`atlas` omits the source tier. All three surfaces expose the authoritative
`publication_decision_posture=not_assessed`.

The next verification wave is intentionally narrower. Its retrospective
selection ledger records that apparent effect direction was not used, but this
process statement is not independently reproducible because no 118-row
screening-and-exclusion ledger was created. Every selected row therefore
remains blocked from stable admission and ranking. See
[protocol/STABLE_CORE_SELECTION.md](protocol/STABLE_CORE_SELECTION.md). The
ranking design is scenario-specific, treats gates as non-compensable and
missing required evidence as unrankable, and remains
`draft_not_preregistered`; see
[protocol/RANKING_PROTOCOL.md](protocol/RANKING_PROTOCOL.md).

## Data

The source snapshot is under
[data/draft-v0.3/](data/draft-v0.3/). The internal Sheets version is retained
for provenance. Claim-specific corrections are applied from the transparent
[data/curation-v0.4/](data/curation-v0.4/) overlay; the current public dataset
release uses semantic version v0.2.0-beta.1. The evidence curation remains
`curation-v0.4-wave1`; the additive v0.2 release introduces the provisional
selection, readiness tables, governance, and preservation controls without
upgrading any evidentiary claim.

Run:

~~~bash
uv sync --frozen --group dev
uv run --frozen python policy-atlas/scripts/build_release.py
uv run --frozen python policy-atlas/scripts/validate_release.py
npm ci --prefix policy-atlas
npm --prefix policy-atlas run build:parquet
uv run --frozen python policy-atlas/scripts/validate_release.py
~~~

The validator checks stable IDs, uniqueness, foreign keys, controlled
vocabularies, package membership, family counts, source verification, and
claim-discipline invariants. It also fails if a core candidate is presented as
stable or rankable, if a ranking template loses its draft/prohibited status,
or if the proposed core and registry stop being exact complements.

## Publication

Publishing is manual-only from a reviewed `main` commit. The operator must
enter this version and the exact commit SHA, then approve the protected
`policy-atlas-release` environment. The workflow fails closed unless it can
verify the matching immutable Git tag, authenticate as `apol`, reproduce the
committed release byte-for-byte, encode
the unresolved evidence blockers in the beta manifest, pass validation, match
the staged and remote inventories exactly, and bind the immutable version tag
before promoting the same bytes to the Hugging Face `main` branch.

The target dataset repository must already exist. The environment must require
a reviewer and restrict deployments to `main`; its
`POLICY_ATLAS_HF_TOKEN` secret must be a separate fine-grained token with write
access only to `apol/agency-transfer-policy-atlas`. These external settings
cannot be inferred from the workflow file and must be verified before dispatch.

The reviewed publication commit must replace the changelog's
`(unreleased candidate)` suffix and add `date-released` to `CITATION.cff` using
the actual **UTC** dispatch date. Create the immutable `v0.2.0-beta.1` Git tag
at that exact commit before dispatch; the workflow rejects a missing or moved
tag and records the full GitHub SHA in both Hugging Face commit messages.

## Responsible use

This dataset maps defensive interventions and public evidence. It does not
include targeting profiles, operational campaign playbooks, safeguard bypasses,
or raw harmful model outputs. Case links motivate control design; they do not
establish vote effects or counterfactual policy effectiveness.

## Status

- Artifact version: v0.2.0-beta.1
- Source snapshot: sheets-v0.3
- Curation overlay: curation-v0.4-wave1
- Stable-core selection: stable-core-selection-v0.1 — provisional
- Ranking protocol: ranking-protocol-v0.1 — draft, not preregistered
- Source as-of date: 2026-08-11
- Release preparation date: 2026-08-15
- Language: English

## Citation

Until a stable release is archived, cite the repository and version. A DOI
should be minted only after claim-by-claim verification reaches the stable
release gate.

If this reviewed candidate is published, its immutable dataset snapshot is
`https://huggingface.co/datasets/apol/agency-transfer-policy-atlas/tree/v0.2.0-beta.1`.
The matching source snapshot is
`https://github.com/apolmig/agencytransfer/tree/v0.2.0-beta.1/policy-atlas`.

Zenodo is reserved as the single DOI authority for a future stable release.
The local preservation bundler refuses this beta and performs no network or
deposit action; see [DOI_RELEASE.md](DOI_RELEASE.md).
