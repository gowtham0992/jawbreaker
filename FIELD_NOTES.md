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
- Additional sponsor-specific runtime pivots. A stable Backyard AI submission matters more than chasing every possible badge.

Current remaining field-work need: collect or choose one realistic, sanitized scam story for the demo video. The story should show a person pasting a suspicious message, receiving one safe action, and copying the trusted-person handoff.
