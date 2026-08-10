# Agency Transfer Benchmark

[![Deploy GitHub Pages](https://github.com/apolmig/agencytransfer/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/apolmig/agencytransfer/actions/workflows/deploy-pages.yml)

> **Draft in progress.** Part of Miguel Guerrero’s Cambridge:ERA research on
> **Frontier AI, Harmful Manipulation, and Election Security**. This is
> independent research, not an official ERA benchmark.

Agency Transfer Benchmark (ATB) is a source-linked, longitudinal map of model
behaviour that may matter for harmful influence. The public site leads with a
fixed 2024–2026 release timeline and keeps each benchmark in its native metric.
It does **not** collapse compliance, persuasion attempts, honesty, or agentic
task completion into a synthetic score.

Explore the live project at **[miguelguerrero.eu/agencytransfer](https://miguelguerrero.eu/agencytransfer/)**.

## What the frontier view includes

- **Open-weight frontier:** exact public checkpoints released in 2025–2026
  with at least 100 billion total parameters, plus only the historical anchors
  needed to interpret a published series.
- **Hosted frontier:** provider-designated frontier APIs in a separate access
  class. Their parameter counts are recorded as undisclosed; the project never
  implies that they pass the 100B threshold.
- **Published observations:** dated results from InfoOpsBench v2, SaferAI’s
  GLM-5.2 risk evaluation, Anthropic system cards, APE, MASK, and DisElect,
  subject to each source’s protocol and licensing boundary.
- **Project testing:** bounded OpenRouter pilots with route metadata, item
  hashes, aggregate labels, validation status, cost, and explicit failures.
  Raw harmful generations are not published.

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

## 10 August 2026 OpenRouter pilot

The first ATB-generated run sent the same 20 hash-selected
noncontroversially harmful APE topics and six benign controls to 12 exact
OpenRouter routes (312 target calls). The automated judge labelled 7 of 18
usable DeepSeek V4 Pro responses and 1 of 20 Gemini 3.6 Flash responses as
attempts; it labelled zero attempts for the other ten endpoints among their
usable responses. Claude Fable 5 had only 7 usable harmful responses and
Qwen3.8 Max had 13, so their zeroes are especially weak evidence. No target call
had a transport failure.

The run cost estimate, including judges, was $2.1208. A preselected 20% audit
produced 46 parseable second-judge pairs (14.7% of responses) after two audit-
batch parse failures; agreement among those parsed pairs was 100%, but no blind
human validation has yet been completed. The results are therefore
**exploratory**, not a full APE replication or a ranking. Read the
[model-by-model notes](research/testing/README.md) and
[aggregate artifacts](data/runs/2026-08-10-ape-frontier-pilot-v01/).

## Repository map

```text
data/models/          canonical frontier model registry
data/published/       transformed, source-linked published observations
data/runs/            aggregate-only project run artifacts
evals/                bounded evaluation runner and frozen configs
public/data/          versioned frontend data
research/testing/     one clear research note per project-tested model
scripts/              deterministic validation and preparation
src/                  React/TypeScript website
huggingface/          Hugging Face dataset card
METHODS.md            estimands, comparability, and statistics
SOURCES.md            primary-source and model-identity ledger
OPENROUTER_PROTOCOL.md serving and route-integrity protocol
RESPONSIBLE_RELEASE.md safety and publication boundary
```

## Reproduce the website

Requirements: Node.js 24 and npm.

```bash
npm ci
npm run validate:data
npm run typecheck
npm run build
```

`npm run build` writes the static site to `dist/`. GitHub Actions deploys that
artifact after a successful build on `main`.

## Reproduce the bounded APE-derived pilot

The runner requires a local checkout of the pinned APE topic file and an
`OPENROUTER_API_KEY` environment variable. Never place a credential in a
command, config file, frontend bundle, issue, or report.

```bash
python evals/run_openrouter_ape_pilot.py \
  --config evals/config/ape-frontier-pilot-v0.1.json \
  --topics /path/to/AttemptPersuadeEval/src/topics/diverse_topics.jsonl \
  --run-dir data/runs/2026-08-10-ape-frontier-pilot-v01 \
  --raw-dir /restricted/private/run-directory
```

The public run directory contains only hashes, aggregate labels, sanitised
route metadata, validation status, and a manifest. The private directory must
remain access-controlled. Automated-only pilot results are labelled
**exploratory** until blind human validation is complete.

## Scientific and release commitments

- Compare only rows sharing an exact protocol and comparability group.
- Keep benchmark-native metrics separate; never publish an “Agency Transfer
  Score.”
- Record requested and returned model identities, provider, evaluation date,
  errors, tokens, and cost.
- Separate model refusal, provider block, transport failure, and invalid judge
  output.
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
