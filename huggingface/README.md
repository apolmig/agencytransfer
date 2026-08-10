---
pretty_name: Agency Transfer Benchmark
license: cc-by-4.0
language:
  - en
tags:
  - model-evaluation
  - ai-safety
  - manipulation
  - persuasion
  - frontier-models
  - release-series
size_categories:
  - n<1K
configs:
  - config_name: hmc_proxy
    default: true
    data_files:
      - split: train
        path: "hmc-proxy-v0.1.csv"
  - config_name: frontier_models
    data_files:
      - split: train
        path: "frontier-models.csv"
  - config_name: infoopsbench
    data_files:
      - split: train
        path: "infoopsbench-2026-07-26.csv"
  - config_name: ape_mask_glm52
    data_files:
      - split: train
        path: "saferai-glm52-ape-mask.csv"
  - config_name: agentic_influence
    data_files:
      - split: train
        path: "anthropic-agentic-influence.csv"
  - config_name: diselect
    data_files:
      - split: train
        path: "diselect-summary.csv"
  - config_name: mask_original
    data_files:
      - split: train
        path: "mask-original-results.csv"
  - config_name: openrouter_pilot
    data_files:
      - split: train
        path: "runs/2026-08-10-ape-frontier-pilot-v01/aggregate.csv"
---

# Agency Transfer Benchmark — frontier draft 0.2

> Draft in progress. Part of Miguel Guerrero’s Cambridge:ERA research on
> **Frontier AI, Harmful Manipulation, and Election Security**. Independent
> research; not an official ERA benchmark.

This aggregate-only dataset accompanies the interactive
[Agency Transfer Benchmark](https://miguelguerrero.eu/agencytransfer/) and its
[source repository](https://github.com/apolmig/agencytransfer).

## What is included

- a canonical 2022–2026 frontier-model registry, separating open-weight
  checkpoints with at least 100B total parameters from hosted frontier APIs
  whose parameter counts are undisclosed;
- source-linked published observations from InfoOpsBench v2, SaferAI APE/MASK,
  Anthropic's helpful-only agentic evaluation, MASK, and DisElect;
- an experimental HMC proxy ledger with weights, modelled intervals, evidence
  grades, sensitivity checks, source IDs, input hashes, and explicit gaps;
- an exploratory 12-endpoint APE-derived OpenRouter pilot with aggregate labels,
  hashes, sanitised route metadata, cost, and validation status; and
- one short research note per project-tested endpoint.

The records contain no raw harmful prompts or generations, personal data,
credentials, targeting material, or current-election operational content.

## Exploratory OpenRouter pilot — excluded from comparative results

The 312-call pilot tested the pipeline, not the models. It used one APE
category, 20 harmful items per endpoint, provider-default routing, and automated
labels without blind human validation. Usable denominators were uneven and two
audit batches failed to parse. The run is therefore excluded from the public
Testing result view and from the HMC proxy. Aggregate artifacts remain available
for reproducibility and failure analysis.

## Files

The Hub Viewer exposes each tabular artifact as a separate configuration. Its
`train` label is a technical container required by the Viewer, not a claim that
these evaluation results form a model-training split.

| File | Description |
|---|---|
| `frontier-models.json` / `frontier-models.csv` | Canonical release, access, parameter, source, and route metadata |
| `frontier-observations.json` | Published and project-generated observations in native metrics |
| `hmc-estimates.json` / `hmc-proxy-v0.1.csv` | Experimental proxy medians, intervals, evidence grades, components, sensitivity, and source IDs |
| `hmc-frontier.json` | Draw-wise stepwise frontier envelopes for all, open-weight, and hosted views |
| `hmc-proxy-v0.1-manifest.json` | Fixed seed, weights, input hashes, counts, and limitations |
| `ESTIMATED_SCORE.md` | Full proxy method and interpretation boundary |
| `infoopsbench-2026-07-26.csv` | Frozen, transformed InfoOpsBench v2 paper snapshot |
| `saferai-glm52-ape-mask.csv` | Transcribed APE/MASK cohort results |
| `testing-notes.json` | Website research-note records |
| `runs/2026-08-10-ape-frontier-pilot-v01/` | Aggregate-only pilot artifacts |
| `anthropic-agentic-influence.csv` | Helpful-only simulated agentic-influence series |
| `diselect-summary.csv` | Aggregate DisElect classification results |
| `mask-original-results.csv` | Original MASK table values for selected ≥100B open-weight models |
| `PROVENANCE.md` | Source locators, transformations, and claim boundaries |

## Intended use and measurement boundary

Use these files to reproduce the website, audit provenance, and compare native
rows only inside an exact protocol or `comparabilityGroup`. The separately
versioned HMC proxy is an ATB-authored modelled synthesis, not an observed
benchmark result or “Agency Transfer Score.” Missing results are not zeroes.

InfoOps compliance is not human persuasion. APE detects attempted persuasion,
not persuasive success. MASK lying is not the complement of honesty. Simulated
agentic task completion is not deployed behaviour or electoral effect. The
OpenRouter pilot is automated-only and exploratory until blind human validation
is complete.

## Frontier inclusion rule

The open-weight panel requires an exact public instruction/chat checkpoint with
at least 100B total parameters. Hosted models use a separate provider-documented
frontier/flagship rule and record parameters as undisclosed. The 100B threshold
is a sampling rule, not a scientific boundary. Total and active parameters are
not interchangeable.

## Provenance, licensing, and citation

Read [PROVENANCE.md](https://github.com/apolmig/agencytransfer/blob/main/data/PROVENANCE.md),
[METHODS.md](https://github.com/apolmig/agencytransfer/blob/main/METHODS.md),
[ESTIMATED_SCORE.md](https://github.com/apolmig/agencytransfer/blob/main/ESTIMATED_SCORE.md), and
[RESPONSIBLE_RELEASE.md](https://github.com/apolmig/agencytransfer/blob/main/RESPONSIBLE_RELEASE.md).
Each reuse must cite both this project and the applicable primary source.

Project-authored aggregates and metadata are CC BY 4.0, subject to upstream
rights. Upstream materials are not relicensed. Code is Apache-2.0.
