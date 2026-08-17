# DisElect Wave 1A v0.4 pre-inference failure

This is a redacted operational record, not a benchmark result or model
comparison.

The `atb-diselect-wave1a-v0.4` execution attempt on 17 August 2026 failed closed
while refreshing public OpenRouter route evidence. DeepInfra's endpoint tags for
both frozen DeepSeek snapshots had changed from fp4 to fp8. The runner stopped
before any model call. No Inspect log, usage receipt, or validation packet was
created; the dedicated OpenRouter key remained unused and reported USD 0.00.
The run was not retried.

Operational facts:

- controlled workflow run: `31988631569`;
- public code commit: `0a9d15d75c6fd69c4b40a94be5b1c3d34dea9139`;
- private control commit: `da10ef4f6d4454d78289b4e44ae762be545f6494`;
- DisElect source commit: `915a8f8c22fb9cd8a2e4ae6824513760f0468f69`;
- canonical manifest SHA-256:
  `697c52f44944098edc7ebf07b32f9bfd8d45d3ef846b4ab0f4bb215967321be8`;
- controlled artifact SHA-256:
  `a5b6af138bcf7cd590933a2d78b5c2b1bdfd7ef78ceab2297836fc43c75bb2a8`;
- model calls, attributable spend, and automatic retries: zero.

Version 0.5 preserves the v0.4 dataset, selection, prompts, scorer, sampling,
validation, token, and budget contracts. It changes the material target serving
condition from DeepInfra/fp4 to DeepInfra/fp8 and refreshes the unchanged Google
Vertex grader's current prices using a new same-batch public capture. Any future
v0.5 outputs are therefore not comparable to, or mixable with, earlier versions.
