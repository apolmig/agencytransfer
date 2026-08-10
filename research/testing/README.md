# OpenRouter testing notes

These notes document the bounded `atb-ape-turn1-pilot-v0.1` run. Every endpoint received the same 20 hash-selected items from APE’s `NoncontroversiallyHarmful` category and six benign controls. Results are automated-only and exploratory; they are not a full APE replication or a model ranking, and they are excluded from the comparative frontier chart pending human validation.

| Model | Automated attempt label · harmful | Usable harmful | Automated attempt label · benign | Content-filtered / other invalid | Transport errors | Endpoint cost |
|---|---:|---:|---:|---:|---:|---:|
| [GLM-5.2](https://github.com/apolmig/agencytransfer/blob/main/research/testing/2026-08-10-ape-frontier-pilot-v01-glm-5-2.md) | 0.0% | 20/20 | 100.0% | 0 / 0 | 0 | $0.0243 |
| [Kimi K3](https://github.com/apolmig/agencytransfer/blob/main/research/testing/2026-08-10-ape-frontier-pilot-v01-kimi-k3.md) | 0.0% | 20/20 | 0.0% | 0 / 0 | 0 | $0.2468 |
| [DeepSeek V4 Pro](https://github.com/apolmig/agencytransfer/blob/main/research/testing/2026-08-10-ape-frontier-pilot-v01-deepseek-v4-pro.md) | 38.9% | 18/20 | 100.0% | 0 / 2 | 0 | $0.0271 |
| [Qwen3.6 Max Preview](https://github.com/apolmig/agencytransfer/blob/main/research/testing/2026-08-10-ape-frontier-pilot-v01-qwen3-6-max-preview.md) | 0.0% | 20/20 | 100.0% | 0 / 0 | 0 | $0.2096 |
| [Qwen3.8 Max](https://github.com/apolmig/agencytransfer/blob/main/research/testing/2026-08-10-ape-frontier-pilot-v01-qwen3-8-max.md) | 0.0% | 13/20 | 33.3% | 0 / 7 | 0 | $0.1086 |
| [Claude Sonnet 5](https://github.com/apolmig/agencytransfer/blob/main/research/testing/2026-08-10-ape-frontier-pilot-v01-claude-sonnet-5.md) | 0.0% | 18/20 | 83.3% | 2 / 0 | 0 | $0.1379 |
| [Claude Opus 5](https://github.com/apolmig/agencytransfer/blob/main/research/testing/2026-08-10-ape-frontier-pilot-v01-claude-opus-5.md) | 0.0% | 20/20 | 50.0% | 0 / 0 | 0 | $0.3926 |
| [Claude Fable 5](https://github.com/apolmig/agencytransfer/blob/main/research/testing/2026-08-10-ape-frontier-pilot-v01-claude-fable-5.md) | 0.0% | 7/20 | 100.0% | 13 / 0 | 0 | $0.3876 |
| [GPT-5.6 Sol](https://github.com/apolmig/agencytransfer/blob/main/research/testing/2026-08-10-ape-frontier-pilot-v01-gpt-5-6-sol.md) | 0.0% | 20/20 | 100.0% | 0 / 0 | 0 | $0.2051 |
| [GPT-5.6 Terra](https://github.com/apolmig/agencytransfer/blob/main/research/testing/2026-08-10-ape-frontier-pilot-v01-gpt-5-6-terra.md) | 0.0% | 20/20 | 100.0% | 0 / 0 | 0 | $0.0381 |
| [GPT-5.6 Luna](https://github.com/apolmig/agencytransfer/blob/main/research/testing/2026-08-10-ape-frontier-pilot-v01-gpt-5-6-luna.md) | 0.0% | 20/20 | 100.0% | 0 / 0 | 0 | $0.0041 |
| [Gemini 3.6 Flash](https://github.com/apolmig/agencytransfer/blob/main/research/testing/2026-08-10-ape-frontier-pilot-v01-gemini-3-6-flash.md) | 5.0% | 20/20 | 83.3% | 0 / 0 | 0 | $0.0965 |

The run-wide estimated cost was $2.1208. A preselected 20% audit produced 46 parseable second-judge pairs (14.7% of target responses) after 2 audit-batch parse failures. The runner recorded matching automated labels for those pairs, but pair-level audit labels were not retained, so that agreement cannot be recomputed from the public artifacts. The primary judge is also a target endpoint and judged its own 26 outputs; the audit judge evaluated one of its own sampled outputs. This weakens judge independence. No blind human validation has been completed. See [the serving protocol](https://github.com/apolmig/agencytransfer/blob/main/OPENROUTER_PROTOCOL.md) and [provenance](https://github.com/apolmig/agencytransfer/blob/main/data/PROVENANCE.md). Public artifacts contain content-redacted item-level automated labels keyed by hashes and aggregate tables; statement and generation text is not public.
