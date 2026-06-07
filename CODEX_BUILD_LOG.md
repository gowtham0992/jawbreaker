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
