# Priority evidence review

Review date: 2026-08-13

The six control-effect claims labelled `Established evidence` in the working
register were checked first because they could most easily be misread as
demonstrated policy effects. None is fully supported as written. Two retain
established evidence only for narrower experimental endpoints; four require a
downgrade, a new source, or both.

The public release preserves the source wording for provenance but marks every
unchecked established claim `Unverified candidate`. The structured review is
in [priority_claim_review.csv](priority_claim_review.csv).

## Effect claims

| Claim | Review | Required publication treatment |
|---|---|---|
| CLM-0016 | Unsupported as written | Downgrade to strong inference. Evidence on credible corrections and prebunking does not establish that assistant grounding prevents voting-access errors or abstention. |
| CLM-0115 | Partially supported with different evidence | Limit the endpoint to consent choices in privacy and commerce interfaces; do not infer pluralism or agency transfer. |
| CLM-0181 | Partially supported | Forwarding limits add friction and delay, but evidence is not a causal estimate of reduced electoral harm and evasion remains possible. |
| CLM-0184 | Partially supported | Keep only recognition, discernment, and sharing-quality outcomes measured in the experiments; remove unmeasured pluralism and reflective-agency claims. |
| CLM-0232 | Unsupported as written | Separate data-protection duties from intervention effectiveness; downgrade the manipulation and dependency claim. |
| CLM-0235 | Unsupported as written | Separate the conditional GDPR right from functional assistant-state portability; downgrade the effect claim. |

Primary or first-party sources used in the review include the [Science
Advances correction and prebunking study](https://www.science.org/doi/10.1126/sciadv.adv3758),
the [consent-interface field experiment](https://doi.org/10.1145/3313831.3376321),
the [forwarding-limit observational study](https://doi.org/10.1609/icwsm.v18i1.31372),
the [inoculation experiments](https://www.science.org/doi/10.1126/sciadv.abo6254),
and the [data-portability study](https://doi.org/10.1177/1461444820934033).

## Legal-scope corrections queued

The review also identified publication-critical scope corrections. These are
queued for claim-by-claim incorporation before a stable release:

- EU AI Act Article 5 prohibits only practices satisfying all statutory
  elements; it does not mandate a specific technical enforcement layer.
- EU AI Act Article 55 duties apply to providers of general-purpose AI models
  with systemic risk; named testing methods are not thereby mandatory.
- DSA risk assessment, researcher access, audits, and non-profiled recommender
  options apply to designated VLOPs or VLOSEs and include procedural limits.
- The EU Code of Conduct on Disinformation remains voluntary; for signatory
  VLOPs or VLOSEs, commitments can serve as a DSA compliance benchmark and
  audit object rather than autonomous universal duties.
- GDPR access, deletion, portability, and automated-decision provisions are
  conditional and do not create a general legal object called assistant
  memory.
- The Council of Europe AI Framework Convention is not treated as a present
  binding obligation before entry into force.

This review is a triage layer, not independent peer review. Stable publication
requires the corrected claims and sources to be incorporated into the
relational tables and checked by a second reviewer.
