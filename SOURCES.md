# Sources and evidence registry

This repository separates **published observations** from **contextual evidence**. A source appearing in this registry does not imply that its results are numerically comparable with another source, and an entry in the evidence ledger does not imply that any score has been ingested.

The row-level lineage, denominators, transformations, and known limitations for the three published datasets are recorded in [`data/PROVENANCE.md`](data/PROVENANCE.md).

## Published observations used by the site

### Anthropic agentic influence

- **Construct:** raw capability to carry out a simulated influence operation with tools.
- **Primary result sources:**
  - Anthropic, *Claude Opus 4.7 System Card*, Section 5.1.3, Table 5.1.3.A, PDF page 81: <https://cdn.sanity.io/files/4zrzovbb/website/037f06850df7fbe871e206dad004c3db5fd50340.pdf>
  - Anthropic, *Claude Sonnet 5 System Card*, Section 5.1.3, Table 5.1.3.A, PDF page 56: <https://www-cdn.anthropic.com/9e6a1044980d8c4ed85669faf9c2a8342e2e9f1e/Claude%20Sonnet%205%20System%20Card.pdf>
- **Author label:** “Agentic influence operation evaluation results, helpful-only model.”
- **Comparability group:** `anthropic-agentic-influence-helpful-only-mean-v1`.
- **Data file:** [`data/published/anthropic-agentic-influence.csv`](data/published/anthropic-agentic-influence.csv)
- **Upstream revision:** no public source-control commit is supplied for the system-card PDFs. The immutable-looking document URLs and the table locator are retained instead.
- **Important condition:** every plotted score is from a `helpful-only` model, not the default deployed safeguard condition.

Official model-release metadata used for the time axis:

- Claude Opus 4.6 — 2026-02-05: <https://www.anthropic.com/news/claude-opus-4-6>
- Claude Sonnet 4.6 — 2026-02-17: <https://www.anthropic.com/news/claude-sonnet-4-6>
- Claude Mythos Preview — 2026-04-07: <https://www-cdn.anthropic.com/8b8380204f74670be75e81c820ca8dda846ab289.pdf>
- Claude Opus 4.7 — 2026-04-16: <https://www.anthropic.com/news/claude-opus-4-7>
- Claude Opus 4.8 — 2026-05-28: <https://www.anthropic.com/news/claude-opus-4-8>
- Claude Mythos 5 — 2026-06-09: <https://www-cdn.anthropic.com/d00db56fa754a1b115b6dd7cb2e3c342ee809620.pdf>
- Claude Sonnet 5 — 2026-06-30: <https://www.anthropic.com/news/claude-sonnet-5>

### DisElect

- **Publication:** Williams et al., *Large language models can consistently generate high-quality content for election disinformation operations*, PLOS ONE 20(3), e0317421, published 2025-03-17: <https://doi.org/10.1371/journal.pone.0317421>
- **Result locator:** DisElect evaluation section and Figure 1, “Heatmap of model response classification proportions across the 3 use cases within DisElect.”
- **Author repository:** <https://github.com/alan-turing-institute/election-ai-safety>
- **Pinned upstream commit:** [`915a8f8c22fb9cd8a2e4ae6824513760f0468f69`](https://github.com/alan-turing-institute/election-ai-safety/tree/915a8f8c22fb9cd8a2e4ae6824513760f0468f69)
- **Pinned inputs:**
  - [`data/evals/voting/results.csv`](https://github.com/alan-turing-institute/election-ai-safety/blob/915a8f8c22fb9cd8a2e4ae6824513760f0468f69/data/evals/voting/results.csv)
  - [`data/evals/mps/results.csv`](https://github.com/alan-turing-institute/election-ai-safety/blob/915a8f8c22fb9cd8a2e4ae6824513760f0468f69/data/evals/mps/results.csv)
  - [`data/evals/baseline/results.csv`](https://github.com/alan-turing-institute/election-ai-safety/blob/915a8f8c22fb9cd8a2e4ae6824513760f0468f69/data/evals/baseline/results.csv)
  - [`data/models.csv`](https://github.com/alan-turing-institute/election-ai-safety/blob/915a8f8c22fb9cd8a2e4ae6824513760f0468f69/data/models.csv)
- **Transformation:** [`scripts/prepare_diselect.py`](scripts/prepare_diselect.py) counts the four published judgement labels and calculates percentages. It does not ingest or publish model response text.
- **Comparability group:** `diselect-author-labels-915a8f8c`.
- **Data file:** [`data/published/diselect-summary.csv`](data/published/diselect-summary.csv)

### MASK

- **Publication:** Ren et al., *The MASK Benchmark: Disentangling Honesty From Accuracy in AI Systems*, arXiv:2503.03750v3: <https://arxiv.org/html/2503.03750v3>
- **Result locator:** Appendix A.10, Table 3, “Model performance metrics for honesty and accuracy.”
- **Protocol locators:** Sections 4.1–4.3 describe the 1,500-example dataset, belief elicitation, pressure prompts, judging, and metrics.
- **Author repository:** <https://github.com/centerforaisafety/mask>
- **Data file:** [`data/published/mask-original-results.csv`](data/published/mask-original-results.csv)
- **Upstream revision:** the paper is pinned to arXiv version 3. No Git commit was recorded during this ingestion, so the GitHub repository must not be treated as revision-pinned.

Model identity and release metadata are cross-checked against organization-controlled pages:

- Qwen1.5-110B-Chat: <https://qwenlm.github.io/blog/qwen1.5-110b/> and <https://huggingface.co/Qwen/Qwen1.5-110B-Chat>
- Llama 3.1 405B Instruct: <https://ai.meta.com/blog/meta-llama-3-1/> and <https://huggingface.co/meta-llama/Llama-3.1-405B-Instruct>
- DeepSeek V3: <https://arxiv.org/abs/2412.19437> and <https://huggingface.co/deepseek-ai/DeepSeek-V3>
- DeepSeek R1: <https://api-docs.deepseek.com/news/news250120/> and <https://huggingface.co/deepseek-ai/DeepSeek-R1>

### InfoOpsBench v2 — frozen 2026-07-26 paper snapshot

- **Publication:** Quelle et al., *InfoOps Bench: A live information operations safety benchmark*, arXiv:2607.28503v2: <https://arxiv.org/html/2607.28503v2>
- **Result locator:** Table 1, “Results by model (%), 2026-07-26 refresh.” Table 2 contains controls, not the model result panel.
- **Denominators:** Appendix A, Table 3.
- **Metric:** source-defined `compliance_pct = amplified + preserved`; lower is safer under this protocol.
- **Comparability group:** `infoopsbench-v2-2026-07-26-openrouter`.
- **Data file:** [`data/published/infoopsbench-2026-07-26.csv`](data/published/infoopsbench-2026-07-26.csv)

This is a frozen paper table, not a retrieval from the changing live benchmark. A later live retrieval is a new observation and must not overwrite these rows.

#### Live drift check — observed 2026-08-10

The live companion had already moved after the paper refresh. A retrieval on
2026-08-10 produced HTML SHA-256
`091fb91ede78bfe0bbaba452c9e1b342df3f8587f1a038b4a2b9f708e7bbad74`.
The following leaderboard values are recorded as a research audit, not loaded
into the default hero and not treated as a model-release series:

| Model | Live compliance (%) | Leaderboard n |
|---|---:|---:|
| Claude Sonnet 5 | 9.8 | 1,280 |
| Claude Opus 5 | 12.7 | 1,280 |
| Kimi K3 | 25.5 | 1,280 |
| GPT-5.6 Sol | 43.6 | 1,280 |
| GPT-5.6 Luna | 48.0 | 1,280 |
| GPT-5.6 Terra | 52.4 | 1,280 |
| Gemini 3.6 Flash | 62.3 | 1,280 |
| DeepSeek V4 Flash | 66.4 | 1,280 |
| DeepSeek V4 Pro | 62.1 | 2,376 |
| Llama 4 Maverick | 66.9 | 5,536 |
| GLM-5.2 | 75.4 | 2,000 |

For Llama 4 Maverick, an embedded aggregate object exposed `n = 5,723` while
the rendered leaderboard showed 5,536, so the audit retains the user-visible
leaderboard denominator and flags the conflict instead of resolving it by
assumption. The movement between snapshots can reflect claim mix, routing,
endpoint revisions, filters, and prompt framing; it is not a clean model-weight
effect.

| Model | Compliance (%) | n |
|---|---:|---:|
| Claude Sonnet 5 | 5.5 | 200 |
| Claude Opus 5 | 11.1 | 199 |
| Kimi K3 | 23.4 | 197 |
| GPT-5.6 Sol | 27.1 | 199 |
| GPT-5.6 Luna | 28.9 | 197 |
| GPT-5.6 Terra | 37.8 | 196 |
| Gemini 3.6 Flash | 52.8 | 199 |
| DeepSeek V4 Flash | 59.9 | 197 |
| DeepSeek V4 Pro | 62.6 | 1,482 |
| Llama 4 Maverick | 67.2 | 5,042 |
| GLM-5.2 | 76.5 | 1,096 |

The paper evaluates served endpoints through OpenRouter. These results do not identify a weights-only causal effect and do not measure factuality, human persuasion, campaign reach, exposure, or real-world harm.

### SaferAI GLM-5.2 APE and MASK cohort

- **Primary report page:** <https://www.safer-ai.org/research/glm-5-2-evaluation-report>
- **Report PDF:** *GLM-5.2 Evaluation Report*, published 2026-08-02: <https://www.safer-ai.org/u/2026/08/SaferAI-GLM-Evaluation-Report.pdf>
- **APE locator:** Section 5.2 and Figure 10; method in Appendix A.8. The full evaluation contains 600 prompts, 100 per category; the stored harmful-topic rows use `n = 100` per model and category.
- **MASK locator:** Section 5.1 and Figure 9; Wilson intervals and category details in Appendix A.7.1. Each model has `n = 1,000`.
- **Stored observations:** [`public/data/frontier-observations.json`](public/data/frontier-observations.json)

APE uses a supporting-role, turn-1, maximum-reasoning configuration. Categories remain separate comparability groups because their base rates and task content differ. Attempt rate is a behavioral propensity, not evidence that a person was persuaded.

| APE attempt rate (%) | GLM-5.2 | Claude Opus 4.7 | GPT-5.5 |
|---|---:|---:|---:|
| Conspiracy | 43 | 8 | 18 |
| Undermining control | 47 | 0 | 22 |
| Noncontroversially harmful | 0 | 0 | 0 |

The timeline stores only the MASK lie outcome. The complete rounded Figure 9 inventory is retained here so that lie is not mistaken for the complement of accuracy or honesty.

| MASK outcome (%) | GLM-5.2 | Claude Opus 4.7 | GPT-5.5 |
|---|---:|---:|---:|
| Lie | 21 | 17 | 10 |
| Honest | 61 | 64 | 73 |
| Evaded / no belief | 18 | 19 | 17 |
| Correct | 85 | 89 | 88 |
| Incorrect | 12 | 8 | 10 |
| Accuracy no belief | 3 | 3 | 2 |

SaferAI ran the GLM-5.2 evaluation. The report states that the Claude Opus 4.7 and GPT-5.5 MASK comparison values came from CAIS dashboard numbers shared by CAIS. No public raw-run artifact is asserted. The publication date is used on the timeline because the report does not supply a separate run date.

## Frontier model registry

The canonical registry is [`data/models/frontier-models.csv`](data/models/frontier-models.csv), mirrored for the client in [`public/data/frontier-models.json`](public/data/frontier-models.json). The longitudinal inclusion rule is:

1. Include a 2025–2026 open-weight model only when a primary model card or architecture source reports at least 100B **total** parameters. Active parameters alone do not determine eligibility.
2. Admit a concise hosted-frontier envelope when the provider withholds parameter count; store `totalParamsB = null` and say why the model is retained.
3. Preserve previews, served tiers, and post-training revisions as such. Do not silently treat a preview endpoint or routing alias as a new base architecture.
4. Exclude small families and sub-threshold open checkpoints, including Gemma and Mistral Small. Mistral Large 3 remains eligible at 675B total.

Every registry row carries its organization-controlled `sourceUrl`, eligibility rationale, and an OpenRouter route only where a direct catalog entry was identified. Provider evidence is grouped below; the row-level URL is the authoritative locator for a specific release.

| Provider | Registry coverage | Primary sources |
|---|---|---|
| DeepSeek | R1, R1-0528, V3.2, V4 Pro, V4 Flash | [R1 launch](https://api-docs.deepseek.com/news/news250120/), [R1-0528](https://api-docs.deepseek.com/news/news250528/), [V3.2 card](https://huggingface.co/deepseek-ai/DeepSeek-V3.2), [V4 preview](https://api-docs.deepseek.com/news/news260424/) |
| Meta | Llama 4 Maverick | [Llama 4 announcement](https://ai.meta.com/blog/llama-4-multimodal-intelligence/) |
| OpenAI | o3; GPT-5, 5.2, 5.4, 5.5, and 5.6 tiers | [o3](https://openai.com/index/introducing-o3-and-o4-mini/), [GPT-5](https://openai.com/index/introducing-gpt-5/), [GPT-5.2](https://openai.com/index/introducing-gpt-5-2/), [GPT-5.4](https://openai.com/index/introducing-gpt-5-4/), [GPT-5.5](https://openai.com/index/introducing-gpt-5-5/), [GPT-5.6](https://openai.com/index/gpt-5-6/) |
| Alibaba / Qwen | Qwen3 235B, Qwen3 Max, Qwen3.5 397B, Qwen3.6 Max Preview, Qwen3.8 Max | [Qwen3](https://qwenlm.github.io/blog/qwen3/), [Qwen3.5 card](https://huggingface.co/Qwen/Qwen3.5-397B-A17B), [release ledger](https://www.alibabacloud.com/help/en/model-studio/newly-released-models), [current model ledger](https://help.aliyun.com/zh/model-studio/models) |
| Anthropic | Claude Opus 4/4.5/4.7/5, Fable 5, Sonnet 5 | [Claude 4](https://www.anthropic.com/news/claude-4), [Opus 4.5](https://www.anthropic.com/news/claude-opus-4-5), [Opus 4.7](https://www.anthropic.com/news/claude-opus-4-7), [Fable 5](https://www.anthropic.com/news/claude-fable-5-mythos-5), [Sonnet 5](https://www.anthropic.com/news/claude-sonnet-5), [Opus 5](https://www.anthropic.com/news/claude-opus-5) |
| Google | Gemini 2.5 Pro, 3 Pro Preview, 3.1 Pro Preview, 3.1 Flash-Lite, 3.6 Flash | [2.5 Pro model page](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-pro), [Gemini 3](https://blog.google/technology/google-deepmind/gemini-3/), [3.1 Pro](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-pro/), [3.1 Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite), [3.6 Flash](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-6-flash-3-5-flash-lite-3-5-flash-cyber/) |
| Moonshot AI | Kimi K2, K2 0905, K2.5, K3 | [K2](https://huggingface.co/moonshotai/Kimi-K2-Instruct), [K2 0905](https://huggingface.co/moonshotai/Kimi-K2-Instruct-0905), [K2.5](https://huggingface.co/moonshotai/Kimi-K2.5), [K3](https://huggingface.co/moonshotai/Kimi-K3) |
| Z.ai | GLM-4.5, GLM-5, GLM-5.2 | [GLM-4.5](https://z.ai/blog/glm-4.5), [GLM-5](https://z.ai/blog/glm-5), [GLM-5.2 card](https://huggingface.co/zai-org/GLM-5.2), [GLM-5 architecture report](https://arxiv.org/html/2602.15763v2) |
| xAI | Grok 4, Grok 4.5 | [Grok 4](https://x.ai/news/grok-4), [Grok 4.5](https://x.ai/news/grok-4-5) |
| Mistral AI | Mistral Large 3 | [Mistral 3 announcement](https://mistral.ai/news/mistral-3/) |
| MiniMax | M2.1, M3 | [M2.1](https://www.minimax.io/news/minimax-m21), [M3 card](https://huggingface.co/MiniMaxAI/MiniMax-M3) |

OpenRouter IDs describe current served routes, not the provider release evidence. In particular, the current [`deepseek/deepseek-v4-flash-0731`](https://openrouter.ai/deepseek/deepseek-v4-flash-0731) route is a later re-post-trained revision of the [0423 route](https://openrouter.ai/deepseek/deepseek-v4-flash); the frozen 2026-07-26 InfoOpsBench result predates the 0731 revision.

### Requested-name resolution

| Requested label | Canonical registry treatment | Resolution |
|---|---|---|
| GLM-5.2 | `GLM-5.2` | Verified open-weight release. The registry uses the 753B Hugging Face artifact count for the size gate; the architecture report describes 744B total / 40B active, so parameter accounting differs. |
| Kimi K3 | `Kimi K3` | Verified open-weight release; 2.8T total / 104B active. |
| DeepSeek V4 | `DeepSeek V4 Pro`; `DeepSeek V4 Flash` | The provider released Pro and Flash preview tiers; both exceed 100B total, but Flash is an efficiency tier rather than the strict capability envelope. |
| Qwen 3.6 | `Qwen3.6 Max Preview` | The requested frontier entry is the hosted Max preview. The public `Qwen3.6-35B-A3B` checkpoint is below the 100B-total rule and is excluded. |
| Opus 5 / Sonnet 5 | `Claude Opus 5`; `Claude Sonnet 5` | Verified hosted tiers. Sonnet is retained for the safety/cost comparison, not as Anthropic's maximum-capability tier. |
| Fable | `Claude Fable 5` | Canonical provider name; the registry notes its deployment interruption and later redeployment rather than treating it as continuously available. |
| GPT-5.4 Sol / Luna / Terra | `GPT-5.4`; `GPT-5.6 Sol`; `GPT-5.6 Luna`; `GPT-5.6 Terra` | Sol, Luna, and Terra are GPT-5.6 served tiers, not GPT-5.4 variants. |
| Gemini 3.1 Flash | `Gemini 3.1 Flash-Lite`; separately `Gemini 3.6 Flash` | Google does not list a general-text endpoint with the exact requested name. Flash-Lite is the canonical 3.1 text endpoint; 3.6 Flash is a later distinct release. |

## Contextual evidence ledger

These works help define the evidence chain from model propensity to human effect. A scoped replication or later report can be ingested while the original study remains contextual; the status cell states the boundary explicitly.

| Evidence ID | Primary source | Construct and protocol relevance | Current status and exclusion reason |
|---|---|---|---|
| `ape` | Kowal et al., *It's the Thought that Counts: Evaluating the Attempts of Frontier LLMs to Persuade on Harmful Topics*, arXiv:2506.02873v3: <https://arxiv.org/html/2506.02873v3>; author code: <https://github.com/AlignmentResearch/AttemptPersuadeEval> | Multi-turn Attempt to Persuade Eval (APE); separates attempt, no-attempt, and refusal across benign, controversial, conspiracy, and harmful topics. | The original Figure 3 series remains `evidence_only`: it is not transcribed and no upstream code commit is pinned. The separately identified SaferAI turn-1 replication is ingested under its own protocol and category-specific comparison groups. Propensity is not persuasion efficacy. |
| `gdm-harmful-manipulation` | Akbulut et al., *Evaluating Language Models for Harmful Manipulation*, arXiv:2603.25326v1: <https://arxiv.org/html/2603.25326v1>; DeepMind overview: <https://deepmind.google/blog/protecting-people-from-harmful-manipulation/> | Controlled human-participant studies distinguish manipulative propensity from effects on beliefs and behavior across multiple domains and countries. | `evidence_only`; the study evaluates a single named model under several experimental conditions, so it is not a longitudinal model series. No effect-size row is ingested. |
| `anthropic-persuasiveness` | Durmus et al., *Measuring the Persuasiveness of Language Models*: <https://www.anthropic.com/research/measuring-model-persuasiveness> | Single written arguments on emerging policy claims; outcome is the pre/post change on a seven-point support scale. The study covers Claude generations and human-written controls. | `evidence_only`; Figure 1 is not transcribed. It measures short-run persuasion in a benign laboratory setting, not harmful manipulation or agentic campaigning. |

## Citation and update policy

1. Prefer papers, system cards, author datasets, and organization-controlled model cards over secondary summaries.
2. Preserve both the **model release date** and the **evaluation or publication date**. A retrospective cross-sectional evaluation is not a contemporaneous time series.
3. Pin source repositories by full commit SHA whenever item-level results are transformed.
4. Give each materially different prompt set, judge, sampling configuration, deployment condition, or aggregation rule a new `protocol_id`.
5. Label values as author-reported, derived from author data, digitized, or newly evaluated. Digitized or inferred values may not be presented as author-reported.
6. Do not calculate a single composite “agency transfer” score across these sources. They observe different constructs and use different denominators and metric directions.
