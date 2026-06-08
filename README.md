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
- Live Space: https://huggingface.co/spaces/build-small-hackathon/jawbreaker
- Final model adapter: https://huggingface.co/build-small-hackathon/jawbreaker-minicpm5-1b-lora-v4
- Public dataset/eval bundle: https://huggingface.co/datasets/build-small-hackathon/jawbreaker-scam-defense-data
- Hugging Face collection: https://huggingface.co/collections/build-small-hackathon/jawbreaker-6a263632dcd0b6d41ca914ff

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

The deployed Space uses `openbmb/MiniCPM5-1B` through Hugging Face Transformers on ZeroGPU with the published Jawbreaker LoRA adapter:

- Adapter: `build-small-hackathon/jawbreaker-minicpm5-1b-lora-v4`
- Training: PEFT/LoRA on Modal A100
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

- 394-case hard guarded eval, 1B v4: `379/394` risk accuracy (`96.19%`), `0` dangerous-as-safe, `0` dangerous-as-needs-check, `0` suspicious-as-safe, `0` unsafe action violations, `0` invalid predictions, `0` model errors.
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
- `training/modal_train.py`: Modal A100 training launcher.
- `training/modal_eval.py`: Modal A100 eval launcher.
- `HONEST_SUBMISSION.md`: guardrails to avoid overclaiming synthetic data, fine-tuning, or runtime behavior.

## Bonus Badges Targeted

- Off the Grid: local model inference, no cloud APIs for scam analysis.
- Llama Champion: local/eval tooling supports the llama.cpp runtime.
- Off-Brand: custom Gradio UI beyond the default look.
- Tiny Titan: targeted; the deployed model is `openbmb/MiniCPM5-1B`.
- Well-Tuned: targeted; the MiniCPM5-1B v4 LoRA adapter is trained, published, and evaluated.
- Sharing is Caring: Codex/agent trace published in this repo.
- Field Notes: build report published before submission.

## Sponsor Eligibility Notes

- OpenAI Codex Track: public GitHub repo with Codex-attributed commits linked in this README.
- OpenBMB Awards: targeted; MiniCPM is the deployed model and performs the central scam analysis.
- Modal Awards: Modal was used for training and eval runs, but Modal is not part of the live deployment path.
- NVIDIA Nemotron Quest: not targeted; no NeMoTron model is used.

## Safety Boundary

Jawbreaker is not legal, financial, or cybersecurity advice. It is a local-first safety aid that helps non-experts slow down and verify suspicious messages. The safest action should never ask the user to click the suspicious link or call a number from the suspicious message.
