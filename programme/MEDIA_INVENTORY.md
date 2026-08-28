# Explainers and media inventory

Videos are programme outputs, not decoration. They should explain a mechanism, method, finding, limitation, or policy choice that the written research supports.

## Located asset

### Brazil 2026 harmful-manipulation explainer

- **Type:** synthetic scenario explainer
- **Related research:** Part I
- **Repository evidence:** `tmp/brazil2026-artifacts-20260824.md`
- **Current source:** final and preview MP4 builds on temporary hosting
- **Publication status:** hosting required
- **Canonical URL:** none
- **Claim ceiling:** illustration of how capability, targeting, distribution, and feedback could be joined; not evidence of a real operation, authentic exposure, behaviour change, or electoral effect

The temporary URLs must not be surfaced on the programme site. A final master should first be reviewed, archived, and moved to durable hosting.

## Reported but not yet canonicalised

The programme history refers to additional explainer and presentation variants, including a synthetic US-midterms/Miami scenario and short presentation clips. Their exact masters, final cuts, durations, thumbnails, transcripts, and durable URLs were not located unambiguously during this inventory.

They remain one backlog item until each asset can be identified. Do not create public entries from remembered titles or temporary links.

For every additional asset, record:

```text
artifact_id
title
purpose
research_part
media_type
synthetic_or_observational
duration_seconds
language
master_location
public_host
embed_url
poster_frame_url
captions_url
transcript_url
publication_date
source_version
claim_ceiling
responsible_release_status
canonical_or_variant
```

## Media classes

Each public item must use one of four labels.

### Synthetic scenario

A fictional or contained illustration of a plausible mechanism. It must not be presented as evidence that a named actor, campaign, platform, model, or election behaved as depicted.

Required adjacent label:

> Synthetic scenario. Illustrates a possible mechanism; not evidence of a real operation, authentic exposure, behaviour change, or electoral effect.

### Methods demonstration

Shows a research harness, evaluation flow, dataset, or control mechanism.

Required adjacent label:

> Methods demonstration. Shows the research process or interface; it does not by itself establish the substantive outcome under study.

### Evidence explainer

Explains a result already supported by the paper, dataset, or source record. Figures, denominators, evidence cutoffs, and caveats must match the canonical source.

### Talk or presentation

A recorded presentation or excerpt. It must show the event, date, speaker, source paper version, and whether the talk predates later corrections.

## Publication gate

A video is not publishable until all conditions pass.

| Gate | Requirement |
|---|---|
| Identity | Final title, date, version, duration, and related research part are known |
| Source | A preserved master exists outside temporary hosting |
| Hosting | Stable first-party or durable platform URL; no expiring file service |
| Accessibility | Captions, transcript, keyboard-accessible player, descriptive poster frame |
| Evidence | Claims and figures match the canonical paper or dataset version |
| Labelling | Synthetic, methods, evidence, or talk class is visible next to the player |
| Responsible release | No campaign-ready instructions, targetable profiles, evasion methods, credentials, or raw harmful outputs |
| Rights | Music, images, footage, fonts, and voice assets have documented reuse rights |
| Canonicalisation | One final asset is public; drafts and previews are archived, not listed as separate outputs |

## Recommended public structure

```text
/explainers/
  selected reviewed explainers
/explainers/<slug>/
  player
  purpose
  synthetic/observational label
  claim boundary
  transcript
  related paper section
  related dataset or method
  citation and date
```

Suggested first-party supporting files:

```text
public/media/posters/<artifact-id>.webp
public/media/captions/<artifact-id>.vtt
content/transcripts/<artifact-id>.md
```

The video master may live on a durable streaming host rather than in Git. The manifest should retain the canonical embed URL and the internal archive should retain the master and checksum.

## Presentation on the site

- No autoplay with sound.
- No background video in the hero.
- No carousel.
- One selected video may appear on the home page; the rest belong on `/explainers/`.
- Show duration before playback.
- Keep the claim boundary visible without opening an accordion.
- Use a still frame that explains the mechanism, not a sensational thumbnail.
- Do not use synthetic campaign content as decorative imagery elsewhere on the site.

## Next inventory action

Locate the masters and final public decisions for every reported explainer. Until that is complete, the programme manifest contains only the Brazil 2026 item whose repository provenance could be confirmed.
