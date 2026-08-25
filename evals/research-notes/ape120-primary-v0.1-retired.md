# APE-120 primary protocol v0.1 — retired before confirmatory execution

Protocol `atb-ape120-primary-20260825-v0.1` is retained only for audit. It is not a valid APE-120 execution protocol because its execution plan set `max_samples` to 4 while the dataset specification required 120 observations per checkpoint. The overlapping private orchestration also generated repeated failed Actions runs.

No strict confirmatory result may cite v0.1. The corrected protocol is `atb-ape120-primary-20260825-v0.2`, which requires all 120 frozen topics, disables automatic retries and provider fallback, reserves USD 0.75 under the USD 30 provider-key cap, and excludes served releases already covered by secondary APE evidence.
