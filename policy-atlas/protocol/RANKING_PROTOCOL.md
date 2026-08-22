# Policy Atlas ranking protocol

## Status

- `protocol_version`: `ranking-protocol-v0.1`
- `preregistration_status`: `draft_not_preregistered`
- `analysis_status`: `prospective_design_only`
- `results_status`: `no_results`

This is a public methodological draft. It has not been preregistered, does
not describe an analysis already conducted, and must not be cited as a
preregistered study. No implementation is scored, ranked, recommended, or
excluded here.

Non-placeholder rows in any result table are prohibited from public release
until an exact protocol and scenario have been preregistered, the evidence and
candidate snapshots have been frozen, independent review has passed, and
every publication check in section 16 is satisfied. The placeholder templates
may remain public in the repository because they contain no observations.

## 1. Purpose and interpretation

The protocol is intended to answer one bounded question:

> Within a prospectively defined policy scenario, which eligible alternatives
> remain preferable across explicitly modelled evidence uncertainty and
> plausible, declared value judgements?

It does not produce a universal league table, estimate whether an intervention
works, or transfer conclusions across jurisdictions. The Policy Atlas remains
the source of claims and evidence. A future ranking is a scenario-specific
decision aid built only from reviewed claims.

The terms `probability`, `acceptability`, and `rank` are conditional on the
registered data, model, candidate set, and preference assumptions. They do not
denote a causal probability that a policy is truly best.

## 2. Unit of comparison and alternatives

The comparison unit is:

> configured alternative × jurisdiction × threat mechanism × target
> population × delivery vector × implementer × comparator × outcome × time
> horizon

An `alternative_id` identifies the exact scenario-specific configuration. It
links to an Atlas `implementation_id` when one exists. Material changes to
safeguards, dosage, scope, implementer, or conditions create a new alternative
rather than silently changing the implementation row.

Alternatives may be compared only when they answer the same decision question
and satisfy the registered homogeneity rule. Broad labels such as
“transparency”, “media literacy”, or “platform governance” do not establish
comparability.

The scenario must also state whether alternatives are mutually exclusive or
substitutable. Complementary packages, sequential choices, interactions, and
budget-constrained portfolios require a prospectively specified portfolio
model; they must not be forced through the additive ranking below.

## 3. Separate ledgers and uncertainty classes

### 3.1 Legal and rights eligibility

Authority, applicability, proportionality, fundamental rights,
contestability, pluralism, equality, and institutional safeguards are assessed
through non-compensable gates. They are never converted into benefit points.

### 3.2 Effect and decision performance

Observed effects and other decision-relevant performance dimensions may enter
criterion scores only when construct, endpoint, raw measure, value function,
direction, anchors, and minimum evidence were defined before candidate scores
were extracted.

### 3.3 Evidential certainty

Certainty states how much confidence the evidence warrants. It can determine
eligibility or reporting, but cannot add points or be averaged with the effect.
A certainty label must not mechanically widen a distribution unless a
prospectively calibrated model justifies that mapping.

### 3.4 Uncertainty must not be collapsed

The analysis keeps three sources distinct:

1. **statistical uncertainty** in an estimated performance quantity;
2. **structural uncertainty** about bias, transfer, model form, endpoint
   mapping, and dependence; and
3. **preference uncertainty or heterogeneity** across admissible stakeholder
   value judgements.

Statistical and structural uncertainty concern evidence. Preference
uncertainty concerns values. A single number that mixes them must not be
reported as a posterior probability that an alternative is best.

## 4. Prospective workflow

The order is mandatory:

1. Define the decision question, action class, and scenario.
2. Set the evidence cutoff and freeze the source snapshot.
3. Define the candidate rule and create the complete candidate ledger without
   consulting candidate scores.
4. Freeze the baseline or absolute acceptability floors and the attrition
   abort rule.
5. Freeze criteria, endpoints, value functions, anchors, vetoes, missing-data
   rules, evidence requirements, and the independence assessment.
6. Freeze gate applicability and non-compensable consequences.
7. Register fixed weight sets and any admissible preference space without
   viewing candidate performance.
8. Freeze dependence, uncertainty, convergence, sensitivity, tie, top-k, and
   decision-band rules.
9. Hash the complete bundle and preregister a new immutable version.
10. Extract evidence and conduct independent candidate and gate assessments.
11. Resolve disagreements without displaying provisional ranks.
12. Run the registered analyses and sensitivities.
13. Conduct methodological, legal/domain, affected-group where relevant, and
    reproducibility review.
14. Publish only if section 16 permits it, including exclusions, attrition,
    uncertainty, deviations, code, data, and hashes.

Scoring or model fitting before step 9 is exploratory. It must be discarded or
published only as exploratory and cannot be relabelled retrospectively as
preregistered.

## 5. Scenario, candidate population, baseline, and attrition

`ranking_scenarios.csv` freezes the decision context and analysis rules.
`scenario_candidates.csv` is the population and attrition ledger. It contains
every alternative considered by the frozen candidate rule, including rule
exclusions, later gate exclusions, and unrankable alternatives.

Candidate inclusion must not depend on apparent effect, favourability,
political salience, data completeness, or expected rank. Each disposition
must cite the exact rule clause and undergo assessment before candidate scores
or provisional ranks are visible. The complete ledger and its hash are part of
the registration bundle.

The candidate ledger separates:

- `rule_disposition`: whether the frozen rule included the alternative;
- `gate_disposition`: the outcome of non-compensable review;
- `score_disposition`: whether every required score is usable;
- `final_eligibility_status`: the mechanical analysis disposition; and
- `attrition_stage` and `attrition_reason`: where and why the row left the
  primary comparison.

A scenario must include a configured status-quo or no-action baseline when it
is a feasible decision alternative. If that is not ethical or meaningful, it
must preregister absolute acceptability and veto rules that prevent the best of
a weak set from becoming a recommendation.

The scenario also preregisters at least two rankable alternatives, a maximum
unrankable fraction, and an attrition abort rule. Falling outside those limits
stops the primary ranking and yields an insufficient-evidence report. It must
not crown the last well-studied survivor.

Changing the primary candidate population after registration is a material
deviation and creates a new analysis version. Alternative candidate sets may
appear only as prospectively listed sensitivity cases.

## 6. Non-compensable gates

Gate definitions come from the frozen `decision_gates` table.
`implementation_gate_assessments.csv` records one assessment per scenario,
alternative, and required gate.

Allowed operative decisions are:

- `pass`;
- `conditional_pass`;
- `fail`;
- `uncertain`;
- `not_applicable`; and
- `not_assessed`.

The rights gates in group G0 are mandatory for every scenario unless a
prospectively specified applicability rule and independent legal/domain review
support `not_applicable`. A scenario cannot omit an inconvenient gate after
seeing an alternative.

Cross-field rules are mechanical:

- `applicable=false` is compatible only with `not_applicable` and a written
  applicability rationale;
- an applicable `fail` on an eligibility gate produces
  `excluded_gate_failure`;
- an applicable `uncertain`, `not_assessed`, missing, or unresolved assessment
  produces `unrankable_missing_gate`;
- the canonical or registered source requirement is derived, not chosen by an
  assessor; and
- no criterion score, weight, effect, cost, or certainty can offset a failed
  or unresolved gate.

Some canonical gates imply a non-compensable cap rather than universal
exclusion. Each required gate therefore freezes one consequence:
`exclude`, `cap_to_pilot`, `cap_to_research`, or
`unrankable_until_resolved`. A cap constrains the decision band and is never a
numeric penalty. Primary eligibility gates use `exclude`.

Two assessments are required. When they agree, the agreed decision becomes the
`operative_gate_decision`; when they disagree, an adjudicated decision is
required. Pending or unresolved adjudication is unrankable. Confidence is
descriptive and cannot alter the operative decision.

A `conditional_pass` is rankable only when the condition:

1. is part of the locked alternative specification;
2. is explicit, measurable, legally and operationally feasible;
3. has an accountable owner and verification evidence;
4. can be satisfied at the relevant decision time; and
5. has its cost and residual burdens represented where relevant.

Otherwise the result is `unrankable_unresolved_condition`. A hypothetical
safeguard must not compete as if it already existed.

Enforcement scenarios require checked primary legal or official sources for
authority and temporal and material applicability. Legal existence is not
evidence of effectiveness.

## 7. Criterion definitions and value model

`criterion_definitions.csv` freezes every compensatory or descriptive
criterion. A valid definition includes:

- construct, decision relevance, and bounded endpoint;
- raw measure, unit, range, and direction;
- a cardinal interval value scale for weighted criteria;
- fixed normalization anchors and substantive interpretations;
- absolute floor or veto rules, when applicable;
- admissible effect evidence and endpoint-match rule;
- separate statistical and structural uncertainty representations;
- missing-data treatment; and
- a rationale for preferential independence and a double-counting review.

Ordinal category codes cannot enter an additive sum. A categorical criterion
is weight-eligible only after a prospectively elicited cardinal value function
maps its levels to differences with preference meaning.

Criteria must be complete, non-redundant, operational, and limited to the
smallest set needed. Causal overlap and double counting are assessed through
substantive structure, not correlation alone. Legal status, gate decisions,
and certainty are never weighted criteria.

Residual rights burdens may be described or compared only inside an already
rights-compliant envelope. They cannot make a rights violation acceptable and
must not duplicate the proportionality gate.

Absolute floors and vetoes are evaluated before aggregation. Failure produces
the registered non-compensable disposition; it is not represented by a low
score that another criterion can offset.

## 8. Effect evidence, extraction, and synthesis

`criterion_scores.csv` stores one adjudicated scenario–alternative–criterion
estimate per assessment and criterion version. Multiple studies are first
combined through a prospectively specified synthesis identified by
`evidence_synthesis_id`; analysts must not select a favourable study as the
score.

The effect-evidence framework is distinct from the Atlas mechanism-evidence
codes `Project-C`, `Project-X`, and `E0`–`E3`. Those codes must not be imported
as proof of intervention effectiveness. Before registration, the scenario
defines controlled effect-evidence classes, admissible study designs,
directness, endpoint matching, risk-of-bias rules, and their ordering.

Each usable score retains:

- raw estimate or registered categorical value and unit;
- interval type, level, and lower and upper limits where defensible;
- measured endpoint and exact criterion version;
- effect-evidence framework and class, directness, and risk of bias;
- claim and source identifiers;
- synthesis, extraction, assessor, and adjudication metadata; and
- normalized estimate and uncertainty representation.

Activity, legal obligation, adoption count, or mechanism evidence cannot be
substituted for an outcome effect. If the stricter of the scenario-level and
criterion-level evidence requirements is not met, or the endpoint mismatches,
the required score is missing and the alternative is unrankable.

Independent extraction is required for central effect claims. Disagreements
are adjudicated before ranking and without displaying provisional ranks.
`adjudicated_before_ranking=true`, not “known before analysis”, records this
state.

## 9. Normalization

Every weighted criterion is transformed to a benefit-oriented cardinal scale
bounded by 0 and 1. Anchors and transformations are frozen before extracting
candidate values and must not use the observed candidate minimum and maximum.

For an increasing criterion with fixed lower anchor `L` and upper anchor `U`:

```text
x = clamp((raw - L) / (U - L), 0, 1)
```

For a decreasing criterion:

```text
x = clamp((U - raw) / (U - L), 0, 1)
```

Non-linear functions require prospectively frozen knots and value judgments.
Uncertainty is drawn on the justified raw or model-parameter scale and then
passed through the value function; analysts must not invent a convenient
distribution directly on normalized scores.

If a defensible value function cannot be specified, the criterion remains
descriptive or the alternative is unrankable.

## 10. Missingness and rankability coverage

For every required gate and criterion:

> missing = unrankable

No mean, zero, worst-case, best-case, model-based, or expert-value imputation
is allowed in the primary analysis. `not_applicable` is not missing and
requires a preregistered applicability rule.

A registered secondary sensitivity may examine bounded missing-data
assumptions, but cannot convert an unrankable primary result into a ranked
recommendation. Missingness patterns, rankable coverage, and every excluded or
unrankable alternative are public outputs. The attrition abort rule applies
before any ranks are interpreted.

## 11. Weights and preference information

`weight_scenarios.csv` stores criterion rows grouped into immutable weight
sets. Central weights are non-negative and sum to 1 within `1e-6`. Each set
records its role, stakeholder population, perspective, elicitation method,
sample size, swing ranges, and whether it was locked before candidate scores
were visible.

Weights express the value of a performance swing between the registered
anchors, not abstract criterion importance. Equal weights may be included as
a reference sensitivity but are not a neutral or normative default and cannot
define robustness merely because they are convenient.

Uncertain weights form a **joint** distribution or constrained admissible set
on the simplex. `joint_weight_distribution`,
`joint_weight_parameters_json`, and `joint_constraint_set_json` are identical
for all rows in a weight set. Row-wise uniform or triangular draws followed by
silent renormalization are prohibited. Dirichlet parameters describe the
whole vector, not independent row marginals.

Allowed `weight_set_role` values are `primary_fixed`, `stakeholder_fixed`,
`reference_sensitivity`, and `preference_acceptability`. A set cannot be
chosen or discarded because it produces a desired winner.

Weights apply only to weight-eligible criteria. They never apply to gates,
legal status, certainty, floors, or vetoes.

## 12. Evidence uncertainty and preference acceptability analyses

For eligible alternative `i`, criterion `k`, fixed weight set `w`, and evidence
draw `b`, the additive model is:

```text
V(i,w,b) = sum_k weight(k,w) * benefit_score(i,k,b)
```

The additive model is allowed only after the registered review finds adequate
preferential independence and no material double counting. If relevant
interactions remain, the scenario must preregister another aggregation model
or stop without ranking.

The primary evidence-uncertainty analysis holds one stakeholder weight vector
fixed and propagates statistical uncertainty under the registered dependence
model. Structural assumptions are evaluated in separately labelled model
runs or sensitivities unless a calibrated joint model was preregistered.

A preference-acceptability analysis may explore a registered joint weight
space, with or without evidence draws. Its outputs are SMAA-style rank
acceptability indices conditional on that measure over preferences. They are
not posterior probabilities that an alternative is truly best and must remain
separate from fixed-weight evidence results.

The dependence model must cover shared studies, common baselines, correlated
criteria, repeated endpoints, and cross-alternative estimates where relevant.
Assuming independence requires a written justification and a registered
dependence sensitivity.

## 13. Monte Carlo, ties, and output contracts

Each scenario fixes a seed, initial draw count, maximum draw count, reporting
interval level, indifference threshold, top-k, and Monte Carlo error target.
The initial default is at least 20,000 draws, but precision—not that number—sets
the stopping rule.

Runs use reproducible nested samples or independent registered batches.
Convergence requires the registered Monte Carlo standard-error target and
stability threshold to pass for every published probability, mean, and
quantile. Failure at `max_mc_draws` yields `not_converged` and blocks
publication; increasing draws must not be used to tune substantive results.

Output tables are deliberately separate:

- `rank_results.csv` stores eligibility, values, summary ranks, absolute
  acceptability, decision bands, Pareto status, and robustness;
- `rank_acceptability.csv` stores one row per alternative and rank position;
- `pairwise_results.csv` stores each canonical alternative pair with
  preference and indifference probabilities;
- `sensitivity_results.csv` stores registered case outcomes; and
- `analysis_runs.csv` stores the reproducibility and convergence manifest.

Rank acceptability over preferences and rank probability under fixed weights
must be distinguished through `uncertainty_scope`. Pairwise outputs mean
`P(V_A > V_B + delta)`, `P(|V_A - V_B| <= delta)`, and
`P(V_B > V_A + delta)` under the specified simulation measure. They are not
causal superiority claims.

Expected rank is descriptive and cannot define a decision band. Tie handling,
rank intervals, top-k, and Pareto status use prospectively registered rules.
The full rank distribution is retained rather than hiding multimodality in a
mean rank.

## 14. Sensitivity, robustness, and structural uncertainty

`sensitivity_plans.csv` contains one prospectively frozen case per row.
Required cases cover, where applicable:

1. stakeholder-specific fixed and reference weight sets;
2. leave-one-criterion-out analysis;
3. defensible perturbations of value-function anchors and knots;
4. alternative evidence and structural-uncertainty models;
5. registered dependence assumptions;
6. inclusion and exclusion of conditionally eligible alternatives;
7. gate-threshold boundary cases;
8. prospectively declared alternative candidate-set interpretations;
9. missing-data bounds as secondary outputs only; and
10. baseline, absolute-floor, and decision-band thresholds.

Each case records its primary and alternative settings, plausibility basis,
and the exact definition of a material ordering or decision-band reversal.
“All plausible assumptions” is not sufficient without a bounded registered
set.

A conclusion is `robust` only if every required sensitivity ran and no
registered material reversal occurred. Otherwise it is `sensitive`. If
uncertainty, missingness, attrition, or nonconvergence prevents a defensible
conclusion, it is `inconclusive`, not a tie.

## 15. Results and decision bands

`rank_results.csv` retains eligible, excluded, and unrankable alternatives so
the released set is not survivorship-biased. Allowed eligibility statuses are:

- `eligible`;
- `eligible_conditional`;
- `excluded_gate_failure`;
- `unrankable_missing_gate`;
- `unrankable_unresolved_condition`;
- `unrankable_missing_score`;
- `unrankable_below_evidence_threshold`;
- `unrankable_endpoint_mismatch`;
- `unrankable_attrition_abort`; and
- `unrankable_not_converged`.

Allowed decision bands are `implement_or_enforce`, `pilot`, `research`,
`hold_or_reject`, and `insufficient_evidence`. The structured
`decision_band_rule_json` is frozen before analysis and must include absolute
floors, required gates, evidence requirements, robustness conditions, and
band caps. Rank alone never assigns a band.

A high rank among weak alternatives does not justify implementation. Public
reporting leads with context, candidate coverage, gate status, endpoint,
absolute performance, uncertainty, pairwise and rank acceptability,
sensitivity, and deviations—not a single composite number. No universal 0–100
score or cross-scenario ordering may be published.

## 16. Review and publication gate

Publishing any non-placeholder result row is prohibited unless all conditions
below are true:

- the exact protocol and scenario are `preregistered` at an immutable public
  URI;
- the registration bundle contains hashes for the protocol, candidate ledger,
  evidence snapshot, gates, criteria, scores, weights, sensitivity plan, code,
  and environment lock;
- candidate rules, population, baseline, attrition rule, gates, criteria,
  value functions, weights, uncertainty, and analysis settings were frozen at
  the required stage;
- every candidate disposition and applicable gate has two assessments or a
  resolved adjudication;
- every required score is source-linked and meets the registered effect-
  evidence and endpoint rules;
- missing required data are unrankable and primary results contain no
  imputation;
- candidate coverage passes the attrition rule;
- methodological, legal/domain, relevant affected-group, and reproducibility
  reviews in `review_signoffs.csv` have passed with conflicts disclosed;
- every required sensitivity and convergence check has passed or the result is
  explicitly inconclusive and non-recommendatory;
- released code and inputs reproduce every output; and
- all deviations, withdrawn scenarios, aborted runs, exclusions, and
  unrankable alternatives are disclosed.

Until then, generated result rows retain
`publication_status=prohibited_draft` and remain outside public releases.
Publication status is derived from the gate; it is not a manual analyst choice.

## 17. Runs, registration, review, and deviations

`analysis_runs.csv` records the exact uncertainty scope, input hashes, code
commit, dependency lock, seed, draw counts, error target, convergence result,
review state, and publication state. Repeating hashes in result rows is not a
substitute for this run manifest.

`review_signoffs.csv` records reviewer role, affiliation, conflict statement,
independence, artifact scope and hashes, decision, required changes, and
resolution. “Independent review” without an auditable record does not pass.

`protocol_deviations.csv` records every difference between the registered plan
and execution. Material analytic deviations are exploratory and cannot retain
confirmatory status. Clerical corrections that cannot affect results are still
documented and hashed.

Preregistration always creates a new immutable version. Draft files are never
overwritten or relabelled as registered. A later registration cannot convert
earlier exploratory work into confirmatory work. Registered scenarios that
are withdrawn, aborted, or yield no rank remain discoverable to prevent
selective reporting.

## 18. Template rows

Every CSV in `data/ranking-v0.1/` contains exactly one
`template_placeholder` row so generic tabular tooling can inspect the schema.
These rows are metadata, not observations. Every identifier includes
`TEMPLATE-DO-NOT-ANALYZE`; every row remains
`preregistration_status=draft_not_preregistered`; and every result-like row
remains `publication_status=prohibited_draft` where that field exists.

Analysis code must reject, not merely ignore, placeholder rows. A future
registered analysis copies the directory to a new version, removes all
placeholders, adds validated records, hashes the complete bundle, and
preregisters it before extraction or scoring proceeds.

## 19. Method references

- Lahdelma, R., Hokkanen, J., and Salminen, P. (1998). “SMAA — Stochastic
  multiobjective acceptability analysis.” *European Journal of Operational
  Research*, 106(1), 137–143.
  [doi:10.1016/S0377-2217(97)00163-X](https://doi.org/10.1016/S0377-2217(97)00163-X)
- Lahdelma, R., and Salminen, P. (2001). “SMAA-2: Stochastic multicriteria
  acceptability analysis for group decision making.” *Operations Research*,
  49(3), 444–454.
  [doi:10.1287/opre.49.3.444.11220](https://doi.org/10.1287/opre.49.3.444.11220)
- Marsh, K. et al. (2016). “Multiple criteria decision analysis for health care
  decision making—emerging good practices: report 2 of the ISPOR MCDA Emerging
  Good Practices Task Force.” *Value in Health*, 19(2), 125–137.
  [doi:10.1016/j.jval.2015.12.016](https://doi.org/10.1016/j.jval.2015.12.016)
- HM Treasury and Department for Energy Security and Net Zero (2024). “Use of
  Multi-Criteria Decision Analysis in options appraisal of economic cases.”
  [Official guidance](https://www.gov.uk/government/publications/green-book-supplementary-guidance-use-of-multi-criteria-decision-analysis/use-of-multi-criteria-decision-analysis-in-options-appraisal-of-economic-cases)
