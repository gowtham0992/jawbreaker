import json
from pathlib import Path

from jawbreaker.schema import RISK_LEVELS


def test_eval_dataset_has_100_unique_cases() -> None:
    rows = [
        json.loads(line)
        for line in Path("eval/scam_eval.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(rows) == 100
    assert len({row["id"] for row in rows}) == 100


def test_eval_dataset_required_fields_and_risk_levels() -> None:
    required = {"id", "category", "input", "expected_risk_level", "expected_scam_type", "expected_tactics"}
    rows = [
        json.loads(line)
        for line in Path("eval/scam_eval.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    for row in rows:
        assert required <= set(row)
        assert row["expected_risk_level"] in RISK_LEVELS
        assert isinstance(row["expected_tactics"], list)
        assert ".example" in row["input"] or "http" not in row["input"].lower()

