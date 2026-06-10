# Jawbreaker: Private Scam Defense for Someone You Love

> Draft for Hugging Face Articles / community post.
>
> Status: working draft. Add demo video and final social links before publishing.

![Jawbreaker logo](https://huggingface.co/spaces/build-small-hackathon/jawbreaker/resolve/main/jawbreaker_logo.png)

## Short Version

Jawbreaker is a small-model scam defense app for people who need a clear answer before they click, reply, share a code, or send money.

Paste a suspicious text, email, or DM. Jawbreaker turns it into a simple safety card:

- the risk level
- the warning signs
- who the sender is pretending to be
- what they want
- what could happen
- the safest next step
- a copyable note to send to someone you trust

Live app: https://huggingface.co/spaces/build-small-hackathon/jawbreaker

Model: https://huggingface.co/build-small-hackathon/jawbreaker-minicpm5-1b-lora-v8

Dataset/eval bundle: https://huggingface.co/datasets/build-small-hackathon/jawbreaker-scam-defense-data

Collection: https://huggingface.co/collections/build-small-hackathon/jawbreaker-6a263632dcd0b6d41ca914ff

GitHub: https://github.com/gowtham0992/jawbreaker

## Why We Built It

Most scam-defense tools explain scams after the fact. Jawbreaker is built for the moment before someone acts.

That moment is small but high stakes:

- a package fee link
- a fake bank callback
- a recruiter promising easy money
- a "new phone number" from a family member
- a verification code someone asks you to share

The product goal is not to be a general assistant. It is to help someone pause, understand the message, and choose one safe next step.

Jawbreaker is intentionally narrow:

1. Read one suspicious message.
2. Identify the scam risk and manipulation pattern.
3. Explain the warning signs in plain English.
4. Recommend one safe action.
5. Help the user ask a trusted person to check it.

## The Product Shape

The app is designed around a safety card, not a chatbot.

The reason is simple: scams use urgency. A chat interface can accidentally invite more back-and-forth. Jawbreaker should reduce decisions, not add more.

The current UI shows:

- a message input
- sample messages
- a verdict card
- a "Scam DNA" breakdown
- the safest next step
- a note that can be copied to someone trusted
- session-only history of checked messages

The app also asks users to remove passwords, account numbers, ID numbers, addresses, and personal codes before pasting. Jawbreaker is a safety aid, not legal, financial, or cybersecurity advice.

## The Small Model

Jawbreaker uses a fine-tuned MiniCPM model:

- Base model: `openbmb/MiniCPM5-1B`
- Adapter: `build-small-hackathon/jawbreaker-minicpm5-1b-lora-v8`
- Training: PEFT/LoRA on Modal A100
- Runtime: Hugging Face ZeroGPU
- App: Gradio / Gradio Server

The 1B model matters. Scam defense is a focused task, so the product does not need a giant general-purpose model. It needs reliable structured output, low false negatives, and safe actions.

The model outputs strict JSON for the app renderer. Jawbreaker validates that JSON before rendering the safety card.

## Defense in Depth

The model is not the only safety layer.

Jawbreaker uses a defense-in-depth pipeline:

1. The small model generates structured scam analysis.
2. The app parses the result as JSON.
3. The schema validator checks required fields.
4. A deterministic safety guard catches obvious high-risk patterns.
5. If model output is invalid or weak, the app falls back to a safer deterministic analysis.

The app should never tell someone to click a suspicious link or call a number from the suspicious message. Safe actions point to official channels, known numbers, trusted apps, or a trusted person.

## Training and Calibration

The final adapter is v8.

Earlier adapters helped prove that MiniCPM could produce the right JSON shape. Later passes focused on harder decision boundaries:

- package phishing
- bank and payment phishing
- family impersonation
- tech support scams
- fake job/recruiter scams
- prize and lottery scams
- wrong-number investment grooming
- benign family, school, pharmacy, and logistics messages that should not be overcalled

The v8 pass was failure-driven. We used eval results to find weak spots, then added targeted synthetic/sanitized calibration data and reran guarded evals.

The public dataset/eval bundle includes the training splits, eval files, and reports that support the final model decision.

## Final Eval

Final guarded Modal A100 eval on the 632-case hard v8 suite:

| Metric | Result |
| --- | ---: |
| Cases | 632 |
| Risk accuracy | 579/632, 91.61% |
| Scam type accuracy | 561/632, 88.77% |
| Mean tactic recall | 90.69% |
| Dangerous as safe | 0 |
| Dangerous as needs_check | 0 |
| Safe as dangerous or suspicious | 0 |
| Unsafe action violations | 0 |
| Invalid predictions | 0 |
| Model errors | 0 |

The headline is not just accuracy. For this product, the most important result is zero dangerous undercalls on the final hard suite.

## Why Not Just Use a Bigger Model?

Jawbreaker is a Build Small project. A bigger model could produce richer prose, but richer prose is not the goal.

The goal is:

- narrow task
- readable answer
- structured evidence
- safe next action
- small open model
- no external LLM API in the scam-analysis path

The small-model path also makes the product easier to reason about. The model is doing one job, and the app has deterministic checks around it.

## What Worked

The biggest product decision was to stop treating this as "spam classification" and treat it as "family safety workflow."

Classification alone answers: "Is this spam?"

Jawbreaker answers:

- What is risky?
- How is the message pressuring me?
- What does the sender want?
- What should I do now?
- How can I ask someone I trust for help?

That shift made the UI, evals, training data, and safety guard much clearer.

## What We Would Improve Next

The next steps are practical:

- record the demo video
- test with more sanitized real-world examples
- continue mobile polish
- add more recent scam patterns as held-out evals before training on them
- improve copy quality for the trusted-person handoff
- publish a short model/eval walkthrough for reproducibility

We would also like to keep collecting sanitized examples from public scam alerts and user-submitted messages where private details are removed.

## Try It

Try Jawbreaker here:

https://huggingface.co/spaces/build-small-hackathon/jawbreaker

Good demo inputs:

```text
USPS: Your package is held due to an unpaid fee. Verify now: http://usps-track-secure.example
```

```text
Hi Grandma, I lost my phone. This is my new number. Can you send $800 for rent today? Please don't tell Mom.
```

```text
Your dentist appointment is confirmed for Tuesday at 2:00 PM. Reply C to confirm or R to reschedule.
```

The first two should produce scam warnings. The dentist appointment should show the false-positive boundary: not every official-looking message is dangerous, and not every short message is a scam.

## Built With

- Hugging Face Spaces
- Gradio / Gradio Server
- OpenBMB MiniCPM5-1B
- PEFT/LoRA
- Modal A100 training and eval
- OpenAI Codex for implementation, eval design, UI iteration, and documentation

## Links

- Space: https://huggingface.co/spaces/build-small-hackathon/jawbreaker
- Model: https://huggingface.co/build-small-hackathon/jawbreaker-minicpm5-1b-lora-v8
- Dataset/eval bundle: https://huggingface.co/datasets/build-small-hackathon/jawbreaker-scam-defense-data
- Collection: https://huggingface.co/collections/build-small-hackathon/jawbreaker-6a263632dcd0b6d41ca914ff
- GitHub: https://github.com/gowtham0992/jawbreaker
- Build notes: https://github.com/gowtham0992/jawbreaker/blob/main/FIELD_NOTES.md
- Codex evidence: https://github.com/gowtham0992/jawbreaker/blob/main/CODEX_JUDGE_EVIDENCE.md
