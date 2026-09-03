import { AnatomyIllustration } from "./ResearchIllustrations";
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
  return <AnatomyIllustration paper />;
}
