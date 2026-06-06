# Field Notes

## 2026-06-05

Kickoff confirmed the submission shape:

- Gradio Space under the hackathon organization.
- Demo video and social post proof belong in the Space README.
- Public GitHub repo with Codex-attributed commits matters for the OpenAI Codex Track.
- Sponsor prizes can depend on model or infrastructure choices.

Jawbreaker is scoped for Backyard AI: one real person, one narrow safety task, one clear answer.

Current risk: a generic scam detector will not stand out. The product must show a specific person being helped and a clear small-model fit.

Current differentiator: Scam DNA, a visual breakdown of scam structure rather than a plain label.

Built the first serious evaluation spine: 100 synthetic/sanitized scam, suspicious, needs-check, and safe messages. The eval explicitly tests false positives on legitimate-looking messages because user trust is central to the product.

## 2026-06-06

Runtime decision: deploy with `Qwen/Qwen3-0.6B` through Transformers on ZeroGPU.

Why:

- The initial CPU GGUF path was useful for local/eval tooling, but cold-start behavior was too risky for a judge-facing Space.
- A larger GGUF model was not viable for the live demo latency target.
- ZeroGPU kept the project on a public small model without relying on a commercial LLM API.

The product architecture became defense-in-depth:

- The model produces structured scam analysis.
- The parser rejects invalid JSON.
- The schema validator catches malformed fields.
- A deterministic heuristic guard prevents obvious high-risk scams from being rendered as safe when the small model under-calls danger.

The UI direction shifted from "developer demo" to "calm safety card":

- one primary action: check the message
- warm, readable card layout
- visible scam breakdown instead of chat
- copyable message for asking someone trusted
- session memory that auto-saves checked patterns

What was cut:

- Fine-tuning. The project does not have enough separate training data to fine-tune responsibly without overfitting.
- Multi-model switching UI. It adds confusion without helping the person the tool is built for.
- Additional sponsor-specific runtime pivots beyond OpenBMB. A stable Backyard AI submission matters more than chasing every possible badge.

Current remaining field-work need: collect or choose one realistic, sanitized scam story for the demo video. The story should show a person pasting a suspicious message, receiving one safe action, and copying the trusted-person handoff.

## 2026-06-06 OpenBMB Pivot

Kickoff made clear that MiniCPM needs to be central for OpenBMB award eligibility. Jawbreaker moved the deployed ZeroGPU default from `Qwen/Qwen3-0.6B` to `openbmb/MiniCPM4.1-8B`.

Why:

- MiniCPM is now the primary scam-analysis model, not a side mention.
- The model remains under the 32B limit and fits the small-model theme.
- The OpenBMB model family is explicitly positioned for efficient local and edge deployment.
- The heuristic guard remains in place so obvious scam danger is not under-called if the model output is weak or malformed.

Fallback plan: if Space latency or memory behavior is unacceptable, switch `JAWBREAKER_TRANSFORMERS_MODEL_ID` back to `Qwen/Qwen3-0.6B` and document the OpenBMB bakeoff result honestly.

## 2026-06-06 Training Spine

Jawbreaker now has a training path, but deployment remains eval-gated.

Added:

- deterministic generation of 720 train, 120 dev, and 180 test examples
- generated holdout eval in `eval/generated_eval.jsonl`
- PEFT/LoRA training scaffold for MiniCPM
- Transformers eval backend for direct MiniCPM scoring
- runtime fallback so malformed model JSON falls back to deterministic safety analysis

Deployment rule: publish or deploy a LoRA adapter only if it improves valid JSON and keeps dangerous-as-safe misses at zero. A worse-but-fine-tuned model should not ship.

## 2026-06-06 Submission Honesty

Latest Discord discussion surfaced MiniCPM4.1 Transformers issues around SDPA attention masks and gibberish output. Jawbreaker now defaults `JAWBREAKER_ATTENTION_IMPLEMENTATION=eager` for the MiniCPM path, and keeps fallback analysis visible in the documentation.

Guardrail: winning matters, but not by overclaiming. The project should not claim Well-Tuned, real user validation, Modal usage, or llama.cpp deployment unless those things are actually completed and documented.

## 2026-06-06 Modal Training Plan

Modal credits are the right place to run the MiniCPM LoRA job. Added `training/modal_train.py` so the same generated train/dev split can run on an A100 with outputs stored in a Modal volume.

Claim rule: Modal usage becomes a submission claim only after a real Modal run completes. Well-Tuned becomes a claim only after the resulting adapter is published and beats the base model or fallback on eval.
