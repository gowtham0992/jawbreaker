# OpenAI Codex Judge Evidence

This file is a compact evidence map for the OpenAI/Codex track. It is meant to make the Codex contribution auditable from the public repository without relying on private chat logs.

## What Codex Contributed

Codex materially contributed across the product, model, eval, and submission surface:

- App runtime and UI: `app.py`, `style.css`, `jawbreaker/render.py`
- Scam analysis contract: `jawbreaker/schema.py`, `jawbreaker/analyzers.py`, `jawbreaker/prompt.py`
- Safety guard and schema repair: `jawbreaker/analyzers.py`, `tests/test_app_guard.py`, `tests/test_schema.py`
- Eval harness: `eval/run_eval.py`, `eval/README.md`, `eval/reports/`
- Modal training/eval workflow: `training/train_lora.py`, `training/modal_train.py`, `training/modal_eval.py`
- Data generation/calibration: `training/generate_jawbreaker_data.py`, `training/generate_v3_data.py`, `training/generate_v4_data.py`, `training/generate_v5_data.py`, `training/generate_v6_data.py`, `training/generate_v7_data.py`, `training/generate_v8_data.py`
- Public evidence packaging: `README.md`, `MODEL_CARD_MINICPM5_LORA_V8.md`, `CODEX_BUILD_LOG.md`, `AGENT_TRACE.md`, `FIELD_NOTES.md`, `HONEST_SUBMISSION.md`

## Commit Evidence

Recent Codex-attributed commits include:

| Commit | Evidence |
| --- | --- |
| `28030af` | Adds the final MiniCPM5-1B LoRA v8 model card. |
| `f468585` | Promotes v8 as the final safety-calibrated model and commits the 632-case report. |
| `7a67ead` | Covers indirect wrong-number investment grooming guard gaps. |
| `7b5bbb2` | Calibrates wrong-number investment guard behavior. |
| `74617f3` | Tightens safety guard calibration for benign family/school messages. |
| `1b67b5e` | Adds v8 failure-driven calibration data. |
| `d5215ed` | Extends Modal eval timeout for larger guarded evals. |
| `3407348` | Adds fresh public-pattern calibration data. |
| `05e76bd` | Publishes the custom kitchen-table UI. |

Each listed commit includes:

```text
Co-authored-by: Codex <codex@openai.com>
```

## Final Model Decision

Final judged model:

- Base: `openbmb/MiniCPM5-1B`
- Adapter: `build-small-hackathon/jawbreaker-minicpm5-1b-lora-v8`
- Live app: https://huggingface.co/spaces/build-small-hackathon/jawbreaker
- Model card: https://huggingface.co/build-small-hackathon/jawbreaker-minicpm5-1b-lora-v8
- Dataset/eval bundle: https://huggingface.co/datasets/build-small-hackathon/jawbreaker-scam-defense-data

Final guarded Modal eval:

- Suite: `eval/hard_v8_eval.jsonl`
- Report: `eval/reports/jawbreaker-minicpm5-1b-lora-v8-hard632-safetyguard-v4.json`
- Cases: `632`
- Risk accuracy: `579/632` (`91.61%`)
- Scam type accuracy: `561/632` (`88.77%`)
- Mean tactic recall: `90.69%`
- Dangerous as safe: `0`
- Dangerous as needs-check: `0`
- Safe as dangerous or suspicious: `0`
- Unsafe action violations: `0`
- Invalid predictions: `0`
- Model errors: `0`

## Why This Matters For Codex Judging

The Codex contribution was not limited to boilerplate. Codex helped create the core engineering loop:

1. Build a working Gradio/Gradio Server scam-defense app.
2. Define a strict JSON contract for the small model.
3. Generate and publish synthetic/sanitized training and eval data.
4. Train and evaluate MiniCPM LoRA adapters through Modal.
5. Identify failure modes from eval output.
6. Add targeted calibration data and deterministic safety guards.
7. Re-run hard evals and promote the safer model.
8. Package the final app, model, dataset, collection, model card, and README evidence.

## Local Verification

Useful checks:

```bash
git log --format=full --grep='Co-authored-by: Codex'
python3 -m pytest tests/test_app_guard.py tests/test_schema.py tests/test_eval_dataset.py
python3 -m json.tool eval/reports/jawbreaker-minicpm5-1b-lora-v8-hard632-safetyguard-v4.json
```

The public repository, Space, model card, dataset, and collection are the intended judge-facing evidence. Private chat transcripts are not required to verify the build.
