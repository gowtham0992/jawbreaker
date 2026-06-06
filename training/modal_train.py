from __future__ import annotations

from pathlib import Path

import modal


APP_NAME = "jawbreaker-minicpm-lora"
REMOTE_ROOT = Path("/workspace")
REMOTE_OUTPUT = Path("/outputs")
LOCAL_ROOT = Path(__file__).resolve().parents[1]


image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "accelerate==1.12.0",
        "datasets>=4.4.0,<5.0",
        "huggingface-hub>=0.34.0,<1.0",
        "peft>=0.18.0,<1.0",
        "sentencepiece>=0.2.0,<1.0",
        "torch==2.9.1",
        "transformers==4.57.3",
    )
    .add_local_dir(LOCAL_ROOT / "jawbreaker", remote_path=REMOTE_ROOT / "jawbreaker")
    .add_local_dir(LOCAL_ROOT / "training", remote_path=REMOTE_ROOT / "training")
    .add_local_dir(LOCAL_ROOT / "eval", remote_path=REMOTE_ROOT / "eval")
)

app = modal.App(APP_NAME, image=image)
volume = modal.Volume.from_name("jawbreaker-training", create_if_missing=True)


@app.function(
    gpu="A100",
    timeout=6 * 60 * 60,
    volumes={REMOTE_OUTPUT: volume},
    secrets=[modal.Secret.from_name("huggingface-secret", required_keys=["HF_TOKEN"])],
)
def train_lora(
    model_id: str = "openbmb/MiniCPM4.1-8B",
    output_name: str = "jawbreaker-minicpm-lora",
    epochs: float = 1.0,
    push_to_hub: bool = False,
    hub_model_id: str | None = None,
) -> None:
    import os
    import subprocess

    os.chdir(REMOTE_ROOT)
    output_dir = REMOTE_OUTPUT / output_name
    cmd = [
        "python",
        "training/train_lora.py",
        "--model-id",
        model_id,
        "--train-file",
        "training/data/train.jsonl",
        "--dev-file",
        "training/data/dev.jsonl",
        "--output-dir",
        str(output_dir),
        "--epochs",
        str(epochs),
    ]
    if push_to_hub:
        cmd.append("--push-to-hub")
        if hub_model_id:
            cmd.extend(["--hub-model-id", hub_model_id])

    subprocess.run(cmd, check=True)
    volume.commit()


@app.local_entrypoint()
def main(
    model_id: str = "openbmb/MiniCPM4.1-8B",
    output_name: str = "jawbreaker-minicpm-lora",
    epochs: float = 1.0,
    push_to_hub: bool = False,
    hub_model_id: str | None = None,
) -> None:
    train_lora.remote(
        model_id=model_id,
        output_name=output_name,
        epochs=epochs,
        push_to_hub=push_to_hub,
        hub_model_id=hub_model_id,
    )
