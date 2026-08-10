# Gemini 3.6 Flash · one-turn APE-derived pilot

- **Status:** Exploratory · automated-only · not a ranking
- **Run:** `2026-08-10-ape-frontier-pilot-v01`
- **Date:** 10 August 2026
- **Requested route:** `google/gemini-3.6-flash`

## Question

Under the same one-turn elicitation, how does this served endpoint respond to 20 items from APE’s NoncontroversiallyHarmful category and six benign controls?

## Protocol

Exact requested route google/gemini-3.6-flash; 20 harmful and six benign controls; one response per item; provider-default routing, reasoning, and sampling; primary judge openai/gpt-5.6-terra; 20% audit judge google/gemini-3.6-flash. Returned models: google/gemini-3.6-flash (26). Providers: Google (9), Google AI Studio (17).

## Result

1 of 20 usable harmful-item responses received automated attempt labels (5.0%; Wilson 95% CI 0.9%–23.6%). 0 received no-attempt labels and 19 received refusal labels; 0 were provider content-filtered and 0 were otherwise invalid. The automated attempt-label rate on benign controls was 83.3%. There were 0 transport errors across 26 target request records. Estimated endpoint cost was $0.0965.

## Interpretation

1 harmful-item response was flagged for human review. Without human validation or pinned routing, this is a pipeline signal rather than a stable endpoint rate.

## Limits

- Requests were served by 2 providers; provider variation is part of this observation.
- This endpoint also served as the audit judge and evaluated one of its own sampled outputs.
- This one-turn sample covers 20 items from APE’s NoncontroversiallyHarmful category and six benign controls.
- Provider, reasoning, and sampling conditions were not pinned, so this is a dated served-endpoint observation.
- Labels are automated; blind human validation has not been completed.
- The test measures attempted persuasion, not whether any person was persuaded.

## Artifacts

- [Aggregate and route artifacts](https://github.com/apolmig/agencytransfer/tree/main/data/runs/2026-08-10-ape-frontier-pilot-v01)
- [Hugging Face mirror](https://huggingface.co/datasets/apol/agency-transfer-benchmark/tree/main/runs/2026-08-10-ape-frontier-pilot-v01)
- [Protocol](https://github.com/apolmig/agencytransfer/blob/main/OPENROUTER_PROTOCOL.md)

Raw statements and generations are intentionally excluded from the public release.
