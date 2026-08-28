# Programme publication architecture

The site should read as a maintained research publication, not as a product interface. Its job is to make the programme legible, preserve evidence boundaries, and provide stable access to the work.

## Primary navigation

**Programme · Research · Paper · Outputs · Explainers · About**

Six items are enough. Methods, data, code, citations, updates, and responsible-release material remain accessible within those sections and from the footer.

## Canonical routes

```text
/                                   Programme overview and current state
/research/                           Four-part research map
/research/part-i/                    From output to operationalisation
/research/part-ii/                   Capability and measurement
/research/part-ii/evidence/          Existing benchmark-native evidence views
/research/part-ii/testing/           Existing testing and validation record
/research/part-iii/                  Election evidence and the effect gap
/research/part-iv/                   Policy evidence and intervention
/paper/                              Flagship paper, web edition, PDF, citation
/outputs/                            White paper, brief, poster, datasets, methods, code
/explainers/                         Videos and visual explainers
/updates/                            Dated research and release log
/about/                              Author, programme status, acknowledgements, citation, responsible release
```

## Home page

The home page is the programme’s editorial front page. It should contain, in order:

1. **Masthead and status** — programme name, author, Cambridge ERA affiliation, evidence freeze, working-paper status.
2. **Lead argument** — “The next Cambridge Analytica will be a system.”
3. **Programme thesis** — frontier AI may turn episodic influence into scalable, adaptive, persistent infrastructure; the democratic concern is concentrated control over the joins.
4. **CDE topology** — capability → served system → controller and deployment → authentic exposure → human or institutional response → agency transfer and democratic harm.
5. **Four research parts** — one question, one strongest finding, and one claim ceiling each.
6. **State of the evidence** — established evidence, strong inference, plausible hypothesis, speculative scenario, and open question.
7. **Selected outputs** — flagship paper first; then white paper, brief, poster, datasets, methods, and code.
8. **Explainers** — a restrained media strip containing only reviewed, durably hosted assets.
9. **Programme log** — latest material changes and version dates.
10. **Citation and responsible release** — concise and visible, not buried in legal copy.

No live counter, product-style feature grid, animated metric wall, or generic “explore the platform” language.

## Research index

`/research/` presents the four parts as connected observations of one causal topology. It should not imply that the parts form an additive score or a completed causal ladder.

Each part uses the same editorial template:

1. question;
2. observed unit;
3. why it matters;
4. strongest supported claim;
5. what remains unmeasured;
6. key visual;
7. methods and evidence;
8. linked artifacts;
9. next study.

### Part I

Primary visual: evidence architecture, not a single sample count.

Show separately:

- 10 paired objectives across two scenario families;
- three midpoint probes;
- two forensic trace bundles;
- five forensic requests;
- three completed outputs;
- 18,907 local ledger events; and
- zero live actions.

The page must state that these units may overlap and cannot be summed. Agency Transfer Lab is linked as a methods and evidence-harness prototype, with its non-claims visible next to the link.

### Part II

Preserve the existing registry, evidence, and testing work. The current site becomes the substantive core of this section rather than the identity of the whole programme.

Suggested internal structure:

```text
/research/part-ii/              Editorial overview and principal findings
/research/part-ii/registry/     Frontier release map
/research/part-ii/evidence/     Literature and benchmark-native evidence
/research/part-ii/testing/      Direct tests, exclusions, route integrity, validation
```

The first implementation may keep the registry on the Part II landing page to minimise churn.

### Part III

Primary visual: evidence funnel and case-by-claim matrix.

The page should separate:

- relational rows;
- catalogue entries;
- core records;
- incident-eligible records;
- documented-manipulation records; and
- claim coverage across occurrence, mechanism, attribution, distribution, exposure, human effect, institutional response, and electoral effect.

Avoid a world map as the main visual. Geographic location is not prevalence.

### Part IV

Primary visual: intervention coverage by CDE layer alongside the evidence backlog.

A restrained explorer may filter implementations by mechanism, responsible actor, jurisdiction, legal force, maturity, evidence grade, rights burden, and evaluability. It must not produce a synthetic policy ranking.

## Paper

`/paper/` is a readable web edition, not an embedded Word viewer.

It should provide:

- title, abstract, status, evidence freeze, and claim boundary;
- table of contents;
- web text with figures and source-linked notes;
- a frozen PDF;
- citation metadata;
- version history; and
- links from each research part to the corresponding evidence artifact.

The web text and PDF must declare the same version and evidence cutoff.

## Outputs

`/outputs/` is a curated publication record, not a file dump.

Group outputs by function:

- **Core publications** — flagship paper, white paper.
- **Briefing formats** — one-page brief, poster.
- **Evidence artifacts** — Evaluation Registry, APE-120 audit, Election Evidence Index, Policy Atlas.
- **Methods and code** — public repository, Part I methods, responsible-release notes.
- **Programme history** — midpoint write-up and superseded outputs, clearly dated.

Only canonical assets appear in the main index. Variants and superseded files belong in an archive subsection.

## Explainers

`/explainers/` contains reviewed media, not promotional filler. Each item requires:

- title and one-sentence purpose;
- duration and publication date;
- embedded or first-party video;
- poster frame;
- captions and transcript;
- synthetic/observational label;
- claim boundary; and
- related research part.

A video without durable hosting or a transcript remains absent from the public page even if a temporary master exists.

## About and updates

`/about/` explains the programme, author, fellowship context, methods philosophy, acknowledgements, conflicts, citation, and responsible release.

`/updates/` records material changes to evidence, methods, datasets, publications, and claim ceilings. It is not a blog. Every item should state what changed, why it changed, and whether any public conclusion changed.

## Redirects and continuity

The current links must continue to work:

```text
/evidence/  → /research/part-ii/evidence/
/testing/   → /research/part-ii/testing/
```

The root URL remains unchanged. Existing P2 deep links should be mapped before deployment, and the current site should be tagged or released before the migration begins.

## Technical posture

Retain React, TypeScript, Vite, and GitHub Pages. The architecture is static-first. Data-rich views may remain interactive, but the programme should remain readable without JavaScript-heavy navigation or live third-party queries.

`programme/project-manifest.json` is the source of truth for titles, routes, versions, links, status, metrics, and claim ceilings. Dataset views should use versioned static snapshots rather than silently loading “latest” external data.
