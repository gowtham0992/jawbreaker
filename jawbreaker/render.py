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
        <section class="retro-window empty-state">
          <div class="window-titlebar"><span>waiting_for_input.sys</span></div>
          <div class="window-body">
            <div class="empty-terminal">
              <p class="terminal-label">STATUS:</p>
              <h2>Paste a message to begin scan.</h2>
              <p>Jawbreaker will classify the threat, explain the scam DNA, and generate a safe copy plan.</p>
            </div>
          </div>
        </section>
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
    <section class="retro-window scanning-state">
      <div class="window-titlebar"><span>running_detector.job</span></div>
      <div class="window-body">
        <h2>RUNNING SCAM DETECTOR...</h2>
        <div class="scan-steps">
          <div class="scan-step done">READ_MESSAGE: OK</div>
          <div class="scan-step active">MATCH_SCAM_SIGNATURES: RUNNING</div>
          <div class="scan-step pending">BUILD_SAFE_REMEDY: QUEUED</div>
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
