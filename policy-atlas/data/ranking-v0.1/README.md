# Ranking data templates v0.1

## Status

- `protocol_version`: `ranking-protocol-v0.1`
- `preregistration_status`: `draft_not_preregistered`
- `record_status`: `template_placeholder`
- analysis run: none
- public rankings: prohibited

These are prospective, repository-only schemas. They contain no policy scores,
gate decisions, analysis runs, or ranking results and are not part of a public
Policy Atlas dataset release. The governing method is
[`protocol/RANKING_PROTOCOL.md`](../../protocol/RANKING_PROTOCOL.md).

Every CSV has one metadata row whose identifiers include
`TEMPLATE-DO-NOT-ANALYZE`. The row is not an observation. Analysis code must
reject placeholder rows. Non-placeholder result rows cannot be published until
the exact registered bundle passes the protocol's publication gate.

## Files

| File | Unit of observation | Purpose |
| --- | --- | --- |
| `ranking_scenarios.csv` | One bounded decision scenario | Freezes the decision context, candidate and attrition rules, gates, criteria, uncertainty, analysis, and reporting plan. |
| `scenario_candidates.csv` | One scenario × configured alternative | Preserves the complete population and rule, gate, score, and final attrition dispositions. |
| `criterion_definitions.csv` | One versioned criterion | Defines construct, endpoint, cardinal value scale, anchors, evidence requirements, floors, vetoes, and uncertainty roles. |
| `implementation_gate_assessments.csv` | One scenario × alternative × gate assessment | Records non-compensable applicability, two assessments, adjudication, conditions, and operative outcome. |
| `criterion_scores.csv` | One scenario × alternative × criterion estimate | Stores versioned raw evidence, synthesis, normalized value, statistical uncertainty, and structural uncertainty without mixing certainty or preferences into benefit. |
| `weight_scenarios.csv` | One weight set × criterion | Stores swing weights and the shared joint preference distribution or constraint set. |
| `sensitivity_plans.csv` | One prospective sensitivity case | Freezes primary and alternative settings, plausibility basis, and material-reversal rule. |
| `analysis_runs.csv` | One reproducible analysis run | Stores input hashes, code and environment identity, uncertainty scope, seed, precision target, and convergence. |
| `rank_results.csv` | One run × weight set × alternative | Stores eligibility, absolute acceptability, summary value and rank, decision band, and robustness. |
| `rank_acceptability.csv` | One run × weight set × alternative × rank | Stores the complete rank distribution or SMAA-style rank acceptability profile. |
| `pairwise_results.csv` | One run × weight set × canonical alternative pair | Stores preference and indifference probabilities conditional on the registered simulation measure. |
| `sensitivity_results.csv` | One run × sensitivity case × alternative | Stores execution and material-reversal outcomes. |
| `protocol_deviations.csv` | One deviation | Preserves differences between the registered plan and execution. |
| `review_signoffs.csv` | One scoped review | Records role, independence, conflicts, artifact hashes, decision, and resolution. |

## Core rules

1. Ranking is scenario-specific; there is no global policy league table.
2. `alternative_id` identifies the exact configured choice. An Atlas
   `implementation_id` alone is insufficient when safeguards or conditions
   differ.
3. The candidate ledger contains every rule inclusion and exclusion. Missing
   evidence must not silently shrink the denominator.
4. A status-quo/no-action alternative or preregistered absolute floors prevent
   selection of the best option in a uniformly weak set.
5. Applicable gates, floors, and vetoes are non-compensable.
6. Missing required gate or criterion evidence means `unrankable`; there is no
   primary-analysis imputation.
7. Statistical evidence uncertainty, structural uncertainty, and stakeholder
   preference uncertainty remain separately identified.
8. Weight uncertainty is joint on the simplex; row-wise independent draws and
   silent renormalization are prohibited.
9. Rank acceptability over a preference space is not a posterior probability
   that an alternative is truly best.
10. Results require preregistration, complete hashes, convergence, independent
    review, and reproducibility.

## General encoding

- UTF-8, comma-delimited CSV, one header row.
- Dates use `YYYY-MM-DD`; timestamps use ISO 8601 with a timezone.
- Booleans are lowercase `true` or `false`.
- Decimal numbers use `.` and no thousands separator.
- Null values are empty. Do not substitute `0`, `NA`, `unknown`, or `none`
  unless that value is explicitly controlled.
- Lists of stable IDs use `|` with no spaces.
- Structured JSON is allowed only in fields ending `_json`. It is compact,
  valid JSON with sorted keys for reproducibility.
- Free text is quoted when it contains commas, quotes, or line breaks.
- Stable IDs are never reused. Registered IDs and versions are immutable.
- SHA-256 fields contain 64 lowercase hexadecimal characters.

Recommended prefixes are `SCN-` for scenarios, `SC-` for candidate records,
`ALT-` for configured alternatives, `CRIT-` for criteria, `GA-` for gate
assessments, `CS-` for criterion scores, `WS-` and `WR-` for weight sets and
rows, `SENS-` and `SENSCASE-` for sensitivity plans and cases, `RUN-` for
analysis runs, `RR-` for rank results, `RA-` for rank acceptability, `PW-` for
pairwise results, `DEV-` for deviations, and `REV-` for reviews. Atlas
implementation, claim, source, and gate IDs are reused unchanged.

## Common controlled values

### `record_status`

- `template_placeholder`: schema metadata; always rejected by analysis.
- `draft`: editable prospective record outside a registration.
- `locked`: immutable record covered by the cited registration.
- `deviation_exploratory`: post-registration material deviation excluded from
  confirmatory results.

### `preregistration_status`

- `draft_not_preregistered`
- `preregistered`
- `deviation_exploratory`

The v0.1 templates use only `draft_not_preregistered`. Registration creates a
new immutable directory; it never relabels these drafts.

## `ranking_scenarios.csv`

Before registration, a scenario completes:

- identity, decision action, jurisdiction, civic context, comparison
  dimensions, endpoint, and horizon;
- baseline, alternative relationship, candidate rule and hash, minimum
  rankable count, maximum unrankable fraction, and attrition abort rule;
- evidence cutoff, snapshot hash, and a versioned effect-evidence framework;
- mandatory rights and other gate rules, criterion IDs and exact versions,
  conditional-gate rule, and missing-data rule;
- normalization, additive-model assumptions, and preferential-independence
  assessment;
- separate statistical, structural, preference, and dependence methods;
- sensitivity plan, structured decision-band and absolute-acceptability rules,
  top-k, ties, interval level, seed, draw limits, error target, and convergence
  method; and
- registration bundle hash, URI, timestamp, creator, and state.

`minimum_rankable_alternatives` is at least 2. Exceeding the registered
attrition threshold stops the primary rank. `scenario_status` is `draft`,
`locked_not_run`, `analysis_complete`, `aborted`, or `withdrawn`; aborted and
withdrawn registered scenarios remain discoverable.

## `scenario_candidates.csv`

The ledger contains every alternative considered by the frozen rule, not just
those with complete data. `alternative_specification` freezes safeguards,
scope, conditions, implementer, and other material configuration details.

`rule_disposition` is `included`, `excluded_rule`, or `not_assessed`.
`gate_disposition` is `eligible`, `eligible_conditional`,
`excluded_gate_failure`, `unrankable`, or `not_assessed`.
`score_disposition` is `complete`, `unrankable_missing`, or `not_assessed`.
`final_eligibility_status` uses the eligibility vocabulary documented under
`rank_results.csv`.

Each disposition cites its rule clause and reason, is double-assessed or
adjudicated, and is locked before scores or provisional ranks are visible.
The scenario's baseline has `is_baseline=true`.

## `criterion_definitions.csv`

Weighted criteria require `value_scale_type=cardinal_interval` and
`score_direction=higher_better` or `lower_better`. `descriptive_only` criteria
are never weighted. Raw ordinal codes cannot enter the additive value model.

Normalization methods are `linear_fixed_anchors`,
`piecewise_fixed_anchors`, `categorical_predeclared`, or `descriptive_only`.
Anchors are externally meaningful and cannot be observed candidate extrema.

`absolute_floor_rule_json` and `veto_rule_json` are evaluated before
aggregation. Legal status, gate decisions, certainty, floors, and vetoes are
not compensatory criteria. `preferential_independence_rationale` and
`double_counting_review_status=passed` are required for every weighted set.

## `implementation_gate_assessments.csv`

`criterion_code` references the frozen Atlas `decision_gates` table. Gate group
and primary-source requirement are derived from that table and the registered
scenario; assessors do not choose them.

Assessment decisions are `pass`, `conditional_pass`, `fail`, `uncertain`,
`not_applicable`, and `not_assessed`. Mechanical constraints include:

- `applicable=false` only with `not_applicable` and a rationale;
- applicable `fail` on an eligibility gate means exclusion;
- applicable missing, uncertain, or unresolved assessments mean unrankable;
- disagreements require adjudication; and
- only the resolved `operative_gate_decision` controls eligibility.

`noncompensable_consequence` is `exclude`, `cap_to_pilot`,
`cap_to_research`, or `unrankable_until_resolved`. It never supplies a numeric
penalty. A conditional pass is rankable only when the verified condition is
inside the locked alternative specification with an owner and evidence.

## `criterion_scores.csv`

`assessment_version` and `criterion_version` make the extraction auditable.
The row retains raw scale, interval type and level, the registered value
function, and normalized benefit values.

Statistical fields contain the estimate distribution and sampling basis.
Structural fields contain bias, transfer, endpoint-mapping, or model-form
assumptions. They are not silently pooled. All parameter objects use the
`*_parameters_json` convention.

The effect-evidence framework is separate from Atlas mechanism codes. Controlled
effect classes, admissible designs, directness, risk of bias, and certainty
rules are defined before registration. The stricter scenario-level or
criterion-level evidence requirement wins.

`missing_status` is `observed`, `missing_required`,
`below_evidence_threshold`, `endpoint_mismatch`, `not_applicable`, or
`not_assessed`. Every required state other than `observed` is unrankable.
`adjudicated_before_ranking=true` is required for a confirmatory score.

## `weight_scenarios.csv`

One weight set has exactly one row per weight-eligible criterion. Central
weights are non-negative and sum to 1 within `1e-6`; `weight_set_sum` records
the validated sum.

`weight_set_role` is `primary_fixed`, `stakeholder_fixed`,
`reference_sensitivity`, or `preference_acceptability`.
`preference_uncertainty_mode` is `fixed`, `joint_distribution`, or
`constrained_weight_space`.

Joint distribution and constraint fields describe the complete weight vector
and repeat identically across its rows. Dirichlet parameters belong to the
vector. Row-wise uniform or triangular draws followed by renormalization are
invalid. Elicitation uses the registered criterion swing ranges, not abstract
importance. `locked_before_candidate_scores_visible=true` is required for
confirmatory use.

## `sensitivity_plans.csv` and `sensitivity_results.csv`

Each plan row freezes one case, including primary and alternative settings,
plausibility basis, material-ordering definition, decision-band reversal rule,
and execution order. Required cases cannot be omitted because their result is
unfavourable.

Result rows record execution, band and ordering changes, pairwise changes,
robustness implication, and output hash. A missing required case prevents
`robust` status.

## `analysis_runs.csv`

This is the run manifest. It binds the protocol, scenario, candidate ledger,
evidence, gate assessments, criteria, scores, weights, sensitivity plan, code,
and dependency environment by hash. It also records uncertainty scope, seed,
initial and final draws, error target, convergence method, maximum observed
Monte Carlo standard error, and review and publication states.

`uncertainty_scope` distinguishes at least `fixed_weight_evidence`,
`structural_sensitivity`, and `preference_acceptability`. A run that reaches
its draw cap without meeting the registered precision target is
`not_converged` and cannot publish ranks.

## Result tables

### `rank_results.csv`

This is generated output, never manual scoring. Eligibility values are:

- `eligible`
- `eligible_conditional`
- `excluded_gate_failure`
- `unrankable_missing_gate`
- `unrankable_unresolved_condition`
- `unrankable_missing_score`
- `unrankable_below_evidence_threshold`
- `unrankable_endpoint_mismatch`
- `unrankable_attrition_abort`
- `unrankable_not_converged`

Decision bands are `implement_or_enforce`, `pilot`, `research`,
`hold_or_reject`, and `insufficient_evidence`. Absolute floors, gate caps,
attrition, and robustness are evaluated before a favourable band is possible.

### `rank_acceptability.csv`

One row stores one alternative and rank position. Across all positions, the
indices for an eligible alternative sum to 1 within the registered numerical
tolerance. `uncertainty_scope` determines whether the profile is conditional
on fixed weights or explores a preference space. The latter is an
acceptability index, not a probability of true optimality.

### `pairwise_results.csv`

Each unordered alternative pair appears once in canonical ID order. The three
probabilities for A preferred, indifferent, and B preferred sum to 1 within
tolerance. The indifference threshold and uncertainty scope are registered.
“Preferred” concerns the value model, not causal effectiveness.

All result-like templates remain `publication_status=prohibited_draft` and
`independent_review_status=not_reviewed`.

## `protocol_deviations.csv` and `review_signoffs.csv`

Every execution difference is recorded. Material analytic deviations become
`analysis_classification=exploratory` and lose confirmatory eligibility.
Registered scenarios with no result remain visible.

Review records disclose role, affiliation, conflicts, independence, exact
artifact scope and hashes, decision, requested changes, and resolution.
Required review types are methods, legal/domain, affected-group when relevant,
and reproducibility. A prose assertion of review without these records does
not pass.

## Before any analysis

1. Copy this directory to a new version; never edit v0.1 in place.
2. Remove every placeholder and validate that none remains.
3. Complete scenario, population, criteria, gates, weights, sensitivity, and
   decision rules in the protocol order.
4. Freeze and hash the protocol, candidate ledger, evidence snapshot, code,
   environment, and every input table.
5. Preregister the immutable bundle and record its URI, timestamp, and hash.
6. Only then extract candidate-specific evidence or enter assessments.
7. Run only registered analyses, record deviations, obtain scoped reviews, and
   release results only if the publication gate passes.
