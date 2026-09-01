# Comparative recommendation groups

> **Current recommendations · 1 September 2026:** The later [source-linked review](review/source-linked-20260901/README.md) supersedes the A–F presentation for current recommendations. It distinguishes bounded human outcomes, technical authority, frontier defensive pilots and structural safeguards. This document retains the historical classification; the published beta.3 data and empirical verification flags are unchanged.

**Classification: 1 September 2026 · provisional author synthesis · not peer reviewed**

The six records originally selected for re-audit were the strongest prior effect claims, not six effective policies. The working register now assigns all 118 implementations to six recommendation postures. Public release v0.1.0-beta.3 publishes these assignments in the dataset itself.

## What this comparison can support

The groups combine evidence relevance, causal fit, implementation maturity and policy posture. They guide attention and evaluation; they do not establish an ordinal efficacy ranking. An intervention in E can be more structurally important than one in A. Group size is an inventory count, not an evidentiary vote.

| Group | Count | Recommendation | Examples | Claim ceiling |
|---|---:|---|---|---|
| A · Bounded controls | 5 | Prioritize narrow uses, subject to the actual source and local evaluation | Choice architecture; forwarding friction; technique-based prebunking; official-source grounding; data minimisation | Support varies. Intended endpoints are consent, sharing, recognition, factual accuracy and data exposure. Membership does not prove beneficial implementation effects. |
| B · Control infrastructure | 41 | Build and test control and observability | Scoped permissions; action confirmation; traces; independent access; incident response; viable institutional exit | Causal fit and adjacent-domain practice motivate the controls. A manipulation-specific effect estimate is not established for every implementation. |
| C · Applicable baselines | 31 | Enforce relevant duties and evaluate effects separately | Platform, advertising, targeting, data, audit, complaint and remedy requirements | Legal applicability must be checked for the jurisdiction and date. Compliance is not efficacy. |
| D · Auxiliary controls | 16 | Use authenticity and disclosure for their specified vectors | Provenance; labels; detection; caller authentication; sponsor notices; ad repositories | These do not by themselves constrain targeting, relationship-building or optimization power. Their contribution depends on coverage and response. |
| E · Bounded pilots | 19 | Pilot urgent frontier-specific and structural safeguards | Purpose and workflow controls; memory/dependency safeguards; assistant loyalty; agency assessment; functional portability | Mechanistic relevance is not demonstrated policy efficacy. Use prespecified endpoints, rights safeguards, stopping rules and displacement measures. |
| F · Validate general gates | 6 | Research before using general triggers as automatic gates | Broad capability/reach thresholds; APE/MASK release gates; blanket release rules; constitutional-significance triggers | Constructs, calibration and decision rules need validation. This posture does not suspend applicable law or preclude action on a separately evidenced serious risk. |

## Source-specific recommendation discipline

The underlying checked review retains **one established bounded component effect, three strong inferences and two open questions**. Immediate recognition of specifically taught manipulation techniques is the retained established component effect. A dark-pattern study measures effects of interface design, not automatically the effectiveness of a prohibition. A message experiment is not an evaluation of an official-source-connected assistant. A reduced-data recommendation study is not a test of conversational memory safeguards.

The forwarding-limit review remains an open question; its membership in A must not be read as a positive causal efficacy finding. Functional portability is in E: exporting an archive does not establish successful import, switching or restored agency. No current group establishes durable agency preservation or electoral protection.

## What has and has not been verified

All 118 implementations have a classification. The reproducible core still has six checked empirical effect claims; the other 112 lack a checked empirical claim-source relation. This release adds no adjudications. It does not establish that no relevant literature exists for those 112 or that their controls are ineffective.

Use `effect_claim_checked`, `publication_claim_class`, `publication_epistemic_status`, the linked sources and the measured endpoint for evidence judgments. The `comparative_*` fields are a separate author-synthesis layer. A source description or group rationale is not an independent empirical source.

## Agency-transfer test

```text
AI capability → controller → influence vector → target → change in belief,
attention, trust, behaviour or dependency → agency transfer → concentration
of power → democratic harm → mitigation
```

Locate the control at its directly targeted node. Ask who loses or gains authority, who holds the evidence, and whether affected people can understand, refuse, contest, exit and seek remedy. Evaluate that endpoint without borrowing strength from a different layer.

## Reproducibility

The source-defined memberships and original group descriptions are in [groups.json](data/comparative-v0.4/groups.json), with the workbook hash, source sheet and classification status. The generated release includes six `evidence_groups` rows, 118 `implementation_evidence_groups` rows and joined fields in the default `atlas`. Tests prohibit silent changes to existing evidence fields.

The recommendations remain provisional until priority claims receive source-specific adjudication and independent review. See [METHODS.md](METHODS.md), [PUBLICATION_STATUS.md](PUBLICATION_STATUS.md), and [the six-record audit](review/PRIORITY_VERIFICATION.md).
