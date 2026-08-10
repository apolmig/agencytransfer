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

## Evidence ledger: identified but not numerically ingested

These works are retained because they help define the evidence chain from model propensity to human effect. They have no rows in `data/published/` at this release. Consequently, the site must not display a score for them until a separate ingestion records exact model versions, table or figure locators, denominators, and protocol identifiers.

| Evidence ID | Primary source | Construct and protocol relevance | Current status and exclusion reason |
|---|---|---|---|
| `ape` | Kowal et al., *It's the Thought that Counts: Evaluating the Attempts of Frontier LLMs to Persuade on Harmful Topics*, arXiv:2506.02873v3: <https://arxiv.org/html/2506.02873v3>; author code: <https://github.com/AlignmentResearch/AttemptPersuadeEval> | Multi-turn Attempt to Persuade Eval (APE); separates attempt, no-attempt, and refusal across benign, controversial, conspiracy, and harmful topics. | `evidence_only`; Figure 3 contains the multi-model result series, but no numeric rows are transcribed here and no upstream code commit is pinned. Propensity is not persuasion efficacy. |
| `gdm-harmful-manipulation` | Akbulut et al., *Evaluating Language Models for Harmful Manipulation*, arXiv:2603.25326v1: <https://arxiv.org/html/2603.25326v1>; DeepMind overview: <https://deepmind.google/blog/protecting-people-from-harmful-manipulation/> | Controlled human-participant studies distinguish manipulative propensity from effects on beliefs and behavior across multiple domains and countries. | `evidence_only`; the study evaluates a single named model under several experimental conditions, so it is not a longitudinal model series. No effect-size row is ingested. |
| `anthropic-persuasiveness` | Durmus et al., *Measuring the Persuasiveness of Language Models*: <https://www.anthropic.com/research/measuring-model-persuasiveness> | Single written arguments on emerging policy claims; outcome is the pre/post change on a seven-point support scale. The study covers Claude generations and human-written controls. | `evidence_only`; Figure 1 is not transcribed. It measures short-run persuasion in a benign laboratory setting, not harmful manipulation or agentic campaigning. |
| `infoopsbench` | Quelle et al., *InfoOps Bench: A live information operations safety benchmark*, arXiv:2607.28503: <https://arxiv.org/abs/2607.28503> | Live benchmark of model responses to prompts derived from monitored state-backed information-operation claims, with multiple prompt framings. | `evidence_only`; its changing claim stream and contemporary model cohort require a dated snapshot before ingestion. No score is copied into this repository. |

## Citation and update policy

1. Prefer papers, system cards, author datasets, and organization-controlled model cards over secondary summaries.
2. Preserve both the **model release date** and the **evaluation or publication date**. A retrospective cross-sectional evaluation is not a contemporaneous time series.
3. Pin source repositories by full commit SHA whenever item-level results are transformed.
4. Give each materially different prompt set, judge, sampling configuration, deployment condition, or aggregation rule a new `protocol_id`.
5. Label values as author-reported, derived from author data, digitized, or newly evaluated. Digitized or inferred values may not be presented as author-reported.
6. Do not calculate a single composite “agency transfer” score across these sources. They observe different constructs and use different denominators and metric directions.
