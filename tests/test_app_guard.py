from app import remember_current, should_use_heuristic_guard
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
