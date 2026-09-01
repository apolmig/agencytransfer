import { ELECTION_INDEX_URL, POLICY_ATLAS_URL, REPOSITORY_URL, DraftBoundary, PageLead, TextLink } from "./EditorialShell";
import { EditorialRiftVisual } from "./EditorialVisuals";

export function PartIIIPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="Part III · Field evidence" title="Evidence thins downstream" deck="Investigations can often identify accounts, calls, posts, payments, synthetic media, removals, and institutional responses. They rarely identify authentic exposure, prior belief, durable response, or the aggregate counterfactual.">
        <DraftBoundary>No prevalence estimate, causal zero-effect claim, durable agency-transfer estimate, or AI-attributable national-election outcome.</DraftBoundary>
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

export function PartIVPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="Part IV · Policy evidence" title="There are not six effective policies" deck="The six re-audited records were selected because they carried the strongest prior component-effect claims. They were an audit sample, not a shortlist. The 118 implementations are now grouped by comparative support and recommendation posture.">
        <DraftBoundary>The groups are not effect sizes or a universal ranking. They compare current evidence, causal fit, maturity, reversibility, rights costs, and the evidence needed to upgrade each claim.</DraftBoundary>
      </PageLead>
      <section className="v2-metrics-line" aria-label="Policy Atlas scope"><div><strong>68</strong><span>control families</span></div><div><strong>118</strong><span>implementations</span></div><div><strong>6</strong><span>comparative recommendation postures</span></div></section>
      <section className="v2-three-column">
        <article><p className="v2-eyebrow">A · 5 controls</p><h2>Act now on bounded component evidence</h2><p>Dark-pattern restrictions, forwarding friction, technique-based prebunking, official-source grounding, and data minimisation or user control have the strongest current support for narrow outcomes.</p><small>Claim ceiling: consent quality, sharing friction, recognition, factual accuracy, or data exposure—not durable agency preservation or electoral effect.</small></article>
        <article><p className="v2-eyebrow">B · 41 controls</p><h2>Build control and observability infrastructure</h2><p>Least privilege, consequential-action confirmation, traces, independent access, incident response, procurement exit, continuity, and retained public capability.</p><small>Strong causal fit; manipulation-specific downstream effectiveness remains mostly inferred.</small></article>
        <article><p className="v2-eyebrow">C · 31 controls</p><h2>Enforce legal and operational baselines</h2><p>Enforce platform, political-advertising, targeting, data-rights, audit, complaint, and high-risk election-AI duties where applicable.</p><small>Legal existence and compliance must remain separate from evidence of reduced agency transfer.</small></article>
      </section>
      <section className="v2-three-column">
        <article><p className="v2-eyebrow">D · 16 controls</p><h2>Use authenticity tools only as auxiliaries</h2><p>Provenance, labels, detection, caller authentication, sponsor notices, and ad repositories can improve attribution or observability for specified artefacts.</p><small>They are weak against truthful, relational, adaptive, encrypted, or cross-channel manipulation.</small></article>
        <article><p className="v2-eyebrow">E · 19 controls</p><h2>Pilot frontier-specific and structural controls</h2><p>Test root-purpose provenance, workflow guards, human-causal TEVV, memory and dependency monitoring, assistant loyalty, impact assessment, and functional portability.</p><small>Mechanistically relevant, but direct policy-effect evidence remains limited.</small></article>
        <article><p className="v2-eyebrow">F · 6 controls</p><h2>Research or hold unvalidated general triggers</h2><p>Do not use universal benchmark gates, blanket release or open-weight rules, or broad constitutional triggers as automatic thresholds without validation.</p><small>Construct validity, calibration, comparators, and decision rules remain insufficient.</small></article>
      </section>
      <section className="v2-principles"><p className="v2-eyebrow">Decision rule</p><div>{["Node-specific", "Layered", "Lawful", "Reversible", "Monitored", "Contestable"].map((item) => <span key={item}>{item}</span>)}</div><p>Act on the evidenced mechanism. Prefer narrow and reviewable controls under uncertainty. Combine layers, and stop the claim where the evidence stops.</p></section>
      <section className="v2-data-strip"><div><p>Comparative synthesis</p><strong>Recommendation posture, not a six-winner list</strong><span>The strongest support is for bounded component effects; the most important frontier-specific controls still require pilots.</span></div><TextLink href={`${REPOSITORY_URL}/blob/main/policy-atlas/COMPARATIVE_EVIDENCE_GROUPS.md`} external>Read the grouping</TextLink></section>
      <section className="v2-data-strip"><div><p>Public beta dataset</p><strong>Agency Transfer Policy Atlas</strong><span>Causal mapping, responsibility allocation, and research triage—not a policy-effect leaderboard.</span></div><TextLink href={POLICY_ATLAS_URL} external>Open the Policy Atlas</TextLink></section>
    </main>
  );
}
