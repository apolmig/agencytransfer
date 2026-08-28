# Publishing and maintenance rules

The programme can only remain credible if its public record is stricter than its file system. “Final” in a filename is not a publication decision. A recent upload is not necessarily the latest evidence. A polished visual is not a finding.

## 1. One canonical asset

Every public output has one canonical asset and one canonical URL.

Variants may be retained for provenance, but they must be marked `legacy` or `superseded` and excluded from the main outputs index. The canonical decision belongs in `programme/project-manifest.json`.

## 2. Separate source, release, and site versions

Record these independently:

- **source version** — the research workbook, repository snapshot, or manuscript from which the output was built;
- **public release version** — the immutable version users can cite or download;
- **evidence cutoff** — the latest date included in the evidence;
- **site snapshot** — the date on which the website imported or rendered the public release.

A later source workbook does not silently replace a public dataset release. The site must state which one it displays.

## 3. Counts need denominators

Never publish a large number without identifying its unit.

Required fields:

- numerator;
- denominator or universe;
- inclusion rule;
- exclusions and missingness;
- evidence cutoff; and
- whether the count is a record, observation, request, condition, case, claim, implementation, or source.

Part I units must not be added. Part III relational rows and catalogue entries must not be called cases. Part IV implementations must not be called proven interventions.

## 4. Every claim stops somewhere

Each substantive result must state:

1. observed unit;
2. exact system or source;
3. evidence grade;
4. strongest supported claim;
5. claim ceiling;
6. missing causal bridge; and
7. evidence required to upgrade the claim.

Evidence grades are:

- established evidence;
- strong inference;
- plausible hypothesis;
- speculative scenario; and
- open question.

These categories describe knowledge, not severity.

## 5. Action and public claim are different

Claim ceilings constrain what the programme or an institution may say. They do not imply that every upstream mechanism must remain unaddressed until an electoral effect is proved.

Public writing should preserve both rules:

> Do not promote upstream evidence into downstream claims. Do not wait for a downstream claim before acting on an evidenced upstream mechanism.

Any intervention discussion must specify the mechanism, responsible actor, lawful authority, measurable endpoint, rights burden, review path, reversibility, and expiry where relevant.

## 6. Preserve construct boundaries

Do not combine metrics merely because they concern manipulation, persuasion, deception, safeguards, or elections.

A pooled index requires, at minimum:

- construct compatibility;
- protocol compatibility;
- model or condition bridges;
- adequate overlap;
- explicit missingness treatment;
- validation; and
- sensitivity analysis.

Until those conditions are met, benchmark-native outcomes remain separate.

## 7. Static, versioned evidence

The public site should render versioned snapshots committed or generated through a reproducible build. It should not silently query the latest external dataset at runtime.

Every imported dataset snapshot should include:

- source URL;
- version or immutable revision;
- retrieval date;
- checksum where practical;
- transformation script;
- validation output; and
- licence or reuse boundary.

## 8. Private and withheld material

Do not publish or link:

- private control-plane repositories;
- raw harmful prompts or generations;
- campaign-ready operational material;
- targetable profiles;
- evasion or safeguard-bypass instructions;
- credentials, private keys, validation keys, or reviewer mappings;
- raw grader traces that reproduce harmful material; or
- controlled evidence whose release has not passed ethical and dual-use review.

The site may state that controlled evidence exists and describe its aggregate function. It may not imply independent attestation where none exists.

The public Agency Transfer Lab deployment may be linked. Its private source repository may not.

## 9. Media rules

A public video requires:

- durable hosting;
- preserved master and checksum;
- poster frame;
- captions;
- transcript;
- publication date and duration;
- source paper or dataset version;
- synthetic, methods, evidence, or talk label;
- adjacent claim boundary; and
- responsible-release and rights review.

Temporary file hosts are forbidden as canonical URLs. Preview cuts are not separate outputs.

## 10. Corrections and updates

Material corrections receive a dated entry under `/updates/` and in the repository changelog.

Each correction states:

- what changed;
- why it changed;
- affected pages and artifacts;
- whether numbers, evidence grade, or claim ceiling changed;
- old and new versions; and
- whether the previous public asset remains available for provenance.

Do not overwrite an immutable release. Publish a new version.

## 11. Programme history

Midpoint documents, early risk-gate framings, failed pilots, superseded posters, and abandoned interfaces may be valuable. They belong in a dated programme-history archive, not alongside current findings without qualification.

Historical material must show:

- original date;
- status at the time;
- superseding artifact;
- whether the framing or conclusion later changed; and
- whether the item remains citeable.

## 12. Public design discipline

The publication should remain editorial and restrained:

- serif headlines and body text;
- black, grey, paper, and one muted accent;
- one principal visual per section;
- no product metrics, gamification, or risk theatre;
- no decorative maps that imply prevalence;
- no sensational synthetic imagery without a research purpose; and
- no interface element that hides the claim boundary while foregrounding the headline number.

## 13. Release checklist

Before merging a public programme update:

```text
[ ] Manifest updated
[ ] Canonical asset and URL fixed
[ ] Source, release, cutoff, and site versions separated
[ ] Counts and denominators verified
[ ] Claim ceiling reviewed
[ ] Links and redirects tested
[ ] Private and temporary URLs rejected
[ ] Dataset snapshot reproduced and validated
[ ] Media accessibility and rights complete
[ ] Responsible-release review complete
[ ] Mobile and keyboard access checked
[ ] Citation metadata updated
[ ] Correction/update note added when material
```
