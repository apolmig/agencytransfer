import { useMemo, useState } from "react";
import type { WaveModel } from "../types";

const WIDTH = 1120;
const HEIGHT = 360;
const MARGIN = { top: 32, right: 42, bottom: 54, left: 72 };

const formatDate = (iso: string) =>
  new Intl.DateTimeFormat("en-GB", { month: "short", year: "numeric" }).format(
    new Date(`${iso}T00:00:00Z`),
  );

const statusLabel: Record<WaveModel["openRouterStatus"], string> = {
  available: "Listed",
  unavailable: "Not listed",
  verify: "Mutable alias",
};

interface Props {
  models: WaveModel[];
}

export function ModelPanel({ models }: Props) {
  const [activeId, setActiveId] = useState("deepseek-ai/DeepSeek-V4-Flash-0731");
  const sorted = useMemo(
    () => [...models].sort((a, b) => a.releaseDate.localeCompare(b.releaseDate)),
    [models],
  );
  const active = sorted.find((model) => model.canonicalModelId === activeId) ?? sorted.at(-1)!;
  const minTime = new Date(`${sorted[0].releaseDate}T00:00:00Z`).getTime();
  const maxTime = new Date(`${sorted.at(-1)!.releaseDate}T00:00:00Z`).getTime();
  const x = (date: string) => {
    const time = new Date(`${date}T00:00:00Z`).getTime();
    return (
      MARGIN.left +
      ((time - minTime) / (maxTime - minTime)) * (WIDTH - MARGIN.left - MARGIN.right)
    );
  };
  const minLog = Math.log10(100);
  const maxLog = Math.log10(3000);
  const y = (params: number) =>
    MARGIN.top +
    ((maxLog - Math.log10(params)) / (maxLog - minLog)) *
      (HEIGHT - MARGIN.top - MARGIN.bottom);

  return (
    <div className="model-panel">
      <div className="chart-scroller model-chart-scroller">
        <svg
          className="model-timeline"
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          role="img"
          aria-labelledby="model-panel-title model-panel-description"
        >
          <title id="model-panel-title">Candidate open-weight evaluation panel, 2022 to 2026</title>
          <desc id="model-panel-description">
            Release dates and total parameter counts for open-weight models with at least one
            hundred billion total parameters. Availability refers to the OpenRouter catalogue on
            10 August 2026 and is not a performance result.
          </desc>
          {[100, 300, 1000, 3000].map((tick) => (
            <g key={tick} aria-hidden="true">
              <line
                className="grid-line"
                x1={MARGIN.left}
                x2={WIDTH - MARGIN.right}
                y1={y(tick)}
                y2={y(tick)}
              />
              <text className="axis-label y-label" x={MARGIN.left - 14} y={y(tick) + 4}>
                {tick >= 1000 ? `${tick / 1000}T` : `${tick}B`}
              </text>
            </g>
          ))}
          {[2023, 2024, 2025, 2026].map((year) => {
            const position = x(`${year}-01-01`);
            return (
              <g key={year} aria-hidden="true">
                <line
                  className="year-line"
                  x1={position}
                  x2={position}
                  y1={MARGIN.top}
                  y2={HEIGHT - MARGIN.bottom}
                />
                <text className="axis-label" x={position} y={HEIGHT - MARGIN.bottom + 29}>
                  {year}
                </text>
              </g>
            );
          })}
          {sorted.map((model, index) => {
            const px = x(model.releaseDate);
            const py = y(model.totalParamsB);
            const activePoint = model.canonicalModelId === active.canonicalModelId;
            const unavailable = model.openRouterStatus === "unavailable";
            return (
              <g
                className={`model-point-group ${activePoint ? "is-active" : ""}`}
                key={model.canonicalModelId}
              >
                <line
                  className="model-stem"
                  x1={px}
                  x2={px}
                  y1={py}
                  y2={HEIGHT - MARGIN.bottom}
                  aria-hidden="true"
                />
                <circle
                  className={`model-point ${unavailable ? "is-unavailable" : ""}`}
                  cx={px}
                  cy={py}
                  r={activePoint ? 8 : 6}
                  tabIndex={0}
                  role="button"
                  aria-pressed={activePoint}
                  aria-label={`${model.model}, released ${formatDate(model.releaseDate)}, ${model.totalParamsB} billion total parameters, ${statusLabel[model.openRouterStatus]} on OpenRouter`}
                  onMouseEnter={() => setActiveId(model.canonicalModelId)}
                  onFocus={() => setActiveId(model.canonicalModelId)}
                  onClick={() => setActiveId(model.canonicalModelId)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      setActiveId(model.canonicalModelId);
                    }
                  }}
                />
                <text
                  className="model-point-label"
                  x={px}
                  y={py + (index % 2 === 0 ? -13 : 21)}
                  aria-hidden="true"
                >
                  {model.model.replace(" Instruct", "")}
                </text>
              </g>
            );
          })}
          <text
            className="axis-title"
            transform={`translate(20 ${HEIGHT / 2}) rotate(-90)`}
            aria-hidden="true"
          >
            Total parameters · log scale
          </text>
        </svg>
      </div>

      <div className="model-detail" aria-live="polite">
        <div>
          <span className="detail-kicker">Selected candidate</span>
          <strong>{active.model}</strong>
          <span>{active.canonicalModelId}</span>
        </div>
        <dl>
          <div><dt>Total / active</dt><dd>{active.totalParamsB}B / {active.activeParamsB ?? "?"}B</dd></div>
          <div><dt>Release</dt><dd>{formatDate(active.releaseDate)}</dd></div>
          <div><dt>OpenRouter</dt><dd>{statusLabel[active.openRouterStatus]}</dd></div>
          <div><dt>Wave</dt><dd>{active.wave.replaceAll("-", " ")}</dd></div>
        </dl>
        <p>{active.note}</p>
      </div>

      <p className="chart-caption">
        Parameter count is an inclusion rule and deployment descriptor, not a capability score.
        MoE models show total and activated parameters separately. Catalogue status was checked on
        10 August 2026; aliases and providers can change.
      </p>

      <details className="data-table-details">
        <summary>View evaluation manifest ({sorted.length} candidate releases)</summary>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Release</th>
                <th scope="col">Model</th>
                <th scope="col">Total / active</th>
                <th scope="col">Licence</th>
                <th scope="col">OpenRouter route</th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((model) => (
                <tr key={model.canonicalModelId}>
                  <td>{model.releaseDate}</td>
                  <th scope="row">
                    <a href={model.sourceUrl} target="_blank" rel="noreferrer">{model.model}</a>
                  </th>
                  <td>{model.totalParamsB}B / {model.activeParamsB ?? "?"}B</td>
                  <td>{model.licence}</td>
                  <td><code>{model.openRouterId}</code></td>
                  <td>{statusLabel[model.openRouterStatus]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
