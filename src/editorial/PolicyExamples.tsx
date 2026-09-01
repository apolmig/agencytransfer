import "./research-updates.css";

const examples = [
  {
    id: "marking",
    status: "Binding duty · technical evidence · electoral benefit untested",
    title: "Require AI-origin marking, without treating it as a truth label",
    example: "EU AI Act Article 50(2) requires providers to make covered synthetic outputs machine-readable and detectable. Article 50(4) separately requires disclosure of deepfakes and certain public-interest text. Watermarking is one method, not a universal requirement to put a visible watermark on every AI output.",
    evidence: "Dathathri and colleagues’ peer-reviewed SynthID-Text study tested watermarking in nearly 20 million Gemini responses. This supports technical feasibility in that setting, not resistance to political manipulation.",
    recommendation: "Enforce applicable marking and disclosure duties. Test whether origin information survives distribution, remains accessible and can be checked without dependence on one vendor. An absent marker does not establish human authorship; an AI marker does not establish falsity.",
    measure: "Marking coverage, detection errors, persistence across distribution and user understanding. Not votes changed or democracy protected.",
    qualification: "Article 50 generally applies from 2 August 2026. Article 111(4) gives providers of generators placed on the market before that date until 2 December 2026 to comply with Article 50(2). Editing, law-enforcement, creative-work and editorial exceptions must be checked separately. The supporting Code of Practice is voluntary.",
    sources: [
      ["AI Act · Articles 50, 111 and 113", "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02024R1689-20260727"],
      ["Commission · marking and labelling code", "https://digital-strategy.ec.europa.eu/en/policies/code-practice-ai-generated-content"],
      ["Dathathri et al. · Nature, 2024", "https://doi.org/10.1038/s41586-024-08025-4"],
    ],
  },
  {
    id: "dsa-chatgpt",
    status: "Designation confirmed · additional duties phased in · effects not established",
    title: "Use ChatGPT’s DSA designation to scrutinise the service, not just the model",
    example: "On 31 August 2026, the European Commission designated ChatGPT a Very Large Online Search Engine (VLOSE). The DSA’s additional obligations include systemic-risk assessment and mitigation, independent audits and qualified researcher access under specified conditions. They apply four months after notification, not immediately on the announcement date.",
    evidence: "The designation is an established regulatory event. It is not a finding that ChatGPT manipulated an election, evidence of completed compliance, or proof that supervision reduces harm.",
    recommendation: "Use Articles 34–35, 37 and 40 to examine the designated service’s actual interface, algorithms and influence pathways. Seek independent, privacy-protective evidence of concealed steering and electoral risks, rather than relying on a base-model score or provider assurance alone.",
    measure: "Auditable system coverage, identified risks, timely access for authorised scrutiny, mitigation performance and remedies. Test whether affected people gain practical control, not just whether reports exist.",
    qualification: "VLOSE means Very Large Online Search Engine. This is a service-specific designation, not automatic DSA designation of every chatbot. We use the statutory four-month rule rather than infer a calendar deadline without a verified notification date.",
    sources: [
      ["Commission · designation, 31 August 2026", "https://digital-strategy.ec.europa.eu/en/news/commission-designates-chatgpt-reddit-roblox-under-digital-services-act"],
      ["DSA · Articles 33–35, 37 and 40", "https://eur-lex.europa.eu/eli/reg/2022/2065/oj/eng"],
    ],
  },
  {
    id: "accuracy-prompts",
    status: "Experimental human evidence · bounded sharing outcome",
    title: "Prompt for accuracy, rather than add indiscriminate friction",
    example: "Pennycook and colleagues tested brief prompts directing attention to accuracy, including a Twitter field experiment. The study found improved quality of subsequently shared news. This is a specific intervention, not evidence that every extra click, forwarding cap or warning works.",
    evidence: "Peer-reviewed experiments support an attention-to-accuracy mechanism in the tested settings. The endpoint is sharing quality, not durable preference change, agency or election results.",
    recommendation: "Pilot concise accuracy prompts where people decide to share. Compare them with no prompt and generic friction; check whether truthful information and legitimate participation are impeded.",
    measure: "Sharing discernment, actual sharing, persistence and unequal burdens. Re-test in the intended language, platform and conversational setting before scaling.",
    qualification: "Transfer to personalised, multi-turn assistants remains an open question. This is a provisional design recommendation, not a claim that the fellowship ran these experiments.",
    sources: [["Pennycook et al. · Nature, 2021", "https://doi.org/10.1038/s41586-021-03344-2"]],
  },
  {
    id: "timely-corrections",
    status: "Quasi-experimental evidence · timing and coverage matter",
    title: "Make factual corrections arrive before most of the exposure",
    example: "In Slaughter and colleagues’ Community Notes study, synthetic-control estimates imply 46.1% fewer reposts after a note was attached, but 11.6% fewer across the posts’ full lifespans. The difference matters: much engagement can happen before correction.",
    evidence: "This peer-reviewed observational study supports bounded diffusion effects under its identification assumptions. It is not a randomised evaluation of the whole programme, an AI-origin label, or an election-effect estimate.",
    recommendation: "Prioritise timely, accurate, independently reviewable corrections. Pair reporting on treated posts with coverage of eligible content, missed cases, erroneous notes and appeal outcomes.",
    measure: "Time to correction, reach before correction, coverage and subsequent diffusion. Do not present a conditional post-attachment effect as population-wide protection.",
    qualification: "A January 2026 correction concerns competing-interest disclosure, not revised effect estimates. Effects on belief, agency and voting remain separate questions.",
    sources: [["Slaughter et al. · PNAS, 2025; correction 2026", "https://doi.org/10.1073/pnas.2503413122"]],
  },
  {
    id: "authority-boundaries",
    status: "Technical evidence · bounded threat model",
    title: "Put consequential permissions outside the model’s discretion",
    example: "CaMeL separates control flow from untrusted data and enforces security policies in a tested agent architecture. It addresses prompt injection under a threat model that trusts the initiating user query.",
    evidence: "This is technical, configuration-specific evidence. It does not show that the initiating actor’s objective is legitimate, or that a protected agent preserves the agency of people it affects.",
    recommendation: "Test externally enforced limits on recipients, tools and consequential actions, with revocation and review. Separately test harmful authorised objectives: defending an operator against outsiders is not enough to defend citizens against that operator.",
    measure: "Unauthorised-action success, useful-task completion, revocation latency and recovery. Audit who sets and can override the policy.",
    qualification: "The citizen-protection recommendation is an architectural inference from the threat-model boundary, not a measured democratic benefit of CaMeL. The cited source is a research preprint.",
    sources: [["Debenedetti et al. · CaMeL, version 2", "https://arxiv.org/abs/2503.18813v2"]],
  },
  {
    id: "conversational-defenders",
    status: "Early human preprint · replicate before a general mandate",
    title: "Pilot conversational defenders, and evaluate the defender too",
    example: "The August 2026 AI Watchdog preprint studied 150 participants across five conditions. A just-in-time intervention reduced AI-steered choices on a preregistered secondary outcome; the primary manipulation-detection outcome did not significantly improve.",
    evidence: "This is directly relevant but small, early evidence. Less compliance with an assistant does not by itself establish better understanding, goal-consistent choice or restored agency.",
    recommendation: "Independently replicate a user-dismissible defender against a no-defender baseline. Test misleading alerts and conflicts of interest, and let the user inspect, contest and disable it.",
    measure: "Primary and secondary outcomes separately; understanding, user-goal alignment, false alerts, delayed effects and dependence on the defender.",
    qualification: "A universal requirement for this particular design is not justified by this study alone. The safeguard must not quietly transfer authority to a second unaccountable operator.",
    sources: [["Poonsiriwong et al. · AI Watchdog, August 2026 preprint", "https://arxiv.org/abs/2608.21841"]],
  },
] as const;

const briefs: Record<string, string> = {
  marking: "Enforce applicable marking and disclosure duties. Technical feasibility is supported; reduced manipulation is not established.",
  "dsa-chatgpt": "Use service-level risk assessment and independent scrutiny. A designation creates duties, not proof of protection.",
  "accuracy-prompts": "Test an attention-to-accuracy prompt at the point of sharing. Evidence concerns sharing quality, not election results.",
  "timely-corrections": "Deliver accurate corrections early and measure coverage. Post-correction diffusion effects are not population-wide protection.",
  "authority-boundaries": "Enforce consequential permissions outside the model. Protecting an operator does not necessarily protect citizens from that operator.",
  "conversational-defenders": "Run independently evaluated, user-controlled pilots. Early secondary-outcome evidence does not justify a universal mandate.",
};

export function PolicyExamples() {
  return (
    <section className="research-update policy-examples" id="policy-examples" aria-labelledby="policy-examples-heading">
      <p className="research-update-kicker">Concrete examples · 1 September 2026</p>
      <h2 id="policy-examples-heading">Actions, evidence and limits</h2>
      <p>Legal duties and evidence of effectiveness answer different questions. Open an example for the original sources and the boundary of the recommendation.</p>
      <div className="policy-example-grid policy-example-grid--compact">
        {examples.map((item) => (
          <details className="policy-example" key={item.id} id={`example-${item.id}`}>
            <summary><p className="research-update-kicker">{item.status}</p><h3>{item.title}<span className="expand-label">Read more +</span></h3><p className="policy-example-brief">{briefs[item.id]}</p></summary>
            <div className="policy-example-body">
              <p>{item.example}</p>
              <p><strong>Evidence so far.</strong> {item.evidence}</p>
              <p><strong>Provisional recommendation.</strong> {item.recommendation}</p>
              <p><strong>Measure.</strong> {item.measure}</p><p><strong>Limit.</strong> {item.qualification}</p>
              <p className="research-update-sources">{item.sources.map(([label, href], i) => <span key={href}>{i ? " · " : ""}<a href={href} target="_blank" rel="noopener noreferrer">{label}</a></span>)}</p>
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}
