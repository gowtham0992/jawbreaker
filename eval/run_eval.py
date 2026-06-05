import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jawbreaker.schema import ScamAnalysis


def main() -> None:
    path = Path(__file__).with_name("scam_eval.jsonl")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    correct = 0

    for row in rows:
        analysis = ScamAnalysis.from_heuristics(row["input"])
        ok = analysis.risk_level == row["expected_risk_level"]
        correct += int(ok)
        print(f"{row['id']}: expected={row['expected_risk_level']} actual={analysis.risk_level} ok={ok}")

    print(f"risk_level_accuracy={correct}/{len(rows)}")


if __name__ == "__main__":
    main()
