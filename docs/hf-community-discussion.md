# Jawbreaker Submission Package

Jawbreaker is a private scam-defense app for someone you love.

It is built for the moment before someone clicks a suspicious link, replies to an impersonator, shares a code, calls an unknown number, or sends money. The motivating user is a friend's grandmother who had already been affected by scam messages; private identity and message details are intentionally omitted.

## Main Links

- Live Space: https://huggingface.co/spaces/build-small-hackathon/jawbreaker
- Demo video: https://youtu.be/oh0GRKYXvGM
- Final model adapter: https://huggingface.co/build-small-hackathon/jawbreaker-minicpm5-1b-lora-v8
- Dataset/eval bundle: https://huggingface.co/datasets/build-small-hackathon/jawbreaker-scam-defense-data
- Collection: https://huggingface.co/collections/build-small-hackathon/jawbreaker-6a263632dcd0b6d41ca914ff
- GitHub repo: https://github.com/gowtham0992/jawbreaker
- Article draft: https://huggingface.co/spaces/build-small-hackathon/jawbreaker/blob/main/docs/huggingface-article-draft.md

## Model + Runtime

- Base model: `openbmb/MiniCPM5-1B`
- Adapter: `build-small-hackathon/jawbreaker-minicpm5-1b-lora-v8`
- Runtime: Hugging Face ZeroGPU, direct Transformers inference
- Training/eval: Modal A100 PEFT/LoRA runs
- No external hosted LLM API is used in the scam-analysis path

## Final Eval Evidence

Final guarded hard-suite report:

https://huggingface.co/spaces/build-small-hackathon/jawbreaker/blob/main/eval/reports/jawbreaker-minicpm5-1b-lora-v8-hard632-safetyguard-v4.json

Headline metrics:

- Cases: 632
- Risk accuracy: 579/632, 91.61%
- Scam type accuracy: 561/632, 88.77%
- Mean tactic recall: 90.69%
- Dangerous as safe: 0
- Dangerous as needs_check: 0
- Safe as dangerous or suspicious: 0
- Unsafe action violations: 0
- Invalid predictions: 0
- Model errors: 0

## Evidence Docs

- Field notes: https://huggingface.co/spaces/build-small-hackathon/jawbreaker/blob/main/FIELD_NOTES.md
- Codex evidence: https://huggingface.co/spaces/build-small-hackathon/jawbreaker/blob/main/CODEX_JUDGE_EVIDENCE.md
- Build log: https://huggingface.co/spaces/build-small-hackathon/jawbreaker/blob/main/CODEX_BUILD_LOG.md
- Honest submission guardrails: https://huggingface.co/spaces/build-small-hackathon/jawbreaker/blob/main/HONEST_SUBMISSION.md

## Claimed Fit

- Backyard AI: real family-safety workflow for scam defense
- Best MiniCPM Build: MiniCPM5-1B is the live model family
- Well-Tuned: published MiniCPM5-1B LoRA adapter and eval suite
- Tiny Titan: 1B model under the 4B threshold
- Off the Grid: no external hosted LLM API in the analysis path
- Off Brand: custom Gradio Server UI, not stock component layout
- Sharing is Caring: public model, dataset/evals, collection, build docs
- Field Notes: product/model/runtime decisions documented
- Modal: training and guarded eval runs on Modal A100
- Codex/OpenAI: public GitHub with Codex-attributed commits and file-level evidence

## Remaining Public Story Work

- Demo video: published
- Social post: pending
- Hugging Face Article: drafted, pending publication through the Articles UI

The current submission is intended to be judged from the live Space plus the public model/dataset/collection/GitHub evidence above.
