# Submission Checklist

## Required

- [x] Gradio Space created under `build-small-hackathon`
- [x] Space made public before June 15, 2026
- [x] Demo video linked in Space README: https://youtu.be/oh0GRKYXvGM
- [x] Social post linked in Space README: https://www.reddit.com/r/huggingface/comments/1u48yt6/finetuned_a_1b_model_that_helps_families_check/
- [x] Public GitHub repo linked in Space README
- [x] Repo includes Codex-attributed feature commits
- [x] README frontmatter includes track and target badge tags
- [x] MIT license file included

## Backyard AI Evidence

- [x] Real user identified: friend's grandmother, private identity omitted
- [x] Real suspicious message pattern collected with private details removed
- [x] Privacy preserved: no public user quote is included; identity and private details are intentionally omitted
- [x] Demo script shows the real-user story

## Technical Evidence

- [x] Model name and parameter count documented
- [x] Eval set included
- [x] Sanitized dataset page published on Hugging Face
- [x] Hugging Face collection links Space, model, dataset, and reports
- [x] Runtime decision documented
- [x] Local-first vs ZeroGPU demo boundary documented
- [x] Local inference path documented
- [x] Fine-tuned MiniCPM LoRA adapter published and evaluated
- [x] Modal training/eval evidence documented
- [x] No commercial cloud API path documented

## Bonus Badges

- [x] Off-Brand
- [x] Well-Tuned
- [x] Sharing is Caring
- [x] Field Notes
- [x] Best Demo evidence finalized

## Codex Track Evidence

- [x] Public GitHub repo exists
- [x] GitHub repo is linked from README
- [x] Codex build log exists
- [x] Agent trace exists
- [x] README includes file-level Codex contribution summary
- [x] Meaningful feature commits include Codex co-author trailer
- [x] UI warns users to redact sensitive private data before pasting

## Final Manual Tasks

- [x] Set Space variables to MiniCPM5-1B + Jawbreaker LoRA v8.
- [x] Publish sanitized dataset/eval artifact page.
- [x] Create/update Hugging Face collection for the full submission package.
- [x] Choose one real or realistic sanitized scam message for the primary demo.
- [x] Publish Hugging Face article / community story: https://huggingface.co/blog/build-small-hackathon/jawbreaker-private-scam-defense
- [x] Record demo video.
- [x] Add demo video link to README.
- [x] Publish social post: https://www.reddit.com/r/huggingface/comments/1u48yt6/finetuned_a_1b_model_that_helps_families_check/
- [x] Add social post link to README.
- [x] Make the Hugging Face Space public.
- [x] Final smoke test after making the Space public: `/health` returned `status=ok`, `backend=zerogpu`, and `model=MiniCPM5-1B + Jawbreaker LoRA v8` on June 12, 2026.
