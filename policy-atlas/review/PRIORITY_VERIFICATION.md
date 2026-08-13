# Priority evidence review

Review date: 2026-08-13

The six control-effect claims initially labelled `Established evidence` were
checked against primary empirical sources. None supported the original policy
effect as written. The release therefore rewrites all six claims to the
observed endpoint and separately recodes the implementation-level inference.

This distinction matters: an empirical result can be established for a narrow
endpoint while remaining indirect, negative, or insufficient evidence for the
proposed policy.

The structured review, including source IDs, designs, samples, endpoints, and
limitations, is in [priority_claim_review.csv](priority_claim_review.csv).

## Effect claims

| Claim | Observed endpoint | Implementation treatment |
|---|---|---|
| CLM-0016 | Survey confidence, fraud beliefs, and factual accuracy after static election-security messages | `Strong inference`; no assistant or voting-access endpoint |
| CLM-0115 | Cookie-notice acceptance under first-page button prominence | `Strong inference`; no test of regulatory enforcement or agency |
| CLM-0181 | Substantial non-coverage of FMT labels among duplicated media in selected public groups | `Open question`; no causal estimate of friction, reach, or harm |
| CLM-0184 | Immediate recognition of specifically taught manipulation techniques | Retains `Established — component effect` only for this bounded endpoint |
| CLM-0232 | Recommender quality under reduced per-user rating histories | `Strong inference`; no assistant-memory or manipulation endpoint |
| CLM-0235 | Data receipt but failed functional import/direct transfer across four IoT systems | `Open question`; negative implementation evidence, not assistant-state portability |

All six corrected claims now have a `Claim checked — empirical source`
relation. This does not make the wider interventions effective: 112 of 118
control-effectiveness claims still lack checked empirical support, and five of
the six priority implementations are no longer classified as established
component effects.

## Legal-scope wave

Five previously source-less legal instruments were also checked against
official primary sources:

- the DMA applies only to formally designated gatekeepers and core platform
  services, even though virtual assistants are within the service taxonomy;
- the UK ATRS mandate is an administrative policy for in-scope central
  government organisations, not a general statutory duty;
- the Seoul commitments are voluntary commitments by listed frontier-AI
  organisations;
- the UCPD is binding through national transposition, while the 2021
  Commission guidance is expressly non-binding; and
- the Digital Fairness Act remains a planned Q4 2026 initiative with no legal
  force or adopted proposal as of 2026-08-13.

This is a claim-specific internal evidence audit, not independent peer review.
Stable publication still requires verification of the remaining public claims
and independent review of the policy packages.
