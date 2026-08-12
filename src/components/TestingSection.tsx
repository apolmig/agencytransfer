export type TestingNoteStatus = "planned" | "running" | "complete" | "blocked" | "exploratory";

export interface TestingArtifactLink {
  label: string;
  url: string;
  type: "github" | "hugging-face" | "data" | "methods" | "other";
}

export interface TestingNoteRecord {
  id: string;
  title: string;
  status: TestingNoteStatus;
  validationStatus: "pending" | "validated" | "failed";
  validatedAt?: string;
  validationMethod?: string;
  validationArtifactUrl?: string;
  date: string;
  benchmark: string;
  models: string[];
  summary: string;
  question: string;
  protocol: string;
  result: string;
  interpretation: string;
  limitations: string[];
  artifacts: TestingArtifactLink[];
}

interface TestingSectionProps { notes: TestingNoteRecord[] }

const isValidatedResult = (note: TestingNoteRecord) =>
  note.status === "complete" &&
  note.validationStatus === "validated" &&
  Boolean(note.validationArtifactUrl);

const formatDate = (iso: string) => {
  const value = new Date(iso.includes("T") ? iso : `${iso}T00:00:00Z`);
  if (Number.isNaN(value.getTime())) return iso;
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }).format(value);
};

export function TestingSection({ notes }: TestingSectionProps) {
  const validated = notes.filter(isValidatedResult).sort((first, second) => second.date.localeCompare(first.date));
  const exploratory = notes.filter((note) => !isValidatedResult(note));

  return (
    <section className="section testing-section" id="validated-results" aria-labelledby="testing-heading">
      <div className="section-heading split-heading">
        <div><p className="section-number">Validation gate</p><h2 id="testing-heading">No outcome-tuned claims</h2></div>
        <p>Statistical significance is not a target to tune toward. The protocol, sample size, judge validation, exclusions, and stopping rule must be frozen before a confirmatory run.</p>
      </div>

      {validated.length === 0 ? (
        <div className="testing-gate">
          <p className="mini-label">No validated project result yet</p>
          <h3>The pilot did not pass the publication gate.</h3>
          <p>It was small, automated-only, provider-heterogeneous, and produced uneven usable denominators. It remains a historical failed engineering audit—not a ranked benchmark result.</p>
          <ol>
            <li><strong>1 · Freeze</strong><span>Protocol, routes, items, exclusions, power analysis, and stopping rule.</span></li>
            <li><strong>2 · Validate</strong><span>Blind human audit of labels and inter-rater agreement.</span></li>
            <li><strong>3 · Run</strong><span>Comparable endpoints with complete route and error logs.</span></li>
            <li><strong>4 · Publish</strong><span>Effect sizes, uncertainty, failures, sensitivity, and preregistered analyses.</span></li>
          </ol>
          <a href="https://github.com/apolmig/agencytransfer/tree/main/research/testing" target="_blank" rel="noreferrer">Exploratory audit trail ({exploratory.length} notes) ↗</a>
        </div>
      ) : (
        <div className="testing-notes">
          {validated.map((note) => (
            <article className="testing-note" id={`testing-${note.id}`} key={note.id}>
              <div className="testing-note-heading">
                <div><p className="mini-label">Validated · {note.benchmark}</p><h3>{note.title}</h3></div>
                <time dateTime={note.date}>{formatDate(note.date)}</time>
              </div>
              <p className="testing-note-summary">{note.summary}</p>
              <dl className="validated-result-grid">
                <div><dt>Result</dt><dd>{note.result}</dd></div>
                <div><dt>Interpretation</dt><dd>{note.interpretation}</dd></div>
                <div><dt>Limits</dt><dd>{note.limitations.join(" ")}</dd></div>
              </dl>
              <div className="testing-artifacts">
                {note.artifacts.map((artifact) => <a href={artifact.url} key={artifact.url} target="_blank" rel="noreferrer">{artifact.label} ↗</a>)}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
