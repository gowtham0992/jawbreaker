# Honest Submission Guardrails

Jawbreaker should compete hard without gaming the hackathon.

## What We Can Claim

- Backyard AI: Jawbreaker is built for a real, specific safety problem: helping someone pause before clicking, replying, or sending money.
- Small-model constraint: the deployed model is under 32B parameters.
- Gradio Space: the app runs as a Gradio app under the hackathon organization.
- OpenBMB targeting: MiniCPM is central to the deployed scam analysis path.
- Codex usage: the GitHub repo has Codex-attributed commits and the build logs document Codex's role.
- Custom UI: the app uses a custom Gradio interface, not the default demo look.
- Eval work: the repo includes hand-curated synthetic/sanitized eval cases plus generated synthetic train/dev/test data.
- Safety guardrails: model JSON is validated, unsafe actions are checked in eval, and a deterministic fallback handles malformed model output.

## What We Should Not Claim Unless Completed

- Do not claim the Well-Tuned badge unless a fine-tuned adapter is actually trained, published on Hugging Face, and used or evaluated honestly.
- Do not claim real-world user validation until the target person has actually tried the app.
- Do not claim the generated synthetic dataset is real user data.
- Do not claim benchmark superiority unless we publish the eval command, dataset, and result.
- Do not claim llama.cpp as the deployed runtime unless the live Space actually uses the llama.cpp path.
- Do not claim Modal usage unless training or inference actually runs on Modal.
- Do not hide fallback behavior. If MiniCPM fails and Jawbreaker uses deterministic safety fallback, document that as a reliability layer.

## Training Rules

- Training data and eval data must stay separated.
- `eval/scam_eval.jsonl` is the hand-curated eval set and should not be used as training data.
- `training/data/test.jsonl` and `eval/generated_eval.jsonl` are holdout data and should not be used for LoRA training.
- A LoRA adapter should only be deployed if it improves valid JSON and safety metrics without increasing dangerous false negatives.
- If synthetic training mostly teaches format-following, say that. Do not describe it as learning from real scam victims.

## Demo Rules

- The demo can use sanitized examples.
- If a real family story is used, remove names, phone numbers, addresses, account details, and links.
- The demo should show the actual Space behavior, not a scripted mockup.
- If the Space is slow because of ZeroGPU or MiniCPM loading, say so in field notes rather than pretending it is instant.

## Winning Without Cheating

The strongest honest story is:

Jawbreaker is a narrow, polished Backyard AI tool using OpenBMB MiniCPM under the 32B limit. It turns a suspicious message into a clear scam DNA breakdown and a safe next step for a non-technical person. The repo shows evals, safety fallbacks, training scaffolding, Codex traces, and field notes. Claims are limited to what is actually built and measured.
