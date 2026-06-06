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

## Current Runtime Decision

The deployed Space uses `openbmb/MiniCPM4.1-8B` through Transformers on ZeroGPU to make OpenBMB MiniCPM central to the app.

The GGUF / `llama-cpp-python` path remains available for local eval and badge evidence, but it is not the primary live demo path. The live app also uses a deterministic heuristic guard so an obvious high-risk scam is not rendered as safe if the small model under-calls the risk.

If MiniCPM Space latency is unacceptable during final demo testing, `Qwen/Qwen3-0.6B` remains the fallback via `JAWBREAKER_TRANSFORMERS_MODEL_ID`.

## Running Backends

Heuristic baseline:

```bash
python3 eval/run_eval.py --backend heuristic
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
