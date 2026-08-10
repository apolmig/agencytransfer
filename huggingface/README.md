---
pretty_name: Agency Transfer Benchmark
license: cc-by-4.0
task_categories:
  - text-classification
language:
  - en
tags:
  - model-evaluation
  - ai-safety
  - manipulation
  - persuasion
  - longitudinal
size_categories:
  - n<1K
---

# Agency Transfer Benchmark — Wave 0

This dataset card accompanies the interactive [Agency Transfer Benchmark](https://miguelguerrero.eu/agencytransfer/) and its [source repository](https://github.com/apolmig/agencytransfer).

## Dataset summary

Wave 0 is a small, provenance-first collection of published aggregate results and model metadata. It includes:

- author-reported agentic influence-campaign completion rates from Anthropic system cards;
- DisElect classification proportions recomputed from the authors' released labels;
- author-reported MASK honesty-under-pressure metrics for selected open-weight models ≥100B; and
- a frozen model-release and serving-availability manifest.

The records do not contain prompts, raw harmful generations, personal data, or current-election operational content.

## Intended use

Use the records to reproduce the website, audit provenance, and compare results only within the stated `comparability_group` or protocol. Do not average metrics across benchmarks. Wave 0 does not directly measure agency transfer, human manipulation, vote change, or democratic harm.

## Files

| File | Description |
|---|---|
| `anthropic-agentic-influence.csv` | Helpful-only agentic influence series |
| `diselect-summary.csv` | Aggregate DisElect classification results |
| `mask-original-results.csv` | Original MASK table values for ≥100B open-weight models |
| `model-manifest.json` | Release, parameter, licence, and serving metadata |

## Provenance and limitations

Read [`data/PROVENANCE.md`](https://github.com/apolmig/agencytransfer/blob/main/data/PROVENANCE.md) and [`METHODS.md`](https://github.com/apolmig/agencytransfer/blob/main/METHODS.md). Each downstream use must cite both this project and the applicable primary source.

## Licensing

Project-authored aggregates and metadata are CC BY 4.0, subject to upstream rights. Upstream materials are not relicensed. Code is Apache-2.0.
