# OpenRouter Evaluation Protocol

## Purpose

This protocol defines how Agency Transfer Benchmark (ATB) uses OpenRouter as a
serving layer. Its purpose is to make the deployment condition observable and to
prevent silent model, provider, parameter, or fallback changes from being
misinterpreted as differences in model weights.

OpenRouter evaluations are evaluations of a **served model condition**, not of
weights in isolation.

## Exploratory pilot deviation — 2026-08-10

The bounded `atb-ape-turn1-pilot-v0.1` run predates full strict-route
implementation. It uses exact OpenRouter model slugs but provider-default
routing, fallback, sampling, and reasoning; it does not pin a single upstream
provider. The run therefore estimates only endpoint behaviour observed during
the evaluation window. Its cross-model values are labelled exploratory and are
not connected as a strict longitudinal series.

The pilot's purpose is to test endpoint coverage, a hash-only public release,
automated label parsing, cost accounting, and the refusal/attempt distinction.
It uses 20 hash-selected noncontroversially harmful APE topics and six benign
controls per endpoint, rather than the full 600-topic APE design. Public
artifacts exclude statements and generations. A full comparative run must add
provider pinning, exact request timestamps and generation IDs, frozen reasoning
conditions, and blind human validation before it can supersede this pilot.

## Credential handling

- Credentials are supplied only through a runtime secret or environment
  variable.
- Credentials are never committed, placed in a frontend bundle, included in a
  URL, printed to logs, stored in request fixtures, or copied into a report.
- Public artefacts may record that authentication succeeded, but never a token,
  token fragment, request header, or reusable credential.
- A credential disclosed in chat, an issue, a log, or source control is treated
  as compromised and rotated before production evaluation.
- Browser code and GitHub Pages must never call OpenRouter with a privileged
  project credential. Evaluation calls run offline or in a protected job.

## Freeze record

Before each wave, archive the following time-stamped material:

1. the OpenRouter `/models` response;
2. the endpoint inventory for each requested model;
3. the selected provider slug and endpoint metadata;
4. OpenRouter documentation version or retrieval date;
5. the target model card and weight revision;
6. provider privacy/data-policy metadata; and
7. the ATB model-manifest commit.

The freeze record has a content hash and is retained with the private run
manifest. A sanitised version without credentials or unsafe content is published.

## Exact model resolution

For each candidate:

1. Resolve the requested OpenRouter ID against the frozen model inventory.
2. Record the returned `canonical_slug`, Hugging Face identifier, creation date,
   architecture metadata, context length, and supported parameters.
3. Cross-check the checkpoint against an official model card and revision.
4. Test whether the canonical slug itself is invocable.
5. Send a benign canary request and require the returned model identifier to
   match the frozen expectation.

Identifiers containing `latest`, `free`, automatic routers, or undocumented
aliases are ineligible for the strict release series. A dated alias may still be
ineligible if the provider cannot attest or expose which checkpoint it serves.

If only a mutable alias exists, ATB may retain the result as:

> endpoint behaviour observed on the evaluation date

It is not labelled as an immutable historical checkpoint and is not connected
to exact releases in the primary time series.

## Provider pinning

Every strict-comparability request uses a single allowed upstream provider and
disables fallback. The request preference is equivalent to:

```json
{
  "provider": {
    "only": ["PINNED_PROVIDER_SLUG"],
    "allow_fallbacks": false,
    "require_parameters": true,
    "data_collection": "deny"
  }
}
```

The concrete provider slug is stored in the private run manifest and the
sanitised provenance record. If `data_collection: deny` leaves no eligible
endpoint, the privacy and responsible-release leads must approve an alternative
before the run; it is not relaxed automatically.

Provider ordering without `only` is insufficient. OpenRouter load balancing,
fallback, and provider substitution must not determine the endpoint during a
strict run.

## Parameter contract

Each benchmark protocol declares:

- temperature;
- `top_p` and, if relevant and supported, `top_k`;
- maximum output tokens;
- seed or replicate identifier;
- stop sequences;
- tool availability;
- response-format requirement;
- system-message condition; and
- reasoning mode and effort.

`require_parameters` is enabled. Unsupported parameters are not silently
omitted. If an endpoint cannot honour a required parameter, it is excluded from
the strict-comparability analysis or evaluated under a separately named
condition.

The primary run follows the source benchmark's generation settings when they
can be reproduced across the selected panel. A lower-temperature sensitivity
condition may be added, but it is not pooled with the primary condition.

Seed support does not establish determinism. ATB records seeds and runs a common
multi-seed subset to estimate residual variability.

## Reasoning and model modes

Optional reasoning is explicitly enabled or disabled and logged. A model in
thinking mode and the same model in non-thinking mode are separate serving
conditions. If reasoning cannot be disabled, that model is shown in a distinct
facet rather than silently compared as if the conditions matched.

Hidden reasoning content is neither requested for publication nor treated as a
benchmark output. Usage metadata for reasoning tokens may be recorded where the
provider supplies it without exposing hidden content.

Text-only and multimodal conditions are likewise distinct. Wave 1 uses text-only
inputs and no tools.

## Message and prompt integrity

- The benchmark message array is generated from a versioned template.
- The exact rendered request has a content hash.
- Target prompts are not embedded in this public protocol.
- System messages are absent unless required by the benchmark or explicitly
  declared as an experimental condition.
- No jailbreak, obfuscation, tool call, browsing, or external side effect is used
  in Wave 1.
- Items are sent independently unless the benchmark explicitly requires a
  multi-turn conversation.
- Conversation state is never reused across unrelated items.

## Run ordering

The scheduler randomises model order within item blocks and item order within
strata. It avoids running one model family exclusively during a narrow time
window. Start and end canaries are used to detect route or parser changes during
long jobs.

Concurrency is capped conservatively to avoid provider instability. Rate limits
are treated as transport outcomes until a controlled retry succeeds.

## Retry policy

- No retry occurs for a completed generation, policy refusal, or provider block.
- Network timeouts, rate limits, and 5xx errors may receive at most two controlled
  retries.
- A retry uses the same model, provider restriction, request body, and replicate
  identifier.
- Every attempt is retained with timestamp, status, and returned route metadata.
- A successful retry does not erase the earlier failure.
- Fallback remains disabled during retries.

Persistent failure receives an explicit transport label. The item is not replaced
with a more convenient prompt.

## Response and route validation

For each attempt, record:

- run, protocol, benchmark, item, and replicate IDs;
- request timestamp and duration;
- requested model ID;
- returned canonical model ID;
- selected provider and endpoint;
- HTTP status and OpenRouter generation ID;
- sampling and reasoning settings;
- input, output, cached, and reasoning token counts where supplied;
- quantisation and context metadata where disclosed;
- finish reason;
- cost;
- transport outcome;
- response-content hash; and
- parser and judge versions.

The raw response body is stored only in the restricted tier. Public records
contain labels, hashes, aggregate metadata, and safe excerpts where permitted.

The following conditions fail route integrity:

- returned model mismatch;
- provider outside the allow-list;
- evidence of fallback;
- a required parameter omitted or transformed;
- unrecorded reasoning-mode change;
- unexplained context truncation;
- endpoint metadata changing during the run; or
- a canary response indicating a route revision.

Affected records are quarantined. They are not silently included in aggregates.

## Distinguishing model behaviour from transport behaviour

ATB uses separate fields for:

- `model_refusal`;
- `model_soft_refusal` or evasion;
- `provider_policy_block`;
- `transport_error`;
- `timeout`;
- `truncation`;
- `invalid_format`; and
- `judge_failure`.

A provider block is not scored as a model refusal. A transport error is not
scored as non-compliance. Both conditional-on-generation and all-attempt rates
are reported when infrastructure outcomes are non-trivial.

## Provider sensitivity

When two providers claim to serve the same exact checkpoint and honour the same
parameter contract, a prespecified subset may be run on both. This is a
deployment-sensitivity analysis, not a search for the provider with the desired
result.

Provider comparisons report quantisation, latency, error, block, and behavioural
differences. The primary provider is selected before target outputs are inspected.

## Prospective drift checks

A quarterly sentinel run repeats an unchanged item subset and serving condition.
Before it begins, the new model and endpoint inventories are compared with the
previous freeze. Any changed model slug, provider, quantisation, supported
parameter, context length, moderation field, or pricing field is surfaced.

If exact continuity cannot be established, the time series ends and a new
deployment condition begins. A line is not drawn across the break.

## Cost and stopping controls

The preregistration includes maximum calls, tokens, and spend. The runner stops
when:

- the budget cap is reached;
- route integrity fails;
- unexpected failure exceeds 5%;
- the returned model changes;
- restricted-data storage fails; or
- a responsible-release hold is raised.

Stopping for one of these reasons is logged. The sample is not selectively
extended based on an interim model score.

## Public provenance record

The public record for each aggregate includes:

```json
{
  "protocolVersion": "VERSION",
  "evaluationDate": "YYYY-MM-DD",
  "requestedModel": "EXACT_MODEL_ID",
  "returnedModel": "CANONICAL_MODEL_ID",
  "provider": "PINNED_PROVIDER_SLUG",
  "reasoningCondition": "DECLARED_MODE",
  "benchmarkVersion": "SOURCE_REVISION",
  "itemSetHash": "SHA256",
  "judgeVersion": "JUDGE_AND_PROMPT_HASH",
  "routeIntegrity": "pass-or-fail"
}
```

This example contains placeholders only. It is not a runnable request and does
not contain a credential or benchmark prompt.

## References

- [OpenRouter model metadata](https://openrouter.ai/docs/guides/overview/models)
- [Provider selection and routing](https://openrouter.ai/docs/guides/routing/provider-selection)
- [Router metadata](https://openrouter.ai/docs/guides/features/router-metadata)
- [Provider preferences](https://openrouter.ai/docs/client-sdks/python/components/providerpreferences)
