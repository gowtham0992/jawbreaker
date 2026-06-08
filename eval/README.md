# Jawbreaker Eval Set

`scam_eval.jsonl` is the project compass for model selection.

The first version contains 100 synthetic/sanitized examples across:

- dangerous scams
- suspicious messages
- legitimate messages that still need verification
- safe benign messages

Primary metrics:

- valid structured output
- exact risk-level match
- dangerous scams mislabeled as safe
- safe messages mislabeled as dangerous or suspicious
- action safety
- tactic recall
- latency

The eval intentionally includes legitimate alerts and ordinary messages. A scam detector that calls everything dangerous is not useful for the person Jawbreaker is built to protect.

There is also a generated holdout set:

```bash
python3 training/generate_jawbreaker_data.py
python3 eval/run_eval.py --dataset eval/generated_eval.jsonl --backend heuristic
```

The generated set is for scale and regression pressure. The 100-case hand-curated set remains the product compass.

## Current Runtime Decision

The deployed Space uses `openbmb/MiniCPM5-1B` through Transformers on ZeroGPU with the published adapter `build-small-hackathon/jawbreaker-minicpm5-1b-lora-v4`.

The GGUF / `llama-cpp-python` path remains available for local eval and badge evidence, but it is not the primary live demo path. The live app also uses a deterministic heuristic guard so an obvious high-risk scam is not rendered as safe if the small model under-calls the risk.

If MiniCPM Space latency is unacceptable during final demo testing, `Qwen/Qwen3-0.6B` remains the fallback via `JAWBREAKER_TRANSFORMERS_MODEL_ID`, but the current judged model path is MiniCPM5-1B LoRA v4.

## Current Results

MiniCPM5-1B LoRA v4:

- Adapter: `build-small-hackathon/jawbreaker-minicpm5-1b-lora-v4`
- 394-case hard guarded eval: `379/394` risk accuracy (`96.19%`), `0` dangerous-as-safe, `0` dangerous-as-needs-check, `0` suspicious-as-safe, `0` unsafe action violations, `0` invalid predictions, `0` model errors
- 320-case hard guarded eval: `310/320` risk accuracy (`96.88%`), `0` dangerous-as-safe, `0` dangerous-as-needs-check, `0` suspicious-as-safe, `0` unsafe action violations, `0` invalid predictions, `0` model errors

## Running Backends

Heuristic baseline:

```bash
python3 eval/run_eval.py --backend heuristic
```

OpenBMB MiniCPM through Transformers:

```bash
python3 eval/run_eval.py \
  --backend transformers \
  --model-id openbmb/MiniCPM5-1B \
  --trust-remote-code \
  --dataset eval/generated_eval.jsonl
```

Published v4 adapter through Transformers:

```bash
python3 eval/run_eval.py \
  --backend transformers \
  --model-id openbmb/MiniCPM5-1B \
  --adapter-id build-small-hackathon/jawbreaker-minicpm5-1b-lora-v4 \
  --trust-remote-code \
  --attn-implementation eager \
  --dataset eval/hard_v5_eval.jsonl
```

Saved prediction replay:

```bash
python3 eval/run_eval.py --backend predictions --predictions eval/predictions/model.jsonl
```

Local GGUF model through `llama-cpp-python`:

```bash
python3 eval/run_eval.py \
  --backend llama-cpp \
  --model-path models/model.gguf \
  --predictions-out eval/predictions/model.jsonl \
  --json-out eval/reports/model.json
```
