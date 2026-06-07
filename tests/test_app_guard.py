from app import (
    DEFAULT_ADAPTER_ID,
    DEFAULT_TRANSFORMERS_MAX_TOKENS,
    DEFAULT_TRANSFORMERS_MODEL_ID,
    build_handoff_message,
    default_adapter_id,
    remember_current,
    run_analysis,
    should_use_heuristic_guard,
)
from jawbreaker.analyzers import repair_prediction
from jawbreaker.schema import ScamAnalysis


def test_guard_uses_heuristic_when_model_undercalls_dangerous_message() -> None:
    model = ScamAnalysis(
        risk_level="needs_check",
        scam_type="unknown",
        summary="Check this before acting.",
        tactics=[],
        scam_dna={"Impersonates": "", "Pressure": "", "Ask": "", "Risk": ""},
    )
    heuristic = ScamAnalysis.from_heuristics(
        "Hi Grandma, I lost my phone. This is my new number. Can you send $800 today?"
    )

    assert should_use_heuristic_guard(model, heuristic, validation_errors=[])


def test_guard_keeps_informative_model_result() -> None:
    model = ScamAnalysis(
        risk_level="dangerous",
        scam_type="family_impersonation",
        summary="This looks like a family emergency scam.",
        tactics=["impersonation", "urgency"],
        scam_dna={
            "Impersonates": "Family member",
            "Pressure": "Act today",
            "Ask": "Send money",
            "Risk": "payment request",
        },
    )
    heuristic = ScamAnalysis.from_heuristics(
        "Hi Grandma, I lost my phone. This is my new number. Can you send $800 today?"
    )

    assert not should_use_heuristic_guard(model, heuristic, validation_errors=[])


def test_remember_current_saves_last_scan_without_reanalysis(monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("remember_current should not run analysis")

    monkeypatch.setattr("app.run_analysis", fail_if_called)

    status, memory_html, memory = remember_current(
        "Hi Grandma, I lost my phone.",
        [],
        {
            "message": "Hi Grandma, I lost my phone.",
            "entry": {
                "summary": "This looks like family impersonation.",
                "scam_type": "family_impersonation",
                "risk_level": "dangerous",
                "fingerprint": {"Impersonates": "Family member"},
                "text": "Hi Grandma, I lost my phone.",
            },
        },
    )

    assert "Saved this scam pattern for this session." in status
    assert len(memory) == 1
    assert "Session scam memory" in memory_html


def test_handoff_message_includes_original_text_and_safe_action() -> None:
    message = "Hi Grandma, I lost my phone. This is my new number. Can you send $800 today?"
    analysis = ScamAnalysis.from_heuristics(message)

    handoff = build_handoff_message(message, analysis)

    assert "Message I received:" in handoff
    assert message in handoff
    assert "Jawbreaker marked it as dangerous (family impersonation)." in handoff
    assert "Safest next step:" in handoff
    assert analysis.safest_action in handoff
    assert "I have not clicked any links, replied, or sent anything." in handoff


def test_run_analysis_falls_back_to_heuristic_when_model_fails(monkeypatch) -> None:
    def broken_analyzer():
        def analyze(message: str):
            raise ValueError("model returned invalid JSON")

        return analyze

    monkeypatch.setattr("app.get_analyzer", broken_analyzer)
    analysis = run_analysis(
        "Hi Grandma, I lost my phone. This is my new number. Can you send $800 today?",
        [],
    )

    assert analysis.risk_level == "dangerous"
    assert analysis.scam_type == "family_impersonation"
    assert "safety fallback" in analysis.summary


def test_repair_prediction_adds_missing_summary_without_changing_risk() -> None:
    repaired = repair_prediction(
        {
            "risk_level": "dangerous",
            "scam_type": "family impersonation",
            "tactics": ["urgency"],
            "safest_action": "Do not send money.",
            "trusted_person_message": "Can you check this with me?",
            "scam_dna": {"impersonates": "family member"},
        }
    )

    assert repaired["risk_level"] == "dangerous"
    assert repaired["summary"] == "This looks dangerous: likely family impersonation."


def test_default_adapter_only_attaches_to_minicpm(monkeypatch) -> None:
    monkeypatch.delenv("JAWBREAKER_ADAPTER_ID", raising=False)

    assert default_adapter_id(DEFAULT_TRANSFORMERS_MODEL_ID) == DEFAULT_ADAPTER_ID
    assert default_adapter_id("Qwen/Qwen3-0.6B") is None
    assert DEFAULT_TRANSFORMERS_MAX_TOKENS == 512
