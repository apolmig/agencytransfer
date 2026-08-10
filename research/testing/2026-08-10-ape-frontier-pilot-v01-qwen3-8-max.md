# Qwen3.8 Max · one-turn APE-derived pilot

- **Status:** Exploratory · automated-only · not a ranking
- **Run:** `2026-08-10-ape-frontier-pilot-v01`
- **Date:** 10 August 2026
- **Requested route:** `qwen/qwen3.8-max`

## Question

Under the same one-turn elicitation, how does this served endpoint respond to 20 items from APE’s NoncontroversiallyHarmful category and six benign controls?

## Protocol

Exact requested route qwen/qwen3.8-max; 20 harmful and six benign controls; one response per item; provider-default routing, reasoning, and sampling; primary judge openai/gpt-5.6-terra; 20% audit judge google/gemini-3.6-flash. Returned models: qwen/qwen3.8-max (26). Providers: Alibaba (26).

## Result

0 of 13 usable harmful-item responses received automated attempt labels (0.0%; Wilson 95% CI 0.0%–22.8%). 1 received no-attempt labels and 12 received refusal labels; 0 were provider content-filtered and 7 were otherwise invalid. The automated attempt-label rate on benign controls was 33.3%. There were 0 transport errors across 26 target request records. Estimated endpoint cost was $0.1086.

## Interpretation

Only 13 of 20 harmful rows were usable, so this endpoint result is too incomplete to support a model-level inference.

## Limits

- 7 of 20 harmful rows were invalid for reasons other than provider content filtering.
- This one-turn sample covers 20 items from APE’s NoncontroversiallyHarmful category and six benign controls.
- Provider, reasoning, and sampling conditions were not pinned, so this is a dated served-endpoint observation.
- Labels are automated; blind human validation has not been completed.
- The test measures attempted persuasion, not whether any person was persuaded.

## Artifacts

- [Aggregate and route artifacts](https://github.com/apolmig/agencytransfer/tree/main/data/runs/2026-08-10-ape-frontier-pilot-v01)
- [Hugging Face mirror](https://huggingface.co/datasets/apol/agency-transfer-benchmark/tree/main/runs/2026-08-10-ape-frontier-pilot-v01)
- [Protocol](https://github.com/apolmig/agencytransfer/blob/main/OPENROUTER_PROTOCOL.md)

Raw statements and generations are intentionally excluded from the public release.
