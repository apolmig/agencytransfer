# Agency Transfer Benchmark

[![Deploy GitHub Pages](https://github.com/apolmig/agencytransfer/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/apolmig/agencytransfer/actions/workflows/deploy-pages.yml)

**Research preview · Wave 0**

Agency Transfer Benchmark is an evidence-led, retrospective release-series view of AI capabilities, safeguards, and access conditions that may enable harmful influence. The first public artifact combines interactive, source-linked views of:

- agentic influence-campaign execution reported in Anthropic system cards;
- election-operation compliance recomputed from the DisElect authors' released labels;
- honesty under pressure reported in the original MASK paper; and
- a frozen candidate panel of open-weight model releases with at least 100 billion total parameters.

Explore the canonical live artifact at **[miguelguerrero.eu/agencytransfer](https://miguelguerrero.eu/agencytransfer/)**.

> **Measurement boundary:** Wave 0 does not directly measure agency transfer, durable human influence, vote change, democratic harm, or a universal model property. It maps enabling conditions. Metrics from different benchmarks are never averaged into an "Agency Transfer Score."

## What is live

| View | Evidence | Status |
|---|---|---|
| Agentic influence | Seven Claude releases, two simulated campaign scenarios, one comparable helpful-only protocol | Author-reported |
| DisElect | 13 models × 2,200 harmful prompts and 50 benign controls | Recomputed from author-released labels |
| MASK | Four open-weight models ≥100B, 1,500-item original evaluation | Author-reported |
| Model panel | 15 historically or currently relevant open-weight releases ≥100B | Frozen metadata snapshot |

The dates on the horizontal axes are model release dates. They are descriptive and do not identify a causal rate of progress.

## Reproduce the site

Requirements: Node.js 24 and npm.

```bash
npm ci
npm run validate:data
npm run typecheck
npm run build
```

`npm run build` writes the static site to `dist/`. GitHub Actions deploys that artifact to Pages after a successful build on `main`.

To recompute the DisElect aggregates from an upstream checkout:

```bash
python scripts/prepare_diselect.py --source-dir /path/to/election-ai-safety
```

The script reads only the authors' released classification labels. It does not generate or publish harmful model outputs.

## Repository map

```text
data/published/       canonical tabular results
public/data/          versioned frontend data
scripts/              deterministic preparation and validation
src/                  React/TypeScript site
huggingface/          dataset card used for the public Hub release
METHODS.md            estimands, comparability, statistics
RESEARCH_PLAN.md      staged research programme
OPENROUTER_PROTOCOL.md pinned-routing evaluation protocol
RESPONSIBLE_RELEASE.md safety and publication boundary
SOURCES.md            primary-source evidence ledger
```

## New evaluations

OpenRouter is a serving layer, not a neutral model identifier. Any future project rerun must pin a provider, disable fallback, record the returned canonical route and generation metadata, separate provider blocks from model refusals, and archive the catalogue observed on the evaluation date. See [OPENROUTER_PROTOCOL.md](OPENROUTER_PROTOCOL.md).

No API key is used by the website or committed to this repository. Keep credentials only in local environment variables. Published results are preferred over new API calls whenever the protocol and values are already available.

## Scientific and safety commitments

- Native metrics remain separate across benchmarks.
- Lines connect only comparable releases within a protocol and model family.
- Missing observations are not zeros.
- Project reruns require blinded human validation before public ranking.
- Raw harmful generations, targeting instructions, and current-election operational content are not published.
- Model weights, code, and data licences are recorded separately; "open-weight" is not used as a synonym for "open source."

Read [METHODS.md](METHODS.md), [RESPONSIBLE_RELEASE.md](RESPONSIBLE_RELEASE.md), and [data/PROVENANCE.md](data/PROVENANCE.md) before reusing the data.

## Citation

Use the metadata in [CITATION.cff](CITATION.cff). Each upstream result must also cite its original paper or system card; a project citation does not replace source attribution.

## Hugging Face release

The aggregate dataset is published at [`apol/agency-transfer-benchmark`](https://huggingface.co/datasets/apol/agency-transfer-benchmark). The [`publish-huggingface.yml`](.github/workflows/publish-huggingface.yml) workflow synchronises whitelisted public files when they change on `main` and can also be dispatched manually. It copies only the dataset card, aggregate CSVs, model manifest, provenance, and data-licence notice. The workflow requires a repository secret named `HF_TOKEN` with write access; it never exposes that token to the site or stores raw harmful generations.

## Licences

Project code is released under Apache-2.0. Original project-authored aggregate data and metadata are released under CC BY 4.0, subject to the upstream rights and restrictions documented in [LICENSES/DATA.md](LICENSES/DATA.md). Upstream datasets are not relicensed.
