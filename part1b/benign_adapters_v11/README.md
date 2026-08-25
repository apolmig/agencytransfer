# ERA Part 1B — private-Hub benign adapters v11

Version 11 is a fresh, additive execution contract for the same two independent
benign interventions retained by v7:

- `transparent_persuasion`: transparent, evidence-grounded argumentation with
  a counterargument, uncertainty, and an autonomy-preserving next step;
- `public_osint`: synthesis of frozen fictional public-source packets with
  explicit citations, chronology, contradiction handling, and calibrated
  abstention.

V10 is permanently quarantined. Its only operational role, write canary C10,
ran once as provider Job `6a8dc9f445686a1580c082eb` and terminated `ERROR`.
The evidence dataset's protected default branch rejected its direct commit
with HTTP 403 and explicitly required `create_pr=1`. The commit was rejected
before any Hub byte changed: the V10 namespace stayed empty, the evidence HEAD
stayed at `287709b5a28e25d0ffceb3675d3c436666721841`, neither target repository
existed, and no training occurred. The single C10 attempt and the complete V10
identity remain consumed under sticky `NO_GO_NO_RETRY`.

V11 preserves the v7 datasets, adapter behavior, dependency lock, QLoRA
contract, and Trainer-owned Trackio lifecycle. It rotates the complete v11
lineage and accepts only
`era-part1b-v11-ed25519-20260825`, whose Ed25519 SPKI is
`MCowBQYDK2VwAyEAd3QI5REl5a+wiMYZKy1ioRTynASsTR6M6ExF8TD+UFk=` and whose
DER SHA-256 is
`34d786014440935c16f57b2f1ad9e8c6b367199ccbb5ecd6ab0a8335a88a9494`.
There is no old-key fallback, dual-key acceptance, or migration path for an
already signed operation. Public payload, receipt, preflight, reservation,
canary, terminal, authorization, and operation schemas are all `/v11`. The
strict private producer identity and intent consumed by the runner are `/v11`.

The two adapters are never merged, stacked, trained in the same Job, or stored
in the same repository. Neither dataset contains political or electoral
persuasion, targeting, live retrieval, real-person research, deception,
coercion, credential discovery, doxxing, or personal geolocation. The OSINT
intervention is source-discipline training on synthetic frozen packets, not a
live collection agent.

## Frozen training contract

Production remains `Qwen/Qwen3-8B` at revision
`b968826d9c46dd6066d109eabc6255188de91218`. Each Job uses QLoRA with NF4
double quantization, BF16, rank 16, alpha 32, dropout 0.05, the seven Qwen
attention/MLP projections, maximum length 2048, learning rate 1e-4, and
exactly 300 optimizer steps on `l4x1`.

The deterministic bilingual datasets remain byte-identical to v4: 1,200
training examples from 120 families, 150 validation examples from 15 disjoint
families, and 300 held-out examples from 30 further families. Held-out rows
are never supplied to TRL. Every family contains five English and five Spanish
variants spanning five templates.

## Authorization and five-commit persistence

The runner accepts only a canonical authorization committed to the private
`apol/era-part1b-training-evidence` dataset at an exact revision. It verifies:

1. the inline authorization bytes, SHA-256, and persisted Hub bytes are identical;
2. an Ed25519 signature under the single v11 public key pinned in the runner;
3. the canonical `era-part1b-hf-operation/v11` bytes are persisted in the same
   Hub revision and match the signed operation path, SHA-256, and evidence PR
   ref `refs/pr/N`;
4. the signed control-repository and producer objects duplicate the exact
   `producer-intent.json` path, revision, and SHA-256; the signed-hash-bound
   identity repeats that triple, and both identity and intent are strict
   canonical JSON read from their exact private revisions;
5. the newest evidence history is physically ordered as authorization,
   identity, producer intent, and write canary, with exact per-commit inventory
   deltas; the fixed prior-run quarantine remains present, 10,060 bytes long,
   and hash-identical at both the canary and identity revisions;
6. a maximum 24-hour validity window and exact script, protocol, runtime,
   control-Job, model, step, adapter, seed, and repository bindings;
7. an exact private provider root whose complete tree is only `.gitattributes`,
   with its signed revision, byte size, and SHA-256;
8. an exact controlled identity head whose complete tree is `.gitattributes`
   plus `bootstrap/slot-identity.json`, with its separately signed revision and
   hashes, and whose `.gitattributes` bytes are unchanged from the root;
9. an exact initial physical history ordered as controlled identity then
   provider root.

Before importing Torch or downloading model weights, the Job atomically
commits `reservations/<slot_id>.json` with the controlled identity revision as
`parent_commit`. A duplicate or replay loses that parent race before spending
GPU training time. A reserved slot is deliberately no-retry: a later failure
burns the slot and requires a new operation and repository.

The required successful CAS-bound physical sequence is exactly five commits:

`provider root → controlled identity → Job reservation → adapter + receipt → terminal seal`

The runner verifies the exact newest-to-oldest sequence after every write, the
exact HEAD, and a successful `parent_commit` compare-and-swap. Hugging Face Hub
1.24 does not expose parent edges in `GitCommitInfo`, so the ordered commit-ID
inventory is not presented as an independent proof of Git graph linearity.
The producer and runner nevertheless bind every controlled write to its exact
expected parent.

The artifact commit is one explicit `create_commit` containing every sorted
path. The model payload is exactly `adapter_model.safetensors`,
`adapter_config.json`, and `README.md`; Trainer state, pickles, tokenizer
copies, checkpoints, and full base-model weights are rejected. The
safetensors header must contain exactly the 504 FP32 LoRA A/B tensors implied
by the pinned 36-layer Qwen3-8B architecture, with exact names, shapes,
offsets, and no base weights. The adapter config and model card both bind the
immutable base-model revision.

The runner reads every uploaded file by exact revision, verifies the lineage
hashes, discards the in-memory trained model, reloads the LoRA from the private
Hub over the pinned base checkpoint, and repeats a deterministic canary. The
terminal seal is a final exact-parent commit and must be repository HEAD.

Only an encrypted Job secret named `HF_TOKEN` is passed to a training Job. Its
value must be an explicit, isolated, least-privilege fine-grained token
authorized for the evidence dataset and the two run-specific private model
repositories. It must not use the connector's read-only OAuth placeholder.
The value never appears in arguments, environment configuration committed to
source, logs, or Git. The Ed25519 private key is never present in the runner,
target repositories, or training Job.

The prior-run quarantine binding is the closed object
`{"path":"runs/era-p1b-v10-20260825t153000z/control/quarantine.json","sha256":"bb10f40b537e622b7a7a007d3f570c4743fa7eee7eb7a3b0673a7e9234ee3311","size_bytes":10060}`.

The first V11 evidence write uses `create_pr=True` against the exact protected
default-branch parent. Its returned `refs/pr/N` is persisted in the canary,
producer intent, identity, operation, and signed authorization. Every later
evidence write uses that same ref plus an exact `parent_commit`; the runner
requires the signed ref to point to the authorization revision. The default
branch and a later PR merge are not execution authority.

## Fresh v11 operation

The controlled plane uses the fresh run ID
`era-p1b-v11-20260825t171000z`, nonce
`4302fb67ad91d52264ae3487770b2762`, a new authorization window, and two
previously unused private repositories:

- `apol/era-p1b-v11-20260825t171000z-transparent-persuasion-qwen3-8b-lora`;
- `apol/era-p1b-v11-20260825t171000z-public-osint-qwen3-8b-lora`.

Each repository must already exist, be private, and have exactly the provider
root followed by the producer-created controlled identity before
authorization. The public runner never creates a repository. V10 and all
earlier quarantined operations remain ineligible for submission.

## Reproducible public bytes

The repository pins LF endings for the v11 method and its workflows. CI rejects
carriage returns, invalid UTF-8, or a missing final newline in the eight
authoritative public artifacts:

- `.dockerignore`;
- `jobs/train_lora.py`;
- `jobs/ml_stack_preflight.py`;
- `protocol.json`;
- `requirements.lock`;
- `runtime-reuse.json`;
- `runtime/Dockerfile`;
- `tests/test_contract.py`.

All operation hashes are SHA-256 over the checked-out LF bytes. Consumers must
not hash a platform-converted copy.

V11 deliberately does not build or smoke a new image. It reuses the already
smoked, dependency-only V10 image
`ghcr.io/apolmig/agencytransfer-part1b-benign-v10-runtime@sha256:97d631c79c40bf2f10a3dce5f300fc7d0570a783916592555e67a1aed52d7289`.
The lock, Dockerfile, and `.dockerignore` remain byte-identical to V10; no
public runner or preflight source is embedded in that image. The exact image,
linux/amd64 manifest, attestation, public merge, and completed smoke Job
`6a8dc027984507d9db4e435c` are frozen in `runtime-reuse.json`. There is no V11
runtime publish workflow, moving V11 tag, or additional smoke authorization.

## Validation and remote submission contract

```bash
python part1b/benign_adapters_v11/jobs/train_lora.py \
  --adapter transparent_persuasion --phase production \
  --run-id era-p1b-v11-validation --seed 17 --validate-only
python -m unittest discover -s part1b/benign_adapters_v11/tests -v
```

The script must be submitted through the controlled physical-file launcher
with flavor `l4x1`, a raw timeout of exactly 5,400 seconds, no volume mount, and only the
encrypted `HF_TOKEN` secret. The launcher carries a deterministic gzip/base64
encoding of the exact script, writes it to a fixed private `/tmp` path,
checks the decompressed SHA-256 before execution, and invokes the preinstalled
`/opt/era-venv/bin/python` on that physical file. Remote arguments additionally include the exact target repo,
authorization base64, authorization SHA-256, authorization revision, and
operation SHA-256. Tokens and private signing material must never appear in
arguments, logs, source, or Git.

The cumulative program cap is 6,000,000 micro-USD. The conservative prior is
3,219,302 micro-USD across 26 Jobs, including the dependency-image smokes and
the fully budgeted failed C10 attempt. Fresh v11 authorization allowance is 2,435,190 micro-USD:
up to seven 30-minute CPU control Jobs at 167 micro-USD per billed minute and
two 90-minute `l4x1` Jobs at 13,334 micro-USD per billed minute. The resulting
worst-case cumulative total is 5,654,492 micro-USD, leaving 345,508 micro-USD
of margin. No retry is authorized.

Before GPU submission, `jobs/ml_stack_preflight.py` runs on `cpu-basic`. It
verifies every dependency pin, the rotated Ed25519 public key, the
parent-bound Hub commit API surface, the QLoRA/TRL contract, and Qwen's
non-thinking chat rendering without loading model weights or writing to the
Hub. It also selects the real Trackio reporter and inspects the frozen
Transformers and Trackio lifecycle: the Trainer callback owns `finish`, and
any post-training callback or evaluation is forbidden.

`COMPLETE_TECHNICAL_ONLY` proves only that an authorized Job trained,
persisted, read back, reloaded, and sealed its adapter. It is not scientific,
deployment, SOTA, real-world persuasion, political-manipulation, or general
lowering-of-access evidence. Scientific promotion still requires three seeds
and the held-out gates in `protocol.json`. The refusal-direction arm remains
separate, private, reversible, and permanently
`DIAGNOSTIC_NO_GO_FOR_DEPLOYMENT`.
