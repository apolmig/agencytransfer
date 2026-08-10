# Responsible Release Policy

## Purpose

Agency Transfer Benchmark (ATB) studies model behaviours that may be relevant to
harmful influence, deception, or delegated operations. Some source items and
model outputs can be dual use. This policy defines what the project may publish,
what remains controlled, and when publication must pause.

The policy applies to the website, GitHub repository, release archives, Hugging
Face repositories, papers, presentations, issue discussions, and any data shared
with collaborators.

## Claim discipline

Every public release must state that current ATB evaluations do not directly
measure agency transfer. Wave 0 maps published benchmark-defined campaign
execution, operational compliance, refusal, and honesty under pressure. APE
measures persuasion attempts, not successful human persuasion. MASK measures
benchmark-defined lying under pressure, not general intent or manipulation.
DisElect does not measure campaign reach, belief change, voting behaviour, or
electoral effect.

The following terms are prohibited unless supported by direct evidence in the
specific study:

- “caused agency transfer”;
- “changed votes”;
- “successfully manipulated people”;
- “safe” or “unsafe” as a global model property;
- “most manipulative model”; and
- “longitudinal improvement” for a retrospective release comparison.

Preferred language includes “benchmark-defined compliance,” “attempt
propensity,” “lying under pressure,” “observed serving condition,” and “best or
lowest observed among the evaluated snapshots.”

An automated-only project pilot is labelled `exploratory` in the website, data,
and research note. It may demonstrate route coverage or identify a follow-up
question, but it is not used to rank models and is not described as a replicated
benchmark result. A status label cannot be removed until the prespecified blind
human-validation gate passes.

## Release tiers

### Public

Suitable for the website, GitHub, or a public Hugging Face dataset:

- aggregate counts, proportions, intervals, and strata;
- model, provider, protocol, and evaluation metadata;
- item identifiers and hashes when the source licence permits;
- human-validation summaries and confusion matrices;
- route-integrity, cost, latency, and failure statistics;
- code, schemas, manifests, and aggregate derivation scripts;
- benchmark cards, limitations, and citations; and
- benign examples or carefully paraphrased qualitative examples.

### Controlled

Stored with access controls and shared only for a documented research purpose:

- raw harmful target-model generations;
- judge traces containing harmful content;
- source prompts whose redistribution rights are unclear;
- outputs that combine operational steps into a usable workflow;
- low-frequency examples that could identify a person or live context; and
- adjudication notes containing reproduced harmful text.

### Withheld

Not distributed outside the minimum authorised team:

- credentials or authentication material;
- novel prompts designed to evade safeguards;
- operational targeting or campaign plans;
- live-election vulnerabilities that have not been responsibly disclosed;
- content that materially lowers the effort required for real-world misuse; and
- personal data not necessary for the research record.

Hashing content does not make unsafe or personal data safe to publish if the
underlying text is also released or readily recoverable.

## No raw harmful-output publication by default

ATB does not publish raw harmful generations by default, even when the source
prompt is already public. Generated continuations can add operational detail not
present in the benchmark. Public reproducibility is supported through item IDs,
content hashes, labels, aggregate code, provenance, and controlled review rather
than unrestricted output dumps.

An exception requires all of the following:

1. a concrete scientific need that cannot be met with a benign, redacted, or
   paraphrased example;
2. confirmed redistribution rights;
3. two-person misuse review;
4. removal of operational, targeting, and personal detail;
5. approval recorded in the release log; and
6. an explanation of why publication benefits exceed residual risk.

## Dataset and licence rules

- Project code is intended for release under Apache-2.0 unless a component
  requires another compatible licence.
- ATB-created aggregate data and original metadata may be released under CC BY
  4.0 after review.
- Upstream datasets retain their original licences and attribution. They are not
  relicensed by ATB.
- A code-repository licence is not assumed to license a separately hosted
  dataset.
- MASK prompts are not vendored or republished until the dataset's redistribution
  terms are unambiguous.
- APE and DisElect material is used only within the scope of the applicable
  repository and content licences; raw target generations remain controlled.
- Dynamic external benchmark data is linked rather than mirrored unless its
  version and redistribution terms are explicit and its licence clearly permits
  redistribution. A dated, transformed table from a paper remains separate from
  a later live leaderboard retrieval; the latter records a retrieval timestamp
  and does not overwrite the former.
- Published figures are not copied merely because a paper is public. ATB
  reconstructs cited numeric values or uses figures only when the publication
  licence permits.

Every data release includes source URLs, source revisions, attribution, the ATB
protocol version, and a machine-readable licence field.

## Election and real-world safety boundary

ATB is an offline evaluation project. It does not:

- contact voters, candidates, campaigns, parties, officials, or platform users;
- target a real demographic, constituency, or individual;
- publish content to a social network;
- use live accounts, autonomous posting, browsing agents, or external action
  tools;
- optimise content for an ongoing election; or
- evaluate whether a harmful operation succeeds in the world.

Wave 0 makes no new target-model calls. Wave 1 is restricted to text-only,
single-turn requests without tools or external side effects. Later departures
require a new threat model and release-policy review.

Examples and summaries avoid current operational details, personal targeting,
and actionable evasion techniques. Research about a live election receives
heightened review and may remain embargoed until the relevant risk has passed.

## Dual-use review

Before publication, two reviewers independently assess:

- whether content adds material operational capability;
- whether it identifies a live target or vulnerability;
- whether an aggregate can be reverse engineered into sensitive item content;
- whether model or provider disclosure could facilitate evasion;
- whether the result requires advance notice to a developer, provider,
  benchmark owner, platform, or election authority;
- whether the title and captions overstate the construct; and
- whether source licences and terms permit the proposed release.

Reviewers record `release`, `release-with-redactions`, `controlled-access`,
`temporary-embargo`, or `withhold`, with rationale. Disagreement defaults to the
more restrictive outcome until adjudicated.

## Responsible disclosure

A disclosure hold is considered when a result reveals:

- a previously undocumented and reproducible safeguard regression;
- a provider-routing or moderation bypass;
- a capability that materially reduces the cost of harmful operations;
- sensitive behaviour tied to a live event; or
- a benchmark or judge vulnerability that invalidates public comparisons.

The project will preserve evidence, stop unnecessary replication, minimise
distribution, and contact the relevant party through an appropriate security or
safety channel. The initial notice describes the affected version, deployment
condition, impact, reproduction boundary, and proposed disclosure timeline
without transmitting more harmful content than necessary.

An embargo is time-limited and reviewed. Public release after remediation still
states the original evaluation date and deployment condition.

## Human reviewer welfare

Human validation may expose reviewers to manipulative, deceptive, discriminatory,
or distressing material. The annotation plan therefore provides:

- an advance content notice;
- the right to skip an item without penalty;
- workload limits and breaks;
- access to a project lead for escalation;
- a codebook that avoids requiring unnecessary rereading of harmful content;
- compensation appropriate to the work; and
- removal of reviewer identities from public item-level records.

Reviewers are not asked to judge real people or disclose personal political
beliefs. Any future human-efficacy study requires independent ethics review and
is not covered by model-output annotation approval.

## Privacy and security

- Public benchmark records contain no personal data beyond already-public
  professional attribution required for citation.
- Restricted outputs use encrypted storage and least-privilege access.
- Access and export events are logged.
- Retention periods are declared before each wave and raw content is deleted
  when it is no longer scientifically or legally necessary.
- Public issue trackers are not used to paste harmful outputs or private
  disclosure details.
- Secrets are supplied at runtime and excluded from source control, build
  artefacts, screenshots, notebooks, and logs.
- Git history and release archives receive a secret scan before publication.

If a credential is exposed, evaluation pauses until it is revoked or rotated and
the exposure path is reviewed.

## Publication checklist

No release is approved until all applicable items are complete:

- [ ] Construct and non-claim language is visible.
- [ ] Wave and protocol versions are frozen.
- [ ] Model and provider provenance passes route-integrity checks.
- [ ] Human-validation thresholds are reported and met, or results are labelled
      experimental-unvalidated.
- [ ] Counts, denominators, missingness, and confidence intervals are present.
- [ ] Native benchmark metrics remain separate; no false composite is shown.
- [ ] Post-publication benchmark exposure is flagged.
- [ ] Licence and attribution fields are complete.
- [ ] Raw harmful outputs and restricted prompts are absent.
- [ ] No personal, targeting, live-election, or evasion detail is exposed.
- [ ] Secret and dependency scans pass.
- [ ] Two-person dual-use review is recorded.
- [ ] Any responsible-disclosure hold is resolved or documented.
- [ ] Downloadable data reproduces the displayed aggregates.

## Corrections, retractions, and versioning

Corrections do not overwrite history without notice. Each release has a date,
protocol version, data hash, and code commit. A correction records the affected
fields, reason, reviewer, and whether charts or conclusions changed.

A result is retracted or quarantined when route identity cannot be established,
licence permission is withdrawn, scoring validity fails, unsafe content was
released, or a material data error invalidates the estimate. The public record
retains a non-sensitive tombstone explaining the retraction.

Major protocol changes, including new prompts, item sets, judges, denominators,
or serving modes, create a new series. They are not backfilled into an old line
without an explicit bridge study.

## External requests for controlled data

Controlled data is not released through a public download link. A request must
state the research purpose, requested fields, security controls, retention
period, intended publication, and institutional contact. Approval may require a
data-use agreement, evidence of ethics or safety review, and a commitment not to
reconstruct or publish harmful workflows.

ATB may provide labels, redacted extracts, or an audited analysis in place of raw
text. Access can be revoked for misuse or policy breach.

## Governance

Until a formal committee is established, every release requires distinct
methodological and responsible-release sign-off. A person who generated a result
may participate in review but may not be the sole approver.

This policy is versioned with the repository. Stricter legal, platform, source,
or institutional requirements take precedence.
