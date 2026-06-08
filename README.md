---
title: Jawbreaker
emoji: 🍬
colorFrom: yellow
colorTo: red
sdk: gradio
sdk_version: 6.16.0
python_version: 3.12
app_file: app.py
license: mit
short_description: Local-first scam defense for someone you love.
tags:
- gradio
- build-small-hackathon
- backyard-ai
- openbmb
- minicpm
- minicpm5
- tiny-titan
- well-tuned
- off-brand
- best-demo
- bonus-quest-champion
- sharing-is-caring
- field-notes
- modal
- codex
- local-first
- scam-defense
- zerogpu
---

<p align="center">
  <img src="jawbreaker_logo.png" alt="Jawbreaker logo" width="160" />
</p>

# Jawbreaker

Scam defense for someone you love.

## TL;DR for Judges

- **Backyard AI:** a practical scam-defense safety card for non-technical people and their families.
- **Best MiniCPM Build / Tiny Titan / Well-Tuned:** `openbmb/MiniCPM5-1B` + [Jawbreaker LoRA v4](https://huggingface.co/build-small-hackathon/jawbreaker-minicpm5-1b-lora-v4), evaluated on a 394-case hard suite with **0 dangerous-as-safe failures**.
- **Best Use of Modal:** Modal A100 was used for LoRA training and guarded eval runs; see [`training/modal_train.py`](training/modal_train.py), [`training/modal_eval.py`](training/modal_eval.py), the [`394-case report`](eval/reports/jawbreaker-minicpm5-1b-lora-v4-hard394-guarded.json), and the [`320-case report`](eval/reports/jawbreaker-minicpm5-1b-lora-v4-hard320-guarded.json).
- **Best Use of Codex:** Codex-attributed commits plus [`AGENT_TRACE.md`](AGENT_TRACE.md) and [`CODEX_BUILD_LOG.md`](CODEX_BUILD_LOG.md), with file-level contribution notes below.
- **Off Brand / Sharing is Caring / Field Notes:** custom candy-brutalist Gradio UI, public [dataset/eval bundle](https://huggingface.co/datasets/build-small-hackathon/jawbreaker-scam-defense-data), and [`FIELD_NOTES.md`](FIELD_NOTES.md).
- **Submission package:** [Live Space](https://huggingface.co/spaces/build-small-hackathon/jawbreaker), [model](https://huggingface.co/build-small-hackathon/jawbreaker-minicpm5-1b-lora-v4), [dataset](https://huggingface.co/datasets/build-small-hackathon/jawbreaker-scam-defense-data), and [collection](https://huggingface.co/collections/build-small-hackathon/jawbreaker-6a263632dcd0b6d41ca914ff).

Jawbreaker is designed for local, on-device inference to protect user privacy. For this hackathon demo, it is hosted on Hugging Face ZeroGPU so judges can try the same app without local setup.

Jawbreaker helps a real person pause before clicking, replying, or sending money. Paste a suspicious text, email, or DM and Jawbreaker breaks it into plain-English warning signs: what the sender is pretending to be, what pressure tactic is being used, what they want, and the safest next step.

## Hackathon

- Event: Hugging Face Build Small Hackathon
- Track: Backyard AI
- App: Gradio Space under `build-small-hackathon`
- Status: Public Space deployed; demo/story polish in progress
- Demo video: To be added before submission
- Social post: To be added before submission
- Public GitHub repo: https://github.com/gowtham0992/jawbreaker
- Live Space: https://huggingface.co/spaces/build-small-hackathon/jawbreaker
- Final model adapter: https://huggingface.co/build-small-hackathon/jawbreaker-minicpm5-1b-lora-v4
- Public dataset/eval bundle: https://huggingface.co/datasets/build-small-hackathon/jawbreaker-scam-defense-data
- Hugging Face collection: https://huggingface.co/collections/build-small-hackathon/jawbreaker-6a263632dcd0b6d41ca914ff

## Built With Codex

This project is being built with OpenAI Codex in the Codex desktop app. Codex is being used for planning, implementation, eval design, Gradio UI iteration, testing, deployment, and submission documentation.

Codex evidence:

- Public GitHub repo linked from this Space README.
- Codex-attributed commits are included for build work.
- Codex scaffolded and iterated on `app.py`, the custom Gradio Server UI, `jawbreaker/` analyzer/schema/render modules, `eval/run_eval.py`, `training/train_lora.py`, `training/modal_train.py`, `training/modal_eval.py`, and the public submission docs.
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

The deployed Space uses `openbmb/MiniCPM5-1B` through Hugging Face Transformers on ZeroGPU with the published Jawbreaker LoRA adapter:

- Adapter: `build-small-hackathon/jawbreaker-minicpm5-1b-lora-v4`
- Training: PEFT/LoRA on Modal A100
- Eval: guarded Modal A100 runs across 320-case and 394-case hard suites
- Runtime: ZeroGPU in the Hugging Face Space

Why this model:

- It makes OpenBMB MiniCPM central to the app, matching the hackathon sponsor track.
- It is a 1B model, which fits the Tiny Titan spirit while staying useful on a narrow task.
- The 1B v4 adapter beat the earlier 8B v3 adapter on the hard guarded evals.
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

- 394-case hard guarded eval, 1B v4: `379/394` risk accuracy (`96.19%`), **`0` dangerous-as-safe**, `0` dangerous-as-needs-check, `0` suspicious-as-safe, `0` unsafe action violations, `0` invalid predictions, `0` model errors.
- 320-case hard guarded eval, 1B v4: `310/320` risk accuracy (`96.88%`), `0` dangerous-as-safe, `0` dangerous-as-needs-check, `0` suspicious-as-safe, `0` unsafe action violations, `0` invalid predictions, `0` model errors.

Training/eval artifacts:

- Hugging Face dataset: `build-small-hackathon/jawbreaker-scam-defense-data` publishes the sanitized/synthetic evals, generated training splits, and final v4 reports.
- `eval/scam_eval.jsonl`: 100 hand-curated synthetic/sanitized eval cases.
- `eval/field_examples.jsonl`: sanitized real-world examples from a friend, with names and phone numbers removed.
- `training/generate_jawbreaker_data.py`: deterministic generator for larger train/dev/test splits.
- `training/generate_v3_data.py`: contrastive hard-case generator used for the v3 LoRA pass.
- `training/generate_v4_data.py`, `generate_v5_data.py`, `generate_v6_data.py`: later calibration generators used to stress-test false positives and trusted-route boundaries.
- `training/data/train.jsonl`, `dev.jsonl`, `test.jsonl`: generated SFT records for Jawbreaker JSON behavior.
- `training/data/train_v3.jsonl`, `dev_v3.jsonl`, `test_v3.jsonl`: v3 contrastive training split.
- `eval/generated_eval.jsonl`: generated holdout eval set.
- `eval/hard_v2_eval.jsonl`: hard eval set used to compare v2 and v3 adapters.
- `eval/hard_v4_eval.jsonl`, `hard_v5_eval.jsonl`, `hard_v6_eval.jsonl`: expanded hard evals used during 1B calibration.
- `eval/reports/jawbreaker-minicpm5-1b-lora-v4-hard394-guarded.json`: main final model evidence.
- `training/train_lora.py`: PEFT/LoRA script for publishing Jawbreaker MiniCPM adapters.
- `training/modal_train.py`: Modal A100 training launcher used for the MiniCPM LoRA passes.
- `training/modal_eval.py`: Modal A100 eval launcher used for guarded hard-suite scoring.
- `HONEST_SUBMISSION.md`: guardrails to avoid overclaiming synthetic data, fine-tuning, or runtime behavior.

## Prize Eligibility

| Prize / Badge | Status | Evidence |
| --- | --- | --- |
| Backyard AI | Targeted | Practical scam-defense app for someone close, with a focused safety workflow. |
| Best MiniCPM Build | Targeted | `openbmb/MiniCPM5-1B` is the core runtime model, with a published Jawbreaker LoRA adapter. |
| Best Use of Codex | Targeted | Public GitHub repo includes Codex-attributed commits plus `AGENT_TRACE.md` and `CODEX_BUILD_LOG.md`. |
| Best Use of Modal | Targeted | Modal A100 was used for PEFT/LoRA training and guarded eval runs across the MiniCPM calibration path; see `training/modal_train.py`, `training/modal_eval.py`, and the committed 394/320-case eval report files. |
| Tiny Titan | Targeted | The deployed model is `openbmb/MiniCPM5-1B`, well under the 4B badge threshold. |
| Off Brand | Targeted | Custom Gradio UI beyond the stock component look. |
| Best Demo | Pending | Demo video and social post still need to be recorded, published, and linked before final submission. |
| Bonus Quest Champion | Stretch target | Jawbreaker stacks multiple bonus criteria: Well-Tuned, Off Brand, Tiny Titan, Sharing is Caring, Field Notes, and Best Demo once the video/social links are added. |
| Judges' Wildcard | Automatic | Every submission is considered. |

Not claiming:

- Best Agent: Jawbreaker is not a multi-step agentic app.
- NVIDIA Nemotron Quest: no NeMoTron model is used.
- llama.cpp as live runtime: local/eval tooling supports GGUF experiments, but the judge-facing Space uses Transformers on ZeroGPU.
- Off the Grid: Jawbreaker uses no external LLM API, but the public demo runs on Hugging Face ZeroGPU, so this is framed as local-first rather than claimed as a live fully local runtime.

## Safety Boundary

Jawbreaker is not legal, financial, or cybersecurity advice. It is a local-first safety aid that helps non-experts slow down and verify suspicious messages. The safest action should never ask the user to click the suspicious link or call a number from the suspicious message.

`FIELD_NOTES.md` is a build-observation log: product decisions, model/runtime pivots, eval results, and packaging notes. It is not presented as ethnographic user research.
