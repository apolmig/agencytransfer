# DisElect Wave 1A v0.2 diagnostic execution

This is a redacted operational record, not a benchmark result or a model
comparison.

The frozen `atb-diselect-wave1a-v0.2` protocol executed all 100 scheduled target
attempts on 13 August 2026. The April snapshot yielded 50/50 scorable samples.
For the July snapshot, 29/50 target calls ended at the frozen 700-token ceiling;
only 21/50 reached the grader. ATB retained the 29 cases as explicit
`truncated` instrument failures, failed the 95% usable-row requirement, skipped
human-review packet generation, and rejected the paired scientific postflight.
The apparently complete April row is not reused as a primary result because
doing so would break the paired protocol and introduce outcome-dependent
selection.

Operational facts:

- controlled workflow run: `31685142915`;
- public code commit: `ed0d42167f78b55d0db8e9a526bae266645148c9`;
- private control commit: `74a85898ee99e2bd18185abf8bfcfb25717f5284`;
- DisElect source commit: `915a8f8c22fb9cd8a2e4ae6824513760f0468f69`;
- manifest SHA-256: `01b6f8353a1c86e7c70dc8b4b85204713d7fdf38d66acebcb0d91cf880f26cef`;
- persisted usage: 72,183 tokens;
- reconciled Inspect/OpenRouter cost: USD 0.05173391;
- retries and provider fallbacks: zero;
- Inspect evidence artifact SHA-256:
  `a4dc20c0848214a88626225188d155bc60ee5768303a45c1902e78375ad771fb`;
- encrypted durable evidence SHA-256:
  `3f786858cffe55ebe507c76a4a2e088726b961ca1fb584385230ac5691c484b9`;
- Scout processed 100 transcripts with zero scanner errors; its 24 empty-message
  findings are private QA diagnostics and are not outcome labels.

The encrypted raw evidence and its verified receipt remain access-controlled.
No prompts, responses, grader traces, secrets, or reviewer mappings are exposed
here.

Version `atb-diselect-wave1a-v0.3` preserves the two snapshots, 50-item
inventory, routes, sampling contract, scorer, missingness rules, zero-retry
policy, and USD 1.00 envelope. It preregisters a 4,096-token target ceiling, a
12,000-token per-sample limit, a 1,200,000-token run envelope, and a new blind-
review sampling seed. Version 0.4 preserved that scientific design and added an
exact provider-side USD 1.00 lifetime cap, but its attempt failed before
inference after the frozen fp4 route evidence drifted. The current v0.5 protocol
refreshes those routes to DeepInfra/fp8 and the grader prices without changing
the dataset, sampling, validation, token, or budget contracts. Both snapshots
must be executed again under v0.5.
