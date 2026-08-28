import type { ElectionCaseRow } from "../programme";
import {
  electionCases,
  mechanismIllustrations,
  policyLayers,
} from "../programme";

export function CdeTopology({ compact = false }: { compact?: boolean }) {
  const nodes = [
    { title: "Capability", detail: "generation · reasoning · persuasion · deception" },
    { title: "Served system", detail: "provider · route · safeguards · tools · memory" },
    { title: "Deployment", detail: "actor · objective · targeting · delivery · repetition" },
    { title: "Authentic exposure", detail: "who encountered what · how often · under which identity" },
    { title: "Effect", detail: "human or institutional · belief · trust · behaviour · decisions" },
  ];

  return (
    <figure className={`programme-topology${compact ? " programme-topology--compact" : ""}`}>
      <div className="programme-topology__controller">
        <strong>Controller and deployment conditions</strong>
        <span>purpose · data · identity · authority · safeguards · distribution · concentration · observability</span>
      </div>
      <div className="programme-topology__nodes" role="list" aria-label="Capability–Deployment–Effect topology">
        {nodes.map((node, index) => (
          <div className="programme-topology__item" role="listitem" key={node.title}>
            <div className="programme-topology__node">
              <span className="programme-topology__index">{index + 1}</span>
              <strong>{node.title}</strong>
              <small>{node.detail}</small>
            </div>
            {index < nodes.length - 1 ? (
              <span className="programme-topology__arrow" aria-hidden="true">→</span>
            ) : null}
          </div>
        ))}
      </div>
      <figcaption>
        <strong>Every arrow is an empirical burden.</strong> A model output is not a campaign. A campaign is not authentic exposure. Exposure is not durable effect. Human and institutional effects are not the same thing.
      </figcaption>
      <div className="programme-topology__outcome">
        Agency transfer · concentration of power · democratic harm
      </div>
    </figure>
  );
}

export function EvidenceRiftVisual() {
  const layers = [
    { label: "Capability", value: "86", x: 92, y: 68 },
    { label: "Served system", value: "62", x: 150, y: 127 },
    { label: "Deployment", value: "32", x: 204, y: 196 },
    { label: "Authentic exposure", value: "10", x: 245, y: 279 },
    { label: "Human & institutional effects", value: "?", x: 268, y: 372 },
    { label: "Electoral outcomes", value: "?", x: 272, y: 459 },
  ];

  return (
    <figure className="rift-figure">
      <svg viewBox="0 0 760 520" role="img" aria-labelledby="rift-title rift-desc">
        <title id="rift-title">The evidence rift</title>
        <desc id="rift-desc">A conceptual cliff showing stronger evidence upstream and thinner evidence downstream. Numbers are evidence observations from different instruments, not an additive score.</desc>
        <defs>
          <linearGradient id="rift-paper" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#f8f6f1" />
            <stop offset="1" stopColor="#dedbd3" />
          </linearGradient>
          <linearGradient id="rift-stone" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#d8d4ca" />
            <stop offset="0.52" stopColor="#9d9c96" />
            <stop offset="1" stopColor="#4b4c4d" />
          </linearGradient>
          <filter id="rift-shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="8" stdDeviation="10" floodOpacity="0.16" />
          </filter>
        </defs>
        <rect width="760" height="520" rx="20" fill="url(#rift-paper)" />
        <path d="M346 42 C420 76 397 131 456 154 C505 173 489 230 536 251 C580 272 560 336 608 365 C648 389 648 441 704 478 L760 520 L309 520 C326 469 303 430 330 385 C354 345 319 308 347 271 C374 235 334 203 362 170 C389 138 339 103 346 42Z" fill="url(#rift-stone)" filter="url(#rift-shadow)" />
        <path d="M337 42 C403 78 377 126 431 152 C475 173 459 219 504 248 C546 274 519 325 566 360 C607 391 601 434 654 478" fill="none" stroke="#f8f6f1" strokeWidth="8" strokeLinecap="round" opacity="0.62" />
        <path d="M308 64 L286 486" stroke="#174d46" strokeWidth="3" />
        <path d="M298 476 L286 496 L274 476" fill="none" stroke="#174d46" strokeWidth="3" />
        <text x="38" y="70" className="rift-label rift-label--strong">UPSTREAM</text>
        <text x="38" y="92" className="rift-note">stronger evidence</text>
        <text x="38" y="458" className="rift-label rift-label--weak">DOWNSTREAM</text>
        <text x="38" y="480" className="rift-note">weaker / uncertain evidence</text>
        {layers.map((layer, index) => (
          <g key={layer.label}>
            <circle cx={layer.x + 210} cy={layer.y} r="24" fill="#f8f6f1" stroke={index < 2 ? "#174d46" : index < 4 ? "#b7792a" : "#8e273b"} strokeWidth="3" />
            <text x={layer.x + 210} y={layer.y + 7} textAnchor="middle" className="rift-value">{layer.value}</text>
            <text x={layer.x - 38} y={layer.y - 5} className="rift-node-title">{layer.label}</text>
            <line x1={layer.x + 108} y1={layer.y} x2={layer.x + 181} y2={layer.y} stroke="#777873" strokeWidth="1.5" strokeDasharray="4 5" />
          </g>
        ))}
        <text x="490" y="82" className="rift-big">THE</text>
        <text x="490" y="111" className="rift-big">EVIDENCE</text>
        <text x="490" y="140" className="rift-big">RIFT</text>
        <text x="490" y="183" className="rift-quote">Not a ladder.</text>
        <text x="490" y="207" className="rift-quote">A system.</text>
        <text x="490" y="231" className="rift-quote">The danger</text>
        <text x="490" y="255" className="rift-quote">sits in the joins.</text>
        <text x="392" y="501" className="rift-footnote">Numbers are evidence observed at different layers—not a score.</text>
      </svg>
      <figcaption>
        Evidence accumulates upstream and thins before authentic exposure, durable human response, and electoral consequence. The gap limits public claims; it does not erase mechanisms already observed.
      </figcaption>
    </figure>
  );
}

export function PartIEvidenceArchitecture() {
  const units = [
    {
      kicker: "Broadest pilot",
      title: "10 paired objectives",
      detail: "2 election-themed scenario families",
      note: "Official and safeguard-reduced configurations were compared descriptively; exact route equivalence is not established.",
    },
    {
      kicker: "Midpoint record",
      title: "3 exploratory probes",
      detail: "Protocol-generating evidence",
      note: "The record does not establish that the probes are disjoint from the paired pilot.",
    },
    {
      kicker: "Deepest forensic subset",
      title: "2 trace bundles · 5 requests",
      detail: "3 outputs · 18,907 ledger events",
      note: "Locally tamper-evident client records from one unidentified served route; no provider attestation.",
    },
    {
      kicker: "Research boundary",
      title: "0 live actions",
      detail: "0 authentic audience exposure",
      note: "Text described targeting, segmentation, and feedback; the route did not perform those actions.",
    },
  ];

  return (
    <figure className="part-i-architecture">
      <div className="part-i-architecture__grid">
        {units.map((unit, index) => (
          <article className={`part-i-unit part-i-unit--${index + 1}`} key={unit.title}>
            <p>{unit.kicker}</p>
            <h3>{unit.title}</h3>
            <strong>{unit.detail}</strong>
            <span>{unit.note}</span>
          </article>
        ))}
      </div>
      <figcaption>
        The ten-objective pilot, three probes, five forensic requests, and three completed outputs are different evidence units. They may partially overlap and should not be summed.
      </figcaption>
    </figure>
  );
}

export function AttemptRateGraphic() {
  const conditions = [
    { value: 66, label: "frozen candidates" },
    { value: 33, label: "started" },
    { value: 28, label: "finalised" },
    { value: 20, label: "well-covered" },
    { value: 0, label: "confirmatory estimates" },
  ];

  return (
    <figure className="attempt-graphic">
      <div className="attempt-graphic__conditions" aria-label="APE-120 condition attrition">
        {conditions.map((condition) => (
          <div className="attempt-condition" key={condition.label}>
            <div className="attempt-condition__bar" style={{ width: `${Math.max(8, (condition.value / 66) * 100)}%` }} />
            <strong>{condition.value}</strong>
            <span>{condition.label}</span>
          </div>
        ))}
      </div>
      <div className="attempt-graphic__records">
        <div>
          <span>Finalised records</span>
          <strong>3,360</strong>
        </div>
        <div>
          <span>Valid target + attempt evaluator</span>
          <strong>2,683</strong>
        </div>
        <div>
          <span>Evaluator-coded attempts</span>
          <strong>2,345</strong>
        </div>
      </div>
      <div className="attempt-graphic__headline">
        <div>
          <strong>87.4%</strong>
          <span>complete-case attempt rate</span>
        </div>
        <div>
          <strong>0 / 28</strong>
          <span>conditions reached the confirmatory gate</span>
        </div>
      </div>
      <div className="attempt-graphic__sensitivity" aria-label="Missingness sensitivity bounds">
        <span>69.8%</span>
        <div className="attempt-graphic__line">
          <i style={{ left: "65%" }} />
        </div>
        <strong>87.4%</strong>
        <span>89.9%</span>
      </div>
      <figcaption>
        The 69.8–89.9% range is a missingness sensitivity bound, not a confidence interval. Zero confirmatory estimates is a harness result, not a finding that every model failed a safety threshold.
      </figcaption>
    </figure>
  );
}

const caseColumns: Array<{ key: keyof ElectionCaseRow; label: string }> = [
  { key: "occurrence", label: "Occurrence" },
  { key: "mechanism", label: "Mechanism" },
  { key: "attribution", label: "Attribution" },
  { key: "distribution", label: "Distribution" },
  { key: "exposure", label: "Authentic exposure" },
  { key: "human", label: "Human effect" },
  { key: "electoral", label: "Electoral effect" },
  { key: "institutional", label: "Institutional response" },
];

export function ElectionEvidenceMatrix({ compact = false }: { compact?: boolean }) {
  return (
    <figure className={`election-matrix${compact ? " election-matrix--compact" : ""}`}>
      <div className="election-matrix__scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">Case</th>
              {caseColumns.map((column) => (
                <th scope="col" key={column.key}>{column.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {electionCases.map((row) => (
              <tr key={row.case}>
                <th scope="row">{row.case}</th>
                {caseColumns.map((column) => {
                  const status = row[column.key] as string;
                  return (
                    <td key={column.key}>
                      <span className={`evidence-cell evidence-cell--${status}`} title={`${column.label}: ${status.replace("-", " ")}`}>
                        <span className="sr-only">{status.replace("-", " ")}</span>
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="election-matrix__legend" aria-label="Evidence status legend">
        <span><i className="evidence-cell evidence-cell--established" /> Established</span>
        <span><i className="evidence-cell evidence-cell--supported" /> Supported / bounded</span>
        <span><i className="evidence-cell evidence-cell--partial" /> Partial / contested</span>
        <span><i className="evidence-cell evidence-cell--not-established" /> Not established</span>
      </div>
      <figcaption>
        Blank or light cells mean that the reviewed public record does not establish the claim. They do not prove that no effect occurred.
      </figcaption>
    </figure>
  );
}

export function PolicyPortfolio() {
  const max = Math.max(...policyLayers.map((layer) => layer.value));
  return (
    <figure className="policy-portfolio">
      <div className="policy-portfolio__metrics">
        <div><strong>68</strong><span>control families</span></div>
        <div><strong>118</strong><span>implementations</span></div>
        <div><strong>6</strong><span>checked effect fields</span></div>
        <div><strong>112</strong><span>effect-evidence backlog</span></div>
      </div>
      <div className="policy-portfolio__layers">
        {policyLayers.map((layer) => (
          <div className="policy-layer" key={layer.label}>
            <span>{layer.label}</span>
            <div><i style={{ width: `${(layer.value / max) * 100}%` }} /></div>
            <strong>{layer.value}</strong>
          </div>
        ))}
      </div>
      <figcaption>
        The portfolio is broad and primarily upstream. The Atlas maps responsibility and evidence maturity; it does not rank proven solutions.
      </figcaption>
    </figure>
  );
}

function MechanismGlyph({ id }: { id: string }) {
  if (id === "discovery") {
    return (
      <svg viewBox="0 0 180 110" aria-hidden="true">
        <circle cx="52" cy="50" r="24" />
        <circle cx="118" cy="33" r="15" />
        <circle cx="126" cy="80" r="18" />
        <path d="M73 44 L102 35 M72 61 L106 75" />
        <path d="M22 93 C48 68 86 68 101 96" />
      </svg>
    );
  }
  if (id === "model") {
    return (
      <svg viewBox="0 0 180 110" aria-hidden="true">
        <path d="M36 86 C36 56 51 24 91 24 C128 24 145 49 145 80" />
        <path d="M63 58 C78 45 105 45 120 58" />
        <circle cx="76" cy="59" r="4" />
        <circle cx="108" cy="59" r="4" />
        <path d="M78 76 C87 82 99 82 108 76" />
        <path d="M29 89 H151" />
      </svg>
    );
  }
  if (id === "identity") {
    return (
      <svg viewBox="0 0 180 110" aria-hidden="true">
        <path d="M27 79 C45 45 68 31 93 31 C121 31 139 47 153 77" />
        <path d="M57 39 C67 17 99 14 115 34" />
        <path d="M43 84 C67 96 112 96 139 83" />
        <path d="M70 62 C82 52 103 52 116 62" />
        <path d="M64 78 C84 66 103 66 122 78" />
      </svg>
    );
  }
  if (id === "distribution") {
    return (
      <svg viewBox="0 0 180 110" aria-hidden="true">
        <path d="M27 55 L78 33 V83 Z" />
        <path d="M78 47 C110 41 129 29 151 15" />
        <path d="M78 58 C111 58 130 58 156 58" />
        <path d="M78 71 C111 76 129 88 151 99" />
        <circle cx="154" cy="14" r="5" />
        <circle cx="159" cy="58" r="5" />
        <circle cx="154" cy="100" r="5" />
      </svg>
    );
  }
  if (id === "adaptation") {
    return (
      <svg viewBox="0 0 180 110" aria-hidden="true">
        <path d="M48 80 C21 53 42 22 76 24" />
        <path d="M67 14 L82 24 L68 36" />
        <path d="M132 30 C157 58 139 89 103 87" />
        <path d="M111 98 L96 87 L111 76" />
        <circle cx="90" cy="56" r="17" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 180 110" aria-hidden="true">
      <rect x="32" y="23" width="116" height="66" rx="8" />
      <path d="M55 43 H126 M55 57 H115 M55 71 H131" />
      <circle cx="137" cy="80" r="18" />
      <path d="M150 94 L163 107" />
    </svg>
  );
}

export function MechanismGallery() {
  return (
    <div className="mechanism-gallery">
      {mechanismIllustrations.map((mechanism) => (
        <article className="mechanism-card" key={mechanism.id}>
          <div className="mechanism-card__visual">
            <MechanismGlyph id={mechanism.id} />
            <span>{mechanism.number}</span>
          </div>
          <p>{mechanism.subtitle}</p>
          <h3>{mechanism.title}</h3>
          <div>{mechanism.body}</div>
        </article>
      ))}
    </div>
  );
}

export function PosterPreview() {
  return (
    <figure className="poster-preview" aria-label="Provisional research poster web preview">
      <div className="poster-preview__header">
        <span>Cambridge ERA flagship working paper</span>
        <strong>Harmful Manipulation<br />and Election Security</strong>
        <em>The Capability–Deployment–Effect Gap</em>
      </div>
      <div className="poster-preview__body">
        <div className="poster-preview__rift">
          <span>UPSTREAM</span>
          <div className="poster-preview__cliff" />
          <ol>
            <li><b>1</b>Capability <i>86</i></li>
            <li><b>2</b>Served system <i>62</i></li>
            <li><b>3</b>Deployment <i>32</i></li>
            <li><b>4</b>Exposure <i>10</i></li>
            <li><b>5</b>Human effects <i>?</i></li>
            <li><b>6</b>Electoral outcomes <i>?</i></li>
          </ol>
          <span>DOWNSTREAM</span>
        </div>
        <div className="poster-preview__panels">
          <article><b>PART I</b><span>Access-to-control evidence, not deployment.</span></article>
          <article><b>PART II</b><span>87.4% descriptive; 0/28 confirmatory.</span></article>
          <article><b>PART III</b><span>Operations are more observable than effects.</span></article>
          <article><b>PART IV</b><span>68 families; thin checked effect evidence.</span></article>
        </div>
      </div>
      <figcaption>
        Provisional web facsimile. It will be replaced by the final poster asset without changing the page structure.
      </figcaption>
    </figure>
  );
}

export function OnePageBriefPreview() {
  return (
    <article className="brief-preview">
      <header>
        <span>Cambridge ERA · One-page brief · August 2026</span>
        <h3>The next Cambridge Analytica will be a system</h3>
        <em>The Capability–Deployment–Effect Gap</em>
      </header>
      <CdeTopology compact />
      <div className="brief-preview__parts">
        <div><b>Part I</b><span>Operational precursors, no live action.</span></div>
        <div><b>Part II</b><span>Broad descriptive attempt evidence, non-confirmatory.</span></div>
        <div><b>Part III</b><span>Field records thin before human and electoral effect.</span></div>
        <div><b>Part IV</b><span>Many interventions, sparse checked effectiveness evidence.</span></div>
      </div>
      <footer>
        Match the intervention to the mechanism evidenced. Public claims stop where the evidence stops.
      </footer>
    </article>
  );
}
