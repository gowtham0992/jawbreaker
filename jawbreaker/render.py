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
    "dangerous": ("CRITICAL: Scam Detected", "verdict_danger_override.log"),
    "suspicious": ("WARNING: Suspicious Pattern Found", "verdict_suspicious_trace.log"),
    "needs_check": ("REVIEW: Verify Before Acting", "verdict_needs_human_check.log"),
    "safe": ("CLEAR: No Strong Scam Pattern", "verdict_safe_route.log"),
}

RISK_WINDOW_CLASS = {
    "dangerous": "risk-dangerous",
    "suspicious": "risk-suspicious",
    "needs_check": "risk-needs_check",
    "safe": "risk-safe",
}

RISK_BADGE = {
    "dangerous": "DANGER",
    "suspicious": "SUSPECT",
    "needs_check": "CHECK",
    "safe": "CLEAR",
}


def render_window(title: str, body: str, class_name: str = "") -> str:
    classes = f"retro-window {class_name}".strip()
    return f"""
    <section class="{classes}">
      <div class="window-titlebar">
        <span>{escape(title)}</span>
      </div>
      <div class="window-body">
        {body}
      </div>
    </section>
    """


def render_analysis_html(message: str, analysis: ScamAnalysis) -> str:
    if not message.strip():
        return """
        <div class="home-stack">
          <section class="retro-window status-window">
            <div class="window-titlebar"><span>system_status.log</span></div>
            <div class="window-body status-body">
              <p class="standing-by">SYSTEM STANDING BY</p>
              <h2>Jawbreaker is ready to shield your loved ones from digital fraud.</h2>
              <p>Paste any text message, email, or DM on the left. The local model will evaluate risk factors, unpack the scam strategy, and deliver a plain-English protection plan.</p>
            </div>
          </section>
          <section class="retro-window guide-window">
            <div class="window-titlebar"><span>quick_start_manual.txt</span></div>
            <div class="window-body guide-body">
              <p>1. Copy a text message from your phone or an email that feels off.</p>
              <p>2. Paste it into the input area on the left of this screen.</p>
              <p>3. Click RUN SCAM DETECTOR to analyze it with private local AI.</p>
            </div>
          </section>
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
    verdict_title, verdict_file = VERDICT_COPY[analysis.risk_level]
    verdict_subtitle = analysis.summary.replace("This looks dangerous: likely ", "Likely ").rstrip(".")
    risk_class = RISK_WINDOW_CLASS[analysis.risk_level]

    verdict = f"""
      <div class="verdict-header">
        <span class="verdict-icon" aria-hidden="true"></span>
        <div>
          <h2 class="verdict-title">{escape(verdict_title)}</h2>
          <p class="verdict-subtitle">{escape(verdict_subtitle)}.</p>
        </div>
      </div>
      {memory_html}
    """

    dna = f"""
      <div class="dna-grid">{dna_html}</div>
      <div class="tactics">{tactic_html or "<span class='tactic'>none found</span>"}</div>
    """

    remedy = f"""
      <div class="remedy-copy">
        <p class="terminal-label">RECOMMENDED ACTION:</p>
        <p>{escape(analysis.safest_action)}</p>
      </div>
      <div class="trusted-inline">{escape(analysis.trusted_person_message)}</div>
    """

    return f"""
    <div class="report-stack">
      {render_window(verdict_file, verdict, f"verdict-window {risk_class}")}
      {render_window("scam_signature_dna.bin", dna, "dna-window")}
      {render_window("safe_remedy_steps.sh", remedy, "action-window")}
    </div>
    """


def render_scanning_html() -> str:
    return """
    <section class="retro-window scanning-state terminal-window">
      <div class="window-titlebar"><span>scanning_in_progress.sh</span></div>
      <div class="window-body">
        <p class="terminal-progress">[██████████░░] 84% COMPLETE</p>
        <div class="terminal-log">
          <p>> importing offline AI model runtime...</p>
          <p>> checking message semantics and urgency markers...</p>
          <p>> comparing against known scam signatures...</p>
          <p>> building safe response plan...</p>
          <p class="terminal-muted">> finalizing report...</p>
        </div>
      </div>
    </section>
    """


def render_memory_html(analysis: ScamAnalysis, memory: list[dict]) -> str:
    if not memory:
        return render_window(
            "threat_history_log.db",
            "<p class='memory-empty'>No scam memory saved yet.</p>",
            "memory-card muted",
        )

    items = "".join(
        f"""
        <div class="memory-row">
          <span>{escape(item.get('summary', ''))}</span>
          <strong class="memory-badge">{escape(RISK_BADGE.get(item.get('risk_level', ''), item.get('risk_level', '')))}</strong>
        </div>
        """
        for item in memory[-5:]
    )
    return render_window("threat_history_log.db", f"<p class='memory-title'>Session scam memory</p>{items}", "memory-card")
