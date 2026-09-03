import { route } from "./EditorialShell";
import "./research-illustrations.css";

const media = (name: string) => route(`media/illustrations/${name}`);

export function AnatomyIllustration({ paper = false }: { paper?: boolean }) {
  const full = media("anatomy-manipulation-1672.webp");
  return (
    <figure className={`research-illustration research-illustration--anatomy${paper ? " paper-concept-figure" : ""}`} aria-labelledby="anatomy-caption">
      <a className="research-illustration-image" href={full} target="_blank" rel="noopener noreferrer" aria-label="Open the Anatomy illustration at full size (new tab)">
        <img src={full} srcSet={`${media("anatomy-manipulation-824.webp")} 824w, ${full} 1672w`} sizes="(max-width: 760px) calc(100vw - 40px), (max-width: 1180px) calc(100vw - 80px), 1080px" width={1672} height={941} loading="lazy" decoding="async" alt="Anatomy of an AI manipulation operation: an operator connects model capability, audience information, content and delivery, with possible feedback and adaptation. A lower strip marks agency, control and safeguard points." />
      </a>
      <figcaption id="anatomy-caption">
        <p className="research-illustration-label">Conceptual illustration · Working draft</p>
        <p><strong>Anatomy of an AI manipulation operation.</strong> A map of possible connections, not a record of a completed operation. The behavioural objective is an intention—not an observed effect.</p>
        <details>
          <summary>How to read this illustration</summary>
          <p><strong>Control.</strong> Start with the actor and objective, not the model alone. The diagram asks which parts of the system one actor could connect and control.</p>
          <p><strong>Missing evidence.</strong> Content creation, delivery, authentic exposure and human response are separate questions. The feedback arrows depict possible adaptation; this programme did not observe the whole loop operating against real people.</p>
          <p><strong>Agency.</strong> The lower strip poses the governance question: can affected people understand, refuse and contest the influence? Neither autonomy of the AI nor a changed choice alone establishes agency transfer.</p>
        </details>
        <a className="research-illustration-full" href={full} target="_blank" rel="noopener noreferrer">Open full-size illustration <span aria-hidden="true">↗</span><span className="sr-only"> (opens a new tab)</span></a>
      </figcaption>
    </figure>
  );
}

export function PolicyIllustration({ linkToEvidence = false }: { linkToEvidence?: boolean }) {
  const full = media("policy-circuit-breakers-1448.webp");
  return (
    <figure className="research-illustration research-illustration--policy" aria-labelledby="policy-map-caption">
      <a className="research-illustration-image" href={full} target="_blank" rel="noopener noreferrer" aria-label="Open the Democratic Circuit Breakers illustration at full size (new tab)">
        <img src={full} srcSet={`${media("policy-circuit-breakers-768.webp")} 768w, ${full} 1448w`} sizes="(max-width: 760px) calc(100vw - 40px), (max-width: 1180px) 65vw, 720px" width={1448} height={1086} loading="lazy" decoding="async" alt="Democratic Circuit Breakers: detection and review connect to possible monitoring, friction, warnings, reach limits and enforcement. Evidence preservation, legal review, public communication and remedy appear below." />
      </a>
      <figcaption id="policy-map-caption">
        <p className="research-illustration-label">Part IV · Conceptual map · Working draft</p>
        <h2>Where could a response intervene?</h2>
        <p>A map of response options, not a ranking of effective policies.</p>
        <div className="research-illustration-reading">
          <p><strong>Review the evidence.</strong> Detection, attribution and impact assessment answer different questions.</p>
          <p><strong>Match the response.</strong> Monitoring, warnings, friction and restrictions are different interventions. Each needs its own evidence and safeguards.</p>
          <p><strong>Keep it contestable.</strong> Preserve records, allow independent review and provide a route to challenge and remedy. Oversight must not become another unaccountable source of control.</p>
        </div>
        <details>
          <summary>What the illustration does not establish</summary>
          <p>The red-to-blue flow, “trusted information” and “informed citizens” depict intended outcomes, not demonstrated results. The image does not show that these measures work together, restore agency or protect an election. Synthetic content and coordinated activity are not automatically harmful.</p>
        </details>
        <p className="research-illustration-links"><a className="research-illustration-full" href={full} target="_blank" rel="noopener noreferrer">Open full-size illustration <span aria-hidden="true">↗</span><span className="sr-only"> (opens a new tab)</span></a>{linkToEvidence ? <a href={route("research/part-iv/#policy-examples")}>Read the policy evidence <span aria-hidden="true">→</span></a> : null}</p>
      </figcaption>
    </figure>
  );
}
