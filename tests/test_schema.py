from jawbreaker.schema import ScamAnalysis
from jawbreaker.analyzers import prediction_to_analysis
from jawbreaker.render import render_analysis_html


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


def test_prediction_to_analysis_normalizes_model_json() -> None:
    analysis = prediction_to_analysis(
        {
            "risk_level": "not_valid",
            "scam_type": "package_phishing",
            "summary": "Fake delivery notice.",
            "tactics": ["fake authority"],
            "safest_action": "Open the official carrier website yourself.",
            "trusted_person_message": "Can you check this?",
            "scam_dna": {
                "impersonates": "USPS",
                "pressure": "Held package",
                "ask": "Open link",
                "risk": "credential theft",
            },
        },
        similar_memory="This resembles a saved pattern.",
    )

    assert analysis.risk_level == "needs_check"
    assert analysis.scam_dna["Impersonates"] == "USPS"
    assert analysis.similar_memory == "This resembles a saved pattern."


def test_render_humanizes_model_style_labels() -> None:
    analysis = ScamAnalysis(
        risk_level="dangerous",
        scam_type="credential_theft",
        summary="This message mentions credential_theft.",
        tactics=["unknown_urgent_action", "credential_theft"],
        safest_action="Do not click the link.",
        scam_dna={
            "Impersonates": "legitimate_company",
            "Pressure": "sense_of_urgency",
            "Ask": "click_link_and_verify",
            "Risk": "credential_theft",
        },
    )

    html = render_analysis_html("USPS: verify now", analysis)

    assert "legitimate company" in html
    assert "click a link and verify" in html
    assert "unknown_urgent_action" not in html
