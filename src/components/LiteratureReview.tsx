interface Paper {
  title: string;
  authors: string;
  year: string;
  url: string;
  measures: string;
  boundary: string;
  role: string;
}

const papers: Paper[] = [
  {
    title: "Sociotechnical Safety Evaluation of Generative AI Systems",
    authors: "Weidinger et al.",
    year: "2023",
    url: "https://arxiv.org/abs/2310.11986",
    measures: "A framework separating model capability, human interaction, and systemic-impact evaluation.",
    boundary: "Conceptual framework, not an empirical manipulation study or scoring formula.",
    role: "Evidence layers",
  },
  {
    title: "A Rosetta Stone for AI Benchmarks",
    authors: "Ho et al. · Epoch AI & Google DeepMind",
    year: "2025",
    url: "https://arxiv.org/html/2512.00193v1",
    measures: "Links model-by-benchmark results through overlapping evaluations on a shared latent scale.",
    boundary: "Validated on a dense accuracy-benchmark network; it does not show that ATB's heterogeneous instruments form one trait.",
    role: "Measurement linking",
  },
  {
    title: "A Mechanism-Based Approach to Mitigating Harms from Persuasive Generative AI",
    authors: "El-Sayed et al.",
    year: "2024",
    url: "https://arxiv.org/abs/2404.15058",
    measures: "Distinctions between persuasion, manipulation, mechanisms, and process or outcome harms.",
    boundary: "Taxonomy and mitigation map, not a comparative model benchmark.",
    role: "Construct definition",
  },
  {
    title: "It’s the Thought that Counts: Evaluating Attempts to Persuade on Harmful Topics",
    authors: "Kowal et al.",
    year: "2026",
    url: "https://arxiv.org/abs/2506.02873",
    measures: "Whether models attempt harmful persuasion across defined strata.",
    boundary: "Attempt propensity, not whether a person is persuaded.",
    role: "P · 20%",
  },
  {
    title: "InfoOps Bench: A Live Information Operations Safety Benchmark",
    authors: "Quelle et al.",
    year: "2026",
    url: "https://arxiv.org/abs/2607.28503",
    measures: "Compliance with and completion of state influence-operation tasks.",
    boundary: "Endpoint behaviour under one protocol, not campaign efficacy.",
    role: "O · 40%",
  },
  {
    title: "Large language models can consistently generate high-quality content for election disinformation operations",
    authors: "Williams et al.",
    year: "2025",
    url: "https://doi.org/10.1371/journal.pone.0317421",
    measures: "Compliance and content generation for election-operation requests.",
    boundary: "Generated responses, not exposure, belief change, or vote change.",
    role: "O · 40%",
  },
  {
    title: "MASK: Disentangling Honesty From Accuracy in AI Systems",
    authors: "MASK authors",
    year: "2025",
    url: "https://arxiv.org/abs/2503.03750",
    measures: "Lying under pressure when a model's stated answer conflicts with its beliefs.",
    boundary: "Deception propensity, not targeted manipulation of a person.",
    role: "D · 10%",
  },
  {
    title: "Agentic influence evaluations",
    authors: "Anthropic",
    year: "2026",
    url: "https://cdn.sanity.io/files/4zrzovbb/website/037f06850df7fbe871e206dad004c3db5fd50340.pdf",
    measures: "Tool-using completion of simulated voter-suppression and polarisation workflows.",
    boundary: "Helpful-only variants; no real people or default deployment safeguards.",
    role: "A · 30%",
  },
  {
    title: "Measuring Model Persuasiveness",
    authors: "Anthropic",
    year: "2024",
    url: "https://www.anthropic.com/research/measuring-model-persuasiveness",
    measures: "Human belief change after single-turn arguments from successive Claude generations.",
    boundary: "One experimental setting; automated judges did not reliably track human effects.",
    role: "Interpretation only",
  },
  {
    title: "Protecting people from harmful manipulation",
    authors: "Google DeepMind",
    year: "2026",
    url: "https://deepmind.google/blog/protecting-people-from-harmful-manipulation/",
    measures: "A framework separating model propensity from human efficacy.",
    boundary: "Risk is context-specific; propensity cannot substitute for efficacy.",
    role: "Construct definition",
  },
  {
    title: "Evaluating Language Models for Harmful Manipulation",
    authors: "Akbulut et al.",
    year: "2026",
    url: "https://arxiv.org/abs/2603.25326",
    measures: "Human-study manipulation efficacy and its relation to automated propensity measures.",
    boundary: "Propensity was not consistently predictive of efficacy.",
    role: "Interpretation only",
  },
  {
    title: "On the Conversational Persuasiveness of GPT-4",
    authors: "Salvi et al.",
    year: "2025",
    url: "https://www.nature.com/articles/s41562-025-02194-6",
    measures: "Post-debate agreement after short personalized and non-personalized GPT-4 or human conversations.",
    boundary: "US sample, randomized debate sides, immediate agreement; no behavior, persistence, or organic exposure.",
    role: "Interpretation only",
  },
  {
    title: "Persuasive Effects of Political Microtargeting in the Age of Generative AI",
    authors: "Hackenburg & Margetts",
    year: "2024",
    url: "https://www.pnas.org/doi/10.1073/pnas.2403116121",
    measures: "Political attitude effects of generic and microtargeted GPT-4 messages in a preregistered experiment.",
    boundary: "Static messages and four issues; attitude change rather than behavior, persistence, or natural reach.",
    role: "Interpretation only",
  },
  {
    title: "The Levers of Political Persuasion with Conversational AI",
    authors: "Hackenburg et al.",
    year: "2025",
    url: "https://www.science.org/doi/10.1126/science.aea3884",
    measures: "Political attitude effects of model choice, prompting, and information density across three large experiments.",
    boundary: "Paid UK experimental engagement; persuasion gains can trade off with factual accuracy.",
    role: "Interpretation only",
  },
  {
    title: "AI Can Persuade People to Take Political Actions",
    authors: "Hackenburg et al.",
    year: "2026",
    url: "https://arxiv.org/abs/2604.09200",
    measures: "Petition signing and donations after multi-turn political conversations.",
    boundary: "Paid UK sample and low-cost actions; no organic reach, high-stakes behavior, or agency transfer.",
    role: "Interpretation only",
  },
];

export function LiteratureReview() {
  return (
    <div className="literature-table-wrap">
      <table className="literature-table">
        <thead>
          <tr><th scope="col">Paper</th><th scope="col">What it measures</th><th scope="col">Critical boundary</th><th scope="col">Use here</th></tr>
        </thead>
        <tbody>
          {papers.map((paper) => (
            <tr key={paper.title}>
              <th scope="row"><a href={paper.url} target="_blank" rel="noreferrer">{paper.title}</a><span>{paper.authors} · {paper.year}</span></th>
              <td>{paper.measures}</td>
              <td>{paper.boundary}</td>
              <td>{paper.role}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
