# Implementation plan

The next stage is a publication migration, not a product redesign. The current Part II interface remains valuable; it must be placed inside a clearer programme structure without turning the rest of the research into dashboards.

## Phase A — Freeze and canonicalise

**Objective:** prevent the interface from encoding unresolved file and version decisions.

Deliverables:

- tag or release the current Part II site before migration;
- publish the flagship paper at stable web and PDF URLs;
- select the standalone white paper, one-page brief, and poster;
- archive superseded visual variants;
- locate all explainer masters and presentation media;
- move public video cuts to durable hosting;
- add poster frames, captions, transcripts, dates, durations, and claim boundaries; and
- update `project-manifest.json` until unresolved warnings reflect only genuine research work, not missing publication hygiene.

Exit condition: every asset shown in the first public release has one canonical URL.

## Phase B — Build the programme shell

**Objective:** replace the benchmark identity at the root with a restrained research-publication front page.

Deliverables:

- programme masthead and navigation;
- home page using the copy hierarchy in `CONTENT_MAP.md`;
- reusable publication, evidence-grade, claim-ceiling, artifact, and status components;
- `/research/`, `/paper/`, `/outputs/`, `/explainers/`, `/updates/`, and `/about/` routes;
- shared metadata and social-card generation from the manifest; and
- footer with citation, repository, evidence freeze, responsible release, and correction links.

Exit condition: the programme can be understood without entering Part II or opening a dataset.

## Phase C — Part I and Part II migration

**Objective:** make the upstream research legible while preserving the current benchmark work.

Part I:

- evidence-architecture figure with distinct units;
- aggregate findings and explicit non-findings;
- Agency Transfer Lab block with adjacent claim ceiling;
- access-to-intervention methods record;
- controlled-evidence and responsible-release note; and
- next-study design.

Part II:

- migrate the current release registry under `/research/part-ii/`;
- retain the existing Evidence and Testing views;
- preserve benchmark-native metrics and missingness display;
- put the 87.4% descriptive rate beside the 0/28 confirmatory result and sensitivity limits; and
- implement redirects from `/evidence/` and `/testing/`.

Exit condition: no historical P2 link breaks and no page presents Part I as an n=5 study.

## Phase D — Part III and Part IV evidence views

**Objective:** turn the datasets into legible research pages without overclaiming.

Part III:

- versioned static snapshot of the public dataset;
- count funnel with the correct units;
- case-by-claim evidence matrix;
- concise case profiles;
- source/public version and cutoff display; and
- no main world map.

Part IV:

- versioned static snapshot of the public Atlas;
- control-family coverage by CDE layer;
- checked-versus-pending evidence backlog;
- restrained implementation explorer;
- separate legal, mechanism, effect, maturity, and verification fields; and
- no composite ranking.

Exit condition: all displayed counts reproduce from committed snapshots and validation scripts.

## Phase E — Paper, outputs, and explainers

**Objective:** make the programme citeable and usable in several formats without creating competing narratives.

Deliverables:

- flagship web edition and frozen PDF with matching version metadata;
- curated outputs index;
- canonical white paper, brief, and poster;
- reviewed explainer pages with transcripts and claim boundaries;
- programme history/archive for midpoint and superseded materials; and
- citation blocks for the programme and each dataset.

Exit condition: every primary output is reachable in two clicks or fewer, and every asset declares its version and evidentiary role.

## Phase F — Review and release

Checks:

- manifest and dataset validation;
- type-check and production build;
- route and redirect tests;
- external-link audit;
- mobile layout;
- keyboard navigation and contrast;
- captions and transcripts;
- social-preview metadata;
- citation consistency;
- responsible-release review;
- no private repository, temporary-host, or raw harmful-material exposure; and
- hostile-reader review of headline claims and numbers.

Release sequence:

1. preview deployment from the migration branch;
2. content and evidence review;
3. visual and accessibility review;
4. merge to `main`;
5. verify production routes and redirects; and
6. publish a dated update note describing what changed and what did not.

## Acceptance standard

The migration is complete when:

- the root clearly presents one research programme;
- the flagship paper supplies the narrative spine;
- P1–P4 each state a question, strongest finding, and claim ceiling;
- P2 retains its methodological depth without defining the whole project;
- P3 distinguishes rows, catalogue entries, records, and incidents;
- P4 does not imply that policy adoption equals policy effectiveness;
- videos are durable, accessible, labelled, and bounded;
- controlled material remains private;
- canonical versions and dates are unambiguous; and
- the site looks like a serious research publication rather than a web application.
