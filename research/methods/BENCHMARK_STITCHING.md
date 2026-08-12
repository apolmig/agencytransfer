# Benchmark stitching

> **Protocol note · v0.1 · 12 August 2026.** ATB is not currently ready to
> estimate a cross-benchmark latent capability scale. This document specifies
> the evidence gate that must pass before such a fit is attempted.

## The useful idea

Ho et al., *A Rosetta Stone for AI Benchmarks*, place model capability and
benchmark difficulty on one scale:

```text
score(m, b) = sigmoid(alpha_b × (C_m - D_b))
```

The attraction is real. A benchmark usually covers only a narrow range before
it saturates. Overlapping model results can connect older and newer instruments
without assuming that capability follows time or training compute.

ATB adopts the paper's discipline, not its conclusion. Harmful-manipulation
evidence is more heterogeneous than a collection of accuracy benchmarks. APE
records attempts to persuade. MASK records benchmark-defined lying. DisElect
and InfoOpsBench record harmful compliance under different safeguards and task
settings. Anthropic's agentic evaluation records simulated workflow completion
with helpful-only variants. A single latent number would currently absorb these
differences and call them capability.

## Current decision

Do not fit. As of 12 August 2026, the public ATB ledger contains 45 observations
from six instruments. No model appears in four or more instruments—the dataset-
screening analogue based on the paper's greater-than-three rule—and no pair of
instruments in the same ATB construct family shares a model anchor. That filter
is necessary here and never sufficient for identification.

The deterministic diagnostic is
[`data/diagnostics/stitching-readiness-v0.1.json`](../../data/diagnostics/stitching-readiness-v0.1.json).
Rebuild it with:

```bash
npm run analyze:stitching
```

It never emits a model capability or benchmark difficulty estimate. Its job is
to make an underidentified fit fail visibly.

## Construct boundary

Stitching is considered only within a defensible construct family:

| Family | Instruments | Present boundary |
| --- | --- | --- |
| Harmful operational support | DisElect; InfoOpsBench | No shared model anchor; protocols and serving conditions differ |
| Persuasion-attempt propensity | APE | One ingested protocol |
| Deceptive behaviour | MASK original; SaferAI MASK | No shared model anchor or equivalent public item-level records |
| Agentic influence execution | Anthropic agentic influence | One helpful-only protocol |

Cross-family overlap is useful for a multidimensional research design. It does
not identify one harmful-manipulation capability axis.

## Readiness gate

An exploratory fit requires all of the following before outputs are inspected:

1. enough model overlap to identify instrument difficulty and slope; the first
   diagnostic mirrors Ho et al. by requiring observations on at least four
   instruments per included model;
2. shared anchors inside each fitted construct family, not bridges created only
   by a different construct;
3. explicit treatment of prompt, scaffold, judge, endpoint, reasoning effort,
   safeguard condition, metric direction, and evaluation date;
4. item-level data where rights and safety permit it, or a weighting rule that
   is invariant to arbitrarily splitting one benchmark into several aggregates;
5. frozen inclusion rules, anchors, estimands, and missingness before fitting.

Passing this gate permits an exploratory model fit. It does not validate a
public index.

## First eligible analysis

When the gate passes, ATB will:

- fit within construct families before considering a multidimensional joint
  model;
- compare sigmoid and clipped-linear links;
- vary anchors, benchmark inclusion, and overlap thresholds;
- use leave-one-instrument-out checks and inspect model-by-instrument residuals
  for specialisation or protocol misfit;
- keep release time out of the latent fit, then examine time only after the
  measurement model is fixed;
- publish uncertainty and failed-fit diagnostics, not only rankings; and
- treat any acceleration detector as a monitoring flag. Ho et al.'s own
  synthetic analysis reports a high false-positive rate, so it cannot support a
  standalone claim of acceleration.

## Relationship to the HMC proxy

HMC proxy v0.1 is a hand-specified visual synthesis with explicit weights and
wide missing-data uncertainty. It is not the Ho et al. model, an Item Response
Theory estimate, or evidence that the four components form one latent trait.
It remains exploratory and must never be used to calibrate benchmark difficulty
or forecast capability. A later, validated stitching model would be a new
version and would not silently overwrite the proxy or any native outcome.

## Source

Anson Ho, Jean-Stanislas Denain, David Atanasov, Samuel Albanie, and Rohin Shah,
*A Rosetta Stone for AI Benchmarks*, arXiv:2512.00193v1 (2025):
<https://arxiv.org/html/2512.00193v1>. Authors are affiliated with Epoch AI and
Google DeepMind; the work was supported by Google DeepMind. Code:
<https://github.com/epoch-research/benchmark-stitching>.
