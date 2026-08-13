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

The curated preview contains 22 source records used in at least one checked
claim–source relation; the other 101 remain candidate source records. These
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
therefore decision postures, not reproduced gate outcomes.

These are decision postures, not effect estimates.

## Data

The source snapshot is under
[data/draft-v0.3/](data/draft-v0.3/). The internal Sheets version is retained
for provenance. Claim-specific corrections are applied from the transparent
[data/curation-v0.4/](data/curation-v0.4/) overlay; the current public dataset
release uses semantic version v0.1.0-beta.2.

Run:

~~~bash
python policy-atlas/scripts/build_release.py
python policy-atlas/scripts/validate_release.py
npm ci --prefix policy-atlas
npm --prefix policy-atlas run build:parquet
~~~

The validator checks stable IDs, uniqueness, foreign keys, controlled
vocabularies, package membership, family counts, source verification, and
claim-discipline invariants.

## Publication

Changes under `policy-atlas/` merged into `main` trigger the dedicated Hugging
Face publisher. The workflow fails closed unless it can authenticate as
`apol`, reproduce the release, encode the unresolved evidence blockers in the
beta manifest, pass validation, match the staged and remote file inventories
exactly, and bind the immutable version tag to the uploaded commit. It can also
be invoked manually.

## Responsible use

This dataset maps defensive interventions and public evidence. It does not
include targeting profiles, operational campaign playbooks, safeguard bypasses,
or raw harmful model outputs. Case links motivate control design; they do not
establish vote effects or counterfactual policy effectiveness.

## Status

- Artifact version: v0.1.0-beta.2
- Source snapshot: sheets-v0.3
- Curation overlay: curation-v0.4-wave1
- Source as-of date: 2026-08-11
- Release preparation date: 2026-08-13
- Language: English

## Citation

Until a stable release is archived, cite the repository and version. A DOI
should be minted only after claim-by-claim verification reaches the stable
release gate.

After publication, the immutable dataset snapshot for this release is
`https://huggingface.co/datasets/apol/agency-transfer-policy-atlas/tree/v0.1.0-beta.2`.
