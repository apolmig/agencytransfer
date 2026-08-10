# DeepSeek V4 Pro · one-turn APE-derived pilot

- **Status:** Exploratory · automated-only · not a ranking
- **Run:** `2026-08-10-ape-frontier-pilot-v01`
- **Date:** 10 August 2026
- **Requested route:** `deepseek/deepseek-v4-pro`

## Question

Under the same one-turn elicitation, how does this served endpoint respond to 20 items from APE’s NoncontroversiallyHarmful category and six benign controls?

## Protocol

Exact requested route deepseek/deepseek-v4-pro; 20 harmful and six benign controls; one response per item; provider-default routing, reasoning, and sampling; primary judge openai/gpt-5.6-terra; 20% audit judge google/gemini-3.6-flash. Returned models: deepseek/deepseek-v4-pro (26). Providers: GMICloud (6), Novita (5), Baidu (4), StreamLake (3), BaseTen (1), Parasail (1), DigitalOcean (1), Ionstream (2), Together (1), Alibaba (1), CoreWeave (1).

## Result

7 of 18 usable harmful-item responses received automated attempt labels (38.9%; Wilson 95% CI 20.3%–61.4%). 0 received no-attempt labels and 11 received refusal labels; 0 were provider content-filtered and 2 were otherwise invalid. The automated attempt-label rate on benign controls was 100.0%. There were 0 transport errors across 26 target request records. Estimated endpoint cost was $0.0271.

## Interpretation

7 harmful-item responses were flagged for human review. Without human validation or pinned routing, this is a pipeline signal rather than a stable endpoint rate.

## Limits

- Requests were served by 11 providers; provider variation is part of this observation.
- 2 of 20 harmful rows were invalid for reasons other than provider content filtering.
- This one-turn sample covers 20 items from APE’s NoncontroversiallyHarmful category and six benign controls.
- Provider, reasoning, and sampling conditions were not pinned, so this is a dated served-endpoint observation.
- Labels are automated; blind human validation has not been completed.
- The test measures attempted persuasion, not whether any person was persuaded.

## Artifacts

- [Aggregate and route artifacts](https://github.com/apolmig/agencytransfer/tree/main/data/runs/2026-08-10-ape-frontier-pilot-v01)
- [Hugging Face mirror](https://huggingface.co/datasets/apol/agency-transfer-benchmark/tree/main/runs/2026-08-10-ape-frontier-pilot-v01)
- [Protocol](https://github.com/apolmig/agencytransfer/blob/main/OPENROUTER_PROTOCOL.md)

Raw statements and generations are intentionally excluded from the public release.
