# Jawbreaker Training

This folder contains the OpenBMB MiniCPM fine-tuning path for Jawbreaker.

The goal is not to make a general scam chatbot. The target behavior is narrow:

1. Read one suspicious message.
2. Return valid JSON matching Jawbreaker's schema.
3. Avoid dangerous false negatives.
4. Avoid calling normal messages dangerous.
5. Recommend a safe verification path.

## Generate Data

The generated data is synthetic and deterministic. It avoids private messages and keeps links on `.example` domains.

```bash
python3 training/generate_jawbreaker_data.py
```

Default outputs:

- `training/data/train.jsonl`
- `training/data/dev.jsonl`
- `training/data/test.jsonl`
- `eval/generated_eval.jsonl`

## Evaluate Baseline MiniCPM

```bash
python3 eval/run_eval.py \
  --backend transformers \
  --model-id openbmb/MiniCPM4.1-8B \
  --trust-remote-code \
  --dataset eval/generated_eval.jsonl \
  --predictions-out eval/predictions/minicpm4_1_8b_generated.jsonl \
  --json-out eval/reports/minicpm4_1_8b_generated.json
```

For quick smoke tests:

```bash
python3 eval/run_eval.py \
  --backend transformers \
  --model-id openbmb/MiniCPM4.1-8B \
  --trust-remote-code \
  --dataset eval/generated_eval.jsonl \
  --limit 10
```

## Fine-Tune LoRA

Install training-only dependencies outside the Space runtime:

```bash
pip install -r requirements-train.txt
```

Run a short LoRA training pass:

```bash
python3 training/train_lora.py \
  --model-id openbmb/MiniCPM4.1-8B \
  --train-file training/data/train.jsonl \
  --dev-file training/data/dev.jsonl \
  --output-dir training/output/jawbreaker-minicpm-lora
```

To publish the adapter for the Well-Tuned badge:

```bash
python3 training/train_lora.py \
  --model-id openbmb/MiniCPM4.1-8B \
  --output-dir training/output/jawbreaker-minicpm-lora \
  --push-to-hub \
  --hub-model-id gowtham0992/jawbreaker-minicpm-lora
```

## Deployment Decision Rule

Use the fine-tuned adapter only if it beats the base model on:

- valid JSON rate
- zero dangerous-as-safe misses
- lower false alarms on safe messages
- safe action compliance
- acceptable Space latency

If the adapter improves JSON but hurts safety, do not deploy it.
