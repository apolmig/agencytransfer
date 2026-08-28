# Agency Transfer Research Programme

[![Deploy GitHub Pages](https://github.com/apolmig/agencytransfer/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/apolmig/agencytransfer/actions/workflows/deploy-pages.yml)

> **Working research programme.** Independent research developed during the ERA:AI Summer Research Fellowship in Cambridge. It is not an official ERA benchmark and has not been peer reviewed.

This repository maintains Miguel Guerrero’s research programme on **frontier AI, harmful manipulation, election security, agency transfer, and concentrated democratic power**.

The programme asks a wider question than whether one model can produce persuasive text:

> When can frontier-AI capability become an operational influence system; who controls that system; what effects follow; and when does that control threaten democratic self-government?

The public project is at **[miguelguerrero.eu/agencytransfer](https://miguelguerrero.eu/agencytransfer/)**.

## Flagship argument

**Harmful Manipulation and Election Security**  
*The Capability–Deployment–Effect Gap*

> **The next Cambridge Analytica will be a system.**

Frontier AI can join generation, personal context, action, distribution, and feedback into influence infrastructure before its downstream effects can be independently measured. The democratic risk is not only false content. It is concentrated control over the environments in which attention, trust, participation, and choice are formed—and over the evidence needed to contest that influence.

The Capability–Deployment–Effect Gap preserves the missing causal bridges:

```text
capability → served system → controller and deployment → authentic exposure
→ human or institutional response → agency transfer → democratic harm
```

A model output is not a campaign. A campaign is not authentic exposure. Exposure is not persuasion. Persuasion is not manipulation. Manipulation of some people is not an electoral effect.

The reverse error is also wrong. Identity deception, unlawful data use, opaque distribution, unbounded action authority, or failed evidence preservation do not become harmless because final vote effects remain unknown.

## Four research parts

| Part | Research object | Strongest current contribution | Claim ceiling |
|---|---|---|---|
| **I. From output to operationalisation** | Served systems, exploratory probes, trace bundles, and access-to-control methods | Bounded routes can produce campaign-planning elements; technical conversion to reproducible intervention remains fragile | No successful intervention, autonomous execution, authentic exposure, persuasion, or electoral effect |
| **II. Capability and measurement** | Evaluation Registry and recovered APE-120 audit | Persuasion attempts are common among valid observations, but the measurement infrastructure remains non-confirmatory | No pooled manipulation score, human-effect estimate, safety ranking, or defensible frontier trend |
| **III. Election evidence** | Claim-level public evidence index | Operations, mechanisms, attribution, distribution proxies, and institutional responses are more observable than human or electoral effects | No prevalence estimate or validated national electoral effect |
| **IV. Policy evidence** | Causal policy atlas | Policy supply is broad; checked and bounded effectiveness evidence is sparse | No global policy-effect estimate or composite “best policy” ranking |

The four parts observe different links in one risk system. They are not an additive score or a completed causal ladder.

## Current public artifacts

### Part I

- **[Agency Transfer Lab](https://agency-transfer-lab.miguelguerrero.eu)** — deterministic evidence-harness and control-semantics prototype. It does not measure frontier capability, persuasion, behaviour change, agency transfer, actor uplift, or electoral impact.
- [`part1b/`](part1b/) — public access-to-intervention methods records and fail-closed contracts. These document technical process, failed attempts, and incomplete transitions; they do not establish a successful model intervention.

### Part II

- **[Frontier Evaluation Registry](https://miguelguerrero.eu/agencytransfer/)** — the current public interface, which will be preserved under Part II as the programme site is restructured.
- **[Agency Transfer Benchmark dataset](https://huggingface.co/datasets/apol/agency-transfer-benchmark)** — aggregate-and-provenance-only public mirror.
- [`evals/`](evals/) — direct evaluation harness, manifests, fixtures, validation, and historical audit records.

The registry retains benchmark-native outcomes. It does not pool unlike instruments into a scalar, ranking, latent capability estimate, or causal time trend.

### Part III

- **[AI, Elections and Agency Transfer Evidence Index](https://huggingface.co/datasets/apol/ai-election-manipulation-cases)**

The public count must be read as:

```text
1,087 relational rows → 64 catalogue entries → 10 core records
→ 8 incident-eligible records → 6 documented-manipulation records
```

Rows and catalogue entries are not cases. The corpus is purposive, not a prevalence sample.

### Part IV

- **[Agency Transfer Policy Atlas](https://huggingface.co/datasets/apol/agency-transfer-policy-atlas)**
- [`policy-atlas/`](policy-atlas/) — source, methods, schemas, validation, and versioned releases.

The beta Atlas contains 68 control families and 118 implementations. It maps interventions, mechanisms, authority, evidence, rights risks, maturity, and research gaps. It does not publish a numeric policy ranking.

## Programme control record

The canonical inventory, content architecture, routes, media requirements, and publication rules are under [`programme/`](programme/):

- [`project-manifest.json`](programme/project-manifest.json)
- [`ARTIFACT_INVENTORY.md`](programme/ARTIFACT_INVENTORY.md)
- [`SITEMAP.md`](programme/SITEMAP.md)
- [`CONTENT_MAP.md`](programme/CONTENT_MAP.md)
- [`MEDIA_INVENTORY.md`](programme/MEDIA_INVENTORY.md)
- [`PUBLISHING_RULES.md`](programme/PUBLISHING_RULES.md)

The manifest separates source versions, public releases, evidence cutoffs, canonical URLs, claim ceilings, public artifacts, and controlled material. Every site build validates it.

## Publication status

The flagship paper, white paper, one-page brief, research poster, and explainer videos are being canonicalised before publication through the programme site. They are not linked from this README until one stable public asset and URL have been fixed for each output.

The current root interface still presents Part II. The planned migration will make the programme the root publication and move the registry, evidence, and testing views under `/research/part-ii/`, while preserving existing links.

## Reproduce the current site

Requirements: Node.js 24 and npm.

```bash
npm ci
npm run generate:frontier
npm run analyze:stitching
npm run validate:programme
npm run validate:data
npm run typecheck
npm run build
```

`npm run build` writes the static site to `dist/`. GitHub Actions deploys that artifact after a successful build on `main`.

## Responsible release

The public programme may publish concepts, aggregates, source-linked claims, non-operational figures, defensive methods, and synthetic explainers. It does not publish raw harmful prompts or generations, campaign-ready outputs, targetable profiles, evasion instructions, live credentials, private reviewer material, or controlled traces that reproduce offensive content.

Synthetic explainers are illustrations. They are not evidence of a real operation, authentic exposure, behaviour change, or electoral effect.

## Citation and reuse

Use [`CITATION.cff`](CITATION.cff) for the repository citation and retain the citations required by each upstream source. Project code is Apache-2.0. Project-authored aggregate data and metadata are CC BY 4.0, subject to the upstream rights recorded in [`LICENSES/DATA.md`](LICENSES/DATA.md).
