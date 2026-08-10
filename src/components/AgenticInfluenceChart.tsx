import { useMemo, useState } from "react";
import type { AgenticInfluenceResult } from "../types";

const WIDTH = 1160;
const HEIGHT = 466;
const MARGIN = { top: 36, right: 42, bottom: 102, left: 66 };

const scenarioLabel: Record<AgenticInfluenceResult["scenario"], string> = {
  "voter-suppression": "Voter suppression",
  "domestic-polarization": "Domestic polarization",
};

const shortName = (model: string) =>
  model.replace("Claude ", "").replace("Mythos Preview", "Mythos Preview");

const formatDate = (iso: string) =>
  new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric" }).format(
    new Date(`${iso}T00:00:00Z`),
  );

interface Props {
  results: AgenticInfluenceResult[];
}

export function AgenticInfluenceChart({ results }: Props) {
  const [activeModel, setActiveModel] = useState("Claude Opus 4.8");
  const models = useMemo(
    () =>
      [...new Map(results.map((row) => [row.model, row])).values()].sort((a, b) =>
        a.releaseDate.localeCompare(b.releaseDate),
      ),
    [results],
  );
  const series = useMemo(
    () =>
      (["voter-suppression", "domestic-polarization"] as const).map((scenario) => ({
        scenario,
        rows: results
          .filter((row) => row.scenario === scenario)
          .sort((a, b) => a.releaseDate.localeCompare(b.releaseDate)),
      })),
    [results],
  );
  const activeRows = results.filter((row) => row.model === activeModel);

  const minTime = new Date("2026-02-01T00:00:00Z").getTime();
  const maxTime = new Date("2026-07-15T00:00:00Z").getTime();
  const x = (date: string) => {
    const time = new Date(`${date}T00:00:00Z`).getTime();
    return (
      MARGIN.left +
      ((time - minTime) / (maxTime - minTime)) * (WIDTH - MARGIN.left - MARGIN.right)
    );
  };
  const y = (value: number) =>
    MARGIN.top + ((100 - value) / 100) * (HEIGHT - MARGIN.top - MARGIN.bottom);

  return (
    <div className="chart-shell agentic-chart-shell">
      <div className="chart-intro-row">
        <p className="chart-measure">
          <strong>Malicious agentic influence campaigns</strong>
          <span>Average share of 70 success criteria completed in a simulated environment.</span>
        </p>
        <p className="chart-legend" aria-label="Legend">
          <span><i className="legend-line voter" aria-hidden="true" /> Voter suppression</span>
          <span><i className="legend-line polarization" aria-hidden="true" /> Domestic polarization</span>
        </p>
      </div>
      <div className="condition-banner">
        <strong>Helpful-only variants.</strong> Harmlessness training was reduced to test raw
        capability. Anthropic reports that fully trained versions refused from the first turn.
      </div>
      <div className="chart-scroller">
        <svg
          className="longitudinal-chart agentic-chart"
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          role="img"
          aria-labelledby="agentic-chart-title agentic-chart-description"
        >
          <title id="agentic-chart-title">
            Claude helpful-only agentic influence campaign completion by release date
          </title>
          <desc id="agentic-chart-description">
            Seven Claude releases between February and June 2026, tested on voter suppression and
            domestic polarization. Completion rates are author-reported raw capability scores and
            do not measure effects on real people.
          </desc>
          {[0, 25, 50, 75, 100].map((tick) => (
            <g key={tick} aria-hidden="true">
              <line
                className="grid-line"
                x1={MARGIN.left}
                x2={WIDTH - MARGIN.right}
                y1={y(tick)}
                y2={y(tick)}
              />
              <text className="axis-label y-label" x={MARGIN.left - 14} y={y(tick) + 4}>
                {tick}%
              </text>
            </g>
          ))}
          {models.map((model, index) => {
            const px = x(model.releaseDate);
            const labelOffset = index % 2 === 0 ? 25 : 59;
            return (
              <g key={model.model} aria-hidden="true">
                <line
                  className="year-line"
                  x1={px}
                  x2={px}
                  y1={MARGIN.top}
                  y2={HEIGHT - MARGIN.bottom}
                />
                <text className="agentic-model-label" x={px} y={HEIGHT - MARGIN.bottom + labelOffset}>
                  {shortName(model.model)}
                </text>
                <text className="agentic-date-label" x={px} y={HEIGHT - MARGIN.bottom + labelOffset + 18}>
                  {formatDate(model.releaseDate).replace(" 2026", "")}
                </text>
              </g>
            );
          })}
          {series.map(({ scenario, rows }) => (
            <polyline
              key={scenario}
              className={`agentic-series ${scenario}`}
              points={rows.map((row) => `${x(row.releaseDate)},${y(row.scorePct)}`).join(" ")}
              aria-hidden="true"
            />
          ))}
          {results.map((row) => {
            const px = x(row.releaseDate);
            const py = y(row.scorePct);
            const selected = activeModel === row.model;
            return row.scenario === "voter-suppression" ? (
              <circle
                key={`${row.model}-${row.scenario}`}
                className={`agentic-point voter ${selected ? "is-active" : ""}`}
                cx={px}
                cy={py}
                r={selected ? 7.5 : 6}
                tabIndex={0}
                role="button"
                aria-pressed={selected}
                aria-label={`${row.model}, ${scenarioLabel[row.scenario]}, ${row.scorePct} percent`}
                onMouseEnter={() => setActiveModel(row.model)}
                onFocus={() => setActiveModel(row.model)}
                onClick={() => setActiveModel(row.model)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    setActiveModel(row.model);
                  }
                }}
              />
            ) : (
              <rect
                key={`${row.model}-${row.scenario}`}
                className={`agentic-point polarization ${selected ? "is-active" : ""}`}
                x={px - (selected ? 7 : 5.5)}
                y={py - (selected ? 7 : 5.5)}
                width={selected ? 14 : 11}
                height={selected ? 14 : 11}
                tabIndex={0}
                role="button"
                aria-pressed={selected}
                aria-label={`${row.model}, ${scenarioLabel[row.scenario]}, ${row.scorePct} percent`}
                onMouseEnter={() => setActiveModel(row.model)}
                onFocus={() => setActiveModel(row.model)}
                onClick={() => setActiveModel(row.model)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    setActiveModel(row.model);
                  }
                }}
              />
            );
          })}
          <text
            className="axis-title"
            transform={`translate(18 ${HEIGHT / 2}) rotate(-90)`}
            aria-hidden="true"
          >
            Success criteria completed
          </text>
        </svg>
      </div>
      <div className="chart-detail" aria-live="polite">
        <div>
          <span className="detail-kicker">Selected release</span>
          <strong>{activeModel}</strong>
          <span>{activeRows[0] ? formatDate(activeRows[0].releaseDate) : ""}</span>
        </div>
        <dl>
          {activeRows.map((row) => (
            <div key={row.scenario}>
              <dt>{scenarioLabel[row.scenario]}</dt>
              <dd>{row.scorePct.toFixed(1)}%</dd>
            </div>
          ))}
          <div><dt>Simulations</dt><dd>9 per scenario</dd></div>
          <div><dt>Criteria</dt><dd>70 per scenario</dd></div>
        </dl>
      </div>
      <p className="chart-caption">
        Author-reported results compiled from the Claude Sonnet 5 System Card, §5.1.3,
        Table 5.1.3.A, p. 56, and the Claude Opus 4.7 System Card, §5.1.3,
        Table 5.1.3.A, p. 81. Each scenario ran three times at three friction levels. Higher means
        greater raw capability and potential uplift to a malicious actor. The sequence is
        non-monotonic, covers only Claude, and does not test human efficacy. No confidence intervals
        were reported in either table.
      </p>
      <details className="data-table-details">
        <summary>View author-reported data table</summary>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Release</th>
                <th scope="col">Model</th>
                <th scope="col">Voter suppression</th>
                <th scope="col">Domestic polarization</th>
                <th scope="col">Condition</th>
              </tr>
            </thead>
            <tbody>
              {models.map((model) => {
                const modelRows = results.filter((row) => row.model === model.model);
                return (
                  <tr key={model.model}>
                    <td>{model.releaseDate}</td>
                    <th scope="row">{model.model}</th>
                    <td>{modelRows.find((row) => row.scenario === "voter-suppression")?.scorePct}%</td>
                    <td>{modelRows.find((row) => row.scenario === "domestic-polarization")?.scorePct}%</td>
                    <td>Helpful-only</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
