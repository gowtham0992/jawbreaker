from app import should_use_heuristic_guard
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
