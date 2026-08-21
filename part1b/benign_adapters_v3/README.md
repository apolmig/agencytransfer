# ERA Part 1B — private-Hub benign adapters v3

The current immutable execution revision accepts only the signing key
`era-part1b-v4-ed25519-20260814`, which is deliberately retained for the fresh
v5 recovery because the key was not implicated in the v4 control failure.
Payload and receipt schemas remain v3; no old-key fallback or dual-key
acceptance exists. Earlier public commits preserve the abandoned v3 and
quarantined v4 execution bytes.

Version 3 is an additive persistence path for the same two independent
interventions defined in v2:

- `transparent_persuasion`: transparent, evidence-grounded argumentation with
  a counterargument, uncertainty, and an autonomy-preserving next step;
- `public_osint`: synthesis of frozen fictional public-source packets with
  explicit citations, chronology, contradiction handling, and calibrated
  abstention.

V2 remains unchanged. V3 removes the Storage Bucket dependency: each GPU Job
writes one LoRA directly to one pre-existing, run-specific, private Hugging
Face model repository. The two adapters are never merged, stacked, or trained
in the same Job or repository.

Neither dataset contains political or electoral persuasion, targeting, live
retrieval, real-person research, deception, coercion, credential discovery,
doxxing, or personal geolocation. The OSINT intervention is source-discipline
training on synthetic frozen packets, not a live collection agent.

## Frozen training contract

Production is `Qwen/Qwen3-8B` at revision
`b968826d9c46dd6066d109eabc6255188de91218`. Each Job uses QLoRA with NF4
double quantization, BF16, rank 16, alpha 32, dropout 0.05, the seven Qwen
attention/MLP projections, maximum length 2048, learning rate 1e-4, and
exactly 300 optimizer steps on `l4x1`.

The deterministic bilingual dataset remains byte-identical to v2: 1,200
training examples from 120 families, 150 validation examples from 15 disjoint
families, and 300 held-out examples from 30 further families. Held-out rows are
never supplied to TRL. Every family contains five English and five Spanish
variants spanning five templates.

## Authorization and single-use persistence

The runner accepts only a canonical authorization committed to the private
`apol/era-part1b-training-evidence` dataset at an exact revision. It verifies:

1. the inline authorization bytes, SHA-256, and persisted Hub bytes are identical;
2. an Ed25519 signature under the public key pinned in the runner;
3. the canonical operation bytes are persisted in the same Hub revision and
   match the signed operation path and SHA-256;
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
copies, checkpoints, and full base-model weights are rejected. The safetensors
header must contain exactly the 504 FP32 LoRA A/B tensors implied by the pinned
36-layer Qwen3-8B architecture, with exact names, shapes, offsets, and no base
weights. The adapter config and model card both bind the immutable base-model
revision. The runner then
reads every uploaded file by exact revision, verifies the lineage hashes,
discards the in-memory trained model, reloads the LoRA from the private Hub over
the pinned base checkpoint, and repeats a deterministic canary. The terminal
seal is a final exact-parent commit and must be repository HEAD.

Only an encrypted Job secret named `HF_TOKEN` is passed to a training Job. Its
value must be the explicit, isolated, least-privilege fine-grained token
authorized for the evidence dataset and the two target model repositories. It
must not use the connector's `$HF_TOKEN` OAuth placeholder, which is read-only.
The value never appears in arguments, environment configuration committed to
source, logs, or Git. The Ed25519 private key is never present in the runner,
target repositories, or training Job.

## Expected run-specific repositories

The v4 operation `era-p1b-v4-20260814t030306z` is quarantined and must never
be resubmitted. For the fresh operation `era-p1b-v5-20260814t034404z`, the
controlled plane uses:

- `apol/era-p1b-v5-20260814t034404z-transparent-persuasion-qwen3-8b-lora`;
- `apol/era-p1b-v5-20260814t034404z-public-osint-qwen3-8b-lora`.

They must already exist, be private, and contain only the producer-created
genesis before authorization. The public runner never creates a repository.

## Validation and remote submission contract

```bash
python part1b/benign_adapters_v3/jobs/train_lora.py \
  --adapter transparent_persuasion --phase production \
  --run-id era-p1b-v5-20260814t034404z --seed 17 --validate-only
python -m unittest discover -s part1b/benign_adapters_v3/tests -v
```

The script must be submitted through the controlled Docker `run` launcher with
flavor `l4x1`, a training-sized timeout, no volume mount, and an encrypted
`HF_TOKEN` secret whose value comes from the separately stored fine-grained
write token. The launcher carries a deterministic gzip/base64 encoding of the
exact script, writes it to a fixed private `/tmp` path, checks the decompressed
SHA-256 before execution, and then invokes `uv run` on that physical file. This
is required because the MCP inline-stdin form does not define `__file__` and a
plain uncompressed command approaches the kernel single-argument size limit.
Do not use the read-only OAuth placeholder for a write-stage Job. Remote arguments additionally include
the exact target repo, authorization base64, authorization SHA-256,
authorization revision, and operation SHA-256. Do not place a token value in
arguments, logs, source, or Git.

Before GPU submission, `jobs/ml_stack_preflight.py` runs on `cpu-basic`. It
verifies every dependency pin, the pinned Ed25519 key, the parent-bound Hub
commit API surface, the QLoRA/TRL contract, and Qwen's non-thinking chat
rendering without loading model weights or writing to the Hub.

`COMPLETE_TECHNICAL_ONLY` proves the authorized Job trained, persisted, read
back, reloaded, and sealed its adapter. It is not scientific, deployment, SOTA,
real-world persuasion, political-manipulation, or general lowering-of-access
evidence. Scientific promotion still requires three seeds and the held-out
gates in `protocol.json`. The refusal-direction arm remains separate, private,
reversible, and permanently `DIAGNOSTIC_NO_GO_FOR_DEPLOYMENT`.
