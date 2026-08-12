import { useMemo, useState } from "react";
import type { HmcEstimate, HmcFrontierPoint } from "../types";

export type FrontierAccessType = "open-weight" | "hosted";

export interface FrontierTimelineModel {
  id: string;
  model: string;
  organisation: string;
  family: string;
  accessType: FrontierAccessType;
  releaseDate: string;
  totalParamsB: number | null;
  openRouterId: string;
  eligibilityBasis: string;
  sourceUrl: string;
}

export interface FrontierTimelineObservation {
  id: string;
  benchmarkId: string;
  protocolId: string;
  modelId: string;
  metricKey: string;
  metricLabel: string;
  scorePct: number;
  n: number;
  evaluationDate: string;
  sourceType: string;
  sourceUrl: string;
  sourceLocator: string;
  comparabilityGroup: string;
  lowerPct: number | null;
  upperPct: number | null;
  artifactUrl: string | null;
  note: string;
}

interface FrontierTimelineProps {
  models: FrontierTimelineModel[];
  observations: FrontierTimelineObservation[];
  estimates: HmcEstimate[];
  frontier: HmcFrontierPoint[];
}

type AccessFilter = "all" | FrontierAccessType;
type MeasureKey = "estimate" | "infoops" | "diselect" | "ape" | "mask" | "agentic";

interface ChartPoint {
  id: string;
  modelId: string;
  scorePct: number;
  lowerPct: number | null;
  upperPct: number | null;
  lower95Pct: number | null;
  upper95Pct: number | null;
  metricLabel: string;
  evaluationDate: string;
  n: number | null;
  sourceUrl: string;
  note: string;
  comparabilityGroup: string;
  evidenceGrade: string | null;
  observedWeight: number | null;
  weightSensitive: boolean;
}

const MEASURES: Array<{ key: MeasureKey; label: string; axis: string; context: string }> = [
  {
    key: "estimate",
    label: "Exploratory weighted synthesis",
    axis: "Exploratory weighted index",
    context: "Index points · assumption band",
  },
  {
    key: "infoops",
    label: "Operational influence · InfoOpsBench",
    axis: "Compliance",
    context: "Models by release date · evaluated 26 Jul 2026",
  },
  {
    key: "diselect",
    label: "Election operations · DisElect",
    axis: "Harmful compliance",
    context: "Published aggregate labels · one protocol",
  },
  {
    key: "ape",
    label: "Persuasion attempts · APE",
    axis: "Attempt rate",
    context: "Three author-reported harmful strata",
  },
  {
    key: "mask",
    label: "Deception under pressure · MASK",
    axis: "Lie rate",
    context: "Author-reported benchmark outcomes",
  },
  {
    key: "agentic",
    label: "Campaign execution · Anthropic",
    axis: "Task completion",
    context: "Helpful-only variants · simulated workflows",
  },
];

const WIDTH = 1200;
const HEIGHT = 410;
const MARGIN = { top: 26, right: 66, left: 58 };
const PLOT_BOTTOM = 310;
const RUG_Y = 342;

const dateTime = (iso: string) => {
  const value = new Date(iso.includes("T") ? iso : `${iso}T00:00:00Z`).getTime();
  return Number.isFinite(value) ? value : Number.NaN;
};

const formatDate = (iso: string) => {
  const value = dateTime(iso);
  if (!Number.isFinite(value)) return "Date not reported";
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(value));
};

const formatParams = (value: number | null) =>
  value === null ? "Not disclosed" : `${value.toLocaleString("en-GB")}B`;

const shortLabel = (value: string, max = 24) =>
  value.length <= max ? value : `${value.slice(0, max - 1)}…`;

const measureMatches = (measure: MeasureKey, observation: FrontierTimelineObservation) => {
  if (measure === "infoops") {
    return observation.benchmarkId === "infoopsbench" && observation.metricKey === "compliance_pct";
  }
  if (measure === "diselect") return observation.benchmarkId === "diselect";
  if (measure === "ape") return observation.benchmarkId === "ape-saferai";
  if (measure === "mask") {
    return ["mask-original", "mask-saferai"].includes(observation.benchmarkId) && observation.metricKey === "lie_pct";
  }
  if (measure === "agentic") return observation.benchmarkId === "anthropic-agentic-influence";
  return false;
};

const stepLinePath = (
  rows: HmcFrontierPoint[],
  x: (releaseDate: string) => number,
  y: (value: number) => number,
  key: "scorePct" | "lower80Pct" | "upper80Pct",
) => {
  if (rows.length === 0) return "";
  let path = `M ${x(rows[0].releaseDate)} ${y(rows[0][key])}`;
  for (let index = 1; index < rows.length; index += 1) {
    path += ` H ${x(rows[index].releaseDate)} V ${y(rows[index][key])}`;
  }
  return path;
};

const stepBandPath = (
  rows: HmcFrontierPoint[],
  x: (releaseDate: string) => number,
  y: (value: number) => number,
) => {
  if (rows.length === 0) return "";
  let path = `M ${x(rows[0].releaseDate)} ${y(rows[0].upper80Pct)}`;
  for (let index = 1; index < rows.length; index += 1) {
    path += ` H ${x(rows[index].releaseDate)} V ${y(rows[index].upper80Pct)}`;
  }
  const last = rows.at(-1)!;
  path += ` L ${x(last.releaseDate)} ${y(last.lower80Pct)}`;
  for (let index = rows.length - 2; index >= 0; index -= 1) {
    path += ` H ${x(rows[index].releaseDate)} V ${y(rows[index].lower80Pct)}`;
  }
  return `${path} Z`;
};

export function FrontierTimeline({ models, observations, estimates, frontier }: FrontierTimelineProps) {
  const [measure, setMeasure] = useState<MeasureKey>("infoops");
  const [accessFilter, setAccessFilter] = useState<AccessFilter>("all");
  const [selectedPointId, setSelectedPointId] = useState<string | null>(null);
  const [selectedModelId, setSelectedModelId] = useState<string | null>(null);

  const modelMap = useMemo(() => new Map(models.map((model) => [model.id, model])), [models]);
  const estimateMap = useMemo(() => new Map(estimates.map((estimate) => [estimate.modelId, estimate])), [estimates]);
  const selectedMeasure = MEASURES.find((option) => option.key === measure)!;

  const yearRange = useMemo(() => {
    const years = models.map((model) => Number(model.releaseDate.slice(0, 4))).filter(Number.isFinite);
    const start = Math.min(2022, ...years);
    const end = Math.max(2026, ...years);
    return { start, end, years: Array.from({ length: end - start + 1 }, (_, index) => start + index) };
  }, [models]);
  const startTime = dateTime(`${yearRange.start}-01-01`);
  const endTime = dateTime(`${yearRange.end}-12-31`);
  const x = (releaseDate: string) =>
    MARGIN.left +
    ((dateTime(releaseDate) - startTime) / (endTime - startTime)) *
      (WIDTH - MARGIN.left - MARGIN.right);
  const y = (score: number) =>
    MARGIN.top + ((100 - Math.max(0, Math.min(100, score))) / 100) * (PLOT_BOTTOM - MARGIN.top);

  const visibleModels = useMemo(
    () => models
      .filter((model) => accessFilter === "all" || model.accessType === accessFilter)
      .sort((first, second) => first.releaseDate.localeCompare(second.releaseDate) || first.id.localeCompare(second.id)),
    [accessFilter, models],
  );
  const visibleModelIds = useMemo(() => new Set(visibleModels.map((model) => model.id)), [visibleModels]);

  const points = useMemo<ChartPoint[]>(() => {
    if (measure === "estimate") {
      return estimates
        .filter((estimate) => visibleModelIds.has(estimate.modelId))
        .filter((estimate) => estimate.evidenceStatus === "estimated" && estimate.scorePct !== null)
        .map((estimate) => ({
          id: estimate.id,
          modelId: estimate.modelId,
          scorePct: estimate.scorePct!,
          lowerPct: estimate.lower80Pct,
          upperPct: estimate.upper80Pct,
          lower95Pct: estimate.lower95Pct,
          upper95Pct: estimate.upper95Pct,
          metricLabel: "HMC proxy estimate v0.1",
          evaluationDate: "2026-08-10",
          n: null,
          sourceUrl: estimate.methodUrl,
          note: estimate.note,
          comparabilityGroup: "hmc-proxy-v0.1",
          evidenceGrade: estimate.evidenceGrade,
          observedWeight: estimate.observedWeight,
          weightSensitive: estimate.weightSensitive,
        }))
        .sort((first, second) =>
          (modelMap.get(first.modelId)?.releaseDate ?? "").localeCompare(modelMap.get(second.modelId)?.releaseDate ?? ""),
        );
    }
    return observations
      .filter((observation) => visibleModelIds.has(observation.modelId))
      .filter((observation) => measureMatches(measure, observation))
      .map((observation) => ({
        id: observation.id,
        modelId: observation.modelId,
        scorePct: observation.scorePct,
        lowerPct: observation.lowerPct,
        upperPct: observation.upperPct,
        lower95Pct: null,
        upper95Pct: null,
        metricLabel: observation.metricLabel,
        evaluationDate: observation.evaluationDate,
        n: observation.n,
        sourceUrl: observation.sourceUrl,
        note: observation.note,
        comparabilityGroup: `${observation.comparabilityGroup}::${observation.metricKey}`,
        evidenceGrade: null,
        observedWeight: null,
        weightSensitive: false,
      }))
      .sort((first, second) =>
        (modelMap.get(first.modelId)?.releaseDate ?? "").localeCompare(modelMap.get(second.modelId)?.releaseDate ?? "") ||
        first.id.localeCompare(second.id),
      );
  }, [estimates, measure, modelMap, observations, visibleModelIds]);

  const pointMap = useMemo(() => new Map(points.map((point) => [point.id, point])), [points]);
  const activePoint = selectedPointId ? pointMap.get(selectedPointId) ?? null : null;
  const activeModel = activePoint
    ? modelMap.get(activePoint.modelId) ?? null
    : selectedModelId
      ? modelMap.get(selectedModelId) ?? null
      : null;
  const estimateForActiveModel = activeModel ? estimateMap.get(activeModel.id) ?? null : null;

  const frontierRows = useMemo(
    () => frontier
      .filter((row) => measure === "estimate" && row.accessFilter === accessFilter)
      .sort((first, second) => first.releaseDate.localeCompare(second.releaseDate)),
    [accessFilter, frontier, measure],
  );
  const latestFrontier = frontierRows.at(-1) ?? null;
  const resultModelIds = useMemo(() => new Set(points.map((point) => point.modelId)), [points]);

  const tableRows: Array<{ model: FrontierTimelineModel; point: ChartPoint | null }> = measure === "estimate"
    ? visibleModels.map((model) => ({ model, point: points.find((point) => point.modelId === model.id) ?? null }))
    : visibleModels.flatMap<{ model: FrontierTimelineModel; point: ChartPoint | null }>((model) => {
      const modelPoints = points.filter((point) => point.modelId === model.id);
      return modelPoints.length > 0
        ? modelPoints.map((point) => ({ model, point }))
        : [{ model, point: null }];
    });

  const choosePoint = (point: ChartPoint) => {
    setSelectedPointId(point.id);
    setSelectedModelId(point.modelId);
  };

  const chooseModel = (model: FrontierTimelineModel) => {
    setSelectedModelId(model.id);
    setSelectedPointId(points.find((point) => point.modelId === model.id)?.id ?? null);
  };

  return (
    <div className="chart-shell frontier-timeline-shell">
      <div className="frontier-toolbar" role="group" aria-label="Chart filters">
        <label>
          <span>Measure</span>
          <select
            value={measure}
            onChange={(event) => {
              setMeasure(event.target.value as MeasureKey);
              setSelectedPointId(null);
              setSelectedModelId(null);
            }}
          >
            {MEASURES.map((option) => <option key={option.key} value={option.key}>{option.label}</option>)}
          </select>
        </label>
        <label>
          <span>Models</span>
          <select
            value={accessFilter}
            onChange={(event) => {
              setAccessFilter(event.target.value as AccessFilter);
              setSelectedPointId(null);
              setSelectedModelId(null);
            }}
          >
            <option value="all">All frontier releases</option>
            <option value="open-weight">Open-weight ≥100B</option>
            <option value="hosted">Hosted frontier</option>
          </select>
        </label>
        <p><strong>{selectedMeasure.axis}</strong><span>{selectedMeasure.context}</span></p>
      </div>

      <p className="chart-scroll-hint">Scroll the 2022–2026 release axis horizontally.</p>

      <div className="chart-scroller frontier-chart-scroller">
        <svg
          className="longitudinal-chart frontier-timeline"
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          role="img"
          aria-labelledby="frontier-chart-title frontier-chart-description"
        >
          <title id="frontier-chart-title">{selectedMeasure.label}, frontier AI releases from 2022 to 2026</title>
          <desc id="frontier-chart-description">
            {measure === "estimate"
              ? "Index points use a zero to one hundred vertical scale. The exploratory view shows proxy medians, eighty percent assumption bands, and a running maximum defined by the proxy assumptions."
              : `The selected ${selectedMeasure.label} view shows benchmark-native percentages on a zero to one hundred vertical scale.`}
            {" "}Hollow release marks mean insufficient evidence in the current view, not a score of zero. An accessible table follows the chart.
          </desc>

          {[0, 25, 50, 75, 100].map((tick) => (
            <g key={tick} aria-hidden="true">
              <line className="grid-line" x1={MARGIN.left} x2={WIDTH - MARGIN.right} y1={y(tick)} y2={y(tick)} />
              <text className="axis-label y-label" x={MARGIN.left - 10} y={y(tick) + 4}>{tick}</text>
            </g>
          ))}

          {yearRange.years.map((year) => {
            const position = x(`${year}-01-01`);
            return (
              <g key={year} aria-hidden="true">
                <line className="year-line" x1={position} x2={position} y1={MARGIN.top} y2={RUG_Y + 9} />
                <text className="axis-label frontier-year-label" x={position} y={HEIGHT - 16}>{year}</text>
              </g>
            );
          })}

          {measure === "estimate" && frontierRows.length > 0 ? (
            <>
              <path className="frontier-estimate-band" d={stepBandPath(frontierRows, x, y)} aria-hidden="true" />
              <path className="frontier-estimate-line" d={stepLinePath(frontierRows, x, y, "scorePct")} aria-hidden="true" />
            </>
          ) : null}

          {points.map((point) => {
            const model = modelMap.get(point.modelId);
            if (!model) return null;
            const px = x(model.releaseDate);
            const py = y(point.scorePct);
            const selected = activePoint?.id === point.id;
            const hasInterval = point.lowerPct !== null && point.upperPct !== null;
            return (
              <g
                className={`frontier-observation-group ${measure === "estimate" ? "is-estimate" : "is-observed"} ${selected ? "is-active" : ""}`}
                key={point.id}
                tabIndex={0}
                role="button"
                aria-pressed={selected}
                aria-label={`${model.model}, ${point.metricLabel}, ${point.scorePct.toFixed(1)} ${measure === "estimate" ? "index points" : "percent"}`}
                onMouseEnter={() => choosePoint(point)}
                onFocus={() => choosePoint(point)}
                onClick={() => choosePoint(point)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    choosePoint(point);
                  }
                }}
              >
                {hasInterval ? (
                  <line className="frontier-point-interval" x1={px} x2={px} y1={y(point.upperPct!)} y2={y(point.lowerPct!)} />
                ) : null}
                <circle className="frontier-point-hit" cx={px} cy={py} r={14} />
                {model.accessType === "hosted" ? (
                  <rect
                    className="frontier-observation-point"
                    x={px - (selected ? 6 : 4.5)}
                    y={py - (selected ? 6 : 4.5)}
                    width={selected ? 12 : 9}
                    height={selected ? 12 : 9}
                    transform={`rotate(45 ${px} ${py})`}
                  />
                ) : (
                  <circle className="frontier-observation-point" cx={px} cy={py} r={selected ? 6 : 4.5} />
                )}
                {selected ? (
                  <text className="point-label frontier-selected-label" x={px} y={py - 15}>
                    {shortLabel(model.model)} · {point.scorePct.toFixed(1)}
                  </text>
                ) : null}
              </g>
            );
          })}

          {latestFrontier ? (
            <text
              className="frontier-line-label"
              x={x(latestFrontier.releaseDate) + 10}
              y={y(latestFrontier.scorePct) - 8}
              aria-hidden="true"
            >
              proxy running max {latestFrontier.scorePct.toFixed(0)}
            </text>
          ) : null}

          <line className="frontier-release-rail" x1={MARGIN.left} x2={WIDTH - MARGIN.right} y1={RUG_Y} y2={RUG_Y} aria-hidden="true" />
          {visibleModels.map((model, index) => {
            const px = x(model.releaseDate);
            const sameDay = visibleModels.filter((candidate) => candidate.releaseDate === model.releaseDate);
            const sameDayIndex = sameDay.findIndex((candidate) => candidate.id === model.id);
            const py = RUG_Y + (sameDayIndex - (sameDay.length - 1) / 2) * 8;
            const hasResult = resultModelIds.has(model.id);
            const selected = activeModel?.id === model.id;
            return (
              <g
                className={`frontier-release-group ${hasResult ? "has-result" : "is-missing"} ${selected ? "is-active" : ""}`}
                key={model.id}
                onMouseEnter={() => chooseModel(model)}
                onClick={() => chooseModel(model)}
                aria-hidden="true"
              >
                <circle className="frontier-rug-hit" cx={px} cy={py} r={9} />
                {model.accessType === "hosted" ? (
                  <rect className="frontier-release-tick" x={px - 2.5} y={py - 2.5} width={5} height={5} transform={`rotate(45 ${px} ${py})`} />
                ) : (
                  <circle className="frontier-release-tick" cx={px} cy={py} r={3.1} />
                )}
                {selected && !activePoint ? (
                  <text className="frontier-release-label" x={px} y={py + 17 + (index % 2) * 11}>{shortLabel(model.model, 20)}</text>
                ) : null}
              </g>
            );
          })}

          <text className="axis-title" transform={`translate(16 ${(MARGIN.top + PLOT_BOTTOM) / 2}) rotate(-90)`} aria-hidden="true">
            {selectedMeasure.axis} · 0–100
          </text>
        </svg>
      </div>

      <div className="frontier-chart-key" aria-label="Chart key">
        {measure === "estimate" ? <span><i className="key-estimate" aria-hidden="true" /> Proxy running max + assumption band</span> : null}
        <span><i className="legend-dot open" aria-hidden="true" /> Open-weight</span>
        <span><i className="legend-dot hosted" aria-hidden="true" /> Hosted</span>
        <span><i className="legend-dot frontier-missing-legend" aria-hidden="true" /> Insufficient evidence</span>
      </div>

      <div className="frontier-compact-detail" aria-live="polite">
        {activeModel && activePoint ? (
          <p>
            <strong>{activeModel.model}</strong>
            <span>{activePoint.metricLabel} · {activePoint.scorePct.toFixed(1)}{measure === "estimate" ? " index points" : "%"}</span>
            {activePoint.lowerPct !== null && activePoint.upperPct !== null ? <span>80% assumption band {activePoint.lowerPct.toFixed(1)}–{activePoint.upperPct.toFixed(1)} points</span> : null}
            {activePoint.lower95Pct !== null && activePoint.upper95Pct !== null ? <span>95% assumption band {activePoint.lower95Pct.toFixed(1)}–{activePoint.upper95Pct.toFixed(1)} points</span> : null}
            {activePoint.evidenceGrade ? <span>coverage tier {activePoint.evidenceGrade} · {Math.round((activePoint.observedWeight ?? 0) * 100)}% of component weight observed</span> : null}
            <a href={activePoint.sourceUrl} target="_blank" rel="noreferrer">Source ↗</a>
          </p>
        ) : activeModel ? (
          <p>
            <strong>{activeModel.model}</strong>
            <span>{estimateForActiveModel?.note ?? "No comparable result in this view."}</span>
            <a href={activeModel.sourceUrl} target="_blank" rel="noreferrer">Model source ↗</a>
          </p>
        ) : (
          <p><span>Hover or select a mark for result, interval, coverage, and source.</span></p>
        )}
      </div>

      <p className="frontier-caveat">
        {measure === "estimate"
          ? "Exploratory weighted proxy—not an observed percentage or validated capability scale. Points can use different source instruments; the running maximum is a property of v0.1 assumptions, not a capability frontier."
          : "Observed percentages retain each benchmark's own protocol and direction; they are not directly comparable across measures."}
        {" "}<a
          href={`https://github.com/apolmig/agencytransfer/blob/main/${measure === "estimate" ? "ESTIMATED_SCORE.md" : "METHODS.md"}`}
          target="_blank"
          rel="noreferrer"
        >Method ↗</a>
      </p>

      <details className="data-table-details frontier-data-details">
        <summary>Data and limitations ({visibleModels.length} releases; {points.length} plotted results)</summary>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Release</th>
                <th scope="col">Model</th>
                <th scope="col">Type</th>
                <th scope="col">Parameters</th>
                <th scope="col">Measure</th>
                <th scope="col">Result</th>
                <th scope="col">Evidence</th>
              </tr>
            </thead>
            <tbody>
              {tableRows.map(({ model, point }) => {
                const estimate = estimateMap.get(model.id);
                return (
                  <tr key={`${model.id}-${point?.id ?? "missing"}`}>
                    <td>{model.releaseDate}</td>
                    <th scope="row"><a href={model.sourceUrl} target="_blank" rel="noreferrer">{model.model}</a></th>
                    <td>{model.accessType}</td>
                    <td>{formatParams(model.totalParamsB)}</td>
                    <td>{point?.metricLabel ?? "No comparable result"}</td>
                    <td>{point ? `${point.scorePct.toFixed(1)}${measure === "estimate" ? " points" : "%"}` : "—"}</td>
                    <td>
                      {measure === "estimate"
                        ? estimate?.evidenceStatus === "estimated"
                          ? `Coverage tier ${estimate.evidenceGrade}; ${Math.round(estimate.observedWeight * 100)}% of component weight observed`
                          : "Insufficient evidence—not zero"
                        : point
                          ? `${formatDate(point.evaluationDate)} · n=${point.n?.toLocaleString("en-GB") ?? "—"}`
                          : "Missing—not zero"}
                    </td>
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
