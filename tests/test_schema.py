from jawbreaker.schema import ScamAnalysis


def test_family_impersonation_is_dangerous() -> None:
    analysis = ScamAnalysis.from_heuristics(
        "Hi Grandma, I lost my phone. This is my new number. Can you send $800 today?"
    )

    assert analysis.risk_level == "dangerous"
    assert analysis.scam_type == "family_impersonation"
    assert "Trust a new number" == analysis.scam_dna["Ask"]


def test_legitimate_fraud_alert_needs_check_not_dangerous() -> None:
    analysis = ScamAnalysis.from_heuristics(
        "Chase fraud alert: Did you attempt a $249.00 purchase at TARGET? Reply YES or NO."
    )

    assert analysis.risk_level == "needs_check"
    assert analysis.scam_type == "possible_legitimate_alert"

