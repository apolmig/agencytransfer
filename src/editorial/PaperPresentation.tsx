import { route } from "./EditorialShell";
import "./paper-presentation.css";

export function PaperCitation() {
  return (
    <section className="v2-citation paper-citation" aria-label="Suggested citation">
      <p className="v2-eyebrow">Citation</p>
      <p>Miguel Guerrero. <em>Harmful Manipulation and Election Security: The Capability–Deployment–Effect Gap.</em> ERA:AI, 2026. Unpublished draft.</p>
    </section>
  );
}

export function PaperConceptFigure() {
  const full = route("media/cde-gap3-hero-1672.webp");
  return (
    <figure className="paper-concept-figure" aria-labelledby="paper-concept-caption">
      <a href={full} target="_blank" rel="noopener noreferrer" aria-label="View the CDE illustration at full size (opens a new tab)">
        <img
          src={full}
          srcSet={`${route("media/cde-gap3-hero-824.webp")} 824w, ${full} 1672w`}
          sizes="(max-width: 760px) calc(100vw - 32px), (max-width: 1180px) calc(100vw - 64px), 1080px"
          width={1672}
          height={941}
          loading="lazy"
          decoding="async"
          alt="The CDE Gap: AI capability and deployment on one side of a rift, electoral consequences on the other. Exposure, attention, beliefs and intentions mark uncertain links between them."
        />
      </a>
      <figcaption id="paper-concept-caption">
        <p><strong>Capability is not deployment; deployment is not effect.</strong> Exposure, attention, beliefs and intentions require separate evidence. This is a conceptual illustration, not a completed causal chain or an estimate of harm.</p>
        <a href={full} target="_blank" rel="noopener noreferrer">View full-size illustration <span aria-hidden="true">↗</span></a>
      </figcaption>
    </figure>
  );
}
