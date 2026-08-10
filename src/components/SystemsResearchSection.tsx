const systemQuestions = [
  {
    title: "Memory and repetition",
    copy: "Hold the model and prompt fixed, then vary whether prior interactions are available. Measure changes in refusal, attempted influence, and user-reported trust across repeated sessions.",
  },
  {
    title: "Objectives and tools",
    copy: "Compare otherwise matched systems with different objectives, tool access, and escalation rules. Keep model behaviour distinct from application-level effects.",
  },
  {
    title: "User control",
    copy: "Test whether disclosure, contestability, memory controls, and easy exit reduce measured influence without making the system unusable.",
  },
];

export function SystemsResearchSection() {
  return (
    <section className="section systems-research-section" id="systems" aria-labelledby="systems-heading">
      <div className="section-heading split-heading">
        <div>
          <p className="section-number">Planned research direction · not current evidence</p>
          <h2 id="systems-heading">From model response to system behaviour</h2>
        </div>
        <p>
          Current benchmarks isolate selected model behaviours. Future work will vary one system
          feature at a time—such as memory, tools, objectives, defaults, or repeated contact—and
          measure the result separately from the base model response.
        </p>
      </div>

      <div className="causal-chain-block systems-causal-block">
        <p className="mini-label">Plausible system-level pathway · to be tested</p>
        <ol className="causal-chain systems-causal-chain">
          <li>Model response</li>
          <li>System condition</li>
          <li>Repeated interaction</li>
          <li>Measured human outcome</li>
          <li>Decision authority</li>
        </ol>
        <p>
          A model score establishes none of the later links. Each link needs its own protocol,
          comparison condition, and evidence.
        </p>
      </div>

      <div className="systems-scenarios" aria-label="Planned system research questions">
        {systemQuestions.map((question) => (
          <article className="systems-scenario" key={question.title}>
            <p className="mini-label">Planned test · no result yet</p>
            <h3>{question.title}</h3>
            <p>{question.copy}</p>
          </article>
        ))}
      </div>

      <aside className="systems-boundary">
        <p className="mini-label">Measurement boundary</p>
        <p>
          These are testable hypotheses for future evaluation. They do not claim that a named model,
          provider, or deployment has changed anyone&apos;s beliefs or transferred decision authority.
        </p>
      </aside>
    </section>
  );
}
