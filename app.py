import gradio as gr

from jawbreaker.render import render_analysis_html, render_memory_html
from jawbreaker.schema import ScamAnalysis


EXAMPLES = [
    "USPS: Your package is held due to an unpaid fee. Verify now: http://usps-track-secure.example",
    "Hi Grandma, I lost my phone. This is my new number. Can you send $800 for rent today? Please don't tell Mom.",
    "Chase fraud alert: Did you attempt a $249.00 purchase at TARGET? Reply YES or NO.",
]


def analyze_message(message: str, memory: list[dict] | None) -> tuple[str, str, list[dict]]:
    memory = memory or []
    analysis = ScamAnalysis.from_heuristics(message, memory)
    return render_analysis_html(message, analysis), render_memory_html(analysis, memory), memory


def remember_current(message: str, memory: list[dict] | None) -> tuple[str, list[dict]]:
    memory = memory or []
    analysis = ScamAnalysis.from_heuristics(message, memory)
    if not message.strip():
        return "Paste a message first.", memory

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
    css = open("style.css", "r", encoding="utf-8").read()
    theme = gr.themes.Soft(
        primary_hue="red",
        secondary_hue="slate",
        neutral_hue="zinc",
        radius_size="sm",
    )

    with gr.Blocks(title="Jawbreaker", theme=theme, css=css) as demo:
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
    build_app().launch()

