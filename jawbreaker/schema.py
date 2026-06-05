from __future__ import annotations

from dataclasses import dataclass, field


RISK_LEVELS = {"dangerous", "suspicious", "needs_check", "safe"}


@dataclass
class ScamAnalysis:
    risk_level: str
    scam_type: str
    summary: str
    tactics: list[str] = field(default_factory=list)
    safest_action: str = ""
    trusted_person_message: str = ""
    scam_dna: dict[str, str] = field(default_factory=dict)
    similar_memory: str = ""

    def __post_init__(self) -> None:
        if self.risk_level not in RISK_LEVELS:
            raise ValueError(f"Invalid risk level: {self.risk_level}")

    @classmethod
    def from_heuristics(cls, message: str, memory: list[dict] | None = None) -> "ScamAnalysis":
        text = message.lower()
        memory = memory or []

        risk_level = "safe"
        scam_type = "none"
        tactics: list[str] = []

        if any(token in text for token in ["verify", "password", "login", "account locked", "account is locked"]):
            risk_level = "dangerous"
            scam_type = "credential_theft"
            tactics.extend(["credential request", "fake authority"])

        if any(token in text for token in ["urgent", "immediately", "today", "24 hours", "act now", "held"]):
            if risk_level == "safe":
                risk_level = "suspicious"
            tactics.append("urgency")

        if any(token in text for token in ["gift card", "zelle", "crypto", "wire", "$800", "send money"]):
            risk_level = "dangerous"
            scam_type = "payment_request"
            tactics.append("payment pressure")

        if any(token in text for token in ["grandma", "new number", "don't tell", "dont tell"]):
            risk_level = "dangerous"
            scam_type = "family_impersonation"
            tactics.extend(["impersonation", "secrecy"])

        if "http://" in text or "https://" in text:
            if risk_level == "safe":
                risk_level = "suspicious"
            tactics.append("suspicious link")

        if "reply yes or no" in text and "fraud alert" in text:
            risk_level = "needs_check"
            scam_type = "possible_legitimate_alert"
            tactics = ["verification needed"]

        tactics = sorted(set(tactics))
        summary = _summary_for(risk_level, scam_type)
        similar_memory = _find_similar_memory(text, memory)

        return cls(
            risk_level=risk_level,
            scam_type=scam_type,
            summary=summary,
            tactics=tactics,
            safest_action=_safe_action_for(risk_level, scam_type),
            trusted_person_message=_trusted_message_for(risk_level, scam_type),
            scam_dna={
                "Impersonates": _guess_impersonation(text),
                "Pressure": _guess_pressure(tactics),
                "Ask": _guess_ask(text, scam_type),
                "Risk": scam_type.replace("_", " "),
            },
            similar_memory=similar_memory,
        )


def _summary_for(risk_level: str, scam_type: str) -> str:
    if risk_level == "dangerous":
        return f"This looks dangerous: likely {scam_type.replace('_', ' ')}."
    if risk_level == "suspicious":
        return "This has warning signs and should be checked before you act."
    if risk_level == "needs_check":
        return "This might be legitimate, but you should verify it using a trusted route."
    return "No strong scam pattern was found in this short scan."


def _safe_action_for(risk_level: str, scam_type: str) -> str:
    if risk_level == "dangerous":
        return "Do not click links, do not reply, and do not send money. Contact the company or person using a number or app you already trust."
    if risk_level == "suspicious":
        return "Pause before acting. Open the official website or app yourself instead of using links from this message."
    if risk_level == "needs_check":
        return "Verify directly through the official app, official website, or a known phone number."
    return "If this came from someone you know and it asks for nothing sensitive, it is probably safe. Still avoid unexpected links."


def _trusted_message_for(risk_level: str, scam_type: str) -> str:
    if risk_level == "safe":
        return "Can you sanity-check this message for me? Jawbreaker did not find a strong scam pattern, but I want to be careful."
    return f"Can you check this for me? Jawbreaker says it may be {scam_type.replace('_', ' ')} and recommends that I do not click or reply yet."


def _guess_impersonation(text: str) -> str:
    if "usps" in text:
        return "USPS or package carrier"
    if "chase" in text or "bank" in text:
        return "Bank or financial institution"
    if "grandma" in text or "new number" in text:
        return "Family member"
    return "Unknown sender"


def _guess_pressure(tactics: list[str]) -> str:
    if "urgency" in tactics:
        return "Act now"
    if "secrecy" in tactics:
        return "Keep it secret"
    if "payment pressure" in tactics:
        return "Send money"
    return "Not obvious"


def _guess_ask(text: str, scam_type: str) -> str:
    if scam_type == "credential_theft":
        return "Verify account or login"
    if scam_type == "payment_request":
        return "Send money"
    if scam_type == "family_impersonation":
        return "Trust a new number"
    if "http://" in text or "https://" in text:
        return "Open a link"
    return "No direct ask found"


def _find_similar_memory(text: str, memory: list[dict]) -> str:
    tokens = set(text.split())
    best_score = 0.0
    best = ""
    for item in memory:
        old_tokens = set(str(item.get("text", "")).lower().split())
        if not old_tokens:
            continue
        score = len(tokens & old_tokens) / max(len(tokens | old_tokens), 1)
        if score > best_score:
            best_score = score
            best = str(item.get("summary", "a previous saved scam"))
    if best_score >= 0.18:
        return f"This resembles a saved pattern: {best}"
    return ""

