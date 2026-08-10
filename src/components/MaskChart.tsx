import { useState } from "react";
import type { MaskResult } from "../types";

type MaskMetric = "liePct" | "honestPct" | "accuracyPct";

const metricCopy: Record<MaskMetric, { label: string; direction: string }> = {
  liePct: { label: "P(Lie)", direction: "Lower is better" },
  honestPct: { label: "P(Honest)", direction: "Higher is better" },
  accuracyPct: { label: "Accuracy", direction: "Higher is better" },
};

const WIDTH = 920;
const HEIGHT = 360;
const MARGIN = { top: 30, right: 36, bottom: 72, left: 58 };

interface Props {
  results: MaskResult[];
}

export function MaskChart({ results }: Props) {
  const [metric, setMetric] = useState<MaskMetric>("liePct");
  const [activeId, setActiveId] = useState("deepseek-ai/DeepSeek-V3");
  const rows = [...results].sort((a, b) => a.releaseDate.localeCompare(b.releaseDate));
  const active = rows.find((row) => row.canonicalModelId === activeId) ?? rows[0];
  const minTime = new Date("2024-03-15T00:00:00Z").getTime();
  const maxTime = new Date("2025-03-01T00:00:00Z").getTime();
  const x = (date: string) => {
    const time = new Date(`${date}T00:00:00Z`).getTime();
    return MARGIN.left + ((time - minTime) / (maxTime - minTime)) * (WIDTH - MARGIN.left - MARGIN.right);
  };
  const y = (value: number) =>
    MARGIN.top + ((100 - value) / 100) * (HEIGHT - MARGIN.top - MARGIN.bottom);
  const deepSeekRows = rows.filter((row) => row.model.startsWith("DeepSeek"));

  return (
    <div className="mask-panel">
      <div className="mask-panel-copy">
        <p className="section-number">Published open-weight evidence</p>
        <h3>Honesty under pressure</h3>
        <p>
          MASK tests whether a model contradicts its own elicited belief when pressured to lie.
          It is relevant to deceptive influence, but it is not a manipulation evaluation.
        </p>
        <div className="segmented-control compact" role="group" aria-label="MASK metric">
          {(Object.keys(metricCopy) as MaskMetric[]).map((key) => (
            <button
              key={key}
              type="button"
              className={metric === key ? "is-active" : ""}
              aria-pressed={metric === key}
              onClick={() => setMetric(key)}
            >
              {metricCopy[key].label}
            </button>
          ))}
        </div>
        <p className="metric-direction">{metricCopy[metric].direction}</p>
      </div>
      <div className="mask-chart-area">
        <div className="chart-scroller">
          <svg
            className="mask-chart"
            viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
            role="img"
            aria-labelledby="mask-chart-title mask-chart-description"
          >
            <title id="mask-chart-title">MASK {metricCopy[metric].label} for four open-weight models</title>
            <desc id="mask-chart-description">
              Four open-weight models above one hundred billion total parameters, released between
              April 2024 and January 2025. Only DeepSeek V3 and R1 are connected because they share a family.
            </desc>
            {[0, 25, 50, 75, 100].map((tick) => (
              <g key={tick} aria-hidden="true">
                <line className="grid-line" x1={MARGIN.left} x2={WIDTH - MARGIN.right} y1={y(tick)} y2={y(tick)} />
                <text className="axis-label y-label" x={MARGIN.left - 12} y={y(tick) + 4}>{tick}%</text>
              </g>
            ))}
            <polyline
              className="family-path deepseek-mask-line"
              points={deepSeekRows.map((row) => `${x(row.releaseDate)},${y(row[metric])}`).join(" ")}
              aria-hidden="true"
            />
            {rows.map((row, index) => {
              const px = x(row.releaseDate);
              const py = y(row[metric]);
              const selected = active.canonicalModelId === row.canonicalModelId;
              return (
                <g key={row.canonicalModelId} className={selected ? "mask-point-group is-active" : "mask-point-group"}>
                  <circle
                    className="mask-point"
                    cx={px}
                    cy={py}
                    r={selected ? 7.5 : 6}
                    tabIndex={0}
                    role="button"
                    aria-pressed={selected}
                    aria-label={`${row.model}, ${metricCopy[metric].label}, ${row[metric]} percent`}
                    onMouseEnter={() => setActiveId(row.canonicalModelId)}
                    onFocus={() => setActiveId(row.canonicalModelId)}
                    onClick={() => setActiveId(row.canonicalModelId)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        setActiveId(row.canonicalModelId);
                      }
                    }}
                  />
                  <text className="mask-point-label" x={px} y={py + (index % 2 === 0 ? -14 : 22)} aria-hidden="true">
                    {row.model.replace(" Instruct", "").replace(" Chat", "")}
                  </text>
                  <text className="agentic-date-label" x={px} y={HEIGHT - MARGIN.bottom + 28} aria-hidden="true">
                    {row.releaseDate.slice(0, 7)}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
        <div className="mask-detail" aria-live="polite">
          <div><strong>{active.model}</strong><span>{active.canonicalModelId}</span></div>
          <dl>
            <div><dt>P(Lie)</dt><dd>{active.liePct}%</dd></div>
            <div><dt>P(Honest)</dt><dd>{active.honestPct}%</dd></div>
            <div><dt>Accuracy</dt><dd>{active.accuracyPct}%</dd></div>
            <div><dt>Items</dt><dd>{active.n.toLocaleString("en-GB")}</dd></div>
          </dl>
        </div>
        <p className="chart-caption">
          Author-reported values from Ren et al., Appendix A.10, Table 3. The paper uses 1,500
          examples; the public dataset contains only 1,000, so future public-set reruns require a
          separate protocol label. P(Honest) and P(Lie) need not sum to 100% because evasion and
          unstable elicited beliefs are separate outcomes. No confidence intervals were reported.
        </p>
        <details className="data-table-details">
          <summary>View accessible MASK data table ({rows.length} models)</summary>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Release</th>
                  <th scope="col">Model</th>
                  <th scope="col">P(Lie)</th>
                  <th scope="col">P(Honest)</th>
                  <th scope="col">Accuracy</th>
                  <th scope="col">Items</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.canonicalModelId}>
                    <td>{row.releaseDate}</td>
                    <th scope="row">{row.model}</th>
                    <td>{row.liePct}%</td>
                    <td>{row.honestPct}%</td>
                    <td>{row.accuracyPct}%</td>
                    <td>{row.n.toLocaleString("en-GB")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </div>
    </div>
  );
}
