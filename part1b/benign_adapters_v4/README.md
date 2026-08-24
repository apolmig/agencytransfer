# ERA Part 1B — private-Hub benign adapters v4

Version 4 is a fresh, additive execution contract for the same two independent
benign interventions defined in v3:

- `transparent_persuasion`: transparent, evidence-grounded argumentation with
  a counterargument, uncertainty, and an autonomy-preserving next step;
- `public_osint`: synthesis of frozen fictional public-source packets with
  explicit citations, chronology, contradiction handling, and calibrated
  abstention.

V3 remains byte-for-byte historical. V4 rotates the authorization key and
payload schemas because the private key pinned for the planned v5 operation is
no longer recoverable. The v5 operation was never executed: no v5 write
canary, repository genesis, authorization, or training Job was submitted. Its
run ID and signing key are retired and must not be reused.

V4 accepts only `era-part1b-v6-ed25519-20260824`, whose Ed25519 SPKI DER
SHA-256 is
`630b86913170ffad4ce274d3f3f3958df150266821adea7b81a22bf6b2296dfa`.
There is no old-key fallback, dual-key acceptance, or migration path for an
already signed operation. Public payload, receipt, preflight, reservation,
canary, terminal, and operation schemas are all `/v4`.

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

The deterministic bilingual datasets remain byte-identical to v3: 1,200
training examples from 120 families, 150 validation examples from 15 disjoint
families, and 300 held-out examples from 30 further families. Held-out rows
are never supplied to TRL. Every family contains five English and five Spanish
variants spanning five templates.

## Authorization and single-use persistence

The runner accepts only a canonical authorization committed to the private
`apol/era-part1b-training-evidence` dataset at an exact revision. It verifies:

1. the inline authorization bytes, SHA-256, and persisted Hub bytes are identical;
2. an Ed25519 signature under the single v6 public key pinned in the runner;
3. the canonical `era-part1b-hf-operation/v4` bytes are persisted in the same
   Hub revision and match the signed operation path and SHA-256;
4. a maximum 24-hour validity window and exact script, protocol, runtime,
   control-Job, model, step, adapter, seed, and repository bindings;
5. the target is private and has the signed one-commit genesis, exact file
   tree, and exact file hashes.

Before importing Torch or downloading model weights, the Job atomically
commits `reservations/<slot_id>.json` with the authorized genesis as
`parent_commit`. A duplicate or replay loses that parent race before spending
GPU training time. A reserved slot is deliberately no-retry: a later failure
burns the slot and requires a new operation and repository.

The required successful CAS-bound commit sequence is:

`authorized genesis → Job reservation → adapter + receipt → terminal seal`

The runner verifies that exact newest-to-oldest commit-ID sequence, the exact
HEAD, and a successful `parent_commit` compare-and-swap at every write. Hub
1.24 does not expose parent edges in `GitCommitInfo`, so this is not presented
as an independent proof of Git graph linearity.

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

## Fresh v6 operation

The controlled plane must choose a new `era-p1b-v6-...` run ID, nonce,
authorization window, and two previously unused private repositories:

- `apol/<v6-run-id>-transparent-persuasion-qwen3-8b-lora`;
- `apol/<v6-run-id>-public-osint-qwen3-8b-lora`.

Each repository must already exist, be private, and contain only the
producer-created genesis before authorization. The public runner never creates
a repository. The non-executed v5 operation and all earlier quarantined
operations remain ineligible for submission.

## Reproducible public bytes

The repository pins LF endings for the v4 method and its workflow. CI rejects
carriage returns, invalid UTF-8, or a missing final newline in the five
authoritative public artifacts:

- `jobs/train_lora.py`;
- `jobs/ml_stack_preflight.py`;
- `protocol.json`;
- `requirements.lock`;
- `tests/test_contract.py`.

All operation hashes are SHA-256 over the checked-out LF bytes. Consumers must
not hash a platform-converted copy.

## Validation and remote submission contract

```bash
python part1b/benign_adapters_v4/jobs/train_lora.py \
  --adapter transparent_persuasion --phase production \
  --run-id era-p1b-v6-validation --seed 17 --validate-only
python -m unittest discover -s part1b/benign_adapters_v4/tests -v
```

The script must be submitted through the controlled physical-file launcher
with flavor `l4x1`, a training-sized timeout, no volume mount, and only the
encrypted `HF_TOKEN` secret. The launcher carries a deterministic gzip/base64
encoding of the exact script, writes it to a fixed private `/tmp` path,
checks the decompressed SHA-256 before execution, and invokes `uv run` on that
physical file. Remote arguments additionally include the exact target repo,
authorization base64, authorization SHA-256, authorization revision, and
operation SHA-256. Tokens and private signing material must never appear in
arguments, logs, source, or Git.

Before GPU submission, `jobs/ml_stack_preflight.py` runs on `cpu-basic`. It
verifies every dependency pin, the rotated Ed25519 public key, the
parent-bound Hub commit API surface, the QLoRA/TRL contract, and Qwen's
non-thinking chat rendering without loading model weights or writing to the
Hub.

`COMPLETE_TECHNICAL_ONLY` proves only that an authorized Job trained,
persisted, read back, reloaded, and sealed its adapter. It is not scientific,
deployment, SOTA, real-world persuasion, political-manipulation, or general
lowering-of-access evidence. Scientific promotion still requires three seeds
and the held-out gates in `protocol.json`. The refusal-direction arm remains
separate, private, reversible, and permanently
`DIAGNOSTIC_NO_GO_FOR_DEPLOYMENT`.
