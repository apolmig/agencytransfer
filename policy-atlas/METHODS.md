# Methods

## Scope

The Policy Atlas maps candidate interventions intended to prevent, limit,
detect, contain, repair, or build resilience against AI-mediated manipulation
and associated transfers of individual, collective, or institutional agency.
It is an evidence map and decision aid, not a causal meta-analysis.

## Inclusion

An entry is included when it specifies:

1. a concrete implementer;
2. an instrument or operational control;
3. a target mechanism or causal-chain point;
4. an expected effect;
5. a failure or evasion mode;
6. a rights or trade-off consideration; and
7. at least one evaluable metric.

Binding law, non-binding guidance, private controls, operational precedents,
pilots, and research proposals are included but never treated as equivalent.

## Exclusion

The Atlas excludes generic aspirations without an implementable control,
partisan content judgements, real-person targeting or campaign playbooks,
claims that infer electoral effects solely from reach or virality, and
composite manipulation or agency-transfer scores lacking construct validity.

## Object model

A control family groups related controls. An implementation records one
jurisdictional rule or operational control. A claim stores one bounded
proposition. A source stores canonical provenance. Bridge tables state exactly
how objects relate.

Cases are typed as observed incidents, prospective implementation studies,
historical governance baselines, audit domains, legitimate-use
counterexamples, or structural risk patterns. These types must not be pooled as
equivalent observations.

## Evidence model

Mechanism evidence uses:

- Project-C: confirmatory project mechanism;
- Project-X: exploratory project finding;
- E0: model or simulation signal;
- E1: immediate controlled human outcome;
- E2: persistence or low-cost real behaviour;
- E3: naturalistic or system-level outcome;
- None.

Intervention-effect evidence is coded separately. A legal obligation or a
documented risk mechanism is not proof that a control reduces harm.

## Source verification

Verification is claim-specific:

- Claim checked — primary legal source;
- Claim checked — primary official policy source;
- Claim checked — empirical source;
- Canonical project URL fixed;
- URL recorded — recheck before citation.

A working URL proves only retrievability. It does not prove that the source
supports the linked claim.

The frozen Sheets snapshot is not silently rewritten. Claim-specific evidence
corrections and additions are stored in a versioned curation overlay and
applied deterministically when building a release. The original claim, the
corrected public claim, and the review decision therefore remain auditable.

## Decision tiers

The Atlas proposes non-compensable rights and institutional gates. This beta
publishes the gate definitions but not implementation-by-gate assessments, so
the working decision tiers must not be read as reproduced pass/fail results.
They reflect current legal authority, operational maturity, causal
plausibility, reversibility, evaluability, and evidence without numeric
aggregation. Because their imperative labels could be mistaken for public
recommendations, the normalized implementation and package tables preserve
them only as explicitly named `working_register_decision_tier` provenance;
families use `working_register_decision_posture`. The default atlas omits the
source tier. `publication_decision_posture=not_assessed` is authoritative for
every implementation, family, and package.

## Proposed stable-core selection

The v0.2 foundation records a retrospective editorial selection of 30
implementations for intensive verification. It was not preregistered. The
recorded process used electoral decision relevance, causal-chain coverage,
jurisdiction and actor coverage, auditability, and non-duplication, and states
that apparent effect direction was not a selection criterion. Because there
is no row-specific screening ledger for all 118 candidates, that statement is
not independently reproducible. The remaining 88 rows stay in the candidate
registry; non-selection does not imply ineffectiveness or rejection. Full
rules and the included-row rationale are in
`protocol/STABLE_CORE_SELECTION.md` and
`data/curation-v0.5/stable_core_selection.csv`.

These 30 rows are proposed candidates only. Admission to a future stable core
requires complete claim disposition, current legal review, implementation-level
gate assessments, independent review, and the other machine-readable stable
release gates.

## Prospective ranking

No ranking has been run. `protocol/RANKING_PROTOCOL.md` is a draft,
non-preregistered design and `data/ranking-v0.1/` contains placeholder
templates only. A future comparison must freeze a homogeneous scenario across
jurisdiction, threat, population, vector, implementer, comparator, endpoint,
and horizon; pass every applicable non-compensable gate; and treat missing
required evidence as unrankable. Legal status, observed effect, and evidence
certainty remain separate ledgers. Rank results are prohibited before
prospective registration and independent review.

## Limitations

The snapshot is English-language and weighted toward the EU, United States,
Brazil, and the selected election cases. Evidence on conversational,
longitudinal, multi-agent, and institutional agency transfer remains weak.
Policy packages are hypotheses about complementary controls, not estimated
treatment bundles.

## Updating

Stable IDs are never renumbered. Corrections record the affected object, prior
value, new value, reason, date, and supporting claim. Material schema or
construct changes require a new minor or major version.
