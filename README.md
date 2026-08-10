# Agency Transfer Benchmark — Wave 0 Evidence Map

[![Deploy GitHub Pages](https://github.com/apolmig/agencytransfer/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/apolmig/agencytransfer/actions/workflows/deploy-pages.yml)

> **Research draft.** Conducted during Miguel Guerrero’s ERA:AI Fellowship in
> Cambridge. Independent work; not an official ERA:AI benchmark.

Agency Transfer Benchmark (ATB) is a source-linked, retrospective release-series
map of model behaviour that may matter for harmful influence. The public site
uses a fixed 2024–2026 release window, with data through 10 August 2026, and
keeps each benchmark in its native metric. It does **not** collapse compliance,
persuasion attempts, honesty, or agentic task completion into a synthetic score.
The project name states the long-run research question; this release does not
measure agency transfer or effects on people.

Explore the live project at **[miguelguerrero.eu/agencytransfer](https://miguelguerrero.eu/agencytransfer/)**.

## What the release/reference view includes

- **Large open-weight panel:** exact public checkpoints released in 2025–2026
  with at least 100 billion total parameters, plus the historical anchors needed
  to interpret a published series. The threshold is a sampling rule, not a
  scientific definition of frontier capability.
- **Hosted frontier/comparison panel:** provider-designated frontier APIs and
  named comparison endpoints in a separate access class. Their parameter counts
  are recorded as undisclosed; the project never implies that they pass the
  100B threshold.
- **Published observations:** dated results from InfoOpsBench v2, SaferAI’s
  GLM-5.2 risk evaluation, Anthropic system cards, APE, MASK, and DisElect,
  subject to each source’s protocol and licensing boundary.
- **Project testing:** a bounded OpenRouter pilot with content-redacted
  item-level automated labels keyed by hashes, aggregates, route metadata,
  validation status, cost, and explicit failures. Raw statement and generation
  text is not published.

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
effect. ATB keeps the links in the research question separate:

`model behaviour → system design and access → repeated exposure → human effect → agency transfer → democratic harm`

The surrounding system is a separate part of the threat model. Future work will
study prompts, memory, tools, organisational objectives, recommender systems,
interface defaults, and repeated contact. These are research hypotheses, not
claims about a named deployment.

## 10 August 2026 OpenRouter pilot

The first ATB-generated run sent the same 20 hash-selected items from APE’s
`NoncontroversiallyHarmful` category and six benign controls to 12 named
OpenRouter routes. It produced 312 target request records, plus 47 automated-
judge batch records; the runner did not retain the number of underlying HTTP
attempts. The public artifacts contain content-redacted item-level automated
labels keyed by item and response hashes, aggregates, route metadata, costs,
failures, and one note per endpoint—not statement or generation text.

Provider routing, reasoning, and sampling were not pinned. A preselected 20%
audit produced 46 parseable second-judge pairs after two audit-batch parse
failures. The runner recorded matching labels, but pair-level audit labels were
not retained, so that agreement cannot be recomputed from public artifacts.
The primary judge is also a target endpoint and judged its own 26 outputs; the
audit judge evaluated one of its own sampled outputs. This weakens judge
independence, and no blind human validation has been completed. The pilot
remains in the Testing section and is excluded from the comparative frontier
chart. It is **exploratory**, not a full APE replication or a model ranking.
Read the
[model-by-model notes](research/testing/README.md) and
[aggregate artifacts](data/runs/2026-08-10-ape-frontier-pilot-v01/).

## Repository map

```text
data/models/          versioned model release/reference registry
data/published/       transformed, source-linked published observations
data/runs/            content-redacted item-level and aggregate run artifacts
evals/                bounded evaluation runner and frozen configs
public/data/          versioned frontend data
research/testing/     one research note per project-tested endpoint
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

To recompute the historical DisElect aggregates from an upstream checkout:

```bash
python scripts/prepare_diselect.py --source-dir /path/to/election-ai-safety
```

That script reads only the authors' released classification labels. It does not
generate or publish harmful model outputs.

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

The public run directory contains content-redacted item-level automated labels
keyed by hashes, aggregate tables, sanitised route metadata, validation status,
and a manifest. The runner rejects a private output directory inside the
checkout or public run tree. That directory still requires appropriate access
control. Automated-only pilot results are labelled **exploratory** until blind
human validation is complete.

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

The content-redacted dataset is mirrored at
[apol/agency-transfer-benchmark](https://huggingface.co/datasets/apol/agency-transfer-benchmark).
The main-branch publishing workflow excludes raw prompts and generations. Use
[CITATION.cff](CITATION.cff) for the project citation and retain the citations
listed in [SOURCES.md](SOURCES.md) for upstream evidence.

Project code is Apache-2.0. Project-authored data and metadata are offered under
CC BY 4.0, subject to the upstream rights documented in
[LICENSES/DATA.md](LICENSES/DATA.md). Upstream materials are not relicensed.
