# Inspect evaluation harness

This directory contains the active ATB evaluation harness. Inspect is the sole
runner for new model evaluations. The earlier
`run_openrouter_ape_pilot.py` and its v0.1 config are frozen historical evidence
of a failed pipeline audit; they are not extended into a result series.

The current migration establishes four boundaries:

1. committed protocol manifests are distinct from runtime credentials and logs;
2. raw `.eval` logs, target outputs, and judge traces stay outside this public
   repository;
3. DisElect prompts are read from a pinned upstream checkout and are not
   vendored here; and
4. no run enters the comparative ledger without route integrity, blind human
   validation, and responsible-release review.

## Install

Use Python 3.12 and the committed lockfile:

```bash
uv sync --frozen
uv run inspect --version
uv run scout --version
```

## Network-free canary

The canary uses Inspect's mock model and benign fixtures. The log directory must
be outside this checkout.

```bash
uv run atb-eval \
  --manifest evals/manifests/inspect-canary-v0.1.json \
  --log-dir /tmp/atb-inspect-canary \
  --execute
```

It runs two conditions of the same mock model with distinct configurations. It
tests task discovery, concurrent paired scheduling, condition identity, scoring,
logs, and resumable `eval_set` mechanics. It makes no claim about model
capability or safety.

## DisElect Wave 1A

`diselect-wave1a-v0.1.json` is deliberately `draft`. It freezes source hashes
and a deterministic 40-harmful/10-benign sampling rule, but paid execution is
blocked until exact model routes and judge roles are added and the manifest is
frozen.

Validate the source checkout and inspect the planned run without making calls:

```bash
uv run atb-eval \
  --manifest evals/manifests/diselect-wave1a-v0.1.json \
  --source-dir /controlled/election-ai-safety \
  --log-dir /controlled/atb/logs/diselect-wave1a
```

Execution of a later frozen paid manifest also requires `--execute
--allow-paid`. The manifest sets per-sample token and recorded-cost stops plus a
conservative planned run envelope over models and epochs. Provider-SDK, sample,
and task retries are all disabled for confirmatory runs. Inspect checks the
per-sample stops after model responses; the planned run envelope is not a
provider billing hard cap. The runner rejects a completed eval set whose
cumulative recorded usage exceeds that envelope. Provider invoices can still
differ after ambiguous transport failures.

The primary outcome is the native four-class DisElect response label. Optional
actionability is a separate exploratory instrument. Personalisation, pressure,
factuality, persuasion efficacy, and agency transfer are not inferred from
DisElect.

### Paid route preflight (draft)

`diselect-route-preflight-v0.1.json` is a transport canary, not a scientific
run. It schedules one benign control against the two exact DeepSeek V4 Flash
aliases, pins both to DeepInfra/fp4, and uses the pinned Gemini grader route.
It has zero harmful items, one epoch, no retries, one connection, a local
USD 0.02 per-sample stop, and a USD 0.04 total envelope. It is ineligible for
public aggregation and makes no safety or comparative-performance claim.

The draft cannot execute until a fresh OpenRouter endpoint inventory is
committed for every condition, its hashes and exact endpoint fields are added
to the manifest, and the manifest is frozen. A controlled execution must also
use a rotated inference-only key and an independent provider/workspace hard cap
of USD 0.10; the Inspect envelope is a post-response safeguard, not a billing
guarantee.

Inspect requests opt in to official OpenRouter Router Metadata. Postflight
requires the requested alias, canonical response model, uniquely selected
provider endpoint, first successful attempt, non-BYOK route, and absence of
pipeline transformations to match the frozen evidence. OpenRouter's optional
`attempts` field and unknown additive fields are tolerated, but any fields that
are present must be internally consistent. Raw OpenRouter `usage.cost` and the
independent Inspect price estimate must each remain under the envelope.

Validate the bounded plan without network calls:

```bash
uv run atb-eval \
  --manifest evals/manifests/diselect-route-preflight-v0.1.json \
  --source-dir /controlled/election-ai-safety \
  --log-dir /controlled/atb/logs/diselect-route-preflight
```

All paid target conditions run concurrently in one eval set with the same
hash-shuffled sample order. Model and role calls are accepted only when their
logged effective configuration, requested model, returned model, role, seed
request field, base URL, and pinned provider match the manifest. Task-owned
target settings cannot be relabelled as condition-level sensitivities; changing
one requires a separate protocol. Mutable aliases and opaque SDK retries are
blocked at freeze time.

## Native APE

APE is imported from `inspect-evals==0.16.0` as `inspect_evals/ape_eval`. The
template manifest records the native one-turn task and requires the target plus
the three native auxiliary roles. It is deliberately draft-only: the manifest
cannot be frozen or executed until a verifier binds the exact multi-role turn
sequence, prompts, transcript state, and native scores. This avoids treating a
route-only check as an APE measurement. A future APE execution will also require
`--source-dir`
pointing to a clean checkout of AttemptPersuadeEval at the manifest commit. The
runner hashes the 600-topic file and requires the native Inspect cache to match
its ID-to-category-and-content mapping. APE measures attempt propensity, not
persuasive effect.

## Scout QA

Scout is a post-hoc QA lane, not a benchmark scorer:

```bash
uv run scout scan evals/atb_eval/scanners.py \
  -T /controlled/atb/logs/diselect-wave1a \
  --model <pinned-scanner-model> \
  --scans /controlled/atb/scans/diselect-wave1a
```

The deterministic empty-message scanner can be used immediately. LLM scanners
for refusal and evaluation awareness require validation against blind human
labels. Multi-role APE transcripts need an additional attribution audit before
Scout output is interpreted.

CI also runs the deterministic scanner end to end over the six mock canary
transcripts and rejects incomplete scans, scanner errors, duplicate transcript
IDs, non-boolean outputs, or any unexpected positive result. LLM scanners stay
diagnostic-only and never feed the release gate.

## Public release gate

Only an allowlisted aggregate candidate with controlled external evidence can
be checked:

```bash
uv run atb-release-gate /controlled/atb/release-candidate.json \
  --manifest evals/manifests/diselect-frozen.json \
  --lock-file uv.lock \
  --source-dir /controlled/election-ai-safety \
  --log-dir /controlled/atb/logs/diselect-frozen/RUN_FINGERPRINT \
  --validation-evidence /controlled/atb/validation/adjudicated.json \
  --repo-root . \
  --public-output /controlled/atb/release/atb-public-aggregate.json
```

The gate recomputes manifest, lockfile, commit, the selected prompt-inventory
hash from a clean pinned DisElect checkout, stratified probability sample,
inverse-probability-weighted validation metrics, aggregate, and blind human-
validation evidence. It rejects dirty or stale logs, fallback routing, provider
substitution, insufficient usable coverage in any condition/subset row, fewer
than two release reviewers, and raw prompt/response/message/content fields. It
writes the only eligible public-payload shape for a future project-ledger
import. The payload binds to one random execution ID and the exact multiset of
controlled `.eval` files. The gate requires exactly one successful log per
condition and rejects any retry history or superseded task attempt.
The current importer remains fail-closed for every ATB-generated observation
until a trusted signature/attestation verifier is provisioned. A passing gate
is necessary but not sufficient: attestation, interval estimation, and
responsible publication remain separate, versioned steps.
