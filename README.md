---
title: Jawbreaker
sdk: gradio
sdk_version: 6.16.0
python_version: 3.12
app_file: app.py
emoji: 🍬
colorFrom: yellow
colorTo: red
license: mit
short_description: Local-first scam defense for someone you love.
tags:
  - gradio
  - build-small-hackathon
  - backyard-ai
  - openbmb
  - minicpm
  - local-first
  - llama-cpp
  - zerogpu
---

<p align="center">
  <img src="jawbreaker_logo.png" alt="Jawbreaker logo" width="160" />
</p>

# Jawbreaker

Scam defense for someone you love.

Jawbreaker helps a real person pause before clicking, replying, or sending money. Paste a suspicious text, email, or DM and Jawbreaker breaks it into plain-English warning signs: what the sender is pretending to be, what pressure tactic is being used, what they want, and the safest next step.

## Hackathon

- Event: Hugging Face Build Small Hackathon
- Track: Backyard AI
- App: Gradio Space under `build-small-hackathon`
- Status: MVP deployed; demo/story polish in progress
- Demo video: To be added before submission
- Social post: To be added before submission
- Public GitHub repo: https://github.com/gowtham0992/jawbreaker

## Built With Codex

This project is being built with OpenAI Codex in the Codex desktop app. Codex is being used for planning, implementation, eval design, Gradio UI iteration, testing, deployment, and submission documentation.

Codex evidence:

- Public GitHub repo linked from this Space README.
- Codex-attributed commits will be included for build work.
- `AGENT_TRACE.md` records the development process.
- `FIELD_NOTES.md` records product and technical decisions.
- `HONEST_SUBMISSION.md` records what the project can and cannot honestly claim.

## Why This Is Small

Jawbreaker is deliberately narrow. It does not try to be a general assistant or chatbot. It performs one safety task:

1. Read one suspicious message.
2. Identify scam risk and manipulation tactics.
3. Give one clear safe action.
4. Help the user ask someone they trust.

## Model Runtime

The deployed Space uses `openbmb/MiniCPM4.1-8B` through Hugging Face Transformers on ZeroGPU with the published Jawbreaker LoRA adapter:

- Adapter: `build-small-hackathon/jawbreaker-minicpm-lora-v3`
- Training: PEFT/LoRA on Modal A100
- Runtime: ZeroGPU in the Hugging Face Space

Why this model:

- It makes OpenBMB MiniCPM central to the app, matching the hackathon sponsor track.
- It is still well below the 32B parameter limit and fits the "small model" constraint honestly.
- MiniCPM4.1 is built for efficient end-side inference, which fits Jawbreaker's local-first safety premise.
- It avoids external commercial model APIs.
- It can produce the structured JSON that Jawbreaker validates before rendering.

The local/eval path still supports GGUF models through `llama-cpp-python`, including Qwen and MiniCPM GGUF candidates. The CPU GGUF path is kept as evidence and tooling, while the judge-facing Space uses ZeroGPU because first-click cold-start latency matters for the product experience.

Safety architecture:

- Model output must parse as JSON and match the required schema.
- A deterministic heuristic guard catches weak model outputs that under-call obvious danger.
- If MiniCPM generation fails or returns malformed JSON, Jawbreaker falls back to deterministic safety analysis instead of showing an unusable error state.
- The UI always recommends verification through official channels or a known phone number, never the suspicious link or number.
- Session memory is local to the current Gradio session and helps show repeated scam patterns.

Current eval results:

- 100-case product eval, raw v3: `90/100` risk accuracy, `0` invalid predictions, `0` model errors, `0` dangerous undercalls.
- 215-case hard eval, raw v3: `210/215` risk accuracy (`97.7%`), `0` dangerous-as-safe, `0` dangerous-as-needs-check, `0` safe-as-dangerous-or-suspicious, `0` unsafe action violations, `0` invalid predictions, `0` model errors.

Training/eval artifacts:

- `eval/scam_eval.jsonl`: 100 hand-curated synthetic/sanitized eval cases.
- `eval/field_examples.jsonl`: sanitized real-world examples from a friend, with names and phone numbers removed.
- `training/generate_jawbreaker_data.py`: deterministic generator for larger train/dev/test splits.
- `training/generate_v3_data.py`: contrastive hard-case generator used for the v3 LoRA pass.
- `training/data/train.jsonl`, `dev.jsonl`, `test.jsonl`: generated SFT records for Jawbreaker JSON behavior.
- `training/data/train_v3.jsonl`, `dev_v3.jsonl`, `test_v3.jsonl`: v3 contrastive training split.
- `eval/generated_eval.jsonl`: generated holdout eval set.
- `eval/hard_v2_eval.jsonl`: hard eval set used to compare v2 and v3 adapters.
- `training/train_lora.py`: PEFT/LoRA script for publishing Jawbreaker MiniCPM adapters.
- `training/modal_train.py`: Modal A100 training launcher.
- `training/modal_eval.py`: Modal A100 eval launcher.
- `HONEST_SUBMISSION.md`: guardrails to avoid overclaiming synthetic data, fine-tuning, or runtime behavior.

## Bonus Badges Targeted

- Off the Grid: local model inference, no cloud APIs for scam analysis.
- Llama Champion: local/eval tooling supports the llama.cpp runtime.
- Off-Brand: custom Gradio UI beyond the default look.
- Well-Tuned: targeted; the v3 MiniCPM LoRA adapter is trained, published, and evaluated.
- Sharing is Caring: Codex/agent trace published in this repo.
- Field Notes: build report published before submission.

## Sponsor Eligibility Notes

- OpenAI Codex Track: public GitHub repo with Codex-attributed commits linked in this README.
- OpenBMB Awards: targeted; MiniCPM is the deployed model and performs the central scam analysis.
- Modal Awards: Modal was used for training and eval runs, but Modal is not part of the live deployment path.
- NVIDIA Nemotron Quest: not targeted; no NeMoTron model is used.

## Safety Boundary

Jawbreaker is not legal, financial, or cybersecurity advice. It is a local-first safety aid that helps non-experts slow down and verify suspicious messages. The safest action should never ask the user to click the suspicious link or call a number from the suspicious message.
