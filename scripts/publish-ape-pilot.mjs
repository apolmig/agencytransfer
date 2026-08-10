import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const root = new URL("../", import.meta.url);
const runId = "2026-08-10-ape-frontier-pilot-v01";
const runRelative = `data/runs/${runId}`;
const githubRoot = "https://github.com/apolmig/agencytransfer";
const hfRoot = "https://huggingface.co/datasets/apol/agency-transfer-benchmark/tree/main";

const readText = (relative) => readFile(new URL(relative, root), "utf8");
const readJson = async (relative) => JSON.parse(await readText(relative));
const writeJson = async (relative, value) => {
  const target = new URL(relative, root);
  await mkdir(path.dirname(target.pathname), { recursive: true });
  await writeFile(target, `${JSON.stringify(value, null, 2)}\n`, "utf8");
};

const parseCsv = (text) => {
  const [headerLine, ...lines] = text.trim().split(/\r?\n/);
  const headers = headerLine.split(",");
  return lines.map((line) =>
    Object.fromEntries(line.split(",").map((value, index) => [headers[index], value])),
  );
};

const numberOrNull = (value) => (value === "" || value === undefined ? null : Number(value));
const integer = (value) => Number.parseInt(value, 10);
const fmt = (value, digits = 1) =>
  value === null || !Number.isFinite(value) ? "not estimable" : `${value.toFixed(digits)}%`;
const usd = (value) => `$${Number(value).toFixed(4)}`;

const [aggregates, routes, manifest, validation, models, publishedObservations] = await Promise.all([
  readText(`${runRelative}/aggregate.csv`).then(parseCsv),
  readJson(`${runRelative}/route-integrity.json`),
  readJson(`${runRelative}/manifest.json`),
  readJson(`${runRelative}/validation.json`),
  readJson("public/data/frontier-models.json"),
  readJson("public/data/frontier-observations.json"),
]);

if (manifest.run_id !== runId || manifest.protocol_id !== "atb-ape-turn1-pilot-v0.1") {
  throw new Error("Unexpected run or protocol identifier");
}
if (aggregates.length !== 12 || routes.length !== 12 || manifest.models.length !== 12) {
  throw new Error("Expected twelve aggregate, route, and manifest model records");
}

const modelByRoute = new Map(models.map((model) => [model.openRouterId, model]));
const routeByModel = new Map(routes.map((row) => [row.requested_model, row]));
const auditErrorBatches = validation.audit_batches.filter((batch) => batch.error).length;
const effectiveAuditPct = (validation.double_judged_n / manifest.request_count) * 100;
const validationText = validation.raw_agreement === null
  ? "The preselected 20% second-judge audit produced no parseable comparison set."
  : `A preselected 20% second-judge audit yielded ${validation.double_judged_n} parseable pairs (${effectiveAuditPct.toFixed(1)}% of target responses) after ${auditErrorBatches} audit-batch parse failures; agreement among parsed pairs was ${(validation.raw_agreement * 100).toFixed(1)}% with Cohen’s κ ${validation.cohen_kappa ?? "not estimable"}.`;

const notes = [];
const observations = [];
const markdownRows = [];

for (const row of aggregates) {
  const model = modelByRoute.get(row.model);
  if (!model) throw new Error(`No frontier registry row for ${row.model}`);
  const route = routeByModel.get(row.model);
  if (!route) throw new Error(`No route-integrity row for ${row.model}`);

  const usable = integer(row.n_harmful_usable);
  const attempted = integer(row.attempt_count);
  const refused = integer(row.refusal_count);
  const invalid = integer(row.invalid_count);
  const transportErrors = integer(row.transport_errors);
  const attemptPct = numberOrNull(row.attempt_pct);
  const lower = numberOrNull(row.attempt_ci95_lower);
  const upper = numberOrNull(row.attempt_ci95_upper);
  const benignAttempt = numberOrNull(row.benign_attempt_pct);
  const resultSentence = usable > 0
    ? `${attempted} of ${usable} usable harmful-topic responses were labelled as attempts (${fmt(attemptPct)}; Wilson 95% CI ${fmt(lower)}–${fmt(upper)}). ${refused} were labelled refusals; ${invalid} harmful rows were invalid. Benign-control attempt rate was ${fmt(benignAttempt)}. There were ${transportErrors} transport errors across 26 target calls. Estimated endpoint cost was ${usd(row.estimated_cost_usd)}.`
    : `No harmful-topic attempt rate was estimable. All harmful rows were invalid or unavailable; the 26 target calls contained ${transportErrors} transport errors. Estimated endpoint cost was ${usd(row.estimated_cost_usd)}.`;

  const returnedModels = Object.entries(route.returned_models)
    .map(([name, count]) => `${name} (${count})`)
    .join(", ");
  const providers = Object.entries(route.providers)
    .map(([name, count]) => `${name} (${count})`)
    .join(", ");
  const slug = model.id;
  const notePath = `research/testing/${runId}-${slug}.md`;
  const runUrl = `${githubRoot}/tree/main/${runRelative}`;
  const noteUrl = `${githubRoot}/blob/main/${notePath}`;
  const hfRunUrl = `${hfRoot}/runs/${runId}`;

  const note = {
    id: `${runId}-${slug}`,
    title: `${model.model} · one-turn APE-derived pilot`,
    status: "exploratory",
    validationStatus: "failed",
    validationMethod: "Automated primary judge with a preselected 20% second-judge audit; no blinded human validation.",
    validationArtifactUrl: `${githubRoot}/blob/main/${runRelative}/validation.json`,
    date: "2026-08-10",
    benchmark: "ATB APE-derived pilot v0.1",
    models: [model.model],
    summary: usable > 0
      ? `${fmt(attemptPct)} attempt rate among ${usable} usable responses from 20 hash-selected noncontroversially harmful topics; automated-only and not a full APE replication.`
      : "No attempt-rate estimate; endpoint or judging failures are retained as the pilot result.",
    question: "Under the same one-turn elicitation, does this served endpoint attempt to persuade on 20 noncontroversially harmful APE topics while still engaging six benign controls?",
    protocol: `Exact requested route ${row.model}; 20 harmful and six benign controls; one response per item; provider-default routing, reasoning, and sampling; primary judge ${validation.primary_judge}; 20% audit judge ${validation.audit_judge}. Returned models: ${returnedModels || "not reported"}. Providers: ${providers || "not reported"}.`,
    result: resultSentence,
    interpretation: `This is an endpoint and pipeline diagnostic, not a model ranking. ${validationText} The result can motivate a full, provider-pinned, human-validated run but cannot establish persuasion success or real-world harm.`,
    limitations: [
      "Only one APE harmful category is sampled; conspiracy and undermining-control topics are absent.",
      "Twenty harmful items and one generation per item yield wide uncertainty.",
      "Provider, reasoning, and sampling conditions were not pinned, so this is a dated served-endpoint observation.",
      "Labels are automated; blind human validation has not been completed.",
      "The test measures attempted persuasion, not whether any person was persuaded.",
    ],
    artifacts: [
      { label: "GitHub run artifacts", url: runUrl, type: "github" },
      { label: "Automated validation report", url: `${githubRoot}/blob/main/${runRelative}/validation.json`, type: "data" },
      { label: "Full research note", url: noteUrl, type: "methods" },
      { label: "Hugging Face mirror", url: hfRunUrl, type: "hugging-face" },
    ],
  };
  notes.push(note);

  if (usable > 0 && attemptPct !== null) {
    observations.push({
      id: `atb-ape-pilot-${slug}-attempt`,
      benchmarkId: "ape-atb-pilot",
      protocolId: manifest.protocol_id,
      modelId: model.id,
      metricKey: "attempt_pct",
      metricLabel: "APE-derived attempt rate · exploratory",
      scorePct: attemptPct,
      n: usable,
      evaluationDate: "2026-08-10",
      sourceType: "atb-project-exploratory",
      sourceUrl: noteUrl,
      sourceLocator: `${runRelative}/aggregate.csv; row ${row.model}`,
      comparabilityGroup: "atb-ape-turn1-pilot-v0.1-provider-default",
      lowerPct: lower,
      upperPct: upper,
      artifactUrl: `${githubRoot}/blob/main/${runRelative}/aggregate.csv`,
      note: "Exploratory automated-only pilot on 20 noncontroversially harmful items; not the full APE protocol or evidence of persuasive efficacy.",
    });
  }

  const markdown = `# ${note.title}\n\n**Status:** Exploratory · automated-only · not a ranking  \n**Run:** \`${runId}\`  \n**Date:** 10 August 2026  \n**Requested route:** \`${row.model}\`\n\n## Question\n\n${note.question}\n\n## Protocol\n\n${note.protocol}\n\n## Result\n\n${resultSentence}\n\n## Interpretation\n\n${note.interpretation}\n\n## Limits\n\n${note.limitations.map((item) => `- ${item}`).join("\n")}\n\n## Artifacts\n\n- [Aggregate and route artifacts](${runUrl})\n- [Hugging Face mirror](${hfRunUrl})\n- [Protocol](${githubRoot}/blob/main/OPENROUTER_PROTOCOL.md)\n\nRaw statements and generations are intentionally excluded from the public release.\n`;
  const target = new URL(notePath, root);
  await mkdir(path.dirname(target.pathname), { recursive: true });
  await writeFile(target, markdown, "utf8");
  markdownRows.push(`| [${model.model}](${githubRoot}/blob/main/${notePath}) | ${fmt(attemptPct)} | ${usable} | ${refused} | ${transportErrors} | ${usd(row.estimated_cost_usd)} |`);
}

const retainedPublished = publishedObservations.filter((row) => row.benchmarkId !== "ape-atb-pilot");
await writeJson("public/data/testing-notes.json", notes);
await writeJson("public/data/frontier-observations.json", [...retainedPublished, ...observations]);
await writeJson(`${runRelative}/research-notes.json`, notes);

const indexMarkdown = `# OpenRouter testing notes\n\nThese notes document the bounded \`${manifest.protocol_id}\` run. Every endpoint received the same 20 hash-selected noncontroversially harmful APE topics and six benign controls. Results are automated-only and exploratory; they are not a full APE replication or a model ranking.\n\n| Model | Attempt rate | Usable harmful n | Refusals | Transport errors | Endpoint cost |\n|---|---:|---:|---:|---:|---:|\n${markdownRows.join("\n")}\n\nThe run-wide estimated cost was ${usd(manifest.estimated_total_cost_usd)}. ${validationText} See [the serving protocol](${githubRoot}/blob/main/OPENROUTER_PROTOCOL.md) and [provenance](${githubRoot}/blob/main/data/PROVENANCE.md). Raw statements and generations are not public.\n`;
await mkdir(new URL("research/testing/", root), { recursive: true });
await writeFile(new URL("research/testing/README.md", root), indexMarkdown, "utf8");
await writeFile(new URL(`${runRelative}/README.md`, root), indexMarkdown, "utf8");

console.log(`Published ${notes.length} testing notes and ${observations.length} exploratory chart observations.`);
