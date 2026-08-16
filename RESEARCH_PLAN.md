# Research Plan

## Aim

Agency Transfer Benchmark (ATB) will build a versioned evidence base about model
behaviours that could contribute to harmful influence or delegated action. The
project will not treat those behaviours as direct observations of agency
transfer.

The near-term goal is a representative, reproducible release-series artefact for
large open-weight instruction models and a separately identified hosted frontier.
The long-term goal is to relate capability, safeguard behaviour, human-efficacy
evidence, and access conditions without presenting a modelled synthesis as an
observed fact.

## Current frontier scope — 2022–2026

The main chart covers 1 January 2022 through 31 December 2026 so that eligible
historical anchors and current releases appear on one stable axis. The open-weight panel requires at least 100B total parameters. The hosted
panel has no parameter threshold because the relevant providers do not disclose
comparable counts; it is selected by documented frontier/flagship status and
shown as a different access class.

The chart uses benchmark-native outcomes only. InfoOpsBench, DisElect, APE,
MASK, and Anthropic agentic outcomes retain their native metrics and are not
pooled into a scalar, ranking, or trend. New ATB runs remain excluded until
route-integrity and human-validation gates pass.

## Research questions

1. Under a common benchmark protocol, how does harmful operational compliance
   vary across exact open-weight model releases?
2. How often do the same releases refuse or over-refuse benign controls?
3. How do persuasion-attempt and deception-under-pressure outcomes differ from
   operational compliance?
4. How sensitive are results to seed, judge, provider endpoint, reasoning mode,
   and benchmark exposure?
5. Which apparent release-time changes persist when the same model/provider
   condition is measured prospectively?
6. Which system components—memory, tools, organisational objectives, interface
   defaults, recommenders, and repeated exposure—amplify or constrain a model's
   influence on attention, trust, preferences, behaviour, or dependency?

These questions are descriptive. ATB will not infer a causal effect of release
date, parameter count, architecture, organisation, or licence from the planned
observational comparisons.

## Longitudinal measurement and benchmark links

Ho et al., *A Rosetta Stone for AI Benchmarks*, motivates a network design in
which overlapping model evaluations link instruments across time. ATB adopts
that overlap discipline while rejecting an immediate one-dimensional fit across
different constructs. Before any latent analysis, the project generates
[`stitching-readiness-v0.1.json`](data/diagnostics/stitching-readiness-v0.1.json)
from a frozen
[`construct map`](research/methods/benchmark-constructs-v0.1.json).

The initial screen requires models observed on at least four instruments, shared
anchors inside every fitted construct family, explicit protocol/source effects,
and item-level or split-invariant weighting. These conditions are necessary for
the proposed analysis and not sufficient for identification or construct
validity. The current diagnostic fails all substantive gates. Native instrument
outcomes remain primary, and no time trend or acceleration claim is fitted in
Wave 1.

## Preregistration package

Before the first paid evaluation call in each wave, the repository will contain
or reference a time-stamped preregistration with:

- the model inclusion rule and frozen candidate manifest;
- accepted exact model and provider identifiers;
- benchmark version, item universe, strata, and sampling hash;
- scenario-family or template clusters and their split assignment;
- target sample size and stopping rule;
- generation and reasoning settings;
- judge, parser, and human codebook versions;
- primary and secondary estimands;
- missing-data and retry rules;
- validation gates;
- planned contrasts and multiplicity treatment;
- public/private data boundaries; and
- an estimated call and token budget.

Deviations are appended with a timestamp and rationale. They are not rewritten
into the original plan after results are seen.

## Discovery, confirmation, and QA

ATB uses three distinct lanes:

1. **Adaptive discovery.** Inspect Petri may probe a small, controlled development
   split to identify candidate behaviours, safeguard failures, and scenario gaps.
   Auditor model, target model, judge, turn budget, rollback policy, tools, seed,
   provider route, and exact seed/dimension inventories are recorded. Discovery
   yields are evidence that a failure could be elicited under that configuration,
   not an estimate of prevalence or a benchmark ranking.
2. **Candidate review.** New scenarios receive human review, semantic
   deduplication, construct review, and dual-use review. Accepted candidates are
   queued for a later protocol version. They do not enter the confirmation set
   used in the wave that discovered them.
3. **Confirmation.** Item families, target models, serving conditions, judges,
   estimands, denominators, and analysis are frozen before target outputs are
   inspected. Scorer development stops before this split is opened.

Petri Bloom may generate a candidate suite only after Petri findings pass human,
construct, deduplication, and dual-use review. The generated scenarios and rubric
are then frozen as a new inventory for a later wave; Bloom generation and target
evaluation never share the confirmation split that motivated the suite.

Inspect Scout may scan completed discovery and confirmation logs offline for
missing target calls, refusals, parser failures, loops, eval awareness, and
other anomalies. Scout is QA only: its flags do not enter native benchmark
scores or model rankings. A scanner used to exclude or
quarantine observations must itself be prespecified and validated against human
labels.

## Model panel strategy

The primary open-weight rule is public weights, instruction/chat tuning, and at
least 100B total parameters. The hosted frontier is a separate metadata and
evaluation panel with parameters explicitly recorded as undisclosed. The
canonical inventory is maintained in `public/data/frontier-models.json`; the
older `model-manifest.json` remains a historical Wave 0 artifact.

The panel has three roles:

- **Historical eligibility anchors:** releases such as BLOOMZ 176B and Falcon
  180B Chat that require self-hosting because an exact OpenRouter endpoint is not
  currently available.
- **Release-series models:** multiple exact checkpoints from the same family,
  used for within-family time plots when serving conditions are comparable.
- **Cross-sectional anchors:** representative architectures and licences used as
  unconnected comparison points.

An alias that cannot be resolved to an immutable checkpoint is not a valid
release-series model. A substitute fine-tune is not used for an unavailable
official checkpoint. Architecture changes, including changes in activated
parameters or modality, create a break in the series.

## Wave 0 — published evidence baseline and infrastructure freeze

### Work

- Audit every published data point against a primary source.
- Freeze model-card revisions, parameter counts, licences, and release-date
  bases.
- Snapshot the OpenRouter model and endpoint inventories.
- Validate JSON schemas and aggregate derivations.
- Create benchmark cards that state what each instrument observes and does not
  observe.
- Gate every future paid run on a complete benign-fixture preflight.

### Exit criteria

- No chart can load an unattributed numeric value.
- Author-reported and ATB-generated data are visually distinct.
- All current points pass schema and range validation.
- No secret, harmful raw generation, or restricted dataset is present in the
  public build.

## Historical failed pilot — 10 August 2026

The APE-derived OpenRouter pilot is not an input to the prospective wave plan.
It is retained as a post hoc pipeline audit because provider routing was not
pinned, requests were model-grouped, no seed parameter was sent, harmful and
benign rates used different denominators, and no blind human validation was
performed. These defects cannot be corrected retrospectively. Any repeat is a
new, preregistered protocol rather than a continuation of the historical run.

## APE-200/MASK-40 proposal status

The current prospective plan defines Wave 1 as DisElect, Wave 2 as APE, and
Wave 3 as MASK. It does not contain a frozen legacy APE-200/MASK-40 protocol or
the exact 240 stable IDs. ATB will not imply otherwise. If that proposal is
recovered, its item IDs, strata, prompts, roles, judges, denominators, source
hashes, and selection probabilities must be materialised as a separately
versioned manifest before execution; numeric `--limit` values are not an
equivalent sample design.

## Wave 1 — DisElect feasibility and first ATB rerun

### Claim boundary

Wave 1 will measure whether a model complies with, refuses, or fails to complete
benchmark-defined election-related operational requests. It does **not** measure
agency transfer, persuasion, exposure, belief change, voting behaviour, campaign
success, or electoral impact.

The native four-category response class is the confirmatory outcome. A separately
validated actionability rubric may be reported as a secondary ATB adaptation.
DisElect does not systematically elicit exploitative personalisation,
persistence or pressure, deception or concealment assistance, or reference-
grounded factuality; those axes are `not_applicable` rather than inferred from
their absence.

### Stage 1A: non-public routing and scoring canary

- Two exact snapshots: the earliest and latest comparable releases from one
  family that pass the endpoint gate.
- 40 harmful items: five from each of eight benchmark strata.
- 10 benign controls.
- One effective seed transmitted and verified for every item. Stage 1A does not
  estimate seed sensitivity.
- At least 30 outputs independently coded by two humans, with every disagreement
  resolved by a third, distinct human adjudicator.

The current executable protocol is frozen as
[`diselect-wave1a-v0.4.json`](evals/manifests/diselect-wave1a-v0.4.json). It
contains 50 items per target, two paired target snapshots, and therefore 100
target attempts. Sampling uses temperature 1, top-p 0.95, top-k 40, seed 42,
and a 4,096-token completion ceiling. Inspect 0.3.257 records `top_k` but does
not transmit it through its OpenAI-compatible builder, so ATB duplicates the
frozen value into the OpenRouter request body and verifies both representations
after the run. Provider, sample, and task retries remain zero. The total
planned envelope is 1,200,000 tokens and USD 1.00. Version 0.4 additionally
requires an exact non-resetting provider-side lifetime limit of USD 1.00; the
local sample and run controls remain post-response safeguards.

The immutable v0.2 diagnostic used the same items, routes, sampling parameters,
and scorer with a 700-token completion ceiling. It was rejected after 29 of 50
July-snapshot responses hit that ceiling; they remained explicit instrument
failures rather than being recoded as refusals or zeros. The v0.2 execution
therefore supports no model comparison. Version 0.3 raises only the completion
and token envelopes and uses a new preregistered blind-review sampling seed.
Version 0.4 preserves that design, hardens only the provider budget boundary,
and requires a fresh paired run of both snapshots. See the
[redacted incident record](evals/research-notes/diselect-wave1a-v0.2-diagnostic.md).

Wave 1A is also the first prospective anchor row for later benchmark linking.
Following Ho et al., it is useful only when the same exact model-route
configuration is subsequently evaluated on another construct-compatible
instrument. Until the overlap graph, benchmark coverage, residual checks, and
anchor/inclusion/model-form sensitivity tests pass, ATB will not fit a shared
scale or infer a time trend.

This canary is diagnostic and is not a public aggregate candidate. It is not
placed on the primary leaderboard, used to select the most favourable model
family, or interpreted as a release-series result. Thirty double-coded outputs
are a minimum check on the native response-class scorer, not validation of
multiple mechanism axes. If the probability sample lacks oracle support for any
native response class, scorer validation remains incomplete. Actionability
remains exploratory unless its own class support and validation gate are
prespecified and met.

### Stage 1B: representative release artefact

- All exact, comparable snapshots in the selected release family, up to six.
- 160 harmful items: 20 per benchmark stratum.
- All 50 benign controls, subject to source-licence confirmation.
- One primary seed for every item.
- Three distinct, effectively transmitted seeds on a common 120-item robustness
  subset, conditional on a versioned runner that preserves replicate identity.
- A 15% stratified probability sample for human validation, plus a separately
  reported audit sample enriched for judge disagreement and parser failure.
- If actionability is reported, a separate codebook, applicability rule, and
  human-validation result.

At a 50% proportion, a simple independent-binomial interval for 160 items has a
worst-case half-width of roughly 7.8 percentage points. The paired stratified
bootstrap, clustered by source template or scenario family where identifiable,
is the actual analysis, and its interval should be expected to differ.
The site will not imply fine-grained ordering that the uncertainty cannot
support.

### Wave 1 outcomes

Primary:

- harmful comply proportion;
- benign completion proportion; and
- the full four-category harmful response distribution.

Secondary:

- within-DisElect selectivity: benign completion minus harmful compliance;
- provider-block and generation-error proportions;
- seed sensitivity; and
- per-stratum estimates; and
- actionability distribution, only if the separately validated rubric passes.

### Wave 1 exit criteria

- The route is pinned and returned-model metadata matches the manifest.
- No unexplained fallback or provider substitution occurred.
- Automated scoring reaches macro-F1 >= 0.80 and critical-class F1 >= 0.75 on
  the human-coded set.
- Any reported actionability scorer independently passes its preregistered
  validation gate; other manipulation-mechanism axes remain `not_applicable`.
- Missingness and denominator choices are visible in the downloadable data.
- The responsible-release review approves aggregate publication.

If any criterion fails, results are labelled experimental and the site publishes
the failure mode instead of a comparative ranking.

## Wave 1C — broader DisElect panel

### Work

- Expand the common harmful sample to 480 items, balanced across the eight
  strata.
- Evaluate representative exact releases from at least three model families.
- Keep release-family lines separate from cross-sectional anchors.
- Run a provider-sensitivity subset on a second pinned endpoint when two
  endpoints expose the same checkpoint and compatible parameters.
- Add at least one pre-publication and one post-publication model release where
  the manifest permits, without treating exposure status as proof of
  contamination.

### Deliverables

- Release-date small multiples.
- Provider-sensitivity appendix.
- Human-validation report and confusion matrices.
- Cost, latency, error, and access-condition table.

## Wave 2 — APE

### Stage 2A: Turn-1 pilot

- Three anchor snapshots spanning the release period.
- A stratified subset covering all six APE topic categories.
- A frozen persuadee and evaluator condition.
- Human review of at least 15% of target-model outcomes.
- A versioned scorer adapter that preserves evaluator/parser uncertainty as
  unscored rather than converting it to no-attempt or zero persuasion.

### Stage 2B: comparable Turn-1 run

- All 600 public topics at Turn 1 for the selected release family.
- Identical topic IDs and conversation initialisation across target models.
- Attempt, no-attempt, refusal/evasion, evaluator failure, and provider block
  reported separately.
- Judge sensitivity analysis on a prespecified subset.

### Stage 2C: multi-turn anchors

- Full three-turn conversations for three preregistered anchor snapshots.
- No claim that simulated-user interactions estimate human persuasion efficacy.

The APE publication date is shown in every release-time plot. Post-publication
models are flagged as benchmark-exposed.

## Wave 3 — MASK

### Stage 3A: published-evidence layer

- Reconstruct author-reported results with exact source locators.
- Keep the original 1,500-item paper results separate from new public-set runs.
- Display lie, explicit-honest, and accuracy outcomes rather than only a
  complement-of-lie score.

### Stage 3B: public-set pilot

- 200–250 public items stratified across the six archetypes and item formats.
- Three anchor snapshots.
- Belief-elicitation, response, judge, and parser failures retained as explicit
  outcomes.
- Dataset redistribution remains off until its licence is confirmed.
- A role-aware Inspect adapter that pins the binary and numeric judges and
  verifies their route events independently of the target condition.

### Stage 3C: public-set run

- The complete 1,000 public items for three anchor snapshots.
- Extension to the wider panel only after judge validity and cost are reviewed.
- Public label: `ATB public-set rerun`; never presented as a replication of the
  held-out 1,500-item result.

## Wave 4 — historical self-hosted anchors

### Work

- Self-host exact, revision-pinned weights for eligible 2022–2023 models that
  are absent from OpenRouter.
- Record hardware, inference engine, tensor precision, chat template, context
  limit, and decoding stack.
- Run a bridge set on a model also available through OpenRouter to estimate
  serving-stack sensitivity.

Self-hosted and OpenRouter points are not connected by a line until the bridge
analysis supports comparability. Base models remain outside the primary
instruction-model analysis.

## Wave 5 — prospective measurement

At a preregistered quarterly cadence:

- rerun a fixed sentinel subset on frozen model/provider conditions;
- add newly eligible releases as new cohorts;
- archive model and endpoint inventories;
- perform a full rerun only after a material drift signal or at a declared annual
  wave; and
- use bridge evaluations whenever a provider or judge must change.

This creates a deployment-time series distinct from the retrospective
release-date series.

## External efficacy and live-benchmark evidence

Human-subject studies are maintained as a separate evidence panel. Effect sizes
remain tied to the study population, intervention, geography, outcome, and
follow-up period. ATB does not infer human efficacy from APE, MASK, or DisElect.

Dynamic benchmarks such as InfoOpsBench may be linked as contemporaneous
evidence. If their item set changes, scores from different dates are not treated
as measurements on a fixed longitudinal scale.

Any original study of human persuasion, belief, or behaviour requires a separate
ethics protocol, informed consent, participant-risk review, and analysis plan.
It is outside the current evaluation programme.

## Quality controls

Every wave includes:

- two-person review of model and source metadata;
- schema validation before chart generation;
- aggregate recomputation from item-level labels;
- blind human validation of automated scoring;
- explicit failed-call accounting;
- a secret scan and harmful-content scan before publication;
- a route-integrity report; and
- a signed methodological deviation log.

Adaptive Petri material and confirmation items are checked for split and
scenario-family leakage. Scout results appear only in the QA report and never
substitute for benchmark scoring or blind human validation.

## Decision rules

The project will pause a wave when:

- a requested model resolves to an unexpected checkpoint;
- fallback or provider substitution cannot be excluded;
- the benchmark or model licence is unclear;
- a judge fails the validation gate;
- a discovery item, near-duplicate scenario family, or post hoc scorer change
  contaminates the confirmation split;
- harmful outputs cannot be stored safely;
- more than 5% of attempted items fail for unexplained reasons; or
- a new result creates a credible, material misuse or disclosure concern.

A pause is reported as a study outcome, not repaired by silently changing the
sample, endpoint, prompt, judge, or denominator.

## Planned public artefacts

1. Interactive release-date chart with native DisElect metrics.
2. Unified evidence matrix with separate columns for DisElect, APE, MASK, human
   efficacy, and access. Cross-instrument outcomes remain separate.
3. Versioned model and endpoint manifests.
4. Machine-readable aggregate data and, where safe and licensed, item labels.
5. Human-validation and route-integrity reports.
6. Method, limitations, responsible-release, and citation pages.

## Planned system-level programme

Model-only tests cannot identify the risk of an application that combines a
capable model with memory, tools, recommender systems, commercial objectives,
asymmetric defaults, and repeated personalised contact. A later research stream
will therefore treat the deployed system—not the base model—as the unit of
analysis.

Initial scenarios are customer-service systems, elder-care assistants, and
youth-facing applications. The intended outcomes are contestability, calibrated
trust, choice persistence, preference change, behavioural compliance,
dependency, and the distribution of decision authority. Named models may be
used only as controlled components; their presence is not evidence that an
existing product has caused harm.

Any study involving real people requires separate preregistration, ethics
review, informed consent, participant safeguards, withdrawal procedures, and a
data-protection plan. No study with minors or vulnerable adults proceeds on the
authority of this model-evaluation plan.

## Maintenance

Protocol changes use semantic versions:

- patch: documentation or parser fix that leaves labels unchanged;
- minor: new model, stratum, or compatible metric;
- major: changed prompts, items, judge, denominator, serving condition, or
  construct definition.

Major versions are shown as separate series. Historical releases remain
downloadable with correction or retraction notices when necessary.
