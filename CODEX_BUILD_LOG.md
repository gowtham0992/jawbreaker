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

## Runtime Pivot

Codex helped compare the practical runtime paths and move the deployed app to Transformers on ZeroGPU with `Qwen/Qwen3-0.6B`.

The local GGUF/llama.cpp path remains in the repo for eval and local experimentation, but the judge-facing Space uses ZeroGPU because first-click cold-start latency is part of the product experience.

Follow-up hardening included:

- strict JSON parsing and validation
- Qwen thinking-token suppression/stripping
- deterministic heuristic guardrails for obvious scam danger
- hidden model warmup on Space load
- Gradio loading and dark-mode fixes for a stable demo surface
