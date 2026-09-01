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
- CSV for diff-friendly review and typed Parquet for Hugging Face/Data Studio;
- a six-group comparative recommendation synthesis in
  [COMPARATIVE_EVIDENCE_GROUPS.md](COMPARATIVE_EVIDENCE_GROUPS.md).

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
publication-ready support.

The first evidence wave checked six priority effect claims because they carried
the strongest prior component-effect classifications. Re-audit rewrote each to
its observed endpoint and recoded five of the six implementation-level effect
classifications. **Those six records are an audit sample, not six effective
policies and not a shortlist.** See
[PUBLICATION_STATUS.md](PUBLICATION_STATUS.md),
[review/PRIORITY_VERIFICATION.md](review/PRIORITY_VERIFICATION.md), and
[COMPARATIVE_EVIDENCE_GROUPS.md](COMPARATIVE_EVIDENCE_GROUPS.md).

## Comparative recommendation groups

The 118 implementations are organised into six recommendation postures rather
than ranked by a composite effectiveness score:

- **A · Act now — bounded component evidence (5):** dark-pattern restrictions,
  forwarding friction, technique-based prebunking, official-source grounding,
  and data minimisation or user control;
- **B · Build now — control and observability infrastructure (41):** least
  privilege, confirmations, traces, independent access, incident response,
  continuity, and exit;
- **C · Enforce legal and operational baselines (31):** enforce applicable
  duties while measuring effect separately;
- **D · Auxiliary only — authenticity and disclosure (16):** provenance,
  labels, detection, authentication, sponsor notices, and repositories;
- **E · Pilot urgently — frontier-specific and structural controls (19):**
  memory and dependency monitoring, workflow guards, human-causal TEVV,
  assistant loyalty, impact assessment, and functional portability;
- **F · Research or hold — unvalidated general triggers (6):** universal
  benchmark gates, blanket release rules, and broad constitutional triggers.

The groups compare present support, causal fit, maturity, reversibility, and
evidence gaps. They are recommendation postures, not effect estimates. Even
Group A supports bounded outcomes such as consent quality, sharing friction,
recognition, factual accuracy, or reduced data exposure—not preservation of
democratic autonomy or electoral effect.

## Decision architecture

There is no composite “best policy” score. The release proposes
non-compensable gates for legality, rights, necessity, proportionality,
contestability, remedy, independent oversight, and anti-capture. Applying
those gates implementation by implementation remains a review task; this beta
does not publish gate-assessment results. Working-register action tiers—enforce
now, implement now, prepare, pilot, research or hold, and monitor or shape—are
therefore decision postures, not reproduced gate outcomes.

A control should first be tested at the CDE node it directly changes. A
forwarding limit may reduce rapid redistribution; a provenance rule may improve
attribution; a least-privilege architecture may prevent autonomous escalation.
None of those component endpoints alone establishes preserved voter agency or
election integrity.

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

- Public dataset version: v0.1.0-beta.2
- Source snapshot: sheets-v0.3
- Curation overlay: curation-v0.4-wave1
- Comparative recommendation synthesis: 2026-09-01
- Evidence freeze for comparative groups: 2026-08-28
- Language: English

## Citation

Until a stable release is archived, cite the repository and version. A DOI
should be minted only after claim-by-claim verification reaches the stable
release gate.

After publication, the immutable dataset snapshot for the current public
release is
`https://huggingface.co/datasets/apol/agency-transfer-policy-atlas/tree/v0.1.0-beta.2`.
