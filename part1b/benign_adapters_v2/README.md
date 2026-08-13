# ERA Part 1B — bounded OSINT and transparent-persuasion adapters

This directory defines two independent LoRA interventions on a pinned open-weight
checkpoint:

- `transparent_persuasion`: evidence-grounded, transparent argumentation that
  includes a counterargument, uncertainty, and an autonomy-preserving next step;
- `public_osint`: synthesis of frozen public-source packets with explicit
  claim-to-source links, chronology, contradiction handling, and abstention.

The interventions are deliberately separate. They are never merged or stacked
in the confirmatory comparison. Neither dataset contains political or electoral
persuasion, targeting, private-person research, live retrieval, deception,
coercion, credential discovery, doxxing, or geolocation of people.

## Four-arm research design

| Arm | Intervention | Promotion status |
|---|---|---|
| B | pinned base checkpoint | reference |
| P | transparent-persuasion LoRA | eligible only after held-out gates |
| O | public-OSINT LoRA | eligible only after held-out gates |
| R | reversible refusal-direction intervention | diagnostic only; never deployment GO |

`P+R` and `O+R` are excluded from the primary study. If they are ever run,
they are separate exploratory interactions after B→P, B→O, and B→R are frozen.
The refusal intervention is not a training target and does not specialize OSINT
or persuasion.

## Model ladder

- engineering smoke: `Qwen/Qwen3-1.7B` at
  `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`;
- production candidate: `Qwen/Qwen3-8B` at
  `b968826d9c46dd6066d109eabc6255188de91218`.

Both are Apache-2.0 post-trained text models. A smoke result is operational
evidence only and cannot be pooled with the 8B outcome.

## Dataset and training contract

The training script deterministically constructs, validates, and hashes:

- 1,200 training examples from 12 scenario families;
- 150 validation examples from 3 disjoint families;
- a 300-case held-out manifest from 3 further families, never supplied to the
  trainer.

Each split is balanced English/Spanish. All packets are synthetic and fictional,
with source identifiers rather than live URLs. Production uses QLoRA (NF4,
BF16, rank 16, alpha 32, dropout 0.05, all linear layers), maximum length 2048,
learning rate 1e-4, and exactly 300 optimizer steps. Outputs, Trackio state,
manifests, and SHA-256 inventories are written to a fresh prefix in a private
Hugging Face Storage Bucket.

## GO semantics

`COMPLETE_TECHNICAL_ONLY` means the fixed Job completed, adapter state changed,
files survived read-back, and the receipt is internally hash-consistent. It is
not a scientific or deployment GO.

Scientific promotion requires three seeds, a frozen held-out evaluation,
blinded human comparison, and the gates in `protocol.json`. The R arm always
returns `DIAGNOSTIC_NO_GO_FOR_DEPLOYMENT`; its vector, raw safety outputs, and
operational detail remain controlled.

## Local validation

```bash
python part1b/benign_adapters_v2/jobs/train_lora.py \
  --adapter transparent_persuasion --phase production \
  --run-id local-validation --seed 17 --validate-only
python -m unittest discover -s part1b/benign_adapters_v2/tests -v
```

The remote script is submitted inline to Hugging Face Jobs. The repository path
is the auditable source; a local path is never assumed to exist in the remote
container.
