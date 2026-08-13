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
- 114 canonical sources and an explicit verification log;
- 16 mechanisms, 28 legal instruments, 15 policy packages, 24
  non-compensable decision gates, 9 cases or contexts, and 16 research gaps;
- bridge tables that preserve the many-to-many relations among those objects;
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

The current snapshot contains 98 sources marked “URL recorded — recheck before
citation”. Those records are useful for research triage but must not be treated
as publication-ready support. A priority review found that none of the six
effect claims labelled established was fully supported as written. See
[PUBLICATION_STATUS.md](PUBLICATION_STATUS.md) and
[review/PRIORITY_VERIFICATION.md](review/PRIORITY_VERIFICATION.md).

## Decision architecture

There is no composite “best policy” score. Every candidate first passes
non-compensable gates for legality, rights, necessity, proportionality,
contestability, remedy, independent oversight, and anti-capture. Surviving
candidates are assigned to action tiers: enforce now, implement now, prepare,
pilot, research or hold, and monitor or shape.

These are decision postures, not effect estimates.

## Data

The source snapshot is under
[data/draft-v0.3/](data/draft-v0.3/). The internal Sheets version is retained
for provenance; the first public dataset release uses semantic version
v0.1.0-beta.1.

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

## Responsible use

This dataset maps defensive interventions and public evidence. It does not
include targeting profiles, operational campaign playbooks, safeguard bypasses,
or raw harmful model outputs. Case links motivate control design; they do not
establish vote effects or counterfactual policy effectiveness.

## Status

- Artifact version: v0.1.0-beta.1
- Source snapshot: sheets-v0.3
- Source as-of date: 2026-08-11
- Release preparation date: 2026-08-13
- Language: English

## Citation

Until a stable release is archived, cite the repository and version. A DOI
should be minted only after claim-by-claim verification reaches the stable
release gate.
