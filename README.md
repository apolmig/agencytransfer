# Agency Transfer Benchmark

[![Deploy GitHub Pages](https://github.com/apolmig/agencytransfer/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/apolmig/agencytransfer/actions/workflows/deploy-pages.yml)

> **Draft in progress.** Part of Miguel Guerrero’s Cambridge:ERA research on
> **Frontier AI, Harmful Manipulation, and Election Security**. This is
> independent research, not an official ERA benchmark.

Agency Transfer Benchmark (ATB) is a source-linked retrospective release map of model
behaviour that may matter for harmful influence. The public Home page leads
with a 2022–2026 release chart and a benchmark-native outcome. An explicitly
experimental modelled proxy remains selectable, but it is not an observed
benchmark result, human-efficacy measure, validated latent scale, or “Agency
Transfer Score.”

Explore the live project at **[miguelguerrero.eu/agencytransfer](https://miguelguerrero.eu/agencytransfer/)**.

## What the frontier view includes

- **Open-weight frontier:** exact public checkpoints released in 2022–2026
  with at least 100 billion total parameters, plus only the historical anchors
  needed to interpret a published series.
- **Hosted frontier:** provider-designated frontier APIs in a separate access
  class. Their parameter counts are recorded as undisclosed; the project never
  implies that they pass the 100B threshold.
- **Published observations:** dated results from InfoOpsBench v2, SaferAI’s
  GLM-5.2 risk evaluation, Anthropic system cards, APE, MASK, and DisElect,
  subject to each source’s protocol and licensing boundary.
- **Project testing:** a retained historical OpenRouter pipeline audit and
  prospective, versioned Inspect evaluations with route metadata, item hashes,
  aggregate labels, validation status, cost, and explicit failures. Raw
  harmful generations are not published.

Missing results remain visibly missing. Release date is used descriptively; it
does not establish that time caused a change in capability or safeguards.

## Naming corrections

The frontier registry uses canonical public names rather than requested or
rolling aliases:

- Sol, Terra, and Luna are **GPT-5.6** models, not GPT-5.4 variants.
- There is no general-text endpoint named “Gemini 3.1 Flash.” The relevant
  3.1 flagship is Gemini 3.1 Pro Preview; the lightweight endpoint is Gemini
  3.1 Flash-Lite. The later fast checkpoint is Gemini 3.6 Flash.
- Qwen3.6 Max Preview is a hosted model with undisclosed parameters. The open
  Qwen3.6 checkpoint is below the project’s 100B open-weight threshold.
- DeepSeek V4 is recorded as the exact **V4-Pro Preview** or V4-Flash
  checkpoint, never as an ambiguous family alias.

## Measurement boundary

A model producing or preserving a claim is not evidence that a person was
persuaded. A one-turn refusal rate is not a deployment safety guarantee. A
simulated agent completing campaign criteria is not evidence of real electoral
effect. ATB follows the longest defensible causal chain without skipping its
missing links:

`model behaviour → system design and access → repeated exposure → human effect → agency transfer → democratic harm`

The surrounding system may matter as much as the base model. Future work will
study prompts, memory, tools, organisational objectives, recommender systems,
interface defaults, and repeated contact in applications such as customer
service, elder care, and youth-facing services. Those scenarios are research
hypotheses, not claims that a named deployment has caused harm.

## 10 August 2026 OpenRouter pipeline pilot — historical failure

The first ATB-generated run sent 312 target calls to 12 requested OpenRouter
model slugs. It predates the strict protocol and failed the public comparative-
result gate. The failure is permanent for this run, not a validation task that
can be completed retrospectively:

- the upstream provider was not pinned and fallback was not disabled;
- requests were constructed in model-grouped order rather than randomised;
- the manifest recorded one seed, but the runner sent no seed parameter, so
  there was one uncontrolled stochastic draw rather than a seeded replicate;
- harmful-topic rates excluded invalid responses while benign rates used all
  six attempted controls, creating inconsistent denominators; and
- labels came only from automated judges, with parse failures and no blind human
  validation.

These defects and the decision to exclude the run were documented post hoc,
after the outputs were inspected. The artifacts therefore remain only as a
**historical, failed, exploratory pipeline audit**. They are not a full APE
replication, a model comparison, or evidence about persuasive efficacy. No
per-model pilot rate appears on the Testing page or contributes to the HMC
proxy. Read the
[model-by-model notes](research/testing/README.md) and
[aggregate artifacts](data/runs/2026-08-10-ape-frontier-pilot-v01/).

## Evaluation architecture

ATB separates adaptive discovery from confirmatory measurement. Inspect Petri
may find candidate failure modes in a controlled discovery split. A candidate
can enter only a later protocol version after human review, deduplication,
safety review, and a new preregistration; it never enters the confirmation wave
that discovered it. Petri outcomes describe discoverability under a stated
auditor, serving route, and budget, not prevalence or a benchmark ranking.

After human and dual-use review, Petri Bloom may turn a recurrent finding into a
candidate scenario suite. Its behaviour definition, generated scenarios,
rubric, and model roles must be frozen before a later evaluation; generated
judge scores are never imported directly into the ATB comparative ledger.

Confirmatory comparisons use frozen Inspect tasks, item sets, model conditions,
judges, estimands, and denominators. Inspect Scout scans persisted events
offline for missing calls, route anomalies, retries, truncation, and APE role or
cache violations. Content-judging Scout entry points remain fail-closed until a
target-only projection and a frozen, human-calibrated judge are available. A
Scout flag is not a benchmark score, a model-risk label, or evidence of agency
transfer.

## Benchmark linking

ATB uses Ho et al.'s Epoch AI–Google DeepMind paper
[A Rosetta Stone for AI Benchmarks](https://arxiv.org/abs/2512.00193) as the
conceptual reference for longitudinal measurement. Its central requirement is
overlap: model configurations evaluated across instruments must connect the
benchmark graph. ATB therefore records exact model-route configurations, tests
anchor coverage before fitting, and prespecifies sensitivity to anchor choice,
benchmark inclusion, overlap, and statistical form. Wave 1A creates a paired
within-DisElect anchor only; it does not connect DisElect to APE or MASK.

The present data do not support a shared latent scale. The deterministic
readiness diagnostic finds no model observed on at least four instruments and
no shared model anchor inside either multi-instrument construct family, so it
emits no capability scores, difficulty scores, rankings, trends, or forecasts.
This is also a construct boundary: harmful-manipulation behaviour is
multidimensional, and a mathematically connected graph would not by itself
justify collapsing unlike outcomes into one number.

See the [method and readiness gate](research/methods/BENCHMARK_STITCHING.md) and
the generated
[diagnostic](data/diagnostics/stitching-readiness-v0.1.json). Passing the gate in
a later wave would authorize an exploratory fit and sensitivity analysis, not
validate a public one-number index.

## Repository map

```text
data/models/          canonical frontier model registry
data/estimated/       versioned proxy rows, manifest, hashes, and sensitivity
data/diagnostics/     generated no-fit/readiness diagnostics
data/published/       transformed, source-linked published observations
data/runs/            sanitised historical audits and gated aggregate artifacts
evals/                Inspect harness, manifests, fixtures, and legacy runner
archive/              public recipient certificate and encrypted-archive policy
public/data/          versioned frontend data
research/testing/     one clear research note per project-tested model
research/methods/     construct map and benchmark-linking specification
scripts/              deterministic validation and preparation
src/                  React/TypeScript website
huggingface/          Hugging Face dataset card
METHODS.md            estimands, comparability, and statistics
ESTIMATED_SCORE.md    proxy formula, eligibility, uncertainty, and limitations
SOURCES.md            primary-source and model-identity ledger
OPENROUTER_PROTOCOL.md serving and route-integrity protocol
RESPONSIBLE_RELEASE.md safety and publication boundary
```

## Reproduce the website

Requirements: Node.js 24 and npm.

```bash
npm ci
npm run generate:estimate
npm run analyze:stitching
npm run validate:data
npm run typecheck
npm run build
```

`npm run build` writes the static site to `dist/`. GitHub Actions deploys that
artifact after a successful build on `main`.

To recompute the historical DisElect aggregates from an upstream checkout:

```bash
python scripts/prepare_diselect.py --source-dir /path/to/election-ai-safety
```

That script reads only the authors' released classification labels. It does not
generate or publish harmful model outputs.

## Inspect the historical APE-derived pilot

The legacy source and config are retained only to make the failed pipeline audit
inspectable. Its executable entry point is retired: it cannot be rerun, spend
API credit, or overwrite the historical run ID. Every new evaluation uses the
manifest-driven Inspect harness in [`evals/`](evals/README.md).

The public GitHub audit directory contains hashes, item-level automated labels,
sanitised route metadata, validation status, and a manifest, but no prompts or
generations. The 10 August results remain historical-failed even
if their old labels are later reviewed: routing, ordering, seed, and denominator
defects cannot be repaired after collection.

## Scientific and release commitments

- Compare only rows sharing an exact protocol and comparability group.
- Keep benchmark-native metrics separate. Any cross-source synthesis must be
  separately versioned, explicitly modelled, reproducible, uncertainty-aware,
  and never labelled an “Agency Transfer Score.”
- Require model bridges, within-construct anchors, protocol accounting, and
  split-invariant weighting before attempting any latent benchmark link.
- Record requested and returned model identities, provider, evaluation date,
  errors, tokens, and cost.
- Separate model refusal, provider block, transport failure, and invalid judge
  output.
- Keep adaptive discovery, scorer development, and confirmation on distinct,
  versioned splits. Scout flags remain QA metadata and never become native
  benchmark outcomes.
- Do not publish raw harmful generations, targeting material, or current-
  election operational content.
- Cite both ATB and every applicable primary source.

See [METHODS.md](METHODS.md), [data/PROVENANCE.md](data/PROVENANCE.md),
[RESPONSIBLE_RELEASE.md](RESPONSIBLE_RELEASE.md), and
[LICENSES/DATA.md](LICENSES/DATA.md) before reusing the data.

## Hugging Face and citation

The aggregate-only dataset is mirrored at
[apol/agency-transfer-benchmark](https://huggingface.co/datasets/apol/agency-transfer-benchmark).
The main-branch publishing workflow excludes raw prompts and generations. Use
[CITATION.cff](CITATION.cff) for the project citation and retain the citations
listed in [SOURCES.md](SOURCES.md) for upstream evidence.

Project code is Apache-2.0. Project-authored aggregate data and metadata are CC
BY 4.0, subject to the upstream rights documented in
[LICENSES/DATA.md](LICENSES/DATA.md). Upstream materials are not relicensed.
