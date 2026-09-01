# Agency Transfer Policy Atlas

**Comparative policy recommendations, not six effective policies.**

This Part IV artifact asks which interventions could interrupt AI-enabled agency transfer, where they act, who can implement them, and what evidence, rights burdens and uncertainties attach to them.

## Current canonical release

The public dataset is **v0.1.0-beta.3**. It includes the working register's **v0.4 comparative classification** as actual data, not just narrative documentation: 118 implementation rows with group fields, six group records, and 118 implementation–group relations. CSV and typed Parquet are generated together.

The original empirical curation remains `curation-v0.4-wave1`. The recommendation layer is separately versioned as `comparative-v0.4-20260901`. The frozen `sheets-v0.3` snapshot and previous public versions are preserved.

## Coverage is not verification

**118/118 means classified, not empirically verified.** This synchronization adds no empirical claim-source adjudications and does not raise any pre-existing evidence grade.

The reproducible core still contains six checked empirical effect claims. At implementation level, the retained review supports one established bounded component effect, three strong inferences and two open questions. The other 112 effect claims still lack a checked empirical relation in the released core. That is a verification gap, not a finding that no relevant research exists or that those controls fail.

Twenty-two of 123 source records participate in at least one checked claim-source relation; the remaining 101 are candidates. The underlying review, not group membership, determines what can be cited as established. See [the priority review](review/PRIORITY_VERIFICATION.md) and [publication status](PUBLICATION_STATUS.md).

## Comparative recommendation groups

| Group | Implementations | Working posture |
|---|---:|---|
| A | 5 | Prioritize bounded controls: choice architecture, forwarding friction, technique-based prebunking, official-source grounding and data minimisation |
| B | 41 | Build control and observability: scoped permissions, confirmations, traces, independent access and incident response |
| C | 31 | Enforce relevant legal and operational baselines where applicable; measure effects separately |
| D | 16 | Use authenticity and disclosure for their specific vectors, as auxiliary controls |
| E | 19 | Pilot frontier-specific and structural controls, including memory, dependency, workflow and functional portability |
| F | 6 | Validate general capability and release triggers before using them as automatic gates |

These are **provisional author recommendations**, not an ordinal ranking of efficacy, effect size, legal force, cost-effectiveness or democratic importance. Support differs within A: the retained forwarding-limit review remains an open question. A does not mean five directly proven policies. Functional portability remains in E because downloadable data alone does not establish successful switching or restored agency.

[Detailed grouping and claim ceilings](COMPARATIVE_EVIDENCE_GROUPS.md) · [Machine-readable source](data/comparative-v0.4/groups.json)

## Research object

The Atlas retains 68 control families, 118 jurisdiction-specific or operational implementations, 320 atomic claims, 123 sources, 16 mechanisms, 28 legal instruments, 15 policy packages, 24 decision gates, nine cases or contexts and 16 research gaps. An implementation is the unit, not a general aspiration such as transparency.

```text
AI capability → controller → influence vector → target → change
→ agency transfer → concentration of power → democratic harm → intervention
```

A law's existence, a plausible mechanism, compliance and an intervention's effect are different propositions. The Atlas distinguishes established evidence, strong inference, plausible hypothesis and open question at claim level. Legal status, mechanism evidence, intervention-effect evidence, maturity and verification depth remain separate.

## Decision architecture

There is no composite best-policy score. Proposed non-compensable gates address legality, rights, necessity, proportionality, contestability, remedy, independent oversight and capture. This beta does not publish completed implementation-by-gate assessments. Recommendation postures are not permission to bypass those gates.

Test a control at the node it directly changes and measure its costs, failures, displacement and adversarial adaptation. A more complete log, a consent choice or reduced redistribution does not establish preserved democratic agency or an electoral effect.

## Reproduction and publication

```bash
python policy-atlas/scripts/build_release.py
python policy-atlas/scripts/validate_release.py
npm ci --prefix policy-atlas
npm --prefix policy-atlas run build:parquet
python -m unittest discover -s policy-atlas/tests -p 'test_*.py'
python policy-atlas/scripts/prepare_hf_release.py
```

The builder preserves every existing evidence field while joining the comparative overlay, checks unique and complete 118-row membership, and records source provenance and checksums. The existing publisher authenticates as `apol`, validates exact staged and remote inventories, and binds a new immutable version tag to the uploaded commit. Historical tags are not moved.

## Responsible use and citation

Use the Atlas for defensible prioritization, mechanism comparison, audit and bounded evaluation design, not as a proven-policy list. It contains no targeting profiles, operational campaign playbooks, bypass prompts or raw harmful outputs. Case linkage does not establish causal policy effectiveness.

This is a research preview, not an independently double-screened full-text review of 118 interventions. No DOI is minted for this beta. Use [CITATION.cff](CITATION.cff) and the [immutable v0.1.0-beta.3 dataset](https://huggingface.co/datasets/apol/agency-transfer-policy-atlas/tree/v0.1.0-beta.3).
