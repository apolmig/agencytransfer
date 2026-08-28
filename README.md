# Agency Transfer Research Programme

[![Deploy GitHub Pages](https://github.com/apolmig/agencytransfer/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/apolmig/agencytransfer/actions/workflows/deploy-pages.yml)

> **Working research programme.** Independent research developed during the ERA:AI Summer Research Fellowship in Cambridge. It is not an official ERA benchmark and has not been peer reviewed.

This repository maintains Miguel Guerrero’s research programme on **frontier AI, harmful manipulation, election security, agency transfer, and concentrated democratic power**.

The canonical public programme is **[miguelguerrero.eu/agencytransfer](https://miguelguerrero.eu/agencytransfer/)**.

## Flagship argument

**Harmful Manipulation and Election Security**  
*The Capability–Deployment–Effect Gap*

> **The next Cambridge Analytica will be a system.**

Frontier AI can join generation, personal context, action, distribution, and feedback into influence infrastructure before its downstream effects can be independently measured. The democratic risk is not only false content. It is concentrated control over the environments in which attention, trust, participation, dependency, and choice are formed—and over the evidence needed to contest that influence.

```text
capability → served system → controller and deployment → authentic exposure
→ human or institutional response → agency transfer → democratic harm
```

A model output is not a campaign. A campaign is not authentic exposure. Exposure is not persuasion. Persuasion is not manipulation. Manipulation of some people is not an electoral effect.

## Public programme

- **[Programme](https://miguelguerrero.eu/agencytransfer/)** — editorial overview, CDE topology, evidence status, selected outputs, and current programme log.
- **[Research](https://miguelguerrero.eu/agencytransfer/research/)** — four connected research parts.
- **[Flagship working paper](https://miguelguerrero.eu/agencytransfer/paper/)** — current source-integrated web working edition.
- **[Outputs](https://miguelguerrero.eu/agencytransfer/outputs/)** — paper, white paper, one-page brief, poster, datasets, tools, methods, and code.
- **[Explainers](https://miguelguerrero.eu/agencytransfer/explainers/)** — synthetic scenarios and visual mechanism explainers with visible claim ceilings.
- **[About](https://miguelguerrero.eu/agencytransfer/about/)** — scope, author, evidence policy, citation, and responsible release.

## Four research parts

| Part | Research object | Strongest current contribution | Claim ceiling |
|---|---|---|---|
| **[I. From output to operationalisation](https://miguelguerrero.eu/agencytransfer/research/part-i/)** | Served systems, exploratory probes, trace bundles, and access-to-control methods | Bounded routes can produce campaign-planning elements; technical conversion to reproducible intervention remains fragile | No successful intervention, autonomous execution, authentic exposure, persuasion, or electoral effect |
| **[II. Capability and measurement](https://miguelguerrero.eu/agencytransfer/research/part-ii/)** | Evaluation Registry and recovered APE-120 audit | Persuasion attempts are common among valid observations, but the measurement infrastructure remains non-confirmatory | No pooled manipulation score, human-effect estimate, safety ranking, or defensible frontier trend |
| **[III. Election evidence](https://miguelguerrero.eu/agencytransfer/research/part-iii/)** | Claim-level public evidence index | Operations, mechanisms, attribution, distribution proxies, and institutional responses are more observable than human or electoral effects | No prevalence estimate or validated national electoral effect |
| **[IV. Policy evidence](https://miguelguerrero.eu/agencytransfer/research/part-iv/)** | Causal policy atlas | Policy supply is broad; checked and bounded effectiveness evidence is sparse | No global policy-effect estimate or composite “best policy” ranking |

The four parts observe different links in one risk system. They are not an additive score or a completed causal ladder.

## Principal artifacts

### Part I

- **[Agency Transfer Lab](https://agency-transfer-lab.miguelguerrero.eu)** — deterministic evidence-harness and control-semantics prototype. It does not measure frontier capability, persuasion, behaviour change, agency transfer, actor uplift, or electoral impact.
- [`part1b/`](part1b/) — public access-to-intervention methods records and fail-closed contracts. They document technical process, failed attempts, and incomplete transitions; they do not establish a successful model intervention.
- **[Manuel / Miami explainer](https://miguelguerrero.eu/agencytransfer/explainers/#manuel-miami)** — synthetic scenario illustrating target discovery, synthetic authority, distribution, repetition, and scale.
- **[Brazil 2026 storyboard](https://miguelguerrero.eu/agencytransfer/explainers/#brazil-2026)** — the final master remains withheld from the site until durable hosting, accessibility, and responsible-release requirements pass.

### Part II

- **[Frontier Evaluation Registry](https://miguelguerrero.eu/agencytransfer/research/part-ii/)** — source-linked release map preserving benchmark-native outcomes and visible missingness.
- **[Part II evidence](https://miguelguerrero.eu/agencytransfer/research/part-ii/evidence/)** — literature, construct boundaries, agentic execution, deception, historical election operations, and access conditions.
- **[Part II testing](https://miguelguerrero.eu/agencytransfer/research/part-ii/testing/)** — direct tests, exclusions, route integrity, validation status, and confirmatory publication gate.
- **[Agency Transfer Benchmark dataset](https://huggingface.co/datasets/apol/agency-transfer-benchmark)** — aggregate-and-provenance-only public mirror.

Legacy `/evidence/` and `/testing/` routes remain available and declare the new canonical URLs.

### Part III

- **[AI, Elections and Agency Transfer Evidence Index](https://huggingface.co/datasets/apol/ai-election-manipulation-cases)**

```text
1,087 relational rows → 64 catalogue entries → 10 core records
→ 8 incident-eligible records → 6 documented-manipulation records
```

Rows and catalogue entries are not cases. The corpus is purposive, not a prevalence sample.

### Part IV

- **[Agency Transfer Policy Atlas](https://huggingface.co/datasets/apol/agency-transfer-policy-atlas)**
- [`policy-atlas/`](policy-atlas/) — source, methods, schemas, validation, and versioned releases.

The beta Atlas contains 68 control families and 118 implementations. It maps interventions, authority, mechanism evidence, effect evidence, rights risks, maturity, and research gaps. It does not publish a numeric policy ranking.

## Programme control record

The canonical inventory, routes, content architecture, media requirements, and publishing rules are under [`programme/`](programme/):

- [`project-manifest.json`](programme/project-manifest.json)
- [`ARTIFACT_INVENTORY.md`](programme/ARTIFACT_INVENTORY.md)
- [`SITEMAP.md`](programme/SITEMAP.md)
- [`CONTENT_MAP.md`](programme/CONTENT_MAP.md)
- [`MEDIA_INVENTORY.md`](programme/MEDIA_INVENTORY.md)
- [`PUBLISHING_RULES.md`](programme/PUBLISHING_RULES.md)
- [`IMPLEMENTATION_PLAN.md`](programme/IMPLEMENTATION_PLAN.md)

The manifest separates source versions, public releases, evidence cutoffs, canonical URLs, claim ceilings, public artifacts, and controlled material. Every site build validates it.

## Reproduce the site

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

`npm run build` writes the complete static publication to `dist/`. GitHub Actions validates every canonical and legacy route before deployment to GitHub Pages.

## Responsible release

The public programme may publish concepts, aggregates, source-linked claims, non-operational figures, defensive methods, and synthetic explainers. It does not publish raw harmful prompts or generations, campaign-ready outputs, targetable profiles, evasion instructions, live credentials, private reviewer material, or controlled traces that reproduce offensive content.

Synthetic explainers are illustrations. They are not evidence of a real operation, authentic exposure, behaviour change, or electoral effect.

## Citation and reuse

Use [`CITATION.cff`](CITATION.cff) for the programme citation and retain the citations required by every upstream source. Project code is Apache-2.0. Project-authored aggregate data and metadata are CC BY 4.0, subject to the upstream rights recorded in [`LICENSES/DATA.md`](LICENSES/DATA.md).
