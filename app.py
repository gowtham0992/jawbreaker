import os
from functools import lru_cache
from pathlib import Path
from time import perf_counter

import gradio as gr

from jawbreaker.analyzers import (
    build_llama_cpp_analyzer,
    build_transformers_analyzer,
    heuristic_analyzer,
    prediction_to_analysis,
    validate_prediction,
)
from jawbreaker.render import render_analysis_html, render_memory_html
from jawbreaker.schema import ScamAnalysis

try:
    import spaces
except ImportError:
    spaces = None


EXAMPLES = [
    "USPS: Your package is held due to an unpaid fee. Verify now: http://usps-track-secure.example",
    "Hi Grandma, I lost my phone. This is my new number. Can you send $800 for rent today? Please don't tell Mom.",
    "Chase fraud alert: Did you attempt a $249.00 purchase at TARGET? Reply YES or NO.",
]


def app_theme() -> gr.Theme:
    return gr.themes.Soft(
        primary_hue="red",
        secondary_hue="slate",
        neutral_hue="zinc",
        radius_size="sm",
    )


def app_css() -> str:
    return Path("style.css").read_text(encoding="utf-8")


def gpu_callback(fn):
    if spaces is None:
        return fn
    return spaces.GPU(fn)


def _env_int(name: str, default: int | None = None) -> int | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _env_bool(name: str, default: bool | None = None) -> bool | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_analyzer():
    backend = os.getenv("JAWBREAKER_BACKEND", "llama-cpp").strip().lower()
    if backend == "heuristic":
        return heuristic_analyzer

    if backend == "llama-cpp":
        model_path = resolve_model_path()
        return build_llama_cpp_analyzer(
            model_path,
            chat_format=os.getenv("JAWBREAKER_CHAT_FORMAT") or None,
            n_ctx=_env_int("JAWBREAKER_N_CTX", 1024) or 1024,
            n_threads=_env_int("JAWBREAKER_N_THREADS", 2),
            n_gpu_layers=_env_int("JAWBREAKER_N_GPU_LAYERS", 0) or 0,
            n_batch=_env_int("JAWBREAKER_N_BATCH", 128) or 128,
            n_ubatch=_env_int("JAWBREAKER_N_UBATCH", 128) or 128,
            offload_kqv=_env_bool("JAWBREAKER_OFFLOAD_KQV", True),
            op_offload=_env_bool("JAWBREAKER_OP_OFFLOAD"),
            max_tokens=_env_int("JAWBREAKER_MAX_TOKENS", 256) or 256,
            temperature=float(os.getenv("JAWBREAKER_TEMPERATURE", "0")),
        )

    if backend in {"transformers", "zerogpu"}:
        return build_transformers_analyzer(
            os.getenv("JAWBREAKER_TRANSFORMERS_MODEL_ID", "Qwen/Qwen3-0.6B"),
            max_new_tokens=_env_int("JAWBREAKER_MAX_TOKENS", 192) or 192,
            temperature=float(os.getenv("JAWBREAKER_TEMPERATURE", "0")),
            device_map=os.getenv("JAWBREAKER_DEVICE_MAP", "auto"),
            dtype=os.getenv("JAWBREAKER_TORCH_DTYPE", "auto"),
        )

    raise ValueError(f"Unsupported JAWBREAKER_BACKEND: {backend}")


def resolve_model_path() -> Path:
    model_path = Path(os.getenv("JAWBREAKER_MODEL_PATH", "models/qwen3-0.6b-gguf/Qwen3-0.6B-Q4_K_M.gguf"))
    if model_path.exists():
        return model_path

    repo_id = os.getenv("JAWBREAKER_MODEL_REPO", "unsloth/Qwen3-0.6B-GGUF")
    filename = os.getenv("JAWBREAKER_MODEL_FILE", "Qwen3-0.6B-Q4_K_M.gguf")
    cache_dir = os.getenv("JAWBREAKER_MODEL_CACHE")
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise RuntimeError("huggingface_hub is required to download the configured model file.") from exc

    return Path(hf_hub_download(repo_id=repo_id, filename=filename, cache_dir=cache_dir))


def run_analysis(message: str, memory: list[dict] | None) -> ScamAnalysis:
    memory = memory or []
    heuristic = ScamAnalysis.from_heuristics(message, memory)
    started = perf_counter()
    prediction = get_analyzer()(message)
    validation_errors = validate_prediction(prediction)
    model_analysis = prediction_to_analysis(prediction, similar_memory=heuristic.similar_memory)
    print(f"jawbreaker analyze elapsed={perf_counter() - started:.2f}s", flush=True)
    if should_use_heuristic_guard(model_analysis, heuristic, validation_errors):
        print(
            "jawbreaker guard=heuristic "
            f"model_risk={model_analysis.risk_level} heuristic_risk={heuristic.risk_level}",
            flush=True,
        )
        return heuristic
    return model_analysis


def should_use_heuristic_guard(
    model_analysis: ScamAnalysis,
    heuristic: ScamAnalysis,
    validation_errors: list[str],
) -> bool:
    if validation_errors:
        return True

    risk_rank = {"safe": 0, "needs_check": 1, "suspicious": 2, "dangerous": 3}
    if risk_rank[model_analysis.risk_level] < risk_rank[heuristic.risk_level]:
        return heuristic.risk_level != "safe"

    if heuristic.risk_level == "safe":
        return False

    dna_values = [value.strip() for value in model_analysis.scam_dna.values()]
    has_dna = any(dna_values)
    has_tactics = bool(model_analysis.tactics)
    return not has_dna and not has_tactics


@gpu_callback
def analyze_message(message: str, memory: list[dict] | None) -> tuple[str, str, list[dict]]:
    memory = memory or []
    try:
        analysis = run_analysis(message, memory)
    except Exception as exc:
        analysis = analysis_error(exc)
    return render_analysis_html(message, analysis), render_memory_html(analysis, memory), memory


def analysis_error(exc: Exception) -> ScamAnalysis:
    return ScamAnalysis(
        risk_level="needs_check",
        scam_type="analysis_error",
        summary="Jawbreaker could not finish the model scan in this environment.",
        tactics=["runtime error"],
        safest_action="Do not click links or reply yet. Verify through an official app, website, or known phone number.",
        trusted_person_message=f"Can you check this for me? Jawbreaker hit an analysis error: {exc}",
        scam_dna={
            "Impersonates": "Unknown",
            "Pressure": "Unknown",
            "Ask": "Unknown",
            "Risk": "Could not analyze",
        },
    )


@gpu_callback
def remember_current(message: str, memory: list[dict] | None) -> tuple[str, list[dict]]:
    memory = memory or []
    if not message.strip():
        return "Paste a message first.", memory
    try:
        analysis = run_analysis(message, memory)
    except Exception as exc:
        analysis = analysis_error(exc)

    memory.append(
        {
            "summary": analysis.summary,
            "scam_type": analysis.scam_type,
            "risk_level": analysis.risk_level,
            "fingerprint": analysis.scam_dna,
            "text": message[:240],
        }
    )
    return "Saved this scam pattern for this session.", memory


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Jawbreaker") as demo:
        memory_state = gr.State([])

        gr.HTML(
            """
            <section class="hero">
              <div>
                <p class="eyebrow">Backyard AI</p>
                <h1>Jawbreaker</h1>
                <p class="subtitle">Scam defense for someone you love.</p>
              </div>
              <div class="hero-badge">Local-first small-model app</div>
            </section>
            """
        )

        with gr.Row(elem_classes=["main-grid"]):
            with gr.Column(scale=5, elem_classes=["scan-panel"]):
                message = gr.Textbox(
                    label="Suspicious message",
                    placeholder="Paste a suspicious text, email, or DM here.",
                    lines=10,
                    max_lines=16,
                )
                with gr.Row():
                    analyze = gr.Button("Analyze", variant="primary")
                    remember = gr.Button("Remember this pattern")
                gr.Examples(examples=EXAMPLES, inputs=message, label="Try a sample")

            with gr.Column(scale=7):
                result = gr.HTML(
                    """
                    <div class="empty-state">
                      <h2>Paste a message to scan it.</h2>
                      <p>Jawbreaker will show the risk, the Scam DNA, and the safest next step.</p>
                    </div>
                    """
                )
                memory = gr.HTML("<div class='memory-card muted'>No scam memory saved yet.</div>")
                save_status = gr.Textbox(label="Session memory", interactive=False)

        analyze.click(
            fn=analyze_message,
            inputs=[message, memory_state],
            outputs=[result, memory, memory_state],
        )
        remember.click(
            fn=remember_current,
            inputs=[message, memory_state],
            outputs=[save_status, memory_state],
        )

    return demo


if __name__ == "__main__":
    build_app().launch(theme=app_theme(), css=app_css())
