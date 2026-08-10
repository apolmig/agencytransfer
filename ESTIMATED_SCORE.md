# Experimental harmful-manipulation capability estimate

> **Draft in progress · HMC proxy estimate v0.1.** This is an ATB-authored,
> modelled synthesis. It is not a score reported by any cited paper, an observed
> measure of manipulation, or evidence of persuasion, agency transfer, vote
> change, or real-world harm.

## Purpose

The Home chart needs one legible longitudinal view while the underlying studies
measure different constructs. Version 0.1 therefore publishes a deliberately
uncertain proxy for **manipulation-relevant model behaviour** and keeps every
native benchmark available as a separate chart view.

The proxy does not infer a value from release date, parameter count, model
family, organisation, or a general-capability benchmark. A release with too
little direct evidence receives no number and remains visible as a hollow mark.

## Components and weights

| Component | Weight | Inputs | Interpretation boundary |
| --- | ---: | --- | --- |
| Operational harmful support, `O` | 0.40 | InfoOpsBench compliance or DisElect harmful compliance | Response or workflow support, not campaign efficacy |
| Agentic influence execution, `A` | 0.30 | Mean of Anthropic voter-suppression and polarisation task completion | Helpful-only simulated workflows, not default deployment |
| Harmful persuasion attempt, `P` | 0.20 | Equal-weight macro-average of the three ingested SaferAI APE harmful strata | Attempt propensity, not successful persuasion |
| Deceptive behaviour, `D` | 0.10 | MASK lie rate | Lying under benchmark pressure, not manipulation of a person |

Human-efficacy studies inform interpretation but do not enter v0.1. The small
ATB OpenRouter APE-derived pilot is excluded because it has not passed blind
human validation, route-integrity, coverage, or precision gates.

## Statistical model

For an observed count-like outcome with reported proportion `p`, denominator
`n`, and `k = round(n × p)`:

```text
p_component ~ Beta(k + 0.5, n - k + 0.5)
```

For each of the two agentic scenario aggregates, where only nine runs and a
rounded percentage are available, v0.1 uses a conservative sensitivity
distribution:

```text
p_scenario ~ Beta(0.5 + 9p, 0.5 + 9(1-p))
```

The two scenario draws are averaged. APE strata are drawn separately and
macro-averaged. An unobserved component is not set to zero or predicted from
time; it is represented as:

```text
p_missing ~ Uniform(0, 1)
```

For 20,000 draws using fixed seed `20260810`:

```text
S = 100 × (0.40O + 0.30A + 0.20P + 0.10D)
```

The chart shows the median and 80% modelled interval. The selected-point detail
shows the 95% modelled interval. These intervals describe this synthesis model,
not source-reported confidence intervals and not uncertainty about real-world
harm.

## Eligibility and evidence grade

`observed_weight` is the sum of component weights with direct evidence. A
numeric estimate is plotted only when:

1. `observed_weight >= 0.30`; and
2. operational support or agentic execution is observed.

Weights are never renormalised around available components.

| Grade | Rule | Public treatment |
| --- | --- | --- |
| A | Observed weight at least 0.80 and a direct capability component | Numeric estimate |
| B | Observed weight 0.60–0.79 | Numeric estimate; substantial limitations remain |
| C | Observed weight 0.30–0.59 | Numeric estimate with wide imputation uncertainty |
| D | Observed weight below 0.30 or exploratory-only evidence | No numeric estimate |

The full point-valued partial-identification range is also published: observed
component contributions are held at their medians while every missing component
is allowed to vary from 0 to 100.

## Longitudinal frontier

The dark-red Home line is the draw-wise running maximum among evidence-eligible
releases available by each release date:

```text
F_t = max(S_m) for releases m with release_date <= t
```

It is a step function, not a smoothed trend. It is monotonic by construction,
is sensitive to the number of compared models, and has winner's-curse bias. It
describes the best included estimate under v0.1; it does not describe average
industry progress or a causal effect of time.

The release axis is retrospective. Several models were evaluated later than
their release date, so it is not a contemporaneous cohort.

## Sensitivity checks

Every eligible row is recomputed under:

- equal 25% component weights; and
- capability-only weights, `O = 0.50`, `A = 0.50`, `P = D = 0`.

A row is marked `weight_sensitive` when its median moves by more than 10 points
or its median record-frontier status changes. Sensitivity results are not hidden
when they weaken the headline view.

## Reproduction and outputs

Run:

```bash
npm run generate:estimate
npm run validate:data
```

The deterministic script is
[`scripts/build-hmc-estimates.mjs`](scripts/build-hmc-estimates.mjs). It writes:

- [`public/data/hmc-estimates.json`](public/data/hmc-estimates.json) — frontend estimate ledger;
- [`public/data/hmc-frontier.json`](public/data/hmc-frontier.json) — draw-wise frontier steps for all, open-weight, and hosted views;
- [`data/estimated/hmc-proxy-v0.1.csv`](data/estimated/hmc-proxy-v0.1.csv) — downloadable rows with components, intervals, grades, sensitivity, and source IDs; and
- [`data/estimated/hmc-proxy-v0.1-manifest.json`](data/estimated/hmc-proxy-v0.1-manifest.json) — seed, weights, input hashes, counts, and limitations.

## Non-negotiable limitations

- The source protocols measure different constructs and deployment conditions.
- InfoOpsBench and DisElect mix capability with endpoint safeguards.
- Anthropic's agentic results use helpful-only variants with reduced harmlessness.
- Missing evidence is non-random, and Uniform imputation is a transparent
  ignorance model rather than a factual prior.
- API aliases, providers, guardrails, and model snapshots can drift.
- Benchmark exposure and evaluator error can bias results.
- The proxy has not been validated as a single latent construct.
- No row establishes that a person was manipulated or lost agency.

For native estimands, comparison gates, and responsible release requirements,
see [METHODS.md](METHODS.md), [SOURCES.md](SOURCES.md), and
[RESPONSIBLE_RELEASE.md](RESPONSIBLE_RELEASE.md).
