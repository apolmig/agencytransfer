import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const manifestPath = path.join(root, "programme", "project-manifest.json");

const errors = [];
const warnings = [];

const error = (message) => errors.push(message);
const warn = (message) => warnings.push(message);
const isObject = (value) =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const isDate = (value) =>
  value === null || /^\d{4}-\d{2}-\d{2}$/.test(String(value));
const isHttpUrl = (value) => {
  if (typeof value !== "string" || value.length === 0) return false;
  try {
    const url = new URL(value);
    return url.protocol === "https:" || url.protocol === "http:";
  } catch {
    return false;
  }
};

let manifest;
try {
  manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
} catch (reason) {
  console.error(`Programme manifest could not be read: ${reason.message}`);
  process.exit(1);
}

if (!isObject(manifest)) error("Manifest root must be an object.");
if (!/^\d+\.\d+\.\d+$/.test(manifest.schema_version ?? "")) {
  error("schema_version must use semantic version form.");
}

const programme = manifest.programme;
if (!isObject(programme)) {
  error("programme must be an object.");
} else {
  for (const field of [
    "id",
    "title",
    "subtitle",
    "flagship_title",
    "flagship_subtitle",
    "lead",
    "scope_statement",
    "secondary_lens",
    "thesis",
    "author",
    "affiliation",
    "claim_boundary",
  ]) {
    if (typeof programme[field] !== "string" || programme[field].trim() === "") {
      error(`programme.${field} must be a non-empty string.`);
    }
  }

  if (!isDate(programme.evidence_freeze)) {
    error("programme.evidence_freeze must be YYYY-MM-DD.");
  }
  if (!isDate(programme.last_updated)) {
    error("programme.last_updated must be YYYY-MM-DD.");
  }
  if (!isHttpUrl(programme.canonical_site)) {
    error("programme.canonical_site must be an HTTP(S) URL.");
  }
  if (!isHttpUrl(programme.canonical_repository)) {
    error("programme.canonical_repository must be an HTTP(S) URL.");
  }
}

const grades = Array.isArray(manifest.evidence_grades)
  ? manifest.evidence_grades
  : [];
const gradeIds = new Set(grades.map((grade) => grade?.id));
for (const required of [
  "established",
  "strong_inference",
  "plausible_hypothesis",
  "speculative_scenario",
  "open_question",
]) {
  if (!gradeIds.has(required)) error(`Missing evidence grade: ${required}.`);
}

const parts = Array.isArray(manifest.research_parts)
  ? manifest.research_parts
  : [];
const expectedParts = ["part-i", "part-ii", "part-iii", "part-iv"];
const partIds = parts.map((part) => part?.id);
if (
  partIds.length !== expectedParts.length ||
  expectedParts.some((id) => !partIds.includes(id))
) {
  error("research_parts must contain exactly part-i through part-iv.");
}

const artifacts = Array.isArray(manifest.artifacts) ? manifest.artifacts : [];
const artifactIds = new Set();
const forbiddenPublicFragments = [
  "github.com/apolmig/agencytransfer-controlled",
  "github.com/apolmig/agency-transfer-lab",
];
const temporaryHosts = new Set([
  "tmpfiles.org",
  "www.tmpfiles.org",
  "transfer.sh",
  "file.io",
]);

for (const artifact of artifacts) {
  if (!isObject(artifact)) {
    error("Every artifact must be an object.");
    continue;
  }

  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(artifact.id ?? "")) {
    error(`Invalid artifact id: ${artifact.id ?? "<missing>"}.`);
    continue;
  }
  if (artifactIds.has(artifact.id)) {
    error(`Duplicate artifact id: ${artifact.id}.`);
  }
  artifactIds.add(artifact.id);

  for (const field of [
    "title",
    "kind",
    "part",
    "role",
    "status",
    "visibility",
    "claim_ceiling",
  ]) {
    if (typeof artifact[field] !== "string" || artifact[field].trim() === "") {
      error(`${artifact.id}.${field} must be a non-empty string.`);
    }
  }

  if (!isDate(artifact.evidence_cutoff)) {
    error(`${artifact.id}.evidence_cutoff must be null or YYYY-MM-DD.`);
  }

  for (const field of ["canonical_url", "source_url"]) {
    const value = artifact[field];
    if (value !== null && !isHttpUrl(value)) {
      error(`${artifact.id}.${field} must be null or an HTTP(S) URL.`);
    }
  }

  const urls = [artifact.canonical_url, artifact.source_url].filter(Boolean);
  for (const value of urls) {
    const lower = value.toLowerCase();
    for (const fragment of forbiddenPublicFragments) {
      if (lower.includes(fragment)) {
        error(`${artifact.id} links a private repository: ${fragment}.`);
      }
    }
    try {
      const hostname = new URL(value).hostname.toLowerCase();
      if (temporaryHosts.has(hostname)) {
        error(`${artifact.id} uses forbidden temporary hosting: ${hostname}.`);
      }
    } catch {
      // URL format is reported above.
    }
  }

  if (
    manifest.publication_rules?.stable_url_required_for_published_status &&
    artifact.status === "published" &&
    !artifact.canonical_url
  ) {
    error(`${artifact.id} is published but has no canonical_url.`);
  }

  if (
    ["private", "withheld"].includes(artifact.visibility) &&
    (artifact.canonical_url || artifact.source_url)
  ) {
    error(`${artifact.id} is ${artifact.visibility} but exposes a URL.`);
  }

  if (artifact.status === "release_candidate" && !artifact.canonical_url) {
    warn(`${artifact.id} still requires a canonical public URL.`);
  }
  if (artifact.status === "hosting_required") {
    warn(`${artifact.id} still requires durable hosting.`);
  }

  if (artifact.kind === "video") {
    if (!isObject(artifact.media)) {
      error(`${artifact.id} is a video but has no media metadata.`);
    } else {
      for (const field of ["format", "language", "hosting_status"]) {
        if (
          typeof artifact.media[field] !== "string" ||
          artifact.media[field].trim() === ""
        ) {
          error(`${artifact.id}.media.${field} must be a non-empty string.`);
        }
      }

      if (artifact.status === "published") {
        for (const field of [
          "embed_url",
          "poster_frame_url",
          "captions_url",
          "transcript_url",
        ]) {
          if (!isHttpUrl(artifact.media[field])) {
            error(`${artifact.id} is a published video without ${field}.`);
          }
        }
        if (artifact.media.hosting_status !== "durable_public") {
          error(`${artifact.id} is published without durable_public hosting.`);
        }
      }
    }
  }
}

for (const part of parts) {
  if (!gradeIds.has(part.primary_evidence_grade)) {
    error(`${part.id}.primary_evidence_grade is not declared.`);
  }
  if (!isObject(part.headline_metrics)) {
    error(`${part.id}.headline_metrics must be an object.`);
  }
  if (!Array.isArray(part.artifact_ids) || part.artifact_ids.length === 0) {
    error(`${part.id}.artifact_ids must be a non-empty array.`);
  } else {
    for (const id of part.artifact_ids) {
      if (!artifactIds.has(id)) {
        error(`${part.id} references unknown artifact ${id}.`);
      }
    }
  }
  for (const field of [
    "title",
    "question",
    "observed_unit",
    "strongest_supported_claim",
    "claim_ceiling",
  ]) {
    if (typeof part[field] !== "string" || part[field].trim() === "") {
      error(`${part.id}.${field} must be a non-empty string.`);
    }
  }
}

const partI = parts.find((part) => part.id === "part-i");
if (partI) {
  if (!partI.counting_note) {
    error("part-i requires a counting_note because its evidence units overlap.");
  }
  if (partI.headline_metrics?.live_actions !== 0) {
    error("part-i.live_actions must remain zero unless the underlying research changes.");
  }
}

const partII = parts.find((part) => part.id === "part-ii");
if (partII?.headline_metrics?.conditions_passing_confirmatory_gate !== 0) {
  error("part-ii confirmatory-gate count differs from the current canonical record.");
}

const partIII = parts.find((part) => part.id === "part-iii");
if (partIII) {
  const metrics = partIII.headline_metrics ?? {};
  const chain = [
    metrics.relational_rows,
    metrics.catalogue_entries,
    metrics.core_records,
    metrics.incident_eligible_records,
    metrics.documented_manipulation_records,
  ];
  if (chain.some((value) => typeof value !== "number")) {
    error("part-iii count funnel is incomplete.");
  } else if (
    chain.some((value, index) => index > 0 && value > chain[index - 1])
  ) {
    error("part-iii count funnel must be non-increasing.");
  }
}

const routes = manifest.routes;
if (!isObject(routes)) {
  error("routes must be an object.");
} else {
  const canonical = Array.isArray(routes.canonical_routes)
    ? routes.canonical_routes
    : [];
  if (new Set(canonical).size !== canonical.length) {
    error("routes.canonical_routes contains duplicates.");
  }

  const redirects = Array.isArray(routes.redirects) ? routes.redirects : [];
  for (const redirect of redirects) {
    if (!canonical.includes(redirect.to)) {
      error(`Redirect target is not canonical: ${redirect.to}.`);
    }
    if (redirect.from === redirect.to) {
      error(`Redirect loops to itself: ${redirect.from}.`);
    }
  }
}

const serialized = JSON.stringify(manifest).toLowerCase();
for (const fragment of forbiddenPublicFragments) {
  if (serialized.includes(fragment)) {
    error(`Manifest contains forbidden private repository link: ${fragment}.`);
  }
}
for (const hostname of temporaryHosts) {
  if (serialized.includes(hostname)) {
    error(`Manifest contains temporary-host reference: ${hostname}.`);
  }
}

for (const message of warnings) {
  console.warn(`WARN: ${message}`);
}

if (errors.length > 0) {
  for (const message of errors) {
    console.error(`ERROR: ${message}`);
  }
  console.error(
    `Programme manifest validation failed: ${errors.length} error(s), ${warnings.length} warning(s).`,
  );
  process.exit(1);
}

console.log(
  `Programme manifest valid: ${parts.length} research parts, ${artifacts.length} artifacts, ${warnings.length} unresolved publication warning(s).`,
);
