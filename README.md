---
title: Jawbreaker
sdk: gradio
sdk_version: 6.16.0
app_file: app.py
license: mit
short_description: Local-first scam defense for someone you love.
tags:
  - gradio
  - build-small-hackathon
  - backyard-ai
  - local-first
  - llama-cpp
---

# Jawbreaker

Scam defense for someone you love.

Jawbreaker helps a real person pause before clicking, replying, or sending money. Paste a suspicious text, email, or DM and Jawbreaker breaks it into plain-English warning signs: what the sender is pretending to be, what pressure tactic is being used, what they want, and the safest next step.

## Hackathon

- Event: Hugging Face Build Small Hackathon
- Track: Backyard AI
- App: Gradio Space under `build-small-hackathon`
- Status: In development
- Demo video: To be added before submission
- Social post: To be added before submission
- Public GitHub repo: https://github.com/gowtham0992/jawbreaker

## Why This Is Small

Jawbreaker is deliberately narrow. It does not try to be a general assistant or chatbot. It performs one safety task:

1. Read one suspicious message.
2. Identify scam risk and manipulation tactics.
3. Give one clear safe action.
4. Help the user ask someone they trust.

## Model Plan

The final app will use a local small model through `llama.cpp` / `llama-cpp-python`. Candidate models will be chosen by an eval bakeoff:

- Qwen3-4B GGUF Q4_K_M
- Qwen3-8B GGUF Q4_K_M
- MiniCPM4-8B GGUF Q4_K_M

Decision criteria:

- valid JSON output
- low false positives on legitimate messages
- no dangerous scams labeled safe
- safe recommended actions
- short, clear explanations
- acceptable latency for judges

## Bonus Badges Targeted

- Off the Grid: local model inference, no cloud APIs for scam analysis.
- Llama Champion: model runs through the llama.cpp runtime.
- Off-Brand: custom Gradio UI beyond the default look.
- Well-Tuned: conditional; only if the MVP is stable early enough.
- Sharing is Caring: Codex/agent trace published in this repo.
- Field Notes: build report published before submission.

## Sponsor Eligibility Notes

- OpenAI Codex Track: public GitHub repo with Codex-attributed commits linked in this README.
- OpenBMB Awards: possible if MiniCPM becomes the central model after bakeoff.
- Modal Awards: possible if Modal is used for fine-tuning, evals, or deployment support and documented here.
- NVIDIA Nemotron Quest: only if a NeMoTron model is used; currently not planned.

## Safety Boundary

Jawbreaker is not legal, financial, or cybersecurity advice. It is a local-first safety aid that helps non-experts slow down and verify suspicious messages. The safest action should never ask the user to click the suspicious link or call a number from the suspicious message.
