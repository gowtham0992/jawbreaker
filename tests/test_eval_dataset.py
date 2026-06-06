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


def test_generated_training_splits_exist_and_do_not_overlap() -> None:
    paths = {
        "train": Path("training/data/train.jsonl"),
        "dev": Path("training/data/dev.jsonl"),
        "test": Path("training/data/test.jsonl"),
    }
    expected_counts = {"train": 720, "dev": 120, "test": 180}
    seen_messages = set()

    for split, path in paths.items():
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(rows) == expected_counts[split]
        for row in rows:
            assert {"id", "messages", "input", "prediction"} <= set(row)
            assert row["input"] not in seen_messages
            seen_messages.add(row["input"])
            prediction = row["prediction"]
            assert prediction["risk_level"] in RISK_LEVELS
            assert set(prediction["scam_dna"]) == {"impersonates", "pressure", "ask", "risk"}
            assert row["messages"][-1]["role"] == "assistant"


def test_generated_eval_has_test_count_and_safe_urls() -> None:
    rows = [
        json.loads(line)
        for line in Path("eval/generated_eval.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(rows) == 180
    assert len({row["id"] for row in rows}) == 180
    for row in rows:
        assert row["expected_risk_level"] in RISK_LEVELS
        assert ".example" in row["input"] or "http" not in row["input"].lower()
