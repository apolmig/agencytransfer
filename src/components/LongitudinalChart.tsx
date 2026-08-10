import { useMemo, useState } from "react";
import type {
  AccessType,
  DisElectResult,
  HarmfulSubset,
  MetricKey,
} from "../types";

type AccessFilter = "all" | AccessType;

const WIDTH = 1160;
const HEIGHT = 540;
const MARGIN = { top: 34, right: 40, bottom: 58, left: 66 };

const metricCopy: Record<MetricKey, { label: string; description: string }> = {
  complyPct: {
    label: "Harmful task compliance",
    description: "Share labelled Comply by the upstream judge.",
  },
  refusePct: {
    label: "Explicit refusal",
    description: "Share labelled Refuse; soft refusals remain separate.",
  },
  benignCompletionPct: {
    label: "Benign completion",
    description: "Share of the 50 benign election prompts labelled Comply.",
  },
};

const subsetCopy: Record<HarmfulSubset, string> = {
  "all-harmful": "All harmful tasks",
  "voter-targeting": "Voter-targeting tasks",
  "mp-targeting": "MP-targeting tasks",
};

const formatDate = (iso: string) =>
  new Intl.DateTimeFormat("en-GB", { month: "short", year: "numeric" }).format(
    new Date(`${iso}T00:00:00Z`),
  );

const formatParams = (value: number | null) =>
  value === null ? "Not reported" : `${value.toLocaleString("en-GB")}B`;

const csvEscape = (value: string | number | null) => {
  const text = value === null ? "" : String(value);
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
};

interface Props {
  results: DisElectResult[];
}

export function LongitudinalChart({ results }: Props) {
  const [metric, setMetric] = useState<MetricKey>("complyPct");
  const [subset, setSubset] = useState<HarmfulSubset>("all-harmful");
  const [access, setAccess] = useState<AccessFilter>("all");
  const [activeModel, setActiveModel] = useState<string | null>(null);

  const rows = useMemo(() => {
    const effectiveSubset = metric === "benignCompletionPct" ? "benign" : subset;
    return results
      .filter((row) => row.subset === effectiveSubset)
      .filter((row) => access === "all" || row.accessType === access)
      .sort((a, b) => a.releaseDate.localeCompare(b.releaseDate));
  }, [access, metric, results, subset]);

  const timeRange = useMemo(() => {
    const dates = rows.map((row) => new Date(`${row.releaseDate}T00:00:00Z`).getTime());
    if (dates.length === 0) {
      return [
        new Date("2019-01-01T00:00:00Z").getTime(),
        new Date("2024-12-31T00:00:00Z").getTime(),
      ] as const;
    }
    const min = Math.min(...dates);
    const max = Math.max(...dates);
    const pad = Math.max((max - min) * 0.04, 1000 * 60 * 60 * 24 * 45);
    return [min - pad, max + pad] as const;
  }, [rows]);

  const x = (date: string) => {
    const value = new Date(`${date}T00:00:00Z`).getTime();
    return (
      MARGIN.left +
      ((value - timeRange[0]) / (timeRange[1] - timeRange[0])) *
        (WIDTH - MARGIN.left - MARGIN.right)
    );
  };
  const y = (value: number) =>
    MARGIN.top + ((100 - value) / 100) * (HEIGHT - MARGIN.top - MARGIN.bottom);
  const valueFor = (row: DisElectResult) =>
    metric === "benignCompletionPct" ? row.complyPct : row[metric];

  const familySeries = useMemo(() => {
    const grouped = new Map<string, DisElectResult[]>();
    for (const row of rows) {
      const familyRows = grouped.get(row.family) ?? [];
      familyRows.push(row);
      grouped.set(row.family, familyRows);
    }
    return [...grouped.entries()].filter(([, familyRows]) => familyRows.length > 1);
  }, [rows]);

  const active = rows.find((row) => row.model === activeModel) ?? rows.at(0) ?? null;

  const downloadCurrentView = () => {
    const headers = [
      "model",
      "canonical_model_id",
      "family",
      "access_type",
      "release_date",
      "subset",
      "metric",
      "score_pct",
      "n",
      "source_type",
      "source_url",
      "source_commit",
    ];
    const body = rows.map((row) =>
      [
        row.model,
        row.canonicalModelId,
        row.family,
        row.accessType,
        row.releaseDate,
        row.subset,
        metric,
        valueFor(row),
        row.n,
        row.sourceType,
        row.sourceUrl,
        row.sourceCommit,
      ]
        .map(csvEscape)
        .join(","),
    );
    const blob = new Blob([[headers.join(","), ...body].join("\n")], {
      type: "text/csv;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `agency-transfer-diselect-${metric}-${access}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const years = Array.from(
    { length: new Date(timeRange[1]).getUTCFullYear() - new Date(timeRange[0]).getUTCFullYear() + 1 },
    (_, index) => new Date(timeRange[0]).getUTCFullYear() + index,
  );

  return (
    <div className="chart-shell">
      <div className="chart-intro-row">
        <p className="chart-measure">
          <strong>{metricCopy[metric].label}</strong>
          <span>{metricCopy[metric].description}</span>
        </p>
        <p className="chart-legend" aria-label="Legend">
          <span><i className="legend-dot open" aria-hidden="true" /> Open-weight</span>
          <span><i className="legend-dot hosted" aria-hidden="true" /> Hosted API</span>
          <span><i className="legend-line" aria-hidden="true" /> Same model family</span>
        </p>
      </div>

      <p className="chart-scroll-hint">Scroll the timeline horizontally on smaller screens.</p>

      <div className="chart-scroller">
        <svg
          className="longitudinal-chart"
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          role="img"
          aria-labelledby="diselect-chart-title diselect-chart-description"
        >
          <title id="diselect-chart-title">
            DisElect {metricCopy[metric].label.toLowerCase()} by original model release date
          </title>
          <desc id="diselect-chart-description">
            Thirteen published model results from 2019 to 2024. Lines connect only releases in
            the same model family. The series measures benchmark response labels, not human
            manipulation or electoral outcomes.
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

          {years.map((year) => {
            const date = `${year}-01-01`;
            const position = x(date);
            if (position < MARGIN.left || position > WIDTH - MARGIN.right) return null;
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

          {familySeries.map(([family, familyRows]) => (
            <polyline
              key={family}
              className="family-path"
              points={familyRows.map((row) => `${x(row.releaseDate)},${y(valueFor(row))}`).join(" ")}
              aria-hidden="true"
            />
          ))}

          {rows.map((row, index) => {
            const px = x(row.releaseDate);
            const py = y(valueFor(row));
            const isActive = active?.model === row.model;
            const labelAbove = index % 2 === 0;
            const accessibleLabel = `${row.model}, ${formatDate(row.releaseDate)}, ${valueFor(row).toFixed(1)} percent`;
            return (
              <g className={isActive ? "point-group is-active" : "point-group"} key={row.model}>
                {row.accessType === "hosted" ? (
                  <path
                    className="data-point hosted-point"
                    d={`M ${px} ${py - 7} L ${px + 7} ${py} L ${px} ${py + 7} L ${px - 7} ${py} Z`}
                    tabIndex={0}
                    role="button"
                    aria-pressed={isActive}
                    aria-label={accessibleLabel}
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
                  <circle
                    className="data-point open-point"
                    cx={px}
                    cy={py}
                    r={6.5}
                    tabIndex={0}
                    role="button"
                    aria-pressed={isActive}
                    aria-label={accessibleLabel}
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
                )}
                <text
                  className="point-label"
                  x={px}
                  y={py + (labelAbove ? -14 : 22)}
                  aria-hidden="true"
                >
                  {row.model}
                </text>
              </g>
            );
          })}

          <text
            className="axis-title"
            transform={`translate(18 ${HEIGHT / 2}) rotate(-90)`}
            aria-hidden="true"
          >
            Share of responses
          </text>
          <text
            className="axis-title"
            x={(MARGIN.left + WIDTH - MARGIN.right) / 2}
            y={HEIGHT - 10}
            aria-hidden="true"
          >
            Original model announcement date used by the source paper
          </text>
        </svg>
      </div>

      <div className="chart-controls" role="group" aria-label="Chart controls">
        <fieldset>
          <legend>Measure</legend>
          <div className="segmented-control">
            {(Object.keys(metricCopy) as MetricKey[]).map((key) => (
              <button
                className={metric === key ? "is-active" : ""}
                key={key}
                type="button"
                aria-pressed={metric === key}
                onClick={() => setMetric(key)}
              >
                {metricCopy[key].label}
              </button>
            ))}
          </div>
        </fieldset>
        <label>
          Task set
          <select
            value={subset}
            disabled={metric === "benignCompletionPct"}
            onChange={(event) => setSubset(event.target.value as HarmfulSubset)}
          >
            {(Object.keys(subsetCopy) as HarmfulSubset[]).map((key) => (
              <option key={key} value={key}>
                {subsetCopy[key]}
              </option>
            ))}
          </select>
        </label>
        <label>
          Access
          <select
            value={access}
            onChange={(event) => setAccess(event.target.value as AccessFilter)}
          >
            <option value="all">All models</option>
            <option value="open-weight">Open-weight</option>
            <option value="hosted">Hosted API</option>
          </select>
        </label>
        <button className="text-button" type="button" onClick={downloadCurrentView}>
          Download current CSV
        </button>
      </div>

      {active && (
        <div className="chart-detail" aria-live="polite">
          <div>
            <span className="detail-kicker">Selected release</span>
            <strong>{active.model}</strong>
            <span>{active.canonicalModelId}</span>
          </div>
          <dl>
            <div><dt>Score</dt><dd>{valueFor(active).toFixed(1)}%</dd></div>
            <div><dt>Release</dt><dd>{formatDate(active.releaseDate)}</dd></div>
            <div><dt>Prompts</dt><dd>{active.n.toLocaleString("en-GB")}</dd></div>
            <div><dt>Parameters</dt><dd>{formatParams(active.totalParamsB)}</dd></div>
            <div><dt>Access</dt><dd>{active.accessType}</dd></div>
          </dl>
        </div>
      )}

      <p className="chart-caption">
        Recomputed from aggregate labels released by Williams et al. at upstream commit <code>915a8f8</code>.
        Each harmful point uses 2,200 prompts; benign points use 50. The original GPT‑3.5 Turbo judge
        reported Macro‑F1 0.76 on a 100-response human check. Dates describe original model announcements,
        not necessarily the exact checkpoint date. Lines connect only same-family releases and are descriptive.
      </p>

      <details className="data-table-details">
        <summary>View accessible data table ({rows.length} models)</summary>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Model</th>
                <th scope="col">Release</th>
                <th scope="col">Access</th>
                <th scope="col">Score</th>
                <th scope="col">N</th>
                <th scope="col">Parameters</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.model}>
                  <th scope="row">{row.model}</th>
                  <td>{row.releaseDate}</td>
                  <td>{row.accessType}</td>
                  <td>{valueFor(row).toFixed(1)}%</td>
                  <td>{row.n.toLocaleString("en-GB")}</td>
                  <td>{formatParams(row.totalParamsB)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
