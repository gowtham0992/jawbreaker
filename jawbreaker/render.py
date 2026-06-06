from __future__ import annotations

from html import escape

from jawbreaker.schema import ScamAnalysis


DNA_LABELS = {
    "Impersonates": "Who they pretend to be",
    "Pressure": "How they pressure you",
    "Ask": "What they want",
    "Risk": "What could happen",
}

VERDICT_COPY = {
    "dangerous": ("This looks dangerous", "danger"),
    "suspicious": ("This looks suspicious", "warning"),
    "needs_check": ("Check this before you act", "check"),
    "safe": ("This looks safe", "safe"),
}


def render_analysis_html(message: str, analysis: ScamAnalysis) -> str:
    if not message.strip():
        return """
        <div class="empty-state">
          <div class="shield-mark" aria-hidden="true"></div>
          <h2>Paste a message to scan it.</h2>
          <p>Got a text, email, or DM that feels off? Paste it here.<br>Jawbreaker will tell you if it's safe and what to do next.</p>
        </div>
        """

    tactic_html = "".join(f"<span class='tactic'>{escape(tactic)}</span>" for tactic in analysis.tactics)
    dna_html = "".join(
        f"""
        <div class="dna-item">
          <div class="dna-label">{escape(DNA_LABELS.get(label, label))}</div>
          <div class="dna-value">{escape(value)}</div>
        </div>
        """
        for label, value in analysis.scam_dna.items()
    )
    memory_html = f"<p><strong>Memory:</strong> {escape(analysis.similar_memory)}</p>" if analysis.similar_memory else ""
    verdict_title, icon_class = VERDICT_COPY[analysis.risk_level]
    verdict_subtitle = analysis.summary.replace("This looks dangerous: likely ", "Likely ").rstrip(".")

    return f"""
    <section class="verdict-card risk-{escape(analysis.risk_level)}">
      <p class="section-kicker">Verdict</p>
      <div class="verdict-header">
        <span class="verdict-icon verdict-icon-{escape(icon_class)}" aria-hidden="true"></span>
        <div>
          <h2 class="verdict-title">{escape(verdict_title)}</h2>
          <p class="verdict-subtitle">{escape(verdict_subtitle)}.</p>
        </div>
      </div>
      <div class="action-card">
        <strong>What to do</strong>
        <p>{escape(analysis.safest_action)}</p>
      </div>
      <h3>How this scam works 🔍</h3>
      <p class="section-kicker">Scam DNA</p>
      <div class="dna-grid">{dna_html}</div>
      <h3>Warning signs ⚡</h3>
      <div class="tactics">{tactic_html or "<span class='tactic'>none found</span>"}</div>
      {memory_html}
      <h3>Send this to someone you trust 💬</h3>
      <p class="trusted-inline">{escape(analysis.trusted_person_message)}</p>
    </section>
    """


def render_scanning_html() -> str:
    return """
    <section class="scanning-state">
      <div class="shield-pulse" aria-hidden="true"></div>
      <h2>Scanning message...</h2>
      <div class="scan-steps">
        <div class="scan-step done">Reading message</div>
        <div class="scan-step active">Checking for scam patterns</div>
        <div class="scan-step pending">Building safety report</div>
      </div>
    </section>
    """


def render_memory_html(analysis: ScamAnalysis, memory: list[dict]) -> str:
    if not memory:
        return "<div class='memory-card muted'><strong>Session memory</strong><p>No scam memory saved yet.</p></div>"

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
