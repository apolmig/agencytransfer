import { route } from "./EditorialShell";
import "./research-illustrations.css";

const media = (name: string) => route(`media/illustrations/${name}`);

export function AnatomyIllustration({ paper = false }: { paper?: boolean }) {
  const full = media("anatomy-manipulation-1672.webp");
  return (
    <figure className={`research-illustration research-illustration--anatomy${paper ? " paper-concept-figure" : ""}`} aria-labelledby="anatomy-caption">
      <a className="research-illustration-image" href={full} target="_blank" rel="noopener noreferrer" aria-label="Open the Anatomy illustration at full size (new tab)">
        <img
          src={full}
          srcSet={`${media("anatomy-manipulation-824.webp")} 824w, ${full} 1672w`}
          sizes="(max-width: 760px) calc(100vw - 40px), (max-width: 1180px) calc(100vw - 80px), 1080px"
          width={1672}
          height={941}
          loading={paper ? "eager" : "lazy"}
          fetchPriority={paper ? "high" : "auto"}
          decoding="async"
          alt="Anatomy of an AI manipulation operation: an operator connects model capability, audience discovery, vulnerability inference, content generation and delivery, with possible feedback and adaptation. A lower strip marks agency, control and safeguard points."
        />
      </a>
      <figcaption id="anatomy-caption">
        <p className="research-illustration-label">Part I · Conceptual illustration · Working draft</p>
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

export function PolicyAtlasIllustration() {
  const full = media("policy-intervention-atlas-1600.webp");
  return (
    <figure className="research-illustration research-illustration--policy-atlas" aria-labelledby="policy-atlas-caption">
      <a className="research-illustration-image" href={full} target="_blank" rel="noopener noreferrer" aria-label="Open the policy intervention atlas at full size (new tab)">
        <img
          src={full}
          srcSet={`${media("policy-intervention-atlas-800.webp")} 800w, ${full} 1600w`}
          sizes="(max-width: 760px) calc(100vw - 40px), (max-width: 1180px) calc(100vw - 80px), 1080px"
          width={1600}
          height={900}
          loading="eager"
          fetchPriority="high"
          decoding="async"
          alt="Policy intervention atlas showing control families across capability, deployment, exposure, effect or response, cross-layer and institutional areas. The image separates broad policy coverage from the much smaller set of checked effect fields."
        />
      </a>
      <figcaption id="policy-atlas-caption">
        <p className="research-illustration-label">Part IV · Evidence map · Working draft</p>
        <h2>Where interventions act—and where their evidence stops</h2>
        <p>The policy portfolio is broad. Checked implementation-effect evidence is much narrower and depends on the endpoint measured.</p>
        <div className="research-illustration-reading research-illustration-reading--columns">
          <p><strong>Coverage is not effectiveness.</strong> The family counts show where controls are aimed, not whether they protect autonomy, institutions or elections.</p>
          <p><strong>Measure the nearest endpoint.</strong> A disclosure, audit, friction mechanism or access rule should first be assessed against the decision it directly changes.</p>
          <p><strong>Preserve the next bridge.</strong> Evidence must remain available for independent challenge before stronger claims are made.</p>
        </div>
        <details>
          <summary>What the visual does not establish</summary>
          <p>The displayed counts are a dated snapshot of the Part IV working register. They are not a ranking of interventions, six proven policy winners, or evidence that the remaining entries fail. The illustrated links are conceptual, not observed causal pathways.</p>
        </details>
        <p className="research-illustration-links"><a className="research-illustration-full" href={full} target="_blank" rel="noopener noreferrer">Open full-size illustration <span aria-hidden="true">↗</span><span className="sr-only"> (opens a new tab)</span></a><a href={route("research/part-iv/#policy-examples")}>Read the policy evidence <span aria-hidden="true">→</span></a></p>
      </figcaption>
    </figure>
  );
}

export function CircuitBreakersIllustration({ linkToEvidence = false }: { linkToEvidence?: boolean }) {
  const full = media("policy-circuit-breakers-1448.webp");
  return (
    <figure className="research-illustration research-illustration--circuit" aria-labelledby="circuit-breakers-caption">
      <a className="research-illustration-image" href={full} target="_blank" rel="noopener noreferrer" aria-label="Open the Democratic Circuit Breakers illustration at full size (new tab)">
        <img
          src={full}
          srcSet={`${media("policy-circuit-breakers-768.webp")} 768w, ${full} 1448w`}
          sizes="(max-width: 760px) calc(100vw - 40px), (max-width: 1180px) 65vw, 720px"
          width={1448}
          height={1086}
          loading="lazy"
          decoding="async"
          alt="Democratic Circuit Breakers: detection and review connect to possible monitoring, friction, warnings, reach limits and enforcement. Evidence preservation, legal review, public communication and remedy appear below."
        />
      </a>
      <figcaption id="circuit-breakers-caption">
        <p className="research-illustration-label">Artifacts · Conceptual response map · Working draft</p>
        <h2>A practical map of intervention points</h2>
        <p>This illustration makes the programme’s policy artifacts easier to navigate. It is not a validated defence package.</p>
        <div className="research-illustration-reading">
          <p><strong>Review before acting.</strong> Detection, attribution, technical analysis and impact assessment answer different questions.</p>
          <p><strong>Match response to mechanism.</strong> Monitoring, warnings, friction, reach limits and enforcement require different authority and evidence.</p>
          <p><strong>Keep power contestable.</strong> Preserve records, enable legal review, communicate publicly and provide remedy.</p>
        </div>
        <details>
          <summary>What the illustration does not establish</summary>
          <p>The red-to-blue flow, “trusted information” and “informed citizens” depict desired outcomes. The image does not show that these measures work together, restore agency or protect an election. Synthetic content and coordinated activity are not automatically harmful.</p>
        </details>
        <p className="research-illustration-links"><a className="research-illustration-full" href={full} target="_blank" rel="noopener noreferrer">Open full-size illustration <span aria-hidden="true">↗</span><span className="sr-only"> (opens a new tab)</span></a>{linkToEvidence ? <a href={route("research/part-iv/#policy-examples")}>Read the policy evidence <span aria-hidden="true">→</span></a> : null}</p>
      </figcaption>
    </figure>
  );
}
