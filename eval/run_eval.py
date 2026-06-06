import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jawbreaker.schema import RISK_LEVELS, ScamAnalysis


UNSAFE_ACTION_PHRASES = [
    "click the link",
    "open the link",
    "use the link",
    "call the number in the message",
    "call the number shown",
    "reply with your code",
    "send the code",
    "send money",
    "buy gift cards",
    "share your password",
    "share your pin",
]


def load_rows(path: Path) -> list[dict]:
    rows = []
    ids = set()
    errors = []

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: invalid JSON: {exc}")
            continue

        missing = {"id", "category", "input", "expected_risk_level", "expected_scam_type", "expected_tactics"} - set(row)
        if missing:
            errors.append(f"line {line_number}: missing fields: {sorted(missing)}")

        if row.get("id") in ids:
            errors.append(f"line {line_number}: duplicate id: {row.get('id')}")
        ids.add(row.get("id"))

        if row.get("expected_risk_level") not in RISK_LEVELS:
            errors.append(f"line {line_number}: invalid expected_risk_level: {row.get('expected_risk_level')}")

        if not isinstance(row.get("expected_tactics"), list):
            errors.append(f"line {line_number}: expected_tactics must be a list")

        rows.append(row)

    if errors:
        raise SystemExit("Eval dataset validation failed:\n" + "\n".join(errors))
    return rows


def has_unsafe_action(action: str) -> bool:
    text = action.lower()
    for phrase in UNSAFE_ACTION_PHRASES:
        if phrase not in text:
            continue
        if f"do not {phrase}" in text or f"never {phrase}" in text or f"don't {phrase}" in text:
            continue
        return True
    return False


def tactic_recall(expected: list[str], actual: list[str]) -> float:
    if not expected:
        return 1.0
    expected_set = set(expected)
    actual_set = set(actual)
    return len(expected_set & actual_set) / len(expected_set)


def main() -> None:
    path = Path(__file__).with_name("scam_eval.jsonl")
    rows = load_rows(path)
    started = perf_counter()

    risk_correct = 0
    scam_type_correct = 0
    dangerous_as_safe = []
    safe_as_dangerous = []
    unsafe_actions = []
    recalls = []
    risk_confusion: Counter[tuple[str, str]] = Counter()
    category_counts: Counter[str] = Counter()
    category_correct: Counter[str] = Counter()
    failures_by_category: dict[str, list[str]] = defaultdict(list)

    for row in rows:
        analysis = ScamAnalysis.from_heuristics(row["input"])
        expected_risk = row["expected_risk_level"]
        category = row["category"]
        risk_ok = analysis.risk_level == expected_risk
        type_ok = analysis.scam_type == row["expected_scam_type"]
        recall = tactic_recall(row["expected_tactics"], analysis.tactics)

        risk_correct += int(risk_ok)
        scam_type_correct += int(type_ok)
        recalls.append(recall)
        risk_confusion[(expected_risk, analysis.risk_level)] += 1
        category_counts[category] += 1
        category_correct[category] += int(risk_ok)

        if expected_risk == "dangerous" and analysis.risk_level == "safe":
            dangerous_as_safe.append(row["id"])
        if expected_risk == "safe" and analysis.risk_level in {"dangerous", "suspicious"}:
            safe_as_dangerous.append(row["id"])
        if has_unsafe_action(analysis.safest_action):
            unsafe_actions.append(row["id"])
        if not risk_ok:
            failures_by_category[category].append(f"{row['id']} expected={expected_risk} actual={analysis.risk_level}")

    elapsed = perf_counter() - started
    total = len(rows)

    print(f"cases={total}")
    print(f"risk_level_accuracy={risk_correct}/{total} ({risk_correct / total:.1%})")
    print(f"scam_type_accuracy={scam_type_correct}/{total} ({scam_type_correct / total:.1%})")
    print(f"mean_tactic_recall={sum(recalls) / len(recalls):.1%}")
    print(f"dangerous_as_safe={len(dangerous_as_safe)} {dangerous_as_safe}")
    print(f"safe_as_dangerous_or_suspicious={len(safe_as_dangerous)} {safe_as_dangerous}")
    print(f"unsafe_action_violations={len(unsafe_actions)} {unsafe_actions}")
    print(f"elapsed_seconds={elapsed:.3f}")

    print("\nrisk_confusion expected->actual:")
    for (expected, actual), count in sorted(risk_confusion.items()):
        print(f"  {expected:12s} -> {actual:12s} {count}")

    print("\ncategory_risk_accuracy:")
    for category, count in sorted(category_counts.items()):
        correct = category_correct[category]
        print(f"  {category:24s} {correct:2d}/{count:2d} ({correct / count:.1%})")

    if failures_by_category:
        print("\nfirst_failures_by_category:")
        for category, failures in sorted(failures_by_category.items()):
            print(f"  {category}:")
            for failure in failures[:5]:
                print(f"    {failure}")


if __name__ == "__main__":
    main()
