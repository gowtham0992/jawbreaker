from __future__ import annotations

from html import escape

from jawbreaker.schema import ScamAnalysis


def render_analysis_html(message: str, analysis: ScamAnalysis) -> str:
    if not message.strip():
        return """
        <div class="empty-state">
          <h2>Paste a message to scan it.</h2>
          <p>Jawbreaker will show the risk, the Scam DNA, and the safest next step.</p>
        </div>
        """

    tactic_html = "".join(f"<span class='tactic'>{escape(tactic)}</span>" for tactic in analysis.tactics)
    dna_html = "".join(
        f"""
        <div class="dna-item">
          <div class="dna-label">{escape(label)}</div>
          <div class="dna-value">{escape(value)}</div>
        </div>
        """
        for label, value in analysis.scam_dna.items()
    )
    memory_html = f"<p><strong>Memory:</strong> {escape(analysis.similar_memory)}</p>" if analysis.similar_memory else ""

    return f"""
    <section class="verdict-card risk-{escape(analysis.risk_level)}">
      <span class="risk-pill">{escape(analysis.risk_level.replace("_", " "))}</span>
      <p class="summary">{escape(analysis.summary)}</p>
      <div class="action-card">
        <strong>Safest next step</strong>
        <p>{escape(analysis.safest_action)}</p>
      </div>
      <h3>Scam DNA</h3>
      <div class="dna-grid">{dna_html}</div>
      <h3>Warning signs</h3>
      <div class="tactics">{tactic_html or "<span class='tactic'>none found</span>"}</div>
      {memory_html}
      <h3>Ask someone you trust</h3>
      <p>{escape(analysis.trusted_person_message)}</p>
    </section>
    """


def render_memory_html(analysis: ScamAnalysis, memory: list[dict]) -> str:
    if not memory:
        return "<div class='memory-card muted'>No scam memory saved yet.</div>"

    items = "".join(
        f"<li><strong>{escape(item.get('risk_level', ''))}</strong>: {escape(item.get('summary', ''))}</li>"
        for item in memory[-5:]
    )
    return f"""
    <div class="memory-card">
      <strong>Session scam memory</strong>
      <ul>{items}</ul>
    </div>
    """

