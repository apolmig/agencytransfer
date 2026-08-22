# FronteraEval

**Find the right evaluation. Know what it proves.**

FronteraEval is a public decision-support catalogue for frontier AI evaluation. It is designed for researchers, policy analysts, assurance teams and technically informed general analysts.

It is not a universal leaderboard. It separates:

- source discovery;
- protocol interpretation;
- evidence reach;
- model-system results;
- deployment and downstream-effect claims.

## Initial scope

Every build imports the current internal task registry and distributed register from the official `UKGovernmentBEIS/inspect_evals` repository. It then adds a curated set of canonical evaluation suites from METR, MLCommons, Stanford CRFM, Epoch AI, ARC Prize, CAIS, Meta, Anthropic, Google DeepMind and other upstream authors.

Records have three visible states:

1. `imported`: official metadata, discovery only;
2. `catalogued`: a primary source is identified;
3. `reviewed`: FronteraEval has added a bounded interpretation with an explicit inference ceiling.

## Weekly freshness

A Netlify Scheduled Function runs Sundays at 02:17 UTC. It:

1. fetches the official Inspect registry and repository tree;
2. detects new, missing or renamed tasks and register entries;
3. checks selected canonical sources;
4. stores live status in Netlify Blobs;
5. exposes the result at `/api/weekly-status`.

The first request initializes the live store when no scheduled result exists yet. Automation does not author substantive editorial fields.

## Agency Transfer collection

Agency Transfer is the first editorial collection. It maps evaluations relevant to persuasion, manipulation, deception, social influence and human agency against the inference chain:

`capability → deployment → individual effect → aggregate consequence`

The collection explicitly rejects aggregation across non-equivalent constructs.

## Build

```bash
npm install
npm run build
npm run check
```

Netlify publishes `site/` and deploys functions from `netlify/functions/`.

## Data

Generated outputs:

- `/data/catalog.json`
- `/data/catalog.csv`
- `/data/freshness.json`

Stable IDs use source prefixes such as `inspect:`, `register:` and `canonical:`.

## Current limitations

The first release is strongest as a discovery and interpretation layer. It does not yet normalise every protocol version, implementation, model-system configuration, run and result. Imported records must not be represented as independently validated by FronteraEval.
