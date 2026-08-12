# Inspect evaluation harness

This directory contains the active ATB evaluation harness. Inspect is the sole
runner for new model evaluations. The earlier
`run_openrouter_ape_pilot.py` and its v0.1 config are frozen historical evidence
of a failed pipeline audit; they are not extended into a result series.

The frozen environment currently uses `inspect-ai==0.3.257`,
`inspect-evals==0.16.0`, and `inspect-scout==0.4.46`. Inspect owns tasks,
solvers, scorers, model roles, retries, `.eval` logs, and primary outcomes.
Scout only reads completed Inspect logs offline.

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

Execution of a frozen paid manifest also requires an owner-only external
execution permit in addition to `--execute --allow-paid`. The manifest sets
per-sample token and recorded-cost stops plus a conservative planned run
envelope over models and epochs. Provider-SDK, sample, and task retries are all
disabled for confirmatory runs. Inspect checks the per-sample stops after model
responses; the planned run envelope is not a provider billing hard cap. The
runner audits cumulative persisted usage before it accepts or rejects the
scientific postflight, so partial/unscored runs still receive the same envelope
check. Provider invoices can still differ after ambiguous transport failures.

The primary outcome is the native four-class DisElect response label. Optional
actionability is a separate exploratory instrument. Personalisation, pressure,
factuality, persuasion efficacy, and agency transfer are not inferred from
DisElect.

### Paid route preflight (frozen)

`diselect-route-preflight-v0.3.json` is a transport canary, not a scientific
run. It schedules one benign control against the two invocable DeepSeek V4 Flash
IDs, binds each ID to its permanent canonical slug, pins both to DeepInfra/fp4,
and pins the Gemini grader to the ZDR-eligible Google Vertex endpoint.
It has zero harmful items, one epoch, no retries, one connection, a local
USD 0.02 per-sample stop, and a USD 0.04 total envelope. It is ineligible for
public aggregation and makes no safety or comparative-performance claim.

The frozen v0.2 canary was executed once on 12 August 2026. Both target routes
responded, but the 0731 route used 231 of its 250 completion tokens for internal
reasoning. It returned a 140-character partial completion, but `stop=max_tokens`
made that output non-scorable. Inspect preserved the sample as unscored; the ATB
postflight then rejected the paired eval set. The other route completed. The
logged OpenRouter `usage.cost` and Inspect's locally calculated estimate both totalled
USD 0.000534322. Version 0.3 raises the target completion allowance from 250 to
700 tokens (the native `diselect_pilot` default) and gives Inspect a
3,000-token per-sample/6,000-token run envelope;
the USD 0.02 per-sample and USD 0.04 run limits are unchanged. The v0.2 manifest
is immutable. Its controlled evidence is retained as GitHub Actions run
`31619679583` (artifact SHA-256
`ea5eff2438461b310b343229b8e3cc52704b4c6c05ab25bdd394e079888971de`);
artifact retention is operationally limited and must not be described as
permanent archival.

The frozen v0.3 canary was then executed once in GitHub Actions run
`31622800735`. Inspect completed and scored both benign samples as `comply`,
with no instrument failures, 990 tokens across target and grader calls, and an
exact OpenRouter billed total of USD 0.001067362. Scout's deterministic offline
QA scanned both transcripts with zero errors and zero empty-assistant findings.
The paid step nevertheless reported failure because the ATB postflight compared
Inspect attachment references with their resolved values and compared the
selected OpenRouter endpoint snapshot with the invocable alias. Both were
deterministic verifier defects: the persisted outputs and routes matched after
using Inspect's attachment resolver and the manifest's frozen canonical slugs.
The original workflow failure remains part of the audit trail. A content-bound
offline receipt may record corrected transport-postflight acceptance, but this
benign canary remains ineligible for a scientific or comparative model claim.

Revalidate a retained artifact without model calls after checking out the exact
clean validation commit:

```bash
uv run --frozen atb-offline-revalidate \
  --manifest evals/manifests/diselect-route-preflight-v0.3.json \
  --artifact-archive /controlled/atb/canary-31622800735.zip \
  --log-root logs \
  --execution-commit 62249de148b1e33adc46a85ca4372d472b129d19 \
  --validation-commit "$(git rev-parse HEAD)" \
  --artifact-sha256 efc1305cc0df2309c21baab757eb177fae14e1a499dbb5a4095c0597ed870e7f \
  --workflow-run-id 31622800735 \
  --output /controlled/atb/receipts/canary-31622800735.json
```

The revalidator uses the same complete persisted-execution predicate as the live
runner. Its offline boundary first hashes the exact regular, single-link ZIP,
extracts only a bounded safe inventory, verifies the complete checksum manifest,
and scans the whole artifact locally. It then resolves Inspect attachments
fail-closed, reconciles Inspect event usage with OpenRouter billing, verifies the
exact route-capture inventory, and writes only hashes, provenance, usage and
acceptance state. The original workflow outcome is derived from the checked
artifact receipt; it is not supplied by the operator. The revalidator never
emits prompts, responses or provider bodies. The Inspect artifact SHA-256 is
`efc1305cc0df2309c21baab757eb177fae14e1a499dbb5a4095c0597ed870e7f`;
the associated Scout artifact SHA-256 is
`da8532d85c0928b3873cde8ef2b78e902a7e8cb63edbc24bb0c2da2496479f29`.

The manifest is frozen against a credential-free capture of OpenRouter's model,
endpoint, and ZDR inventories, including content-addressed raw provider
responses. Reproduce a fresh candidate capture in a new directory with:

```bash
uv run python scripts/capture_openrouter_routes.py \
  --output-dir /controlled/atb/route-capture
```

A controlled v0.3 execution may use an inference-only key with a lifetime
per-key cap no greater than USD 30 configured with
`include_byok_in_limit=true`. That limit bounds the credential's total exposure;
it is not the authorization for this run. A separate permit must exactly match
the USD 0.04 planned-run envelope. The runner verifies the lifetime cap through
`GET /api/v1/key`, requires an authorization denial
from the management-only key-list API, rejects a management key on the
evaluation host, and repeats the public route capture immediately before
spending. Any canonical-ID, route, ZDR, supported-parameter, reasoning-effort,
completion-limit, token-price, or fixed-request-price drift blocks the run. The
complete fresh public capture is retained with owner-only permissions beside
the Inspect logs; a content hash of its receipt is embedded in every log. The
Inspect envelope and permit remain post-response/local safeguards, not a
transactional provider billing guarantee. The frozen v0.1 and executed v0.2
manifests are retained unchanged; v0.1 still requires a dedicated USD 0.04
lifetime key.

The external permit is a mode-`0600` JSON file outside the repository. It records
the operator's deliberate acknowledgement and binds it to the exact protocol,
canonical manifest hash, clean Git commit, and maximum USD 0.04 run envelope:

```json
{
  "schema_version": "atb-paid-execution-permit-v0.1",
  "protocol_id": "atb-diselect-route-preflight-v0.3",
  "manifest_sha256": "<canonical manifest SHA-256>",
  "code_commit": "<40-character merged commit>",
  "acknowledged_by": "<operator identity>",
  "acknowledged_at": "<UTC timestamp>",
  "expires_at": "<later UTC timestamp>",
  "maximum_cost_usd": 0.04
}
```

This file is a local execution interlock, not a cryptographic signature or
evidence of independent review. Independent authorization would require a
separately issued signed token or an external approval service.

On the controlled host, with no proxy variables and no management key present:

```bash
uv run atb-eval \
  --manifest evals/manifests/diselect-route-preflight-v0.3.json \
  --source-dir /controlled/election-ai-safety \
  --log-dir /controlled/atb/logs/diselect-route-preflight \
  --execute --allow-paid \
  --paid-permit /controlled/atb/permits/route-preflight.json
```

Inspect requests opt in to official OpenRouter Router Metadata. Postflight
requires the requested invocable ID and top-level response model ID to match,
the uniquely selected endpoint and any reported attempt to match the permanent
canonical slug frozen in the inventory, the first attempt to succeed, a non-BYOK
route, and absence of pipeline transformations.
OpenRouter's optional `attempts` field and unknown additive fields are tolerated,
but any fields that are present must be internally consistent. Raw OpenRouter
`usage.cost` and Inspect's locally calculated price estimate must each remain under
the envelope.

Validate the bounded plan without network calls:

```bash
uv run atb-eval \
  --manifest evals/manifests/diselect-route-preflight-v0.3.json \
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

There is an additional freeze blocker in `inspect-evals==0.16.0`: some evaluator
parse failures in the native one-turn scorer are represented as zero attempt or
zero persuasion instead of explicit uncertainty. ATB will not treat those zeros
as outcomes. A versioned adapter must preserve evaluator failure as unscored and
pass fixture-level equivalence tests before any APE manifest can be frozen.

## Native MASK status

`inspect_evals.mask` is installed but is not yet an ATB task. Its public task
uses a gated 1,000-item dataset and resolves binary and numeric judges by model
name inside the scorer, rather than through the explicit Inspect roles required
by the ATB route gate. A future `ATB public-set adaptation` therefore needs a
role-aware adapter, exact stable-ID inventory, explicit failure outcomes, and
route-event validation. `--limit 40` is not a frozen stratified MASK-40 design.

## Scout QA

Scout is an offline post-hoc QA lane, not a benchmark scorer:

```bash
uv run scout scan evals/atb_eval/scanners.py \
  -T /controlled/atb/logs/diselect-wave1a \
  --model <pinned-scanner-model> \
  --scans /controlled/atb/scans/diselect-wave1a
```

Controlled Inspect and Scout artifacts are scanned fail-closed before upload.
The scanner reads raw bytes and also parses compressed `.eval` and Parquet
content, so a credential marker hidden by container compression cannot pass the
artifact gate:

```bash
uv run --frozen python -m atb_eval.artifact_scan /controlled/atb/artifacts
```

Scanner findings do not alter benchmark outcomes or denominators. They control
artifact handling only.

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
