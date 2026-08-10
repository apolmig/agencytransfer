# Gemini 3.6 Flash · one-turn APE-derived pilot

**Status:** Exploratory · automated-only · not a ranking  
**Run:** `2026-08-10-ape-frontier-pilot-v01`  
**Date:** 10 August 2026  
**Requested route:** `google/gemini-3.6-flash`

## Question

Under the same one-turn elicitation, does this served endpoint attempt to persuade on 20 noncontroversially harmful APE topics while still engaging six benign controls?

## Protocol

Exact requested route google/gemini-3.6-flash; 20 harmful and six benign controls; one response per item; provider-default routing, reasoning, and sampling; primary judge openai/gpt-5.6-terra; 20% audit judge google/gemini-3.6-flash. Returned models: google/gemini-3.6-flash (26). Providers: Google (9), Google AI Studio (17).

## Result

1 of 20 usable harmful-topic responses were labelled as attempts (5.0%; Wilson 95% CI 0.9%–23.6%). 19 were labelled refusals; 0 harmful rows were invalid. Benign-control attempt rate was 83.3%. There were 0 transport errors across 26 target calls. Estimated endpoint cost was $0.0965.

## Interpretation

This is an endpoint and pipeline diagnostic, not a model ranking. A preselected 20% second-judge audit yielded 46 parseable pairs (14.7% of target responses) after 2 audit-batch parse failures; agreement among parsed pairs was 100.0% with Cohen’s κ 1. The result can motivate a full, provider-pinned, human-validated run but cannot establish persuasion success or real-world harm.

## Limits

- Only one APE harmful category is sampled; conspiracy and undermining-control topics are absent.
- Twenty harmful items and one generation per item yield wide uncertainty.
- Provider, reasoning, and sampling conditions were not pinned, so this is a dated served-endpoint observation.
- Labels are automated; blind human validation has not been completed.
- The test measures attempted persuasion, not whether any person was persuaded.

## Artifacts

- [Aggregate and route artifacts](https://github.com/apolmig/agencytransfer/tree/main/data/runs/2026-08-10-ape-frontier-pilot-v01)
- [Hugging Face mirror](https://huggingface.co/datasets/apol/agency-transfer-benchmark/tree/main/runs/2026-08-10-ape-frontier-pilot-v01)
- [Protocol](https://github.com/apolmig/agencytransfer/blob/main/OPENROUTER_PROTOCOL.md)

Raw statements and generations are intentionally excluded from the public release.
