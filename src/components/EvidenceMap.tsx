import type { BenchmarkRecord } from "../types";

const statusCopy: Record<BenchmarkRecord["status"], string> = {
  live: "Live in Wave 0",
  ingestion: "Published results in review",
  planned: "Project rerun planned",
  external: "External evidence",
};

const layerCopy: Record<BenchmarkRecord["evidenceLayer"], string> = {
  capability: "Operational capability",
  safeguard: "Safeguard behaviour",
  efficacy: "Human efficacy",
  access: "Practical access",
};

interface Props {
  benchmarks: BenchmarkRecord[];
}

export function EvidenceMap({ benchmarks }: Props) {
  return (
    <div className="evidence-map">
      <div className="evidence-axis" aria-hidden="true">
        <span>Capability</span>
        <span>Safeguards</span>
        <span>Human effect</span>
        <span>Agency transfer</span>
      </div>
      <p className="evidence-warning">
        Shared timeline, separate constructs. The empty final column is deliberate: none of these
        instruments directly measures transfer of agency.
      </p>
      <div className="benchmark-grid">
        {benchmarks.map((benchmark) => (
          <article className={`benchmark-card layer-${benchmark.evidenceLayer}`} key={benchmark.id}>
            <div className="benchmark-card-meta">
              <span>{layerCopy[benchmark.evidenceLayer]}</span>
              <span>{statusCopy[benchmark.status]}</span>
            </div>
            <h3>{benchmark.name}</h3>
            <p className="benchmark-construct">{benchmark.construct}</p>
            <dl>
              <div>
                <dt>Measures</dt>
                <dd>{benchmark.observes}</dd>
              </div>
              <div>
                <dt>Does not establish</dt>
                <dd>{benchmark.doesNotObserve}</dd>
              </div>
            </dl>
            <p className="benchmark-foot">
              <span>{benchmark.modelPeriod}</span>
              <a href={benchmark.sourceUrl} target="_blank" rel="noreferrer">
                Primary source <span aria-hidden="true">↗</span>
              </a>
            </p>
          </article>
        ))}
      </div>
    </div>
  );
}
