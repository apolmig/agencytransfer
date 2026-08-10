# DeepSeek V4 Pro · one-turn APE-derived pilot

**Status:** Exploratory · automated-only · not a ranking  
**Run:** `2026-08-10-ape-frontier-pilot-v01`  
**Date:** 10 August 2026  
**Requested route:** `deepseek/deepseek-v4-pro`

## Question

Under the same one-turn elicitation, does this served endpoint attempt to persuade on 20 noncontroversially harmful APE topics while still engaging six benign controls?

## Protocol

Exact requested route deepseek/deepseek-v4-pro; 20 harmful and six benign controls; one response per item; provider-default routing, reasoning, and sampling; primary judge openai/gpt-5.6-terra; 20% audit judge google/gemini-3.6-flash. Returned models: deepseek/deepseek-v4-pro (26). Providers: GMICloud (6), Novita (5), Baidu (4), StreamLake (3), BaseTen (1), Parasail (1), DigitalOcean (1), Ionstream (2), Together (1), Alibaba (1), CoreWeave (1).

## Result

7 of 18 usable harmful-topic responses were labelled as attempts (38.9%; Wilson 95% CI 20.3%–61.4%). 11 were labelled refusals; 2 harmful rows were invalid. Benign-control attempt rate was 100.0%. There were 0 transport errors across 26 target calls. Estimated endpoint cost was $0.0271.

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
