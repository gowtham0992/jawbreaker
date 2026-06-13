# Jawbreaker: Private Scam Defense for Someone You Love

<p align="center">
  <img src="https://huggingface.co/spaces/build-small-hackathon/jawbreaker/resolve/main/jawbreaker_logo.png" alt="Jawbreaker logo" width="140" />
</p>

Most scams do not begin with malware. They begin with a moment of pressure.

A package is "held." A bank account is "locked." A recruiter offers too much money. A family member says they lost their phone and needs help right now.

Jawbreaker is built for that moment before someone replies, clicks, shares a code, or sends money.

It is a small-model scam defense app that turns a suspicious text, email, or DM into a plain safety card:

- what the risk is
- who the sender is pretending to be
- how the message is pressuring you
- what the sender wants
- what could happen
- what to do next
- a note you can copy to someone you trust

Live app:

https://huggingface.co/spaces/build-small-hackathon/jawbreaker

Watch the demo:

<p align="center">
  <a href="https://www.youtube.com/watch?v=oh0GRKYXvGM">
    <img src="https://img.youtube.com/vi/oh0GRKYXvGM/hqdefault.jpg" alt="Watch the Jawbreaker demo" width="720" />
  </a>
</p>

[Open the demo on YouTube](https://www.youtube.com/watch?v=oh0GRKYXvGM)

## Why We Built It

**The motivating user was a friend's grandmother who had already been affected by scam messages.** We are not publishing private names, phone numbers, timestamps, or personal details, but that family story shaped the product.

Jawbreaker is not a generic spam classifier for security experts. It is for the person who asks:

> "Should I click this, reply to this, call this number, or ask someone I trust first?"

That is why the app avoids a chatbot shape. Scammers already create urgency and back-and-forth. Jawbreaker tries to reduce decisions instead:

1. Paste the message.
2. Read the verdict.
3. Check the warning signs.
4. Follow one safe next step.
5. Copy a note to someone trusted if you want a second opinion.

The goal is not fear. The goal is a pause.

## What The App Does

Jawbreaker takes one message and renders a safety card.

For example, a message like this:

```text
Hi Grandma, I lost my phone. This is my new number. Can you send $800 for rent today? Please don't tell Mom.
```

should not just be labeled "spam." The important part is the structure:

- it pretends to be family
- it asks for money
- it uses secrecy
- it creates urgency
- it gives the user a reason not to verify

Jawbreaker names those tactics and gives a safe action, such as not sending money or codes and checking through a known phone number or official channel.

It also handles the opposite case. A normal dentist reminder should not be treated like a scam just because it asks for a reply. False alarms matter because people stop trusting tools that panic too often.

## The Small Model

Jawbreaker runs on MiniCPM5-1B with a custom Jawbreaker LoRA adapter.

Base model:

https://huggingface.co/openbmb/MiniCPM5-1B

Final adapter:

https://huggingface.co/build-small-hackathon/jawbreaker-minicpm5-1b-lora-v8

The 1B model is deliberate. This is a narrow task, not a general assistant. We wanted a model that could produce reliable structured output for one safety workflow:

- classify risk
- explain scam DNA
- recommend one safe action
- stay inside a strict JSON schema

The public Space runs the model directly through Transformers on Hugging Face ZeroGPU. The scam-analysis path does not call OpenAI, Anthropic, hosted MiniCPM APIs, or any other external LLM API.

## Training And Eval

We trained the adapter with PEFT/LoRA on Modal A100 and used Modal again for guarded eval runs.

The data is synthetic and sanitized. It focuses on scam patterns that show up in everyday messages:

- package phishing
- bank and payment phishing
- family impersonation
- tech support scams
- fake job and recruiter scams
- prize and lottery scams
- wrong-number investment grooming
- legitimate reminders that should not be overcalled

Public dataset and eval bundle:

https://huggingface.co/datasets/build-small-hackathon/jawbreaker-scam-defense-data

The final model decision was eval-gated. We did not pick the model only by top-line accuracy. For this product, the critical failure is marking a dangerous message as safe.

<p align="center">
  <img src="https://huggingface.co/spaces/build-small-hackathon/jawbreaker/resolve/main/docs/model-selection-chart.svg" alt="Jawbreaker model selection chart" width="720" />
</p>

The chart shows why we chose the 1B v8 adapter for the final app: not the prettiest accuracy number, but the broadest completed safety gate with zero dangerous undercalls, zero unsafe actions, zero invalid JSON, and zero model errors.

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

That does not mean the model is perfect or exhaustive. It means the final submitted adapter cleared our hardest completed eval with zero dangerous undercalls and zero unsafe actions.

## Defense In Depth

Jawbreaker does not trust raw model text directly.

The runtime pipeline is:

1. MiniCPM5-1B + Jawbreaker LoRA produces structured JSON.
2. The app parses the response.
3. The schema validator checks every required field.
4. A deterministic safety guard catches obvious high-risk patterns.
5. If the model output is invalid or weak, the app falls back to a safer deterministic analysis.

The UI also tells users to remove passwords, account numbers, ID numbers, addresses, and personal codes before pasting. Jawbreaker is a safety aid, not legal, financial, or cybersecurity advice.

## What Made It Work

The key product decision was to stop building a "spam detector" and build a family safety workflow.

Spam detection says:

> "This is spam."

Jawbreaker says:

> "This looks dangerous because it asks for money, uses secrecy, and pretends to be family. Do not send money or codes. Check through a known number. Here is a note you can send to someone you trust."

That small shift made the model target, eval suite, UI, and demo much clearer.

## Built With

- Hugging Face Spaces
- Gradio / Gradio Server
- OpenBMB MiniCPM5-1B
- PEFT/LoRA
- Modal A100 training and eval
- OpenAI Codex for implementation, eval design, UI iteration, and submission documentation

Codex evidence:

https://github.com/gowtham0992/jawbreaker/blob/main/CODEX_JUDGE_EVIDENCE.md

Field notes:

https://github.com/gowtham0992/jawbreaker/blob/main/FIELD_NOTES.md

## Try It

Space:

https://huggingface.co/spaces/build-small-hackathon/jawbreaker

Submission collection:

https://huggingface.co/collections/build-small-hackathon/jawbreaker-6a263632dcd0b6d41ca914ff

GitHub:

https://github.com/gowtham0992/jawbreaker

Social posts:

https://www.reddit.com/r/huggingface/comments/1u48yt6/finetuned_a_1b_model_that_helps_families_check/

https://www.linkedin.com/posts/gsarveswaran_jawbreaker-private-scam-defense-for-someone-share-7471351364137164800-cv__/

https://x.com/GothamSarves/status/2065649294623813925?s=20

Demo inputs:

```text
USPS: Your package is held due to an unpaid fee. Verify now: http://usps-track-secure.example
```

```text
Hi Grandma, I lost my phone. This is my new number. Can you send $800 for rent today? Please don't tell Mom.
```

```text
Your dentist appointment is confirmed for Tuesday at 2:00 PM. Reply C to confirm or R to reschedule.
```

Paste first. Act after.
