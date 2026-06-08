# Setup

## Local Project

Project path:

```bash
cd jawbreaker
```

Current local repo:

```bash
git status
git log --oneline -1
```

## GitHub Repo

The OpenAI Codex Track expects a public GitHub repo linked from the Space README, with Codex-attributed commits.

Because GitHub CLI is not installed locally, create the repo in the GitHub web UI:

- Repo name: `jawbreaker`
- Visibility: public
- Do not initialize with README, license, or gitignore

Then connect this local repo:

```bash
git remote add origin git@github.com:YOUR_GITHUB_USERNAME/jawbreaker.git
git push -u origin main
```

If SSH is not configured, use the HTTPS remote GitHub shows after repo creation:

```bash
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/jawbreaker.git
git push -u origin main
```

## Hugging Face Space

The Space can stay private during development, but must be public before the June 15, 2026 deadline.

Log in locally:

```bash
hf auth login
hf auth whoami
```

Create the private Space under the hackathon org:

```bash
hf repos create build-small-hackathon/jawbreaker --type space --space-sdk gradio --private
```

Add the Space as a second git remote:

```bash
git remote add space https://huggingface.co/spaces/build-small-hackathon/jawbreaker
git push space main
```

### ZeroGPU Mode

For responsive model inference without paid hardware:

- set Space hardware to `ZeroGPU`
- set Space variable `JAWBREAKER_BACKEND=zerogpu`
- keep `JAWBREAKER_TRANSFORMERS_MODEL_ID=openbmb/MiniCPM5-1B` for the OpenBMB/Tiny Titan-targeted build
- keep `JAWBREAKER_ADAPTER_ID=build-small-hackathon/jawbreaker-minicpm5-1b-lora-v4`; the app also defaults to this adapter when the variable is omitted
- keep `JAWBREAKER_TRUST_REMOTE_CODE=true`; MiniCPM requires custom model code through Transformers
- keep `JAWBREAKER_ATTENTION_IMPLEMENTATION=eager`; this remains the conservative MiniCPM Transformers path
- fallback model if latency is unacceptable: `Qwen/Qwen3-0.6B`

CPU fallback remains available with `JAWBREAKER_BACKEND=llama-cpp`.

Before final submission:

- make the Space public
- add demo video link to `README.md`
- add social post link to `README.md`
- add public GitHub repo link to `README.md`
- document bonus badges and model choice
