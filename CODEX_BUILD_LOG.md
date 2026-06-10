# Codex Build Log

This log records how OpenAI Codex is used during the Build Small Hackathon project.

## 2026-06-05

Codex helped:

- read and summarize the hackathon rules, kickoff notes, sponsor requirements, and Discord guidance
- evaluate the Jawbreaker concept against Backyard AI judging criteria
- create the initial Gradio Space scaffold
- create the public GitHub repo structure
- create the Hugging Face Space structure
- add initial eval and test scaffolding
- document submission requirements and badge strategy

Repository evidence:

- GitHub repo: https://github.com/gowtham0992/jawbreaker
- Hugging Face Space: https://huggingface.co/spaces/build-small-hackathon/jawbreaker

Going forward, meaningful build commits should include a Codex co-author trailer in the Git commit message.

## Eval Spine

Codex helped expand the initial seed eval into a 100-case labeled dataset and upgraded the runner to report risk accuracy, scam-type accuracy, tactic recall, dangerous misses, safe-message false alarms, unsafe action violations, and category-level performance.

Codex then made the eval runner backend-aware so the same 100 cases can score the heuristic stub, saved JSONL predictions, or local GGUF models through `llama-cpp-python`.

## Runtime Pivots

Codex helped compare the practical runtime paths and move the deployed app to Transformers on ZeroGPU with `Qwen/Qwen3-0.6B`.

The local GGUF/llama.cpp path remains in the repo for eval and local experimentation, but the judge-facing Space uses ZeroGPU because first-click cold-start latency is part of the product experience.

Follow-up hardening included:

- strict JSON parsing and validation
- Qwen thinking-token suppression/stripping
- deterministic heuristic guardrails for obvious scam danger
- hidden model warmup on Space load
- Gradio loading and dark-mode fixes for a stable demo surface

Codex then helped pivot the deployed default to `openbmb/MiniCPM4.1-8B` for OpenBMB sponsor eligibility. The app now exposes `JAWBREAKER_TRUST_REMOTE_CODE` so MiniCPM can load through Transformers while keeping the Qwen default available as an environment-variable fallback if Space latency becomes unacceptable.

## Training Spine

Codex added a deterministic synthetic data generator, a generated holdout eval set, a Transformers eval backend, and a PEFT/LoRA training script for MiniCPM.

The deployed app also now falls back to deterministic scam analysis when model inference fails or returns malformed JSON, preventing the user-facing "could not analyze" state from becoming the main demo experience.

## MiniCPM LoRA v3

Codex helped build a contrastive hard-case training pass after v2 under-called some dangerous scams as `needs_check`.

The v3 path added:

- `training/generate_v3_data.py` for targeted package, bank, tech-support, prize, job, family, marketplace, and safe/legitimate contrast cases
- Modal A100 training with `openbmb/MiniCPM4.1-8B`
- published adapter `build-small-hackathon/jawbreaker-minicpm-lora-v3`
- Modal eval launcher for scoring the published adapter

Measured results:

- 100-case product eval: `90/100` risk accuracy, `0` dangerous undercalls, `0` invalid predictions, `0` model errors
- 215-case hard eval: `210/215` risk accuracy (`97.7%`), `0` dangerous-as-safe, `0` dangerous-as-needs-check, `0` safe-as-dangerous-or-suspicious, `0` unsafe action violations, `0` invalid predictions, `0` model errors

## MiniCPM5-1B LoRA v4

Codex helped turn the Tiny Titan experiment into the first strong MiniCPM5-1B production candidate.

The v4 path was:

- Base model: `openbmb/MiniCPM5-1B`
- Adapter: `build-small-hackathon/jawbreaker-minicpm5-1b-lora-v4`
- Runtime: Transformers on ZeroGPU
- Training and eval: Modal

The completed hard guarded eval evidence:

- 394 cases
- `96.19%` risk accuracy
- `96.19%` scam type accuracy
- `96.55%` mean tactic recall
- `0` dangerous-as-safe
- `0` dangerous-as-needs-check
- `0` suspicious-as-safe
- `0` unsafe action violations
- `0` invalid predictions
- `0` model errors

Codex also helped add the committed eval reports under `eval/reports/`, update the Space and GitHub code defaults, and keep the Hugging Face Space history separate from GitHub history through cherry-picked Space sync commits.

## MiniCPM5-1B LoRA v8

Codex helped extend the 1B path after fresh scam-pattern evals exposed two failure modes:

- wrong-number crypto / gold / trading grooming could be softened below `dangerous`
- ordinary family, school, pharmacy, and logistics messages could be over-called

The v8 path added:

- `training/generate_v7_data.py` and `training/generate_v8_data.py` for fresh public-pattern and failure-driven calibration
- `training/data/train_v8.jsonl`, `dev_v8.jsonl`, and `test_v8.jsonl`
- `eval/hard_v8_eval.jsonl`
- safety-guard calibration for wrong-number investment grooming
- regression tests in `tests/test_app_guard.py`
- the final report `eval/reports/jawbreaker-minicpm5-1b-lora-v8-hard632-safetyguard-v4.json`
- `MODEL_CARD_MINICPM5_LORA_V8.md`
- `CODEX_JUDGE_EVIDENCE.md`

The final deployed path is:

- Base model: `openbmb/MiniCPM5-1B`
- Adapter: `build-small-hackathon/jawbreaker-minicpm5-1b-lora-v8`
- Runtime: Transformers on ZeroGPU
- Training and eval: Modal A100

The completed hard guarded eval evidence:

- 632 cases
- `91.61%` risk accuracy
- `88.77%` scam type accuracy
- `90.69%` mean tactic recall
- `0` dangerous-as-safe
- `0` dangerous-as-needs-check
- `0` safe-as-dangerous-or-suspicious
- `0` unsafe action violations
- `0` invalid predictions
- `0` model errors

Codex also helped update the Space README, model card, dataset card, collection notes, and public documentation so v8 is presented as the final judged model and v4 is retained as comparison evidence.
