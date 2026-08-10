import { useMemo, useState } from "react";

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
}

interface SeriesOption {
  key: string;
  benchmarkId: string;
  metricKey: string;
  label: string;
}

type AccessFilter = "all" | FrontierAccessType;

const WIDTH = 1200;
const HEIGHT = 620;
const MARGIN = { top: 42, right: 42, left: 70 };
const SCORE_BOTTOM = 420;
const RELEASE_RAIL_Y = 480;
const START_TIME = new Date("2024-01-01T00:00:00Z").getTime();
const END_TIME = new Date("2026-12-31T00:00:00Z").getTime();

const seriesKey = (observation: FrontierTimelineObservation) =>
  `${observation.benchmarkId}::${observation.metricKey}`;

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

const humanise = (value: string) =>
  value.replaceAll("_", " ").replaceAll("-", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

const shortLabel = (value: string, max = 26) =>
  value.length <= max ? value : `${value.slice(0, max - 1)}…`;

const isInfoOpsCompliance = (option: SeriesOption) =>
  /info\s*ops|infoops/i.test(option.benchmarkId) &&
  /compl|compliance/i.test(`${option.metricKey} ${option.label}`);

const activateWithKeyboard = (event: React.KeyboardEvent<SVGElement>, activate: () => void) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    activate();
  }
};

export function FrontierTimeline({ models, observations }: FrontierTimelineProps) {
  const [selectedSeries, setSelectedSeries] = useState("");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [accessFilter, setAccessFilter] = useState<AccessFilter>("all");
  const [selectedObservationId, setSelectedObservationId] = useState<string | null>(null);
  const [selectedModelId, setSelectedModelId] = useState<string | null>(null);

  const modelMap = useMemo(() => new Map(models.map((model) => [model.id, model])), [models]);

  const seriesOptions = useMemo(() => {
    const options = new Map<string, SeriesOption>();
    for (const observation of observations) {
      const key = seriesKey(observation);
      if (!options.has(key)) {
        options.set(key, {
          key,
          benchmarkId: observation.benchmarkId,
          metricKey: observation.metricKey,
          label: observation.metricLabel,
        });
      }
    }
    return [...options.values()].sort((a, b) => {
      if (isInfoOpsCompliance(a) !== isInfoOpsCompliance(b)) return isInfoOpsCompliance(a) ? -1 : 1;
      return `${a.benchmarkId} ${a.label}`.localeCompare(`${b.benchmarkId} ${b.label}`);
    });
  }, [observations]);

  const defaultSeries = seriesOptions.find(isInfoOpsCompliance)?.key ?? seriesOptions[0]?.key ?? "";
  const effectiveSeries = seriesOptions.some((option) => option.key === selectedSeries)
    ? selectedSeries
    : defaultSeries;
  const selectedSeriesOption = seriesOptions.find((option) => option.key === effectiveSeries) ?? null;

  const sourceOptions = useMemo(
    () =>
      [...new Set(observations.filter((row) => seriesKey(row) === effectiveSeries).map((row) => row.sourceType))]
        .filter(Boolean)
        .sort(),
    [effectiveSeries, observations],
  );
  const effectiveSource = sourceFilter === "all" || sourceOptions.includes(sourceFilter)
    ? sourceFilter
    : "all";

  const visibleModels = useMemo(
    () =>
      models
        .filter((model) => {
          const released = dateTime(model.releaseDate);
          return released >= START_TIME && released <= END_TIME;
        })
        .filter((model) => accessFilter === "all" || model.accessType === accessFilter)
        .sort((a, b) => a.releaseDate.localeCompare(b.releaseDate)),
    [accessFilter, models],
  );
  const visibleModelIds = useMemo(
    () => new Set(visibleModels.map((model) => model.id)),
    [visibleModels],
  );

  const visibleObservations = useMemo(
    () =>
      observations
        .filter((row) => seriesKey(row) === effectiveSeries)
        .filter((row) => effectiveSource === "all" || row.sourceType === effectiveSource)
        .filter((row) => visibleModelIds.has(row.modelId))
        .filter((row) => Number.isFinite(row.scorePct))
        .sort((a, b) => {
          const first = modelMap.get(a.modelId)?.releaseDate ?? "";
          const second = modelMap.get(b.modelId)?.releaseDate ?? "";
          return first.localeCompare(second) || a.id.localeCompare(b.id);
        }),
    [effectiveSeries, effectiveSource, modelMap, observations, visibleModelIds],
  );

  const observationsByModel = useMemo(() => {
    const grouped = new Map<string, FrontierTimelineObservation[]>();
    for (const observation of visibleObservations) {
      const rows = grouped.get(observation.modelId) ?? [];
      rows.push(observation);
      grouped.set(observation.modelId, rows);
    }
    return grouped;
  }, [visibleObservations]);

  const comparableSeries = useMemo(() => {
    const grouped = new Map<string, FrontierTimelineObservation[]>();
    for (const observation of visibleObservations) {
      if (!observation.comparabilityGroup) continue;
      const rows = grouped.get(observation.comparabilityGroup) ?? [];
      rows.push(observation);
      grouped.set(observation.comparabilityGroup, rows);
    }
    return [...grouped.entries()].filter(([, rows]) => rows.length > 1);
  }, [visibleObservations]);

  const selectedModelIsVisible = selectedModelId !== null && visibleModelIds.has(selectedModelId);
  const activeObservation = selectedModelIsVisible
    ? visibleObservations.find((row) => row.id === selectedObservationId) ??
      observationsByModel.get(selectedModelId!)?.[0] ??
      null
    : visibleObservations.find((row) => row.id === selectedObservationId) ?? visibleObservations[0] ?? null;
  const activeModel = activeObservation
    ? modelMap.get(activeObservation.modelId) ?? null
    : visibleModels.find((model) => model.id === selectedModelId) ?? visibleModels[0] ?? null;

  const x = (releaseDate: string) =>
    MARGIN.left +
    ((dateTime(releaseDate) - START_TIME) / (END_TIME - START_TIME)) *
      (WIDTH - MARGIN.left - MARGIN.right);
  const y = (score: number) =>
    MARGIN.top + ((100 - Math.max(0, Math.min(100, score))) / 100) * (SCORE_BOTTOM - MARGIN.top);

  const chooseObservation = (observation: FrontierTimelineObservation) => {
    setSelectedObservationId(observation.id);
    setSelectedModelId(observation.modelId);
  };
  const chooseModel = (model: FrontierTimelineModel) => {
    setSelectedModelId(model.id);
    setSelectedObservationId(observationsByModel.get(model.id)?.[0]?.id ?? null);
  };

  const tableRows = visibleModels.flatMap<{
    model: FrontierTimelineModel;
    observation: FrontierTimelineObservation | null;
  }>((model) => {
    const rows = observationsByModel.get(model.id) ?? [];
    return rows.length > 0
      ? rows.map((observation) => ({ model, observation }))
      : [{ model, observation: null }];
  });

  return (
    <div className="chart-shell frontier-timeline-shell">
      <div className="chart-intro-row">
        <p className="chart-measure">
          <strong>{selectedSeriesOption?.label ?? "Frontier benchmark coverage"}</strong>
          <span>
            {selectedSeriesOption
              ? `${selectedSeriesOption.benchmarkId} · native metric, not a cross-benchmark score`
              : "No numeric observation is currently available; release coverage remains visible."}
          </span>
        </p>
        <p className="chart-legend" aria-label="Chart legend">
          <span><i className="legend-dot open" aria-hidden="true" /> Open-weight shape</span>
          <span><i className="legend-dot hosted" aria-hidden="true" /> Hosted API shape</span>
          <span><i className="legend-source published" aria-hidden="true" /> Published result</span>
          <span><i className="legend-source project" aria-hidden="true" /> ATB result</span>
          <span><i className="legend-dot frontier-missing-legend" aria-hidden="true" /> Not tested</span>
          <span><i className="legend-line" aria-hidden="true" /> Exact comparable protocol</span>
        </p>
      </div>

      <div className="chart-controls frontier-chart-controls" role="group" aria-label="Frontier timeline filters">
        <label>
          Benchmark measure
          <select value={effectiveSeries} onChange={(event) => setSelectedSeries(event.target.value)}>
            {seriesOptions.length === 0 ? <option value="">No results loaded</option> : null}
            {seriesOptions.map((option) => (
              <option key={option.key} value={option.key}>
                {option.benchmarkId} · {option.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Source
          <select value={effectiveSource} onChange={(event) => setSourceFilter(event.target.value)}>
            <option value="all">All result sources</option>
            {sourceOptions.map((source) => (
              <option key={source} value={source}>{humanise(source)}</option>
            ))}
          </select>
        </label>
        <label>
          Access
          <select value={accessFilter} onChange={(event) => setAccessFilter(event.target.value as AccessFilter)}>
            <option value="all">All frontier releases</option>
            <option value="open-weight">Open-weight</option>
            <option value="hosted">Hosted API</option>
          </select>
        </label>
      </div>

      <p className="chart-scroll-hint">Scroll the fixed 2024–2026 timeline horizontally on smaller screens.</p>

      <div className="chart-scroller frontier-chart-scroller">
        <svg
          className="longitudinal-chart frontier-timeline"
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          role="group"
          aria-labelledby="frontier-chart-title frontier-chart-description"
        >
          <title id="frontier-chart-title">Frontier AI benchmark observations by model release date, 2024 to 2026</title>
          <desc id="frontier-chart-description">
            The vertical scale shows the selected benchmark&apos;s native percentage. The release rail
            shows every eligible model in the selected access class. Hollow rail markers mean that no
            comparable result exists in the current view; they do not represent zero.
          </desc>

          {[0, 25, 50, 75, 100].map((tick) => (
            <g key={tick} aria-hidden="true">
              <line className="grid-line" x1={MARGIN.left} x2={WIDTH - MARGIN.right} y1={y(tick)} y2={y(tick)} />
              <text className="axis-label y-label" x={MARGIN.left - 14} y={y(tick) + 4}>{tick}%</text>
            </g>
          ))}

          {[2024, 2025, 2026].map((year) => {
            const position = x(`${year}-01-01`);
            return (
              <g key={year} aria-hidden="true">
                <line className="year-line" x1={position} x2={position} y1={MARGIN.top} y2={RELEASE_RAIL_Y + 10} />
                <text className="axis-label frontier-year-label" x={position} y={HEIGHT - 18}>{year}</text>
              </g>
            );
          })}

          {comparableSeries.map(([group, rows]) => (
            <polyline
              key={group}
              className="family-path frontier-comparable-path"
              points={rows
                .map((row) => {
                  const model = modelMap.get(row.modelId);
                  return model ? `${x(model.releaseDate)},${y(row.scorePct)}` : "";
                })
                .filter(Boolean)
                .join(" ")}
              aria-hidden="true"
            />
          ))}

          {visibleObservations.map((observation) => {
            const model = modelMap.get(observation.modelId);
            if (!model) return null;
            const px = x(model.releaseDate);
            const py = y(observation.scorePct);
            const selected = activeObservation?.id === observation.id;
            const hasInterval = observation.lowerPct !== null && observation.upperPct !== null;
            const activate = () => chooseObservation(observation);
            const ariaLabel = `${model.model}, ${observation.metricLabel}, ${observation.scorePct.toFixed(1)} percent, evaluated ${formatDate(observation.evaluationDate)}`;
            const atbGenerated = /atb|rerun|project/i.test(observation.sourceType);
            return (
              <g
                className={`frontier-observation-group ${selected ? "is-active" : ""}`}
                key={observation.id}
              >
                {hasInterval ? (
                  <g className="frontier-interval" aria-hidden="true">
                    <line x1={px} x2={px} y1={y(observation.upperPct!)} y2={y(observation.lowerPct!)} />
                    <line x1={px - 5} x2={px + 5} y1={y(observation.upperPct!)} y2={y(observation.upperPct!)} />
                    <line x1={px - 5} x2={px + 5} y1={y(observation.lowerPct!)} y2={y(observation.lowerPct!)} />
                  </g>
                ) : null}
                {model.accessType === "hosted" ? (
                  <rect
                    className={`frontier-observation-point ${atbGenerated ? "source-atb" : "source-published"}`}
                    x={px - (selected ? 7 : 5.5)}
                    y={py - (selected ? 7 : 5.5)}
                    width={selected ? 14 : 11}
                    height={selected ? 14 : 11}
                    transform={`rotate(45 ${px} ${py})`}
                    tabIndex={0}
                    role="button"
                    aria-pressed={selected}
                    aria-label={ariaLabel}
                    onMouseEnter={activate}
                    onFocus={activate}
                    onClick={activate}
                    onKeyDown={(event) => activateWithKeyboard(event, activate)}
                  />
                ) : (
                  <circle
                    className={`frontier-observation-point ${atbGenerated ? "source-atb" : "source-published"}`}
                    cx={px}
                    cy={py}
                    r={selected ? 7 : 5.5}
                    tabIndex={0}
                    role="button"
                    aria-pressed={selected}
                    aria-label={ariaLabel}
                    onMouseEnter={activate}
                    onFocus={activate}
                    onClick={activate}
                    onKeyDown={(event) => activateWithKeyboard(event, activate)}
                  />
                )}
                {selected ? (
                  <text className="point-label frontier-selected-label" x={px} y={py - 17} aria-hidden="true">
                    {shortLabel(model.model)} · {observation.scorePct.toFixed(1)}%
                  </text>
                ) : null}
              </g>
            );
          })}

          <line
            className="frontier-release-rail"
            x1={MARGIN.left}
            x2={WIDTH - MARGIN.right}
            y1={RELEASE_RAIL_Y}
            y2={RELEASE_RAIL_Y}
            aria-hidden="true"
          />
          <text className="frontier-rail-title" x={MARGIN.left} y={RELEASE_RAIL_Y - 18} aria-hidden="true">
            Frontier releases · hollow marker = no comparable result in this view
          </text>

          {visibleModels.map((model, index) => {
            const px = x(model.releaseDate);
            const sameDayModels = visibleModels.filter((candidate) => candidate.releaseDate === model.releaseDate);
            const sameDayIndex = sameDayModels.findIndex((candidate) => candidate.id === model.id);
            const railY = RELEASE_RAIL_Y + (sameDayIndex - (sameDayModels.length - 1) / 2) * 11;
            const hasResult = observationsByModel.has(model.id);
            const selected = activeModel?.id === model.id;
            const activate = () => chooseModel(model);
            return (
              <g
                className={`frontier-release-group ${hasResult ? "has-result" : "is-missing"} ${selected ? "is-active" : ""}`}
                key={model.id}
              >
                {model.accessType === "hosted" ? (
                  <rect
                    className="frontier-release-tick"
                    x={px - (selected ? 4.75 : 3.75)}
                    y={railY - (selected ? 4.75 : 3.75)}
                    width={selected ? 9.5 : 7.5}
                    height={selected ? 9.5 : 7.5}
                    transform={`rotate(45 ${px} ${railY})`}
                    tabIndex={0}
                    role="button"
                    aria-pressed={selected}
                    aria-label={`${model.model}, released ${formatDate(model.releaseDate)}, ${hasResult ? "result available" : "no comparable result in this view"}`}
                    onMouseEnter={activate}
                    onFocus={activate}
                    onClick={activate}
                    onKeyDown={(event) => activateWithKeyboard(event, activate)}
                  />
                ) : (
                  <circle
                    className="frontier-release-tick"
                    cx={px}
                    cy={railY}
                    r={selected ? 6.5 : 5}
                    tabIndex={0}
                    role="button"
                    aria-pressed={selected}
                    aria-label={`${model.model}, released ${formatDate(model.releaseDate)}, ${hasResult ? "result available" : "no comparable result in this view"}`}
                    onMouseEnter={activate}
                    onFocus={activate}
                    onClick={activate}
                    onKeyDown={(event) => activateWithKeyboard(event, activate)}
                  />
                )}
                {selected ? (
                  <text
                    className="frontier-release-label"
                    x={px}
                    y={railY + 24 + (index % 2) * 16}
                    aria-hidden="true"
                  >
                    {shortLabel(model.model, 22)}
                  </text>
                ) : null}
              </g>
            );
          })}

          <text
            className="axis-title"
            transform={`translate(18 ${(MARGIN.top + SCORE_BOTTOM) / 2}) rotate(-90)`}
            aria-hidden="true"
          >
            Selected benchmark metric
          </text>
        </svg>
      </div>

      {activeModel ? (
        <div className="chart-detail frontier-chart-detail" aria-live="polite">
          <div>
            <span className="detail-kicker">Selected release</span>
            <strong>{activeModel.model}</strong>
            <span>{activeModel.organisation} · {activeModel.openRouterId || "No OpenRouter route recorded"}</span>
          </div>
          {activeObservation ? (
            <>
              <dl>
                <div><dt>Score</dt><dd>{activeObservation.scorePct.toFixed(1)}%</dd></div>
                <div><dt>Interval</dt><dd>{activeObservation.lowerPct !== null && activeObservation.upperPct !== null ? `${activeObservation.lowerPct.toFixed(1)}–${activeObservation.upperPct.toFixed(1)}%` : "Not reported"}</dd></div>
                <div><dt>Items</dt><dd>{activeObservation.n.toLocaleString("en-GB")}</dd></div>
                <div><dt>Released</dt><dd>{formatDate(activeModel.releaseDate)}</dd></div>
                <div><dt>Evaluated</dt><dd>{formatDate(activeObservation.evaluationDate)}</dd></div>
              </dl>
              <p className="frontier-detail-note">
                {activeObservation.note || "No additional interpretation is recorded."}{" "}
                <a href={activeObservation.sourceUrl} target="_blank" rel="noreferrer">Primary source ↗</a>
                {activeObservation.artifactUrl ? <> · <a href={activeObservation.artifactUrl} target="_blank" rel="noreferrer">Run artifact ↗</a></> : null}
              </p>
            </>
          ) : (
            <div className="frontier-missing-detail">
              <p className="mini-label">Missing observation</p>
              <p>No comparable result exists for this release under the current metric and source filters. This is missing data, not a score of zero.</p>
            </div>
          )}
        </div>
      ) : null}

      <p className="chart-caption">
        The horizontal domain is fixed at 1 January 2024–31 December 2026. Dates order model
        releases retrospectively; they do not estimate a causal rate of progress. Lines connect only
        observations carrying the exact same non-empty comparability-group identifier. Published and
        project-generated results remain distinct measurement conditions.
      </p>

      <details className="data-table-details">
        <summary>View accessible frontier table ({visibleModels.length} releases; {visibleObservations.length} results)</summary>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Release</th>
                <th scope="col">Model</th>
                <th scope="col">Access</th>
                <th scope="col">Parameters</th>
                <th scope="col">Benchmark / metric</th>
                <th scope="col">Result</th>
                <th scope="col">Evaluation / source</th>
              </tr>
            </thead>
            <tbody>
              {tableRows.map(({ model, observation }) => (
                <tr key={`${model.id}-${observation?.id ?? "missing"}`}>
                  <td>{model.releaseDate}</td>
                  <th scope="row"><a href={model.sourceUrl} target="_blank" rel="noreferrer">{model.model}</a></th>
                  <td>{model.accessType}</td>
                  <td>{formatParams(model.totalParamsB)}</td>
                  <td>{observation ? `${observation.benchmarkId} · ${observation.metricLabel}` : "No comparable result"}</td>
                  <td>{observation ? `${observation.scorePct.toFixed(1)}% (n=${observation.n.toLocaleString("en-GB")})` : "—"}</td>
                  <td>
                    {observation ? (
                      <a href={observation.sourceUrl} target="_blank" rel="noreferrer">
                        {observation.evaluationDate} · {humanise(observation.sourceType)}
                      </a>
                    ) : "Missing—not zero"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
