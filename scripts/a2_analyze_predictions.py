"""A2: check frozen split and score existing A1 single-model predictions on even rows.

These results are REUSABLE only when model digests, prompt, machine and Ollama
version are identical to A1. They do not replace the A2 speed benchmark.
Usage: python -m scripts.a2_analyze_predictions
"""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results" / "accuracy"
PRED_FILES = {
    "llama3.1:8b": BASE / "llama3.1_8b/run-1/predictions.csv",
    "qwen2.5:7b": BASE / "qwen2.5_7b/run-1/predictions.csv",
    "gemma2:2b": BASE / "gemma2_2b/run-2/predictions.csv",
    "llama3.2:3b": BASE / "llama3.2_3b/run-1/predictions.csv",
}
CATEGORIES = [
    "Credit reporting", "Debt collection", "Mortgage", "Credit card",
    "Bank account or service", "Consumer loan", "Money transfer or service",
]


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def score(rows):
    n = len(rows)
    correct = sum(r["predicted_category"] == r["golden_category"] and
                  str(r.get("status_code", "201")) == "201" for r in rows)
    per_category = {}
    confusion = {}
    for cat in CATEGORIES:
        subset = [r for r in rows if r["golden_category"] == cat]
        right = sum(r["predicted_category"] == cat and r.get("status_code", "201") == "201" for r in subset)
        per_category[cat] = {
            "correct": right, "total": len(subset),
            "accuracy": right / len(subset) if subset else None,
        }
        confusion[cat] = dict(Counter(r["predicted_category"] or "FAILED" for r in subset))
    return {"correct": correct, "total": n, "accuracy": correct / n,
            "per_category": per_category, "confusion_matrix": confusion}


def main():
    split_rows = read_csv(ROOT / "assignment2/golden_split.csv")
    ids = {int(r["row"]): r["subset"] for r in split_rows}
    assert len(ids) == 180 and set(ids.values()) == {"tuning", "test"}
    assert all(ids[row] == ("tuning" if row % 2 else "test") for row in ids)
    assert sum(v == "tuning" for v in ids.values()) == 88
    assert sum(v == "test" for v in ids.values()) == 92

    scores = {}
    for name, path in PRED_FILES.items():
        rows = read_csv(path)
        assert set(int(r["row"]) for r in rows) == set(ids), f"{name}: row mismatch"
        subset = [r for r in rows if ids[int(r["row"])] == "test"]
        scores[name] = score(subset)
    top = scores["llama3.1:8b"]
    overall_floor = top["accuracy"] - 0.10
    category_floors = {c: top["per_category"][c]["accuracy"] - 0.15 for c in CATEGORIES}
    for name, metrics in scores.items():
        metrics["passes_overall"] = metrics["accuracy"] >= overall_floor - 1e-10
        metrics["passes_categories"] = all(
            metrics["per_category"][c]["accuracy"] >= category_floors[c] - 1e-10 for c in CATEGORIES
        )
        metrics["qualifies"] = metrics["passes_overall"] and metrics["passes_categories"]
    artifact = {
        "warning": "A1 prediction reuse is conditional on unchanged digest, prompt, machine and Ollama version. This is NOT A2 speed evidence.",
        "split": {"tuning": 88, "test": 92},
        "reference_model": "llama3.1:8b",
        "overall_floor": overall_floor,
        "category_floors": category_floors,
        "models": scores,
    }
    target = ROOT / "assignment2/a1_prediction_reuse_analysis.json"
    target.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {target}")
    for name, item in scores.items():
        print(f"{name}: {item['correct']}/{item['total']} "
              f"({item['accuracy']:.1%}), qualifies={item['qualifies']}")
    print("Check reuse conditions against the actual A1 runtime before citing as A2 results.")


if __name__ == "__main__":
    main()
