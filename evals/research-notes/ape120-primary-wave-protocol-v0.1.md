# Longitudinal APE-120 primary wave — protocol v0.1

**Status:** execution protocol; primary evidence is not claimed until the controlled run and postflight complete.

## Research question

Under one fixed APE interaction, do historically relevant frontier and quasi-frontier checkpoints differ in whether they attempt persuasion, refuse, or answer non-persuasively?

This is direct primary research. It is designed to fill missing observations in longitudinal model-family trajectories, not to reproduce exact checkpoints for which a secondary source already reports an APE result.

## Exact-checkpoint evidence rule

A candidate is excluded for secondary coverage only when a repository evidence record:

1. identifies APE or *Auditing Persuasion*;
2. identifies the same checkpoint or provider-bound revision, not merely the same model family; and
3. retains an external source or result provenance record.

Evidence for one checkpoint does not exclude earlier or later releases in the family. Ambiguous family-level matches do not count as exact secondary coverage.

Every decision is written to a machine-readable ledger with the checkpoint identity, decision, reason, evidence path, and evidence-record hash.

## Target scope

Eligible targets are:

- stable GPT and frontier o-series checkpoints from OpenAI;
- stable Claude checkpoints other than clearly small tiers;
- stable Gemini checkpoints other than Lite or Nano tiers;
- stable Grok checkpoints other than small or specialised code tiers; and
- open-weight text checkpoints with documented total parameters of at least 100 billion that were frontier or quasi-frontier at release.

The live OpenRouter inventory is authoritative for availability. A target is not silently replaced by a fine-tune, mutable `latest` alias, preview alias, discounted alias, or neighbouring release.

## Route and identity controls

Each target is frozen as:

`requested model ID → canonical revision → one OpenRouter provider endpoint → one quantisation → pricing and parameter contract`.

Provider fallbacks are disabled. The endpoint must be operational, eligible for zero-data-retention routing, support the required generation parameters, expose at least 1,024 completion tokens, and have no conditional pricing override. Raw API responses are hashed; sanitised revision evidence records retain the hashes and route metadata.

## APE task

- Instrument: APE turn 1, public Agency Transfer Benchmark adapter.
- Inventory: 120 fixed topics, 20 per APE category.
- Persuader condition: `persuade`.
- Belief range: native APE range, 0–20.
- Temperature: 0.5.
- Epochs: 1.
- Target seed: identical across target checkpoints.
- Paired interlocutor: one cached persuadee draw per topic within each family batch.
- Target maximum output: 1,024 tokens.
- Automatic retries: disabled; exhausted provider failures become explicit instrumental missingness.

One stable helper configuration is shared across all target checkpoints for the persuadee, evaluator, and refusal judge roles. Helper identity and route are frozen and reported separately from target identity.

## Execution design

Checkpoints are batched by model family or provider lineage, with at most six targets per batch. This preserves paired interlocutor draws for the longitudinal comparison while limiting the number of observations invalidated by a route incident.

Selection prioritises:

1. the oldest eligible checkpoint in each hosted frontier lineage;
2. later checkpoints needed to form a longitudinal trajectory;
3. open-weight ≥100B historical anchors; and
4. additional checkpoints that fit the remaining controlled budget.

The provider key has a non-resetting USD 30 lifetime cap. The controlled execution envelope is USD 29.50 including targets, helper calls, route checks, and any bounded recovery. Recovery must exclude checkpoints already completed in private logs.

## Outcomes

For each checkpoint and category, report:

- attempted-persuasion count and rate;
- refusal count and rate;
- non-persuasive response count and rate;
- unscored or instrumental-missingness count and usable rate;
- provider-recorded token usage and billed cost; and
- within-family checkpoint differences when the paired data remain valid.

Uncertainty is clustered by topic. Missingness is reported, never imputed as refusal or non-persuasion.

## Claim ceiling

APE turn 1 measures response-class behaviour and propensity to attempt persuasion under a fixed simulated interaction. It does **not** establish realised human persuasion, belief change, harmful manipulation efficacy, downstream agency erosion, agency transfer, deployment prevalence, electoral effect, or democratic harm.

Within the Capability–Deployment–Effect framework, these results address part of the **capability** layer. They do not close the deployment or effect gaps.

## Release controls

Raw prompts, target outputs, model API records, judge traces, route receipts, and sample-level logs remain private. Public release candidates are restricted to the protocol, exact-checkpoint ledger, aggregate counts and rates, missingness, route/provenance metadata, costs, and reproducibility hashes, subject to two-person review.
