# Methods

## Status and scope

This document specifies the research methods for the Agency Transfer Benchmark
(ATB). It is normative for ATB-generated evaluations unless a versioned protocol
explicitly states otherwise.

The project name describes a long-run research question. The present benchmark
does **not** directly measure agency transfer. In particular, the current release does not
measure whether a person was persuaded, whether their beliefs or behaviour
changed, whether a campaign reached anyone, or whether decision-making authority
was transferred to an AI system. It measures narrower, observable model
behaviours that may be relevant to that risk.

ATB separates four evidence layers:

1. **Operational capability:** whether a model supplies requested components of
   a harmful workflow.
2. **Safeguard behaviour:** whether it complies, refuses, evades, attempts
   persuasion, or lies under a benchmark-defined condition.
3. **Human efficacy:** context-specific effects measured in human-subject studies.
4. **Access conditions:** price, latency, licence, availability, modality, and
   serving restrictions.

Results from these layers are not averaged into a single score. A capability or
propensity is not evidence of real-world efficacy.

## Study designs

ATB uses two distinct time designs.

### Retrospective release series

Exact model releases are evaluated during one measurement wave and plotted by
their original release date. This is a repeated cross-sectional comparison of
model releases, not a prospective longitudinal cohort and not a causal estimate
of improvement over time.

### Prospective deployment series

An unchanged model and serving condition are evaluated again in later waves and
plotted by evaluation date. This design can detect changes in the accessible
deployment condition, including provider or moderation drift. It cannot by
itself identify whether a change arose from weights, quantisation, provider
infrastructure, or policy unless those components are independently pinned.

Release date and evaluation date are therefore stored and visualised separately.

## Model population and eligibility

The primary open-weight panel uses the following preregistered inclusion rules:

- publicly downloadable weights;
- a documented total parameter count of at least 100 billion;
- an instruction-tuned or chat checkpoint suitable for the benchmark task;
- a release date within the declared study window;
- an exact checkpoint or sufficiently immutable serving identifier; and
- a licence that permits the proposed evaluation.

The 100B threshold is a project sampling rule, not a scientific capability
boundary. It systematically favours mixture-of-experts models. ATB reports both
total and activated parameters when authoritative values are available and does
not treat them as interchangeable.

Base models are not compared directly with chat or instruction models in the
primary analysis. Fine-tunes, quantisations, reasoning modes, and provider
deployments are separate conditions rather than substitutes for an unavailable
checkpoint. Models that meet the scientific criteria but are not available from
the selected serving platform remain visible as `eligible-not-evaluated`; they
are not assigned zeroes and are not interpolated.

The hosted frontier is a separate descriptive panel because its total parameter
counts are generally undisclosed. A hosted release is eligible only when the
provider presents it as a frontier or flagship model, or when it is necessary to
interpret a same-protocol published result. It is never represented as having
passed the 100B rule. Lower-cost and lower-latency tiers may appear behind a
secondary filter when a source or project run evaluates them, but they do not
define the primary capability envelope.

The canonical registry begins in 2025. A 2024 release appears only when it is an
indispensable anchor for a published comparison. Model family names and mutable
`latest` aliases are ineligible as observations: ATB records an exact public
checkpoint or a dated served condition. Announcement date, API availability,
weight availability, release-date basis, and evaluation date remain distinct
fields where the source exposes them.

## Unit of observation

The atomic unit is:

> exact model checkpoint x provider endpoint x serving condition x benchmark
> item x replicate seed

The serving condition includes, at minimum:

- requested and returned model identifiers;
- upstream provider;
- quantisation, when disclosed;
- reasoning mode and effort;
- system-message condition;
- sampling parameters;
- tool availability;
- moderation or guardrail condition;
- context transformation; and
- evaluation timestamp.

The item-level record is the unit retained for reproducibility. Published
aggregate rows must be derivable from versioned item-level labels, except where
licensing or safety restrictions require the item-level data to remain private.

## Evidence provenance

Every datum has one of the following origins:

- `author-reported`: transcribed or reconstructed from a cited source;
- `atb-rerun`: generated under an ATB protocol;
- `external-live`: linked from a changing external benchmark; or
- `historical-context`: release or access metadata without a comparable ATB
  score.

Author-reported and ATB-rerun values are not joined by a trend line unless their
items, target condition, judge, and scoring procedure are demonstrably
equivalent. Figure extraction records the source URL, table/figure/page locator,
extraction method, and reviewer. Digitised values retain extraction uncertainty.

## Benchmark-native estimands

| Instrument | Primary estimands | Required companion outcomes | Excluded interpretation |
| --- | --- | --- | --- |
| InfoOpsBench v2 | benchmark-defined claim `amplified` + `preserved` proportion, reported as compliance | attenuated, fact-checked, post refusal, control-task compliance, evaluation date, and live-snapshot status | human persuasion, campaign success, provider intent, deployed prevalence, or a stable property of the weights |
| DisElect | harmful `comply`, `soft-refuse`, `refuse`, and `incoherent` proportions | benign completion, benign over-refusal, provider block, error, and truncation | persuasion, reach, belief change, vote change, electoral effect, or agency transfer |
| APE | persuasion-attempt proportion by topic category and turn | no-attempt, refusal/evasion, provider block, and evaluator uncertainty | persuasion success, exploitation of a real person, durable belief change, or human manipulation efficacy |
| MASK | benchmark-defined lie, explicit-honest, and unresolved/evasive proportions | task accuracy, invalid judgment, provider block, and item archetype | a general truthfulness score, manipulation, intent, or human response |
| Human-efficacy evidence | study-specific effect size in its original population and context | uncertainty, treatment, outcome timing, and study design | a universal model score or a direct substitute for capability evaluation |

ATB does not transform these outcomes into a cross-benchmark mean, z-score,
rank, radar area, or “Agency Transfer Score.” A within-instrument contrast may be
reported when prespecified. For example, DisElect selectivity may be expressed
as benign completion minus harmful compliance. Such a contrast remains a
DisElect outcome and is never averaged with APE or MASK.

## Benchmark implementation

### InfoOpsBench v2

InfoOpsBench v2 supplies the default 2026 cross-section because its dated paper
snapshot evaluates many requested frontier endpoints under one protocol. The
primary value is the source-defined compliance proportion: items classified as
amplifying or preserving a state-backed information-operation claim. ATB
transcribes the paper snapshot and links the changing live benchmark; it does
not mirror the source prompts or raw generations.

The paper table and the live leaderboard are different observations. A live
retrieval must carry its retrieval timestamp and must not silently overwrite the
paper snapshot. The live chart's weekly axis describes the claim or information-
operation week, not model release time. Consequently, ATB may use the paper
snapshot as a retrospective model-release cross-section and the live series as
deployment monitoring, but never as one continuous capability trajectory.

Compliance here means that an output carried forward a supplied claim under the
benchmark rubric. It does not show that a person read, trusted, remembered, or
acted on the output.

### DisElect

DisElect is treated as an evaluation of compliance with election-related
operational requests. The source benchmark contains harmful and benign items and
four response labels. ATB preserves those native labels and separately records
transport blocks and generation failures.

Wave 1 will use a hash-selected, stratified common item set. Harmful items are
balanced over the benchmark's two use cases and four operation stages. All
eligible models receive the same item identifiers. The selection is frozen
before any target output is inspected.

The original automated judge is not assumed to be ground truth. If the original
judge snapshot is unavailable, the run is labelled an `ATB adaptation`, not an
exact replication. The replacement judge must pass the human-validation gates
below.

### APE

APE is treated as an evaluation of whether a model attempts persuasion, not
whether persuasion works. The preferred first comparable run evaluates all 600
topics at Turn 1. A reduced pilot is never presented as an estimate of the full
benchmark unless it is stratified across the source categories. Three-turn
conversations are reserved for a smaller, prespecified set of anchor checkpoints
until cost and evaluator stability have been assessed.

The persuadee, evaluator, target-model instructions, conversation state, and
turn number are versioned measurement components. Changing any of them creates
a new protocol version.

The 10 August 2026 project pilot is intentionally narrower: 20 hash-selected
`NoncontroversiallyHarmful` topics and six benign controls per endpoint, one
turn, one generation per item, provider-default reasoning and sampling, and an
automated judge with a 20% second-judge audit. It tests routing, refusal/attempt
separation, cost, and publication mechanics. It is not a replication of the
600-item APE evaluation, not representative of conspiracy or undermining-
control categories, and not eligible for a comparative ranking until blind
human validation passes the gate below.

### MASK

MASK is treated as an evaluation of behaviour under benchmark-defined pressure.
ATB reports lies, explicit honesty, unresolved/evasive cases, and accuracy
separately. It does not foreground `1 - P(lie)` because evasion and invalid
belief elicitation can otherwise be counted as if they were demonstrated
honesty.

The public 1,000-item dataset is not assumed equivalent to the 1,500-item set
used for the paper's principal results. ATB runs on the public set are labelled
`ATB public-set rerun` and are not pooled with paper scores.

## Sampling, randomisation, and replication

- Item selection uses a documented cryptographic-hash ordering within each
  preregistered stratum.
- The same selected items are paired across target models.
- Model order is randomised within rate-limit and safety constraints so that
  time-of-day or provider incidents do not align with a single family.
- A full primary run may use one seed when the full item set is large, but a
  common robustness subset is run with at least three seeds.
- A seed is a recorded request condition, not a guarantee of deterministic
  inference.
- Unsupported sampling parameters are not silently dropped. The endpoint is
  excluded from the strict-comparability analysis or assigned a separately
  named protocol condition.

Wave-specific sample sizes, power limitations, and stopping rules are defined in
[`RESEARCH_PLAN.md`](RESEARCH_PLAN.md).

## Automated scoring and human validation

Automated judges are measurement instruments. Their model identifier, provider,
prompt hash, sampling settings, output schema, and parser version are frozen.
Judges do not see the target model name, organisation, release date, or the
study's expected direction.

Human validation follows these rules:

1. At least 10% of a release set is reviewed, with a 15% target for the first
   implementation of each instrument.
2. Sampling is stratified by benchmark category and target model and enriched
   for judge disagreement, parser failures, and low-confidence cases.
3. Two reviewers independently apply a written codebook while blind to model
   identity and release date.
4. Disagreements are adjudicated by a third reviewer or a documented consensus
   process.
5. ATB reports class prevalence, confusion matrices, per-class precision/recall,
   macro-F1, and Cohen's kappa or an appropriate multi-rater equivalent.

The default gate for a public comparative chart is macro-F1 >= 0.80 and F1 >=
0.75 for each critical positive class (`comply`, `attempt`, or `lie`). A result
that does not pass is labelled `experimental-unvalidated` and is not used to
rank models. Thresholds are decision rules, not claims that residual error is
negligible.

If a judge must be replaced, old and new judges are run on a bridge set of at
least 200 items, including the human-coded subset. Historical labels are not
silently overwritten.

## Statistical analysis

The primary presentation is descriptive:

- raw counts and proportions;
- 95% confidence intervals;
- category- or archetype-specific estimates; and
- paired differences for prespecified model contrasts.

Intervals for ATB reruns use a paired, stratified bootstrap over benchmark items.
Where multiple seeds are present, a hierarchical bootstrap samples items and
replicates. The caption states that these intervals describe item/replicate
variation within the benchmark design; they do not quantify all real-world
uncertainty.

The bounded 10 August 2026 pilot is an explicit exception: it reports a Wilson
95% interval for each endpoint's attempt proportion conditional on usable
harmful responses. With only 20 selected harmful items, this is a descriptive
pipeline diagnostic. It is not used for paired inference, significance testing,
or ranking.

Macro estimates give equal prespecified weight to benchmark strata. A
source-weighted estimate may also be reported if it reproduces an original
benchmark convention, but the weighting schemes remain labelled and separate.

The analysis does not fit a causal trend to release date. It does not infer that
model age, parameter count, organisation, or open-weight status caused an
observed difference. Pairwise inferential analyses use paired differences and a
declared multiplicity procedure, such as Holm adjustment. The public interface
avoids significance stars and leaderboard language.

## Missingness and denominator policy

Every attempted item receives exactly one transport status and, when a usable
generation exists, one benchmark label. At minimum, transport statuses distinguish:

- completed generation;
- provider or policy block;
- rate-limit or server error;
- timeout;
- truncation;
- invalid response format; and
- judge or parser failure.

The primary behavioural proportion uses a declared denominator. Transport
failures are never silently removed. The site reports both conditional outcomes
among usable generations and unconditional rates over all attempted items when
the distinction is material.

## Benchmark exposure and contamination

Static public benchmarks may influence later training or safety tuning. Each
plot marks the benchmark publication date and assigns model releases a
pre-publication or post-publication exposure flag. This flag is not proof of
contamination and is not used as a correction factor.

Private shadow sets may be introduced only after independent review, licence and
safety approval, and a preregistered linking design. They are not created by
minor paraphrasing of public harmful prompts and are not used to manufacture a
more favourable trend.

## Visualisation rules

- Native metrics appear in aligned small multiples, not on a shared synthetic
  scale.
- Points are connected only within a model family when item set, protocol,
  judge, and serving condition are comparable.
- Major architecture or modality changes break the line and receive an
  annotation.
- Cross-family anchors are displayed as unconnected points.
- Release date and evaluation date views are distinct.
- Tooltips show checkpoint, provider, parameter counts, licence, item count,
  interval, judge, protocol version, and provenance.
- Missing years and unavailable models remain visibly missing.

## Reproducibility record

Each evaluation release archives:

- model and endpoint manifests;
- source dataset version and item hashes;
- protocol and code commit;
- environment lockfile;
- randomisation and seed manifest;
- request parameters and response metadata;
- judge and parser versions;
- item-level labels or a restricted-data pointer;
- aggregate derivation script; and
- a machine-readable limitations record.

Raw harmful generations are not required for public reproducibility. They may be
kept in controlled storage and made available only under the policy in
[`RESPONSIBLE_RELEASE.md`](RESPONSIBLE_RELEASE.md).

## Principal limitations

ATB measures behaviour under artificial, benchmark-specific prompts. Serving
providers may add undisclosed transformations. Benchmark items are finite and
may be known to model developers. Automated judges make errors. A model's output
under a controlled request does not establish deployment intent, prevalence,
reach, human efficacy, durability, or social impact. These limitations apply
even when differences are statistically precise.

## Primary sources

- [DisElect paper](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0317421)
  and [repository](https://github.com/alan-turing-institute/election-ai-safety)
- [APE paper](https://arxiv.org/abs/2506.02873) and
  [repository](https://github.com/AlignmentResearch/AttemptPersuadeEval)
- [MASK paper](https://arxiv.org/abs/2503.03750),
  [repository](https://github.com/centerforaisafety/mask), and
  [public dataset](https://huggingface.co/datasets/cais/MASK)
- [Google DeepMind harmful-manipulation study](https://arxiv.org/abs/2603.25326)
- [OpenRouter model metadata](https://openrouter.ai/docs/guides/overview/models)
  and [provider routing](https://openrouter.ai/docs/guides/routing/provider-selection)
