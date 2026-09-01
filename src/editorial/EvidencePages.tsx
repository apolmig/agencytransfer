import { ELECTION_INDEX_URL, DraftBoundary, PageLead, TextLink } from "./EditorialShell";
import { EditorialRiftVisual } from "./EditorialVisuals";
import "./research-updates.css";
export { PartIVPage } from "./PolicyPage";

const cetas = "https://cetas.turing.ac.uk/publications/ai-enabled-influence-operations-threat-analysis-2024-uk-and-european-elections";

export function PartIIIPage() {
  return (
    <main id="main-content" className="v2-main">
      <PageLead eyebrow="Part III · Field evidence · Draft / work in progress" title="Real operations. Unresolved electoral effects." deck="AI-enabled impersonation and influence attempts are documented, not merely imagined. What remains much less certain is who was authentically exposed, whose beliefs or behaviour changed, and whether any change altered an election result.">
        <DraftBoundary>This purposive record does not estimate prevalence or growth. Limited field evidence of individual effects is not proof that all effects are small. No AI-attributable national-election outcome is established by this programme’s reviewed evidence.</DraftBoundary>
      </PageLead>

      <section className="research-update" aria-labelledby="field-harms">
        <p className="research-update-kicker">What the evidence supports so far</p>
        <h2 id="field-harms">An unknown vote effect does not make an operation harmless</h2>
        <div className="field-examples">
          <article>
            <h3>Documented attempt: synthetic impersonation</h3>
            <p>The FCC’s 2024 New Hampshire record documents AI-generated candidate-impersonation robocalls and misleading caller identification. The record establishes a delivered influence attempt and an enforcement response, not how many recipients listened, believed it or changed their participation.</p>
            <p className="research-update-sources"><a href="https://docs.fcc.gov/public/attachments/FCC-24-104A1.pdf" target="_blank" rel="noreferrer">FCC · 2024 administrative record</a></p>
          </article>
          <article>
            <h3>Source-reported harm: harassment and confusion</h3>
            <p>CETaS’s review of selected 2024 UK, French and European election incidents documents candidate harassment, threats, distress and confusion about authenticity. It did not identify evidence that those incidents meaningfully altered election results. These harms matter independently of a vote-effect estimate.</p>
            <p className="research-update-sources"><a href={cetas} target="_blank" rel="noreferrer">Stockwell · CETaS, September 2024</a></p>
          </article>
        </div>
        <p><strong>Strong inference: attention and resources can be diverted without persuasion.</strong> An impersonation can force a candidate to rebut it, a journalist to verify it and an institution to investigate it. The documented response is observable; its total additional workload and opportunity cost are not estimated here. When an adversary determines what others must spend time correcting, attention and public capacity can be displaced even if nobody changes their vote.</p>
        <p><strong>Plausible hypothesis: wider access may enable more attempts.</strong> Cheaper generation, translation and automation make proliferation reasonable to anticipate. This Index cannot establish its rate: more recorded incidents could reflect more activity, better detection or changed reporting. Distribution, credibility and repeated access remain separate constraints.</p>
        <p><strong>Open question: when does disruption become durable agency transfer?</strong> That requires evidence that citizens or institutions lose practical control over attention, choices or dependencies while the controlling actor gains it. Noise and response costs are not, by themselves, a measurement of that durable shift.</p>
      </section>

      <div className="v2-wide-figure"><EditorialRiftVisual /><p className="v2-figure-caption">Conceptual illustration, not a prevalence or effect estimate. “No identified effect” is not “zero effect.” Institutional harm does not require every step of a voter-persuasion chain.</p></div>
      <section className="v2-evidence-pair">
        <article><p className="v2-eyebrow">Source-linked observations</p><h2>Operations and responses are real</h2><p>The Romania and Moldova records include coordinated promotion, amplification and institutional investigations. Attribution, the contribution of generative AI and the meaning of reach metrics differ by claim. Not every inauthentic operation is an AI operation, and not every synthetic asset is manipulative.</p></article>
        <article><p className="v2-eyebrow">Bounded and unresolved effects</p><h2>Do not turn reach into changed votes</h2><p>Controlled studies can show individual effects under specified conditions. Field effects are harder to identify, heterogeneous and often weakly observed. Account counts, views and engagement are not unique people, durable persuasion or a causal election result. Nor does an institutional decision establish a voter-level effect.</p></article>
      </section>
      <section className="research-update" aria-labelledby="field-next">
        <p className="research-update-kicker">Provisional recommendation</p>
        <h2 id="field-next">Measure the burden as well as the ballot</h2>
        <p>Alongside authentic exposure and human response, record harassment reports, time to correction, staff hours, delayed decisions, evidence loss and wrongful intervention. Use defined denominators and comparators, preserve privacy and due process, and do not wait for an election-wide causal estimate before responding to an evidenced harm.</p>
      </section>
      <section className="v2-data-strip"><div><p>Draft analytic layer · existing evidence freeze</p><strong>10 claim-coded records · 8 eligible for incident counting</strong><span>The broader catalogue is not a count of confirmed manipulation campaigns. Comparative studies on this page are not added to the incident denominator.</span></div><TextLink href={ELECTION_INDEX_URL} external>Open the Evidence Index</TextLink></section>
      <p className="v2-draft-line"><strong>Work in progress.</strong> Corpus selection, coding and interpretation remain provisional and have not been independently replicated. External incidents are not fellowship interventions; no real audience was targeted by this research.</p>
    </main>
  );
}
