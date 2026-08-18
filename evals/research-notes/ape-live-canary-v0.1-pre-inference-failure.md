# APE live canary v0.1 pre-inference failure

This is a redacted operational record, not an APE result or model comparison.

The controlled `atb-ape-live-canary-v0.1` attempt on 18 August 2026 failed
closed before model generation. Inspect 0.3.257 rejected the explicit cost map
because `openrouter/qwen/qwen3-235b-a22b-2507` was absent from Inspect's local
model-information database. The route itself had already passed the frozen
OpenRouter metadata checks; no prompt was sent and no `.eval` log was created.

Operational facts:

- controlled workflow run: `32114661787`;
- public code commit: `64999d22cef1b3f96c2993409009692e6eda7364`;
- private control commit: `d2aa5af7f2bdeaa644ad2847246c7b5e8a177fd0`;
- APE source commit: `d77a4b14d5d3353ea4ac73fb22df239e36606c1d`;
- canonical manifest SHA-256:
  `4b015dc5f657edd9399182d791de977e6e06ee2d9dc24ba49640dddf14622bd2`;
- controlled artifact id: `9316219313`;
- controlled artifact SHA-256:
  `35685d0ab5832502666591169d042f0b77b747daf6fd987c152532677cd5a1db`;
- automatic retries and model-generation calls: zero.

The workflow produced no usage receipt, so this record does not claim a
provider-accounting value for the attempt. It records only the stronger
execution-path fact established by two independent offline reproductions: the
exception occurs while Inspect applies the local cost registry, before any
model `generate` call.

The corrective change registers only exact manifest model ids that are absent
from Inspect's database, using the already frozen per-token cost. It neither
changes the APE fixture nor any model, provider route, quantization, prompt,
role, generation parameter, or budget. A fresh paid attempt requires a new
explicit authorization; this failed run is never rerun automatically.
