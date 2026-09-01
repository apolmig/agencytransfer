import { ELECTION_INDEX_URL, DraftBoundary, PageLead, TextLink } from "./EditorialShell";
import { EditorialRiftVisual } from "./EditorialVisuals";
export { PartIVPage } from "./PolicyPage";

export function PartIIIPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="Part III · Field evidence" title="Evidence thins downstream" deck="Investigations can often identify accounts, calls, posts, payments, synthetic media, removals, and institutional responses. They rarely identify authentic exposure, prior belief, durable response, or the aggregate counterfactual.">
        <DraftBoundary>No prevalence estimate, causal zero-effect claim, durable agency-transfer estimate, or an AI-attributable national-election outcome.</DraftBoundary>
      </PageLead>
      <div className="v2-wide-figure"><EditorialRiftVisual /><p className="v2-figure-caption">“No identified effect” is not “zero effect.” Every bridge—from delivery to authentic exposure, attention, belief, choice, and electoral consequence—requires new evidence.</p></div>
      <section className="v2-evidence-pair">
        <article><p className="v2-eyebrow">Usually documented</p><h2>Operations and institutional response</h2><ul><li>Occurrence and mechanism</li><li>Some attribution evidence</li><li>Distribution events or proxies</li><li>Removals, enforcement, or judicial response</li></ul></article>
        <article><p className="v2-eyebrow">Usually unresolved</p><h2>Authentic exposure and effect</h2><ul><li>Unique people reached</li><li>Attention and processing</li><li>Durable belief or behavioural change</li><li>Aggregate electoral consequence</li></ul></article>
      </section>
      <section className="v2-data-strip"><div><p>Current analytic layer</p><strong>10 claim-coded records · 8 eligible for incident counting</strong><span>The broader catalogue is not a count of confirmed manipulation campaigns.</span></div><TextLink href={ELECTION_INDEX_URL} external>Open the Evidence Index</TextLink></section>
    </main>
  );
}
