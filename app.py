import os
import json
from dataclasses import asdict
from functools import lru_cache
from html import escape
from pathlib import Path
from time import perf_counter, sleep
from typing import Any

import gradio as gr
from fastapi.responses import HTMLResponse

from jawbreaker.analyzers import (
    build_llama_cpp_analyzer,
    build_transformers_analyzer,
    heuristic_analyzer,
    prediction_to_analysis,
    repair_prediction,
    should_apply_heuristic_guard,
    validate_prediction,
)
from jawbreaker.render import render_analysis_html, render_memory_html, render_scanning_html
from jawbreaker.schema import ScamAnalysis

try:
    import spaces
except ImportError:
    spaces = None


EXAMPLES = [
    "USPS: Your package is held due to an unpaid fee. Verify now: http://usps-track-secure.example",
    "Hi Grandma, I lost my phone. This is my new number. Can you send $800 for rent today? Please don't tell Mom.",
    "Coinbase alert: We received a request to update the phone number on your account. If this wasn't you, call support immediately at [callback number].",
    "Hi! I'm a recruiter from TikTok Shop. We are looking for a part-time assistant. Flexible remote work, 60 minutes per day, $330-$750 per day. Contact me on WhatsApp at [phone number].",
    "Your dentist appointment is confirmed for Tuesday at 2:00 PM. Reply C to confirm or R to reschedule.",
    "Your verification code is 482913. Do not share this code with anyone. We will never ask for it by phone.",
]

DEFAULT_TRANSFORMERS_MODEL_ID = "openbmb/MiniCPM5-1B"
DEFAULT_ADAPTER_ID = "build-small-hackathon/jawbreaker-minicpm5-1b-lora-v4"
DEFAULT_TRANSFORMERS_MAX_TOKENS = 512
LOGO_PATH = Path("jawbreaker_logo.png")

FORCE_LIGHT_JS = """() => {
    const forceLight = () => document.body.classList.remove('dark');
    forceLight();
    new MutationObserver(forceLight).observe(document.body, {
        attributes: true,
        attributeFilter: ['class'],
    });
}"""

FORCE_LIGHT_HEAD = """
<script>
(() => {
  const forceLight = () => {
    if (document.body) document.body.classList.remove("dark");
  };
  const copyPlan = async (button) => {
    const source = button.dataset.copy || "";
    if (!source) return;
    await navigator.clipboard.writeText(source);
    const original = button.textContent || "COPY PLAN";
    button.textContent = "COPIED";
    window.setTimeout(() => {
      button.textContent = original;
    }, 1200);
  };
  document.addEventListener("click", (event) => {
    const button = event.target.closest?.(".inline-copy-btn");
    if (!button) return;
    event.preventDefault();
    copyPlan(button);
  });
  window.addEventListener("DOMContentLoaded", () => {
    forceLight();
    new MutationObserver(forceLight).observe(document.body, {
      attributes: true,
      attributeFilter: ["class"],
    });
  });
})();
</script>
"""


def app_theme() -> gr.Theme:
    theme = gr.themes.Soft(
        primary_hue="red",
        secondary_hue="slate",
        neutral_hue="zinc",
        radius_size="sm",
    )
    theme.set(
        block_label_background_fill="transparent",
        block_label_border_color="transparent",
        block_label_text_color="#6b5144",
        block_label_text_size="13px",
        block_label_text_weight="700",
    )
    return theme


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


def default_adapter_id(model_id: str) -> str | None:
    configured = os.getenv("JAWBREAKER_ADAPTER_ID")
    if configured is not None:
        return configured or None
    if model_id == DEFAULT_TRANSFORMERS_MODEL_ID:
        return DEFAULT_ADAPTER_ID
    return None


@lru_cache(maxsize=1)
def get_analyzer():
    backend = current_backend()
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
        model_id = os.getenv("JAWBREAKER_TRANSFORMERS_MODEL_ID", DEFAULT_TRANSFORMERS_MODEL_ID)
        return build_transformers_analyzer(
            model_id,
            adapter_id=default_adapter_id(model_id),
            max_new_tokens=_env_int("JAWBREAKER_MAX_TOKENS", DEFAULT_TRANSFORMERS_MAX_TOKENS)
            or DEFAULT_TRANSFORMERS_MAX_TOKENS,
            temperature=float(os.getenv("JAWBREAKER_TEMPERATURE", "0")),
            device_map=os.getenv("JAWBREAKER_DEVICE_MAP", "auto"),
            dtype=os.getenv("JAWBREAKER_TORCH_DTYPE", "auto"),
            trust_remote_code=_env_bool("JAWBREAKER_TRUST_REMOTE_CODE", True) or False,
            attn_implementation=os.getenv("JAWBREAKER_ATTENTION_IMPLEMENTATION", "eager") or None,
        )

    raise ValueError(f"Unsupported JAWBREAKER_BACKEND: {backend}")


def current_backend() -> str:
    return os.getenv("JAWBREAKER_BACKEND", "llama-cpp").strip().lower()


def should_warm_model() -> bool:
    return _env_bool("JAWBREAKER_WARM_MODEL", True) and current_backend() in {"transformers", "zerogpu"}


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
    try:
        prediction = get_analyzer()(message)
    except Exception as exc:
        print(
            "jawbreaker analyzer_error fallback=heuristic "
            f"elapsed={perf_counter() - started:.2f}s error={exc!r}",
            flush=True,
        )
        heuristic.summary = f"{heuristic.summary} Jawbreaker used its safety fallback because the model response was not usable."
        return heuristic
    raw_validation_errors = validate_prediction(prediction)
    prediction = repair_prediction(prediction)
    validation_errors = validate_prediction(prediction)
    model_analysis = prediction_to_analysis(prediction, similar_memory=heuristic.similar_memory)
    print(f"jawbreaker analyze elapsed={perf_counter() - started:.2f}s", flush=True)
    if should_use_heuristic_guard(model_analysis, heuristic, validation_errors, message):
        print(
            "jawbreaker guard=heuristic "
            f"model_risk={model_analysis.risk_level} heuristic_risk={heuristic.risk_level}",
            flush=True,
        )
        return heuristic
    if raw_validation_errors:
        print(f"jawbreaker schema_repaired errors={raw_validation_errors}", flush=True)
    return model_analysis


def warm_model_impl() -> None:
    backend = current_backend()
    if not should_warm_model():
        print(f"jawbreaker warm_model skip backend={backend}", flush=True)
        return None

    started = perf_counter()
    print(f"jawbreaker warm_model start backend={backend}", flush=True)
    get_analyzer()
    print(f"jawbreaker warm_model ready elapsed={perf_counter() - started:.2f}s", flush=True)
    return None


@gpu_callback
def warm_model() -> None:
    return warm_model_impl()


def memory_entry_from_analysis(message: str, analysis: ScamAnalysis) -> dict[str, Any]:
    return {
        "summary": analysis.summary,
        "scam_type": analysis.scam_type,
        "risk_level": analysis.risk_level,
        "fingerprint": analysis.scam_dna,
        "text": message[:240],
    }


def render_current_memory(memory: list[dict]) -> str:
    return render_memory_html(ScamAnalysis.from_heuristics("", memory), memory)


def render_save_status(message: str = "") -> str:
    if not message:
        return "<div class='save-status'></div>"
    return f"<div class='save-status'>{message}</div>"


def model_status_label() -> str:
    model_id = os.getenv("JAWBREAKER_TRANSFORMERS_MODEL_ID", DEFAULT_TRANSFORMERS_MODEL_ID)
    adapter_id = default_adapter_id(model_id)
    if model_id == "openbmb/MiniCPM5-1B" and adapter_id == "build-small-hackathon/jawbreaker-minicpm5-1b-lora-v4":
        return "MiniCPM5-1B + Jawbreaker LoRA v4"
    if adapter_id:
        return adapter_id.rsplit("/", 1)[-1].replace("jawbreaker-", "").upper()
    return model_id.rsplit("/", 1)[-1].upper()


def backend_status_label() -> str:
    backend = current_backend()
    if backend == "zerogpu":
        return "ZEROGPU"
    if backend == "transformers":
        return "TRANSFORMERS"
    if backend == "llama-cpp":
        return "LLAMA.CPP"
    if backend == "heuristic":
        return "LOCAL FALLBACK"
    return backend.upper()


def analysis_payload(message: str, memory: list[dict] | None = None) -> dict[str, Any]:
    memory = memory or []
    started = perf_counter()
    if not message.strip():
        analysis = ScamAnalysis.from_heuristics(message, memory)
    else:
        analysis = run_analysis(message, memory)

    entry = memory_entry_from_analysis(message, analysis)
    if message.strip() and (not memory or memory[-1].get("text") != entry.get("text")):
        memory.append(entry)

    return {
        "analysis": asdict(analysis),
        "copy_plan": build_handoff_message(message, analysis),
        "memory": memory[-6:],
        "message": message,
        "model_label": model_status_label(),
        "elapsed_seconds": round(perf_counter() - started, 2),
    }


def logo_data_uri() -> str:
    import base64

    if not LOGO_PATH.exists():
        return ""
    encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def paper_shield_html() -> str:
    examples_json = json.dumps(EXAMPLES).replace("</", "<\\/")
    logo_uri = logo_data_uri()
    model_label = escape(model_status_label())
    backend_label = escape(backend_status_label())
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Jawbreaker</title>
  <style>
    /* Hallmark · macrostructure: Workbench · genre: playful · theme: custom family-safety report
     * pre-emit critique: P5 H4 E4 S5 R4 V4 · contrast: pass target (40-41)
     */
    :root {{
      color-scheme: light;
      --color-bg: #f7f1e4;
      --color-bg-warm: #fbf5e8;
      --color-paper: #fffdf7;
      --color-paper-soft: #fff8ea;
      --color-ink: #17130f;
      --color-muted: #66594e;
      --color-rule: #241a13;
      --color-focus: #246bfe;
      --color-action: #f4c400;
      --color-action-ink: #17130f;
      --color-danger: #d94d4b;
      --color-danger-soft: #ffe1df;
      --color-danger-ink: #17130f;
      --color-coral: #f58b72;
      --color-fold: #f0e4cc;
      --color-terminal-good: #80f2a8;
      --color-terminal-muted: #9f9a92;
      --color-safe: #238756;
      --color-safe-soft: #daf5e4;
      --color-check: #af6b11;
      --color-check-soft: #fff0ca;
      --shadow-soft: 0 18px 45px rgba(36, 26, 19, .12);
      --shadow-hard: 5px 5px 0 var(--color-rule);
      --radius: 8px;
      --font-label: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      --font-display: Georgia, "Times New Roman", Times, serif;
      --font-body: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    * {{ box-sizing: border-box; }}
    html {{
      overflow-x: clip;
      background: var(--color-bg);
    }}
    body {{
      margin: 0;
      min-height: 100vh;
      overflow-x: clip;
      background:
        linear-gradient(135deg, rgba(36, 26, 19, .035) 0 1px, transparent 1px 28px),
        radial-gradient(circle at 8% 4%, rgba(244, 196, 0, .18), transparent 24rem),
        var(--color-bg);
      color: var(--color-ink);
      font-family: var(--font-body);
    }}

    button, textarea {{ font: inherit; }}
    button {{ cursor: pointer; }}

    .shell {{
      width: min(1320px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 56px;
    }}

    .topbar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
      padding-bottom: 18px;
      border-bottom: 2px solid var(--color-rule);
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 14px;
      min-width: 0;
    }}

    .brand img {{
      width: 44px;
      height: 44px;
      border: 2px solid var(--color-rule);
      border-radius: 8px;
      background: var(--color-paper);
    }}

    .brand h1 {{
      margin: 0;
      font-family: var(--font-display);
      font-size: clamp(1.55rem, 3vw, 2.35rem);
      line-height: .92;
      letter-spacing: 0;
      min-width: 0;
      overflow-wrap: anywhere;
    }}

    .brand-copy {{
      display: grid;
      gap: 4px;
      min-width: 0;
    }}

    .tagline {{
      margin: 0;
      color: var(--color-muted);
      font-size: clamp(.86rem, 1vw, .96rem);
      line-height: 1.25;
    }}

    .status {{
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 8px;
      font-family: var(--font-label);
      font-weight: 800;
      font-size: .72rem;
      text-align: right;
    }}

    .status > span {{
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      border: 1.5px solid var(--color-rule);
      border-radius: 999px;
      background: var(--color-paper-soft);
      padding: 6px 10px;
      white-space: nowrap;
    }}

    .hero {{
      display: grid;
      gap: 7px;
      padding: 18px 0 16px;
    }}

    .hero h2 {{
      margin: 0;
      font-family: var(--font-display);
      font-size: clamp(1.45rem, 2.1vw, 1.9rem);
      line-height: 1;
      letter-spacing: 0;
      max-width: 100%;
      min-width: 0;
      white-space: nowrap;
    }}

    .hero p {{
      margin: 0;
      color: var(--color-muted);
      font-size: clamp(.8rem, .9vw, .9rem);
      line-height: 1.35;
      max-width: none;
      white-space: nowrap;
    }}

    .safety-note {{
      width: fit-content;
      max-width: 100%;
      margin-top: 4px;
      border: 1.5px solid var(--color-rule);
      border-radius: 999px;
      background: var(--color-paper-soft);
      padding: 6px 10px;
      color: var(--color-muted);
      font-family: var(--font-label);
      font-size: .62rem;
      font-weight: 800;
      line-height: 1.25;
      white-space: normal;
    }}

    .workspace {{
      display: grid;
      grid-template-columns: minmax(320px, 430px) minmax(0, 1fr);
      gap: 36px;
      align-items: start;
    }}

    .paper {{
      position: relative;
      background: var(--color-paper);
      border: 2px solid var(--color-rule);
      border-radius: var(--radius);
      box-shadow: var(--shadow-soft);
    }}

    .paper::after {{
      display: none;
    }}

    .note {{
      padding: 28px;
    }}

    .section-label {{
      margin: 0 0 13px;
      font-family: var(--font-label);
      font-size: .86rem;
      font-weight: 900;
      text-transform: uppercase;
    }}

    textarea {{
      width: 100%;
      min-height: 255px;
      resize: vertical;
      border: 2px solid var(--color-rule);
      border-radius: 4px;
      background:
        linear-gradient(var(--color-paper) 31px, rgba(36, 26, 19, .08) 32px),
        var(--color-paper);
      background-size: 100% 32px;
      color: var(--color-ink);
      padding: 16px;
      font-size: .92rem;
      line-height: 1.55;
      outline: 2px solid transparent;
      outline-offset: 2px;
    }}

    textarea:focus-visible {{
      outline-color: var(--color-focus);
      box-shadow: 0 0 0 4px rgba(36, 107, 254, .12);
    }}

    .run {{
      width: 100%;
      margin-top: 18px;
      min-height: 58px;
      border: 2px solid var(--color-rule);
      border-radius: 999px;
      background: var(--color-action);
      color: var(--color-action-ink);
      font-family: var(--font-label);
      font-weight: 950;
      font-size: .94rem;
      text-transform: uppercase;
      white-space: nowrap;
      box-shadow: 0 5px 0 var(--color-rule);
      transition: transform .16s ease, box-shadow .16s ease, opacity .16s ease;
    }}

    .run:focus-visible,
    .copy-btn:focus-visible,
    .sample:focus-visible {{
      outline: 2px solid var(--color-focus);
      outline-offset: 3px;
    }}

    .run:active {{
      transform: translateY(3px);
      box-shadow: 0 2px 0 var(--color-rule);
    }}

    .run[disabled] {{
      opacity: .55;
      cursor: wait;
    }}

    .samples {{
      margin-top: 22px;
      display: grid;
      gap: 9px;
    }}

    .sample {{
      border: 1.5px solid var(--color-rule);
      border-radius: 999px;
      background: var(--color-paper-soft);
      padding: 10px 14px;
      text-align: left;
      font-size: .95rem;
      line-height: 1.22;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}

    .result-stack {{
      display: grid;
      gap: 24px;
    }}

    .result-top {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 16px;
      align-items: stretch;
    }}

    .result-top .card {{
      min-height: 100%;
    }}

    .card {{
      position: relative;
      border: 2px solid var(--color-rule);
      border-radius: var(--radius);
      background: var(--color-paper);
      box-shadow: var(--shadow-soft);
      overflow: hidden;
    }}

    .card-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      min-height: 42px;
      padding: 10px 18px;
      border-bottom: 2px solid var(--color-rule);
      background: var(--color-paper-soft);
      color: var(--color-ink);
      font-family: var(--font-label);
      font-weight: 900;
      font-size: .78rem;
      line-height: 1.2;
      overflow-wrap: anywhere;
    }}

    .card-body {{
      padding: clamp(16px, 2.4vw, 24px);
    }}

    .result-top .card-body {{
      padding: clamp(16px, 2.4vw, 24px);
    }}

    .standby-card .card-body {{
      min-height: 260px;
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(240px, .95fr);
      gap: clamp(24px, 4vw, 46px);
      align-items: center;
      text-align: left;
      background:
        linear-gradient(90deg, transparent 49%, rgba(36,26,19,.07) 50%, transparent 51%),
        linear-gradient(0deg, transparent 49%, rgba(36,26,19,.07) 50%, transparent 51%),
        var(--color-paper);
      background-size: 42px 42px;
    }}

    .shield-mark {{
      width: min(112px, 30vw);
      aspect-ratio: 1;
      margin: 0 0 16px;
      border: 2px solid var(--color-rule);
      border-radius: 50%;
      background:
        radial-gradient(circle, var(--color-danger) 0 22%, var(--color-paper-soft) 23% 38%, var(--color-coral) 39% 56%, var(--color-paper-soft) 57% 72%, var(--color-rule) 73% 100%);
      box-shadow: var(--shadow-hard);
    }}

    .standby-card h3 {{
      margin: 0 0 12px;
      max-width: 22ch;
      font-family: var(--font-display);
      font-size: clamp(1.3rem, 2vw, 1.75rem);
      line-height: 1.04;
      min-width: 0;
      overflow-wrap: anywhere;
    }}

    .standby-card p {{
      margin: 0;
      max-width: 34rem;
      color: var(--color-muted);
      line-height: 1.5;
      font-size: .84rem;
    }}

    .standby-list {{
      display: grid;
      gap: 10px;
      margin-top: 16px;
      padding: 0;
      list-style: none;
    }}

    .standby-list li {{
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      gap: 10px;
      align-items: start;
      max-width: 34rem;
    }}

    .standby-list strong {{
      display: inline-grid;
      place-items: center;
      width: 1.45rem;
      height: 1.45rem;
      border: 1.5px solid var(--color-rule);
      border-radius: 999px;
      background: var(--color-action);
      font-family: var(--font-label);
      font-size: .84rem;
    }}

    .standby-preview {{
      display: grid;
      gap: 12px;
      align-self: stretch;
    }}

    .standby-tile {{
      display: grid;
      gap: 6px;
      align-content: center;
      min-height: 72px;
      border: 2px solid var(--color-rule);
      border-radius: 6px;
      background: var(--color-paper-soft);
      padding: 14px;
    }}

    .standby-tile strong {{
      font-family: var(--font-label);
      font-size: .76rem;
      text-transform: uppercase;
    }}

    .standby-tile span {{
      color: var(--color-muted);
      font-size: .9rem;
      line-height: 1.3;
    }}

    .loading-card .card-body {{
      min-height: 300px;
      background: var(--color-rule);
      color: var(--color-paper);
      font-family: var(--font-label);
    }}

    .loading-card .card-head {{
      background: var(--color-rule);
      color: var(--color-paper);
      border-bottom-color: var(--color-rule);
    }}

    .fold-loader {{
      display: grid;
      gap: 18px;
    }}

    .fold-bar {{
      height: 18px;
      border: 2px solid var(--color-paper);
      background: linear-gradient(90deg, var(--color-action) var(--progress, 12%), transparent 0);
      box-shadow: 4px 4px 0 rgba(0,0,0,.35);
    }}

    .loading-line {{
      margin: 0;
      font-weight: 900;
      color: var(--color-terminal-good);
    }}

    .loading-line.muted {{ color: var(--color-terminal-muted); }}

    .verdict-card.dangerous .stamp {{ background: var(--color-danger); color: var(--color-paper); }}
    .verdict-card.suspicious .stamp,
    .verdict-card.needs_check .stamp {{ background: var(--color-check); color: var(--color-paper); }}
    .verdict-card.safe .stamp {{ background: var(--color-safe); color: var(--color-paper); }}

    .verdict-layout {{
      display: grid;
      grid-template-columns: 86px minmax(0, 1fr);
      gap: 20px;
      align-items: center;
    }}

    .stamp {{
      width: 68px;
      height: 68px;
      display: grid;
      place-items: center;
      border: 3px solid var(--color-rule);
      border-radius: 50%;
      font-family: var(--font-label);
      font-size: .54rem;
      font-weight: 950;
      text-align: center;
      text-transform: uppercase;
      transform: rotate(-9deg);
      box-shadow: var(--shadow-hard);
    }}

    .verdict-title {{
      margin: 0 0 10px;
      font-family: var(--font-display);
      font-size: clamp(1.2rem, 1.75vw, 1.55rem);
      line-height: 1.03;
      overflow-wrap: anywhere;
    }}

    .summary {{
      margin: 0;
      font-size: .84rem;
      line-height: 1.45;
    }}

    .action-card {{
      background: var(--color-safe-soft);
      width: min(100%, 920px);
      justify-self: start;
    }}

    .action-card .card-body {{
      display: grid;
      gap: 16px;
      padding: clamp(20px, 3vw, 30px);
    }}

    .action-title {{
      margin: 0;
      font-family: var(--font-label);
      font-weight: 950;
      text-transform: uppercase;
      font-size: .8rem;
    }}

    .action-text {{
      margin: 0;
      font-family: var(--font-display);
      font-weight: 800;
      font-size: clamp(.94rem, 1.1vw, 1.05rem);
      line-height: 1.18;
      overflow-wrap: anywhere;
    }}

    .dna-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }}

    .dna-item {{
      min-height: 70px;
      padding: 10px;
      border: 2px solid var(--color-rule);
      border-radius: 4px;
      background: linear-gradient(135deg, var(--color-paper) 0 78%, var(--color-fold) 79%);
    }}

    .dna-label {{
      margin-bottom: 9px;
      font-family: var(--font-label);
      font-size: .64rem;
      font-weight: 950;
      text-transform: uppercase;
    }}

    .dna-value {{
      font-family: var(--font-display);
      font-size: clamp(.78rem, .9vw, .88rem);
      font-weight: 800;
      line-height: 1.12;
      overflow-wrap: anywhere;
    }}

    .tactics {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 16px;
    }}

    .tag {{
      border: 1.5px solid var(--color-rule);
      background: var(--color-danger);
      color: var(--color-paper);
      padding: 6px 9px;
      border-radius: 999px;
      font-family: var(--font-label);
      font-size: .72rem;
      font-weight: 950;
      text-transform: uppercase;
    }}

    .copy-card {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 160px;
      gap: 14px;
      align-items: stretch;
    }}

    .copy-note {{
      max-height: 136px;
      overflow: auto;
      white-space: pre-wrap;
      border: 2px solid var(--color-rule);
      border-radius: 4px;
      background: var(--color-paper);
      padding: 14px;
      font-size: .78rem;
      line-height: 1.38;
    }}

    .copy-btn {{
      border: 2px solid var(--color-rule);
      border-radius: 4px;
      background: var(--color-paper);
      font-family: var(--font-label);
      font-weight: 950;
      font-size: .78rem;
      text-transform: uppercase;
      box-shadow: var(--shadow-hard);
      white-space: nowrap;
    }}

    .memory {{
      margin-top: 28px;
      padding: 18px;
    }}

    .memory h3 {{
      margin: 0 0 12px;
      font-family: var(--font-label);
      font-size: .86rem;
      text-transform: uppercase;
    }}

    .memory-list {{
      display: grid;
      gap: 10px;
    }}

    .memory-row {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: start;
      padding: 12px;
      border: 1.5px solid var(--color-rule);
      border-radius: 4px;
      background: var(--color-danger-soft);
      font-size: .76rem;
      line-height: 1.28;
    }}

    .memory-row.safe {{
      background: var(--color-safe-soft);
    }}

    .memory-row.needs_check,
    .memory-row.suspicious {{
      background: var(--color-check-soft);
    }}

    .memory-badge {{
      padding: 5px 7px;
      border: 1.5px solid var(--color-rule);
      background: var(--color-danger);
      color: var(--color-paper);
      font-family: var(--font-label);
      font-size: .68rem;
      font-weight: 950;
      text-transform: uppercase;
    }}

    .memory-badge.safe {{
      background: var(--color-safe);
    }}

    .memory-badge.needs_check,
    .memory-badge.suspicious {{
      background: var(--color-check);
    }}

    .footer-strip {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: center;
      gap: 8px 12px;
      margin-top: 30px;
      padding: 14px 18px;
      border-top: 2px solid var(--color-rule);
      color: var(--color-muted);
      font-family: var(--font-label);
      font-size: .78rem;
      font-weight: 800;
      text-align: center;
    }}

    .footer-strip strong {{
      color: var(--color-ink);
    }}

    .footer-dot {{
      color: var(--color-danger);
    }}

    .error {{
      border: 2px solid var(--color-rule);
      background: var(--color-danger-soft);
      padding: 14px;
      border-radius: 4px;
      font-weight: 800;
    }}

    @media (max-width: 1240px) {{
      .dna-grid {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
    }}

    @media (max-width: 860px) {{
      .shell {{
        width: min(100% - 22px, 620px);
        padding-top: 18px;
      }}

      .topbar {{
        align-items: flex-start;
        flex-direction: column;
        gap: 14px;
      }}

      .tagline {{
        font-size: .9rem;
      }}

      .status {{
        text-align: left;
        justify-content: flex-start;
      }}

      .status > span {{
        white-space: normal;
      }}

      .hero {{
        gap: 16px;
        padding: 26px 0 22px;
      }}

      .hero h2 {{
        max-width: 100%;
        white-space: normal;
        font-size: clamp(1.6rem, 7vw, 2.15rem);
      }}

      .hero p {{
        white-space: normal;
      }}

      .workspace {{
        grid-template-columns: 1fr;
        gap: 28px;
      }}

      .note {{
        padding: 20px;
      }}

      textarea {{
        min-height: 190px;
        font-size: .9rem;
      }}

      .paper::after {{
        width: 34px;
        height: 34px;
      }}

      .verdict-layout {{
        grid-template-columns: 1fr;
        justify-items: start;
      }}

      .standby-card .card-body {{
        grid-template-columns: 1fr;
      }}

      .stamp {{
        width: 72px;
        height: 72px;
        font-size: .58rem;
      }}

      .dna-grid {{
        grid-template-columns: 1fr;
      }}

      .result-top {{
        grid-template-columns: 1fr;
      }}

      .copy-card {{
        grid-template-columns: 1fr;
      }}

      .copy-btn {{
        min-height: 58px;
      }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <header class="topbar">
      <div class="brand">
        <img src="{logo_uri}" alt="" />
        <div class="brand-copy">
          <h1>Jawbreaker</h1>
          <p class="tagline">Local-first scam defense for someone you love.</p>
        </div>
      </div>
      <div class="status" aria-label="Runtime status">
        <span>{model_label}</span>
        <span><span id="modelState">READY</span></span>
      </div>
    </header>

    <section class="hero" aria-labelledby="heroTitle">
      <h2 id="heroTitle">Is this message safe?</h2>
      <p>Paste a text, email, or DM. Jawbreaker will show the risk, the warning signs, and the safest next step before you reply, click, or pay.</p>
      <div class="safety-note">Safety aid only, not legal, financial, or cybersecurity advice. Always verify through official channels.</div>
    </section>

    <section class="workspace">
      <aside>
        <form id="scanForm" class="paper note">
          <p class="section-label">Message to check</p>
          <textarea id="messageInput" placeholder="Paste a text, email, or DM here."></textarea>
          <button id="scanButton" class="run" type="submit">Check message</button>
          <div class="samples" id="samples" aria-label="Sample messages"></div>
        </form>
        <section class="paper memory" aria-live="polite">
          <h3>Earlier checks</h3>
          <div class="memory-list" id="memoryList">No scam memory saved yet.</div>
        </section>
      </aside>

      <section id="result" class="result-stack" aria-live="polite"></section>
    </section>

    <footer class="footer-strip" aria-label="Build details">
      <span><strong>Built for Build Small Hackathon</strong></span>
      <span class="footer-dot">•</span>
      <span>Powered by <strong id="modelLabel">{model_label}</strong></span>
      <span class="footer-dot">•</span>
      <span><strong>Gradio Server</strong></span>
      <span class="footer-dot">•</span>
      <span><strong id="runtimeLabel">{backend_label}</strong> runtime</span>
      <span class="footer-dot">•</span>
      <span>trained and evaled on <strong>Modal</strong></span>
    </footer>
  </main>

  <script type="application/json" id="examplesData">{examples_json}</script>
  <script type="module">
    import {{ Client }} from "https://cdn.jsdelivr.net/npm/@gradio/client/dist/index.min.js";

    const examples = JSON.parse(document.getElementById("examplesData").textContent);
    const state = {{ memory: [] }};
    const clientPromise = Client.connect(window.location.origin);
    const form = document.getElementById("scanForm");
    const messageInput = document.getElementById("messageInput");
    const scanButton = document.getElementById("scanButton");
    const result = document.getElementById("result");
    const samples = document.getElementById("samples");
    const memoryList = document.getElementById("memoryList");
    const modelLabel = document.getElementById("modelLabel");
    const modelState = document.getElementById("modelState");

    const labels = {{
      dangerous: ["Dangerous", "This looks dangerous"],
      suspicious: ["Suspicious", "This looks suspicious"],
      needs_check: ["Check first", "Verify before acting"],
      safe: ["Looks safe", "No strong scam pattern"]
    }};

    const dnaLabels = {{
      Impersonates: "Who they pretend to be",
      Pressure: "How they pressure you",
      Ask: "What they want",
      Risk: "What could happen"
    }};

    function escapeHtml(value) {{
      return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }}

    function humanize(value) {{
      return String(value || "Unknown").replaceAll("_", " ").replaceAll("-", " ");
    }}

    function elapsedText(value) {{
      const numeric = Number(value);
      if (!Number.isFinite(numeric) || numeric <= 0) {{
        return "result";
      }}
      return `${{numeric.toFixed(numeric >= 10 ? 0 : 1)}}s`;
    }}

    function showStandby() {{
      result.innerHTML = `
        <article class="card standby-card">
          <div class="card-head"><span>Ready to check</span><span>private model</span></div>
          <div class="card-body">
            <div>
              <div class="shield-mark" aria-hidden="true"></div>
              <h3>Paste first. Act after.</h3>
              <p>Jawbreaker checks who the message pretends to be, what it asks you to do, and what could go wrong. The first scan may take longer while the private GPU wakes up.</p>
              <ul class="standby-list" aria-label="What Jawbreaker checks">
                <li><strong>1</strong><span>Paste the message exactly as you received it.</span></li>
                <li><strong>2</strong><span>Review the verdict and the safest next step before replying.</span></li>
                <li><strong>3</strong><span>Copy the plan if you want a trusted person to check it with you.</span></li>
              </ul>
            </div>
            <div class="standby-preview" aria-label="What Jawbreaker returns">
              <div class="standby-tile">
                <strong>Risk</strong>
                <span>Clear safe, suspicious, or dangerous verdict.</span>
              </div>
              <div class="standby-tile">
                <strong>Warning signs</strong>
                <span>Who they pretend to be, what they ask, and what could happen.</span>
              </div>
              <div class="standby-tile">
                <strong>Next step</strong>
                <span>Plain advice you can copy to someone you trust.</span>
              </div>
            </div>
          </div>
        </article>
      `;
    }}

    function showLoading() {{
      result.innerHTML = `
        <article class="card loading-card">
          <div class="card-head"><span>Checking message</span><span id="progressText">Starting</span></div>
          <div class="card-body">
            <div class="fold-loader">
              <div class="fold-bar" id="foldBar" style="--progress: 12%"></div>
              <p class="loading-line">> waking the local safety model...</p>
              <p class="loading-line">> reading the message...</p>
              <p class="loading-line muted">> checking pressure and impersonation...</p>
              <p class="loading-line muted">> preparing the safest next step...</p>
            </div>
          </div>
        </article>
      `;
      let progress = 12;
      const timer = window.setInterval(() => {{
        progress = Math.min(88, progress + 8);
        const bar = document.getElementById("foldBar");
        const text = document.getElementById("progressText");
        if (!bar || !text) {{
          window.clearInterval(timer);
          return;
        }}
        bar.style.setProperty("--progress", `${{progress}}%`);
        text.textContent = progress < 88 ? `${{progress}}% complete` : "Almost ready";
      }}, 700);
      return timer;
    }}

    function renderMemory(items) {{
      if (!items || !items.length) {{
        memoryList.textContent = "No scam memory saved yet.";
        return;
      }}
      memoryList.innerHTML = items.slice(-4).reverse().map((item) => {{
        const risk = item.risk_level || "needs_check";
        return `
        <div class="memory-row ${{escapeHtml(risk)}}">
          <span>${{escapeHtml(item.summary)}}</span>
          <strong class="memory-badge ${{escapeHtml(risk)}}">${{escapeHtml(risk)}}</strong>
        </div>
      `}}).join("");
    }}

    function renderVerdict(payload) {{
      const analysis = payload.analysis || {{}};
      const risk = analysis.risk_level || "needs_check";
      const label = labels[risk] || labels.needs_check;
      const dna = analysis.scam_dna || {{}};
      const tactics = analysis.tactics || [];
      modelLabel.textContent = payload.model_label || modelLabel.textContent;
      state.memory = payload.memory || state.memory;
      renderMemory(state.memory);

      const dnaHtml = ["Impersonates", "Pressure", "Ask", "Risk"].map((key) => `
        <div class="dna-item">
          <div class="dna-label">${{dnaLabels[key]}}</div>
          <div class="dna-value">${{escapeHtml(humanize(dna[key]))}}</div>
        </div>
      `).join("");

      const tacticsHtml = tactics.length
        ? tactics.map((tag) => `<span class="tag">${{escapeHtml(humanize(tag))}}</span>`).join("")
        : `<span class="tag">none found</span>`;
      const elapsed = elapsedText(payload.elapsed_seconds);

      result.innerHTML = `
        <div class="result-top">
          <article class="card verdict-card ${{escapeHtml(risk)}}">
            <div class="card-head"><span>Jawbreaker says</span><span>${{escapeHtml(elapsed)}}</span></div>
            <div class="card-body">
              <div class="verdict-layout">
                <div class="stamp">${{escapeHtml(label[0])}}</div>
                <div>
                  <h3 class="verdict-title">${{escapeHtml(label[1])}}</h3>
                  <p class="summary">${{escapeHtml(analysis.summary)}}</p>
                </div>
              </div>
            </div>
          </article>

          <article class="card">
            <div class="card-head"><span>Warning signs</span><span>how it works</span></div>
            <div class="card-body">
              <div class="dna-grid">${{dnaHtml}}</div>
              <div class="tactics">${{tacticsHtml}}</div>
            </div>
          </article>
        </div>

        <article class="card action-card">
          <div class="card-head"><span>Safest next step</span><span>send to someone you trust</span></div>
          <div class="card-body">
            <p class="action-title">Recommended action</p>
            <p class="action-text">${{escapeHtml(analysis.safest_action)}}</p>
            <div class="copy-card">
              <div class="copy-note" id="copyNote">${{escapeHtml(payload.copy_plan)}}</div>
              <button class="copy-btn" id="copyButton" type="button">Click to copy</button>
            </div>
          </div>
        </article>
      `;

      document.getElementById("copyButton").addEventListener("click", async () => {{
        await navigator.clipboard.writeText(payload.copy_plan || "");
        const button = document.getElementById("copyButton");
        button.textContent = "Copied";
        window.setTimeout(() => button.textContent = "Click to copy", 1200);
      }});
    }}

    function showError(error) {{
      result.innerHTML = `
        <article class="card">
          <div class="card-head"><span>Could not finish</span><span>try again</span></div>
          <div class="card-body"><div class="error">${{escapeHtml(error.message || error)}}</div></div>
        </article>
      `;
    }}

    examples.forEach((example) => {{
      const button = document.createElement("button");
      button.type = "button";
      button.className = "sample";
      button.textContent = example;
      button.addEventListener("click", () => {{
        messageInput.value = example;
        messageInput.focus();
      }});
      samples.appendChild(button);
    }});

    form.addEventListener("submit", async (event) => {{
      event.preventDefault();
      const message = messageInput.value.trim();
      if (!message) {{
        messageInput.focus();
        return;
      }}
      scanButton.disabled = true;
      modelState.textContent = "CHECKING";
      const timer = showLoading();
      try {{
        const client = await clientPromise;
        const response = await client.predict("/analyze", {{
          message,
          memory: state.memory
        }});
        window.clearInterval(timer);
        renderVerdict(response.data?.[0] || response);
        modelState.textContent = "READY";
      }} catch (error) {{
        window.clearInterval(timer);
        modelState.textContent = "READY";
        showError(error);
      }} finally {{
        scanButton.disabled = false;
      }}
    }});

    showStandby();
  </script>
</body>
</html>"""


def build_server() -> gr.Server:
    app = gr.Server()

    @app.api(name="analyze")
    @gpu_callback
    def analyze_api(message: str, memory: list[dict] | None = None) -> dict[str, Any]:
        return analysis_payload(message, memory)

    @app.api(name="warm")
    @gpu_callback
    def warm_api() -> dict[str, str]:
        warm_model_impl()
        return {"status": "ready", "backend": current_backend(), "model": model_status_label()}

    @app.get("/", response_class=HTMLResponse)
    async def homepage() -> HTMLResponse:
        return HTMLResponse(paper_shield_html())

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "backend": current_backend(), "model": model_status_label()}

    return app


def build_handoff_message(message: str, analysis: ScamAnalysis) -> str:
    cleaned = " ".join(message.strip().split())
    if len(cleaned) > 500:
        cleaned = cleaned[:497].rstrip() + "..."

    risk = analysis.risk_level.replace("_", " ")
    scam_type = analysis.scam_type.replace("_", " ")
    risk_line = f"Jawbreaker marked it as {risk}"
    if scam_type and scam_type != "none":
        risk_line += f" ({scam_type})"

    return (
        "Can you check this message with me before I do anything?\n\n"
        f"Message I received:\n\"{cleaned}\"\n\n"
        f"{risk_line}.\n"
        f"Safest next step: {analysis.safest_action}\n\n"
        "I have not clicked any links, replied, or sent anything."
    )


def should_use_heuristic_guard(
    model_analysis: ScamAnalysis,
    heuristic: ScamAnalysis,
    validation_errors: list[str],
    message: str = "",
) -> bool:
    return should_apply_heuristic_guard(message, model_analysis, heuristic, validation_errors)


@gpu_callback
def analyze_message(
    message: str,
    memory: list[dict] | None,
):
    memory = memory or []
    if not message.strip():
        analysis = ScamAnalysis.from_heuristics(message, memory)
        yield (
            render_analysis_html(message, analysis),
            render_memory_html(analysis, memory),
            memory,
            {},
            gr.update(interactive=True),
            gr.update(interactive=True),
        )
        return

    for active_step, progress in [(0, 12), (1, 30), (2, 54), (3, 76)]:
        yield (
            render_scanning_html(active_step=active_step, progress=progress),
            render_current_memory(memory),
            memory,
            {},
            gr.update(interactive=False),
            gr.update(interactive=False),
        )
        sleep(0.25)

    try:
        analysis = run_analysis(message, memory)
    except Exception as exc:
        analysis = analysis_error(exc)
        yield (
            render_analysis_html(message, analysis),
            render_memory_html(analysis, memory),
            memory,
            {},
            gr.update(interactive=True),
            gr.update(interactive=True),
        )
        return

    last_scan = {
        "message": message,
        "entry": memory_entry_from_analysis(message, analysis),
    }
    entry = last_scan["entry"]
    if not memory or memory[-1].get("text") != entry.get("text"):
        memory.append(entry)
    yield (
        render_analysis_html(message, analysis),
        render_memory_html(analysis, memory),
        memory,
        last_scan,
        gr.update(interactive=True),
        gr.update(interactive=True),
    )


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


def remember_current(message: str, memory: list[dict] | None, last_scan: dict | None) -> tuple[str, str, list[dict]]:
    memory = memory or []
    if not message.strip():
        return render_save_status("Paste a message first."), render_current_memory(memory), memory

    last_scan = last_scan or {}
    entry = last_scan.get("entry")
    if last_scan.get("message") != message or not isinstance(entry, dict):
        return (
            render_save_status("Analyze this message first, then save the pattern."),
            render_current_memory(memory),
            memory,
        )

    if memory and memory[-1].get("text") == entry.get("text"):
        return (
            render_save_status("This pattern is already saved for this session."),
            render_current_memory(memory),
            memory,
        )

    memory.append(entry)
    return render_save_status("Saved this scam pattern for this session."), render_current_memory(memory), memory


def build_app() -> gr.Blocks:
    gr.set_static_paths(paths=[LOGO_PATH.resolve()])
    with gr.Blocks(title="Jawbreaker") as demo:
        memory_state = gr.State([])
        last_scan_state = gr.State({})

        gr.HTML(
            """
            <header class="topbar">
              <div class="brand-lockup">
                <span class="brand-mark" aria-hidden="true">
                  <img src="/gradio_api/file=jawbreaker_logo.png" alt="" />
                </span>
                <span class="brand-name">JAWBREAKER</span>
              </div>
              <div class="status-tags">
                <span>[ SECURE_ENV: ACTIVE ]</span>
                <span>[ STATUS: READY ]</span>
                <span>[ MODEL: MINICPM5_1B_LORA_V4 ]</span>
                <span>[ BUILT_FOR: BUILD_SMALL_HACKATHON ]</span>
              </div>
            </header>
            """
        )

        with gr.Row(elem_classes=["main-grid"]):
            with gr.Column(scale=5, elem_classes=["scan-panel"]):
                gr.HTML(
                    """
                    <div class="window-titlebar input-titlebar">
                      <span class="traffic-dots" aria-hidden="true"><i></i><i></i><i></i></span>
                      <span>Message to check</span>
                    </div>
                    <p class="panel-kicker">MESSAGE TO CHECK</p>
                    """
                )
                message = gr.Textbox(
                    label=None,
                    show_label=False,
                    placeholder="Paste a text, email, or DM here.",
                    lines=10,
                    max_lines=16,
                )
                analyze = gr.Button("Check message", variant="primary", elem_classes=["check-btn"])
                gr.Examples(examples=EXAMPLES, inputs=message, label="Try a sample")
                memory = gr.HTML(render_current_memory([]))

            with gr.Column(scale=7):
                result = gr.HTML(
                    """
                    <div class="home-stack">
                      <section class="retro-window status-window">
                        <div class="window-titlebar"><span>Ready to check</span></div>
                        <div class="window-body status-body">
                          <p class="standing-by">SYSTEM STANDING BY</p>
                          <h2>Jawbreaker is ready to shield your loved ones from digital fraud.</h2>
                          <p>Paste any text message, email, or DM on the left. The local model will evaluate risk factors, unpack the scam strategy, and deliver a plain-English protection plan.</p>
                        </div>
                      </section>
                      <section class="retro-window guide-window">
                        <div class="window-titlebar"><span>How to use it</span></div>
                        <div class="window-body guide-body">
                          <p>1. Copy a text message from your phone or an email that feels off.</p>
                          <p>2. Paste it into the input area on the left of this screen.</p>
                          <p>3. Click RUN SCAM DETECTOR to analyze it with private local AI.</p>
                        </div>
                      </section>
                    </div>
                    """
                )
        analyze.click(
            fn=analyze_message,
            inputs=[message, memory_state],
            outputs=[result, memory, memory_state, last_scan_state, message, analyze],
            show_progress="hidden",
        )
        demo.load(
            fn=warm_model,
            inputs=None,
            outputs=None,
            show_progress="hidden",
            api_visibility="private",
        )
    return demo


if __name__ == "__main__":
    if _env_bool("JAWBREAKER_LEGACY_BLOCKS", False):
        build_app().launch(
            theme=app_theme(),
            css=app_css(),
            js=FORCE_LIGHT_JS,
            head=FORCE_LIGHT_HEAD,
            favicon_path=str(LOGO_PATH),
        )
    else:
        build_server().launch(favicon_path=str(LOGO_PATH))
