# GLM-5.2 · one-turn APE-derived pilot

**Status:** Historical failed pipeline audit · permanently excluded · not a ranking

**Run:** `2026-08-10-ape-frontier-pilot-v01`

**Date:** 10 August 2026

**Requested model slug:** `z-ai/glm-5.2`

## Question

Under the same one-turn elicitation, does this served endpoint attempt to persuade on 20 noncontroversially harmful APE topics while still engaging six benign controls?

## Protocol

Requested model slug z-ai/glm-5.2; 20 harmful and six benign controls; one response per item; model-grouped request order; no effective seed; provider-default routing, reasoning, and sampling; primary judge openai/gpt-5.6-terra; 20% audit judge google/gemini-3.6-flash. Returned models: z-ai/glm-5.2 (26). Providers: CoreWeave (25), Alibaba (1).

## Historical automated result

0 of 20 usable harmful-topic responses were labelled as attempts (0.0%; Wilson 95% CI 0.0%–16.1%). 20 were labelled refusals; 0 harmful rows were invalid. Benign-control attempt rate was 100.0%. There were 0 transport errors across 26 target calls. Estimated endpoint cost was $0.0243.

## Interpretation

This is a permanently excluded pipeline diagnostic, not a model ranking. A preselected 20% second-judge audit yielded 46 parseable pairs (14.7% of target responses) after 2 audit-batch parse failures; agreement among parsed pairs was 100.0% with Cohen’s κ 1. Unpinned routing, grouped ordering, no effective seed, incompatible denominators, and absent blind human validation cannot be repaired retrospectively.

## Limits

- Only one APE harmful category is sampled; conspiracy and undermining-control topics are absent.
- Twenty harmful items and one uncontrolled stochastic draw per item yield wide uncertainty.
- Provider, reasoning, and sampling conditions were not pinned; fallback was not disabled.
- Requests were model-grouped, and harmful and benign rates used incompatible denominators.
- Labels are automated; no blind human validation was performed.
- The test measures attempted persuasion, not whether any person was persuaded.

## Artifacts

- [Aggregate and route artifacts](https://github.com/apolmig/agencytransfer/tree/main/data/runs/2026-08-10-ape-frontier-pilot-v01)
- [Hugging Face mirror](https://huggingface.co/datasets/apol/agency-transfer-benchmark/tree/main/runs/2026-08-10-ape-frontier-pilot-v01)
- [Protocol](https://github.com/apolmig/agencytransfer/blob/main/OPENROUTER_PROTOCOL.md)

Raw statements and generations are intentionally excluded from the public release.
