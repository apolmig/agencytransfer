import "../editorial/research-updates.css";

const programme = import.meta.env.BASE_URL;
const record = "https://github.com/apolmig/agencytransfer/blob/main/programme/reviews/20260901-draft-status-and-policy-examples.md";

export function EvidenceStatusKey() {
  return (
    <section className="research-update evidence-status-key" id="evidence-status" aria-labelledby="evidence-status-heading">
      <p className="research-update-kicker">How to read this research</p>
      <h2 id="evidence-status-heading">Work in progress, not settled conclusions</h2>
      <p>All programme results, coding decisions, interpretations and recommendations are draft, provisional and subject to correction. The programme has not been peer reviewed or independently replicated. A source-linked record makes a claim inspectable; it does not make it correct.</p>
      <dl>
        <div><dt>Established evidence</dt><dd>A bounded proposition directly supported by the cited record. It is not a claim that the whole research programme, a causal chain or a policy has been validated.</dd></div>
        <div><dt>Strong inference</dt><dd>A conclusion supported by evidence and a clear mechanism, but not directly observed at the endpoint claimed.</dd></div>
        <div><dt>Plausible hypothesis</dt><dd>A testable explanation with important missing evidence.</dd></div>
        <div><dt>Speculative scenario</dt><dd>A possible combination of conditions not demonstrated by this research.</dd></div>
        <div><dt>Open question</dt><dd>The available design or evidence does not resolve the question. Missing evidence is not evidence of zero harm.</dd></div>
      </dl>
      <p><strong>Source status is separate.</strong> An author-reported pilot is not independently verified. A preprint is not peer reviewed. An external peer-reviewed study does not validate our extrapolation. A binding law establishes an obligation, not its effectiveness.</p>
      <p><strong>The central unresolved outcome is agency transfer:</strong> whether people or public institutions lose practical control over attention, preferences, choices or dependencies while another actor gains it. Persuasion, disagreement with an assistant and voluntary delegation do not by themselves demonstrate that outcome.</p>
      <p className="research-update-sources"><a href={record} target="_blank" rel="noreferrer">Source notes and revision boundaries</a></p>
    </section>
  );
}

export function MeasurementGap({ compact = false }: { compact?: boolean }) {
  return (
    <section className={`research-update measurement-gap${compact ? " measurement-gap--compact" : ""}`} aria-label="Part II provisional measurement finding">
      <p className="research-update-kicker">Part II · provisional review finding</p>
      <h2>Useful evaluations. No shared system-level yardstick.</h2>
      <p>In the sources reviewed, we have not identified a widely accepted, independently validated standard that measures harmful manipulation as framed by the EU GPAI Code of Practice across deployed AI systems. That is a bounded review finding, not a claim that useful evaluations do not exist.</p>
      {compact ? <p className="research-update-sources"><a href={`${programme}registry/evidence/#measurement-gap`}>Why the gap matters, and what an instrument needs →</a></p> : <div id="measurement-gap">
        <p>Many evaluations measure a particular model or served version under fixed prompts. They do not establish the risk of the deployed system: its operator’s objective, interface, retrieval, memory, personalisation, permissions, tools and distribution. Risk can arise in their interaction, even where isolated model outputs look acceptable.</p>
        <p><strong>Important counterevidence.</strong> Some studies already use multi-turn conversations, human participants or agentic simulations. APE measures attempts to persuade on harmful topics. Akbulut and colleagues directly study harmful manipulation, separating propensity from efficacy. These are useful contributions, not a common cross-system certification instrument.</p>
        <p><strong>The regulatory target.</strong> The Code’s Safety and Security chapter identifies harmful manipulation as a systemic-risk category, including strategic distortion of behaviour or beliefs through persuasion, deception or personalised targeting. The Code is a voluntary route supporting binding Article 55 duties for relevant GPAI providers. It is neither a universal ban on persuasion nor a ready-made measurement standard.</p>
        <details><summary>The instrument we still need to build and validate</summary>
          <p>Evaluate the versioned system, not just its model name. Compare benign assistance, transparent persuasion and manipulative strategies in ethically reviewed, consent-based studies. Separate attempted influence, human response and impaired agency. Include repeated interaction, meaningful refusal, contestability, withdrawal and delayed follow-up.</p>
          <p>Record the controller and objective; model and configuration; memory, tools and permissions; human-calibrated measures; failed or missing observations; rights costs; and reproducibility. Re-test after material system changes. An instrument should establish whether a person can understand, direct, refuse and revise a consequential choice, not merely whether an assistant wins an argument.</p>
          <p>This is a research agenda, not a validated instrument delivered by this Registry. Our current data do not support a pooled harmful-manipulation score, a cross-model safety ranking or an election-risk threshold.</p>
        </details>
        <p className="research-update-sources"><a href="https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai" target="_blank" rel="noreferrer">EU GPAI Code of Practice</a> · <a href="https://arxiv.org/abs/2506.02873" target="_blank" rel="noreferrer">Kowal et al. · APE</a> · <a href="https://arxiv.org/abs/2603.25326" target="_blank" rel="noreferrer">Akbulut et al. · harmful manipulation</a> · <a href={record} target="_blank" rel="noreferrer">Review scope</a></p>
      </div>}
    </section>
  );
}

export function BudgetBoundary() {
  return (
    <aside className="research-update budget-boundary" aria-label="Part I budget and evidence boundary">
      <details><summary>What the $10 covers—and what it does not</summary><div>
      <p><strong>Author-reported exploratory pilot.</strong> $10 is a service-spend figure, not the total cost of an operation.</p>
      <p>The project’s draft one-pager reports approximately <strong>US$10 in direct service use</strong> for sandbox prototyping, alongside a <strong>separate, roughly US$500 one-time model-modification compute estimate</strong>. Labour, model acquisition and storage, audience data, accounts, advertising and distribution are excluded. These figures are not a reconciled, independently audited full-cost result.</p>
      <p>“Pretty far” describes the author’s provisional assessment of planning assistance and synthetic prototypes. It does not mean a campaign was deployed, people were persuaded or an election was affected. The more closely inspected trace subset is a different evidence unit and does not independently verify the pilot’s cost or all its reported comparisons.</p>
      <p className="research-update-sources"><a href={record + "#part-i-budget"} target="_blank" rel="noreferrer">Budget provenance and what remains to verify</a></p>
      </div></details>
    </aside>
  );
}

export function WebRevisionNote() {
  return (
    <aside className="research-update web-revision-note" aria-label="Manuscript version">
      <p><strong>Current working version: v1.5, 1 September 2026.</strong> This page is an overview; the complete manuscript and bibliography are linked below. Earlier PDF snapshots remain available. This publication update does not add experiments or change dataset grades.</p>
    </aside>
  );
}
