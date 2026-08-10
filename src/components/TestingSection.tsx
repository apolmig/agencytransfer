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

interface TestingSectionProps {
  notes: TestingNoteRecord[];
}

const statusLabel: Record<TestingNoteStatus, string> = {
  planned: "Planned · no result",
  running: "In progress · no final result",
  complete: "Completed",
  blocked: "Blocked · no result",
  exploratory: "Exploratory",
};

const formatDate = (iso: string) => {
  if (!iso) return "Date pending";
  const value = new Date(iso.includes("T") ? iso : `${iso}T00:00:00Z`);
  if (Number.isNaN(value.getTime())) return iso;
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(value);
};

export function TestingSection({ notes }: TestingSectionProps) {
  const orderedNotes = [...notes].sort((a, b) => b.date.localeCompare(a.date));

  return (
    <section className="section testing-section" id="testing" aria-labelledby="testing-heading">
      <div className="section-heading split-heading">
        <div>
          <p className="section-number">02 · Testing · Exploratory project testing</p>
          <h2 id="testing-heading">Runs, results, and failures</h2>
        </div>
        <p>
          Each note states the exact model condition, protocol, result boundary, and public
          artifacts. Planned work is never presented as evidence; missing or blocked runs remain
          visible.
        </p>
      </div>

      {orderedNotes.length === 0 ? (
        <div className="testing-empty-state">
          <p className="mini-label">No completed project run</p>
          <p>Published evidence is shown elsewhere. This section will report new evaluations only after route integrity and validation checks pass.</p>
        </div>
      ) : (
        <div className="testing-notes">
          {orderedNotes.map((note) => {
            const hasResult = note.status === "complete" || note.status === "exploratory";
            return (
              <article className="testing-note" data-status={note.status} id={`testing-${note.id}`} key={note.id}>
                <div className="testing-note-heading">
                  <div>
                    <p className="mini-label">{statusLabel[note.status]} · {note.benchmark}</p>
                    <h3>{note.title}</h3>
                  </div>
                  <time dateTime={note.date || undefined}>{formatDate(note.date)}</time>
                </div>
                <p className="testing-note-summary">{note.summary}</p>
                <p className="testing-note-models">
                  <strong>Models</strong> {note.models.length > 0 ? note.models.join(" · ") : "Not yet frozen"}
                </p>

                <details className="testing-note-details">
                  <summary>Read the research note</summary>
                  <dl>
                    <div><dt>Question</dt><dd>{note.question}</dd></div>
                    <div><dt>Protocol</dt><dd>{note.protocol}</dd></div>
                    <div>
                      <dt>Result</dt>
                      <dd>{hasResult ? note.result : "No result is reported while this test is planned, running, or blocked."}</dd>
                    </div>
                    <div><dt>Interpretation</dt><dd>{hasResult ? note.interpretation : "Interpretation is deferred until the run and its validation are complete."}</dd></div>
                  </dl>

                  {note.limitations.length > 0 ? (
                    <div className="testing-limitations">
                      <h4>Limits</h4>
                      <ul>{note.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul>
                    </div>
                  ) : null}

                  <div className="testing-artifacts" aria-label={`Artifacts for ${note.title}`}>
                    {note.artifacts.length > 0 ? note.artifacts.map((artifact) => (
                      <a href={artifact.url} key={`${artifact.type}-${artifact.url}`} target="_blank" rel="noreferrer">
                        {artifact.label} <span aria-hidden="true">↗</span>
                      </a>
                    )) : <span>Public artifacts pending.</span>}
                  </div>
                </details>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
