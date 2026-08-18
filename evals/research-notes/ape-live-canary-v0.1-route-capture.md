# APE live canary v0.1 route capture

The public, credential-free route capture ran on 2026-08-18 before any model
inference.

- GitHub Actions run: `32092531105`
- public commit: `cc1fc4a413bd72824cce780aabaeb6055c9bf652`
- artifact id: `9308813898`
- artifact name: `openrouter-route-evidence-ape-stage2a-v01-32092531105`
- artifact ZIP SHA-256: `18e91bb8274e5d1430ea7bd625284dc3837fa4bdadbb82dbe6ee7c57c7e284e0`
- common `observed_at`: `2026-08-18T02:37:58.557134Z`
- network scope: official public OpenRouter model, endpoint, and ZDR metadata
  only; no credential, prompt, output, inference endpoint, or spend

Condition evidence SHA-256 values:

- DeepSeek V4 Flash 0423 / CoreWeave fp8: `59c4ee29b5bfbc1621765dd5bb0649f1409db5e9176baf5e66208df5dc646bce`
- DeepSeek V4 Flash 0731 / CoreWeave fp8: `896db363ddebe951d315b7d4a66360a753eb9671b39bb37342325708043ad3db`
- Qwen3 235B persuadee / Parasail fp8: `262e4c91ac77a542ec66242626958865e6cd76932417de446e72990eed4e2dd8`
- Qwen3 235B evaluator / Parasail fp8: `262e4c91ac77a542ec66242626958865e6cd76932417de446e72990eed4e2dd8`
- Qwen3 30B refusal judge / CoreWeave bf16: `ddf4f13748ba70c06924b442e7c7dd079741377750fd2e756dcfc1e74add4535`

The persuadee and evaluator evidence bytes are deliberately identical because
they use the same observed provider endpoint. They remain separate files and
condition identities because their generation limits and model-event roles are
different. Ten content-addressed raw response files bind the five projections
to one capture window.

OpenRouter metadata establishes the requested model id, canonical metadata,
provider route, quantization, parameters, prices, and ZDR inventory observed at
capture time. It does not attest the exact weight-file digest served by the
provider or guarantee deterministic output.
