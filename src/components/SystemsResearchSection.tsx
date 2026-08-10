const systemScenarios = [
  {
    title: "Customer service",
    copy: "Use a controlled Qwen3.6 Max Preview configuration as one candidate backbone to test whether organisational prompts, memory, escalation rules, and commercial objectives create cumulative pressure absent from a one-turn evaluation.",
  },
  {
    title: "Elder care",
    copy: "Use a controlled Sonnet 5 configuration as one candidate backbone to study repeated reliance, synthetic intimacy, delegated choices, and the ability to contest or leave an assistant-mediated relationship, under an appropriate ethics protocol.",
  },
  {
    title: "Minors",
    copy: "Examine age assurance, repeated exposure, recommendation defaults, dependency, and safety gaps outside conventional chat interfaces. No testing with minors is proposed without independent ethics review.",
  },
];

export function SystemsResearchSection() {
  return (
    <section className="section systems-research-section" id="systems" aria-labelledby="systems-heading">
      <div className="section-heading split-heading">
        <div>
          <p className="section-number">Planned research direction · not current evidence</p>
          <h2 id="systems-heading">The model is not the system</h2>
        </div>
        <p>
          Current benchmarks isolate selected model behaviours. Real-world influence can also emerge
          from the surrounding application: its memory, tools, objectives, interface, defaults,
          recommender, and repeated contact with a person. As AI becomes infrastructure, that effect
          may be incremental and persuasive long before it resembles a single conspicuous chat.
        </p>
      </div>

      <div className="causal-chain-block systems-causal-block">
        <p className="mini-label">Plausible system-level pathway · to be tested</p>
        <ol className="causal-chain systems-causal-chain">
          <li>Model capability</li>
          <li>Prompts, memory, tools, and objectives</li>
          <li>Repeated and personalised interaction</li>
          <li>Attention, trust, preference, behaviour, or dependency</li>
          <li>Agency transfer</li>
          <li>Concentrated power and democratic harm</li>
        </ol>
        <p>
          A model score establishes none of the later links. The research task is to identify which
          system choices create, amplify, constrain, or reverse them—and which actor controls those
          choices.
        </p>
      </div>

      <div className="systems-scenarios" aria-label="Planned system research scenarios">
        {systemScenarios.map((scenario) => (
          <article className="systems-scenario" key={scenario.title}>
            <p className="mini-label">Planned scenario · not evidence of harm</p>
            <h3>{scenario.title}</h3>
            <p>{scenario.copy}</p>
          </article>
        ))}
      </div>

      <aside className="systems-boundary">
        <p className="mini-label">Measurement boundary</p>
        <p>
          These scenarios are hypotheses for future evaluation. They do not claim that a named model,
          provider, or existing deployment has changed anyone&apos;s beliefs or transferred agency.
        </p>
      </aside>
    </section>
  );
}
