# Agent Trace

This project is being built with OpenAI Codex as the coding agent.

## 2026-06-05

- Read hackathon rules, kickoff notes, sponsor details, and peer review feedback.
- Selected `Jawbreaker` as the product name.
- Chose Backyard AI as the main track.
- Established model bakeoff plan before committing to a default model.
- Created initial project scaffold for a Gradio Space and public GitHub repo.
- Created private Hugging Face Space under the hackathon organization.
- Pushed the same Git commit history to GitHub and Hugging Face Spaces.
- Added explicit Codex build evidence after organizer/Discord clarification that Codex Track eligibility depends on commit metadata and GitHub repo evidence.

Open questions:

- Which real/sanitized user story should anchor the demo video?
- What final latency numbers should be reported after the public Space is stable?

## 2026-06-06

Codex helped:

- build the 100-case scam eval dataset and backend-aware eval runner
- wire configurable analyzers for heuristic, saved prediction, llama-cpp, and Transformers paths
- add JSON extraction and schema validation for model responses
- add a heuristic safety guard for weak small-model outputs
- switch the deployed runtime to ZeroGPU + `Qwen/Qwen3-0.6B`
- keep the llama.cpp path for local/eval evidence while avoiding it as the live judge-facing path
- harden Qwen thinking-token handling with `enable_thinking=False` where supported and `<think>` stripping as a fallback
- remove duplicate model calls from session memory saving
- add hidden page-load model warmup for the deployed Space
- redesign the Gradio UI around a calm safety-card experience
- add copyable trusted-person handoff text
- patch Gradio dark-mode/loading-opacity leakage
- pivot the deployed model default to `openbmb/MiniCPM4.1-8B` for OpenBMB eligibility
- add `trust_remote_code` support for MiniCPM's Transformers loader path
- add a generated Jawbreaker train/dev/test corpus for SFT experiments
- add a PEFT/LoRA MiniCPM training script and training-only requirements
- add Transformers eval support for scoring OpenBMB models directly
- add runtime fallback when model output is malformed or inference fails

Current decisions:

- Deployed model: `openbmb/MiniCPM5-1B`.
- Deployed adapter: `build-small-hackathon/jawbreaker-minicpm5-1b-lora-v4`.
- Deployed backend: Transformers on ZeroGPU.
- Local/eval model path: llama-cpp-python remains available for GGUF models.
- Fine-tuning: completed through a Modal-trained MiniCPM5-1B LoRA adapter.
- Primary badges: Off-Brand, Sharing is Caring, Field Notes.
- Defensible badges: Off the Grid and Tiny Titan, documented carefully.
- Sponsor target: OpenBMB, because MiniCPM is central to the app.

## 2026-06-07

Codex helped:

- run and compare MiniCPM5-1B LoRA evals against earlier 8B adapter evidence
- promote `build-small-hackathon/jawbreaker-minicpm5-1b-lora-v4` as the final deployed adapter
- commit 320-case and 394-case hard guarded eval reports
- update README, setup, eval, training, and honest-submission evidence
- refine the custom Gradio Server UI for readability, elderly-friendly wording, copy-to-trusted-person behavior, and final model disclosure

Final model evidence:

- 394-case hard guarded eval: `379/394` risk accuracy (`96.19%`)
- `0` dangerous-as-safe
- `0` dangerous-as-needs-check
- `0` suspicious-as-safe
- `0` unsafe action violations
- `0` invalid predictions
- `0` model errors
