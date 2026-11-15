"""A2 accuracy test: send only even-row golden tickets to the running POST API.

Run once per configuration after starting the correct mode/model/setting.
NO test-set tuning. Outputs are raw evidence, never silently overwritten.
Examples:
  python -m scripts.a2_accuracy_test --name llama31_single
  python -m scripts.a2_accuracy_test --name cascade_A
  python -m scripts.a2_accuracy_test --name cascade_B
"""
import argparse
import csv
import hashlib
import json
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.categories import CATEGORIES

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "data" / "golden_set_final.csv"
SPLIT = ROOT / "assignment2" / "golden_split.csv"


def load_data():
    with SPLIT.open(encoding="utf-8", newline="") as f:
        marks = {int(r["row"]): r["subset"] for r in csv.DictReader(f)}
    with GOLDEN.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 180 or len(marks) != 180 or {int(r["row"]) for r in rows} != set(marks):
        raise ValueError("Golden split does not match the 180 frozen tickets")
    if any(marks[n] != ("tuning" if n % 2 else "test") for n in marks):
        raise ValueError("The split is not the required original-row odd/even split")
    return [r for r in rows if marks[int(r["row"])] == "test"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True, help="Run identifier, e.g. cascade_A")
    p.add_argument("--api-url", default="http://localhost:8000")
    p.add_argument("--timeout", type=float, default=600.0)
    p.add_argument("--mode", choices=["single", "cascade"], required=True)
    p.add_argument("--model", help="Exact selected single-model tag")
    p.add_argument("--small-model", help="Exact cascade small-model tag")
    p.add_argument("--large-model", help="Exact cascade large-model tag")
    p.add_argument("--setting", choices=["A", "B"])
    args = p.parse_args()
    if args.mode == "single" and not args.model:
        p.error("--model is required for single mode")
    if args.mode == "cascade" and not all((args.small_model, args.large_model, args.setting)):
        p.error("--small-model, --large-model, and --setting are required for cascade")
    rows = load_data()
    out = ROOT / "assignment2" / "accuracy" / args.name
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite existing evidence: {out}")
    out.mkdir(parents=True)
    files = {"golden_sha256": hashlib.sha256(GOLDEN.read_bytes()).hexdigest(),
             "split_sha256": hashlib.sha256(SPLIT.read_bytes()).hexdigest()}
    (out / "metadata.json").write_text(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode, "model": args.model, "small_model": args.small_model,
        "large_model": args.large_model, "setting": args.setting,
        "api_url": args.api_url, **files,
        "caution": "Operator must verify actual running API configuration, digests and CPU residency; CLI labels are not verification.",
    }, indent=2) + "\n", encoding="utf-8")
    predictions = []
    with httpx.Client(base_url=args.api_url, timeout=args.timeout) as client:
        with (out / "predictions.csv").open("w", encoding="utf-8", newline="") as f:
            fieldnames = ["row", "golden_category", "predicted_category", "correct", "status_code",
                          "error", "request_id", "ticket_id", "elapsed_ms"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for record in rows:
                start = time.perf_counter()
                predicted, status, error, request_id, ticket_id = "FAILED", 0, "", "", ""
                try:
                    response = client.post("/tickets", json={"narrative": record["narrative"]})
                    status = response.status_code
                    request_id = response.headers.get("x-request-id", "")
                    if status == 201:
                        body = response.json()
                        predicted, ticket_id = body["category"], body["id"]
                        if predicted not in CATEGORIES:
                            predicted, error = "FAILED", "InvalidCategory"
                    else:
                        error = f"HTTP_{status}"
                except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
                    error = type(exc).__name__
                datum = {
                    "row": record["row"],
                    "golden_category": record["final_golden_category"],
                    "predicted_category": predicted,
                    "correct": predicted == record["final_golden_category"] and status == 201,
                    "status_code": status,
                    "error": error,
                    "request_id": request_id,
                    "ticket_id": ticket_id,
                    "elapsed_ms": round((time.perf_counter() - start) * 1000, 2),
                }
                writer.writerow(datum)
                f.flush()
                predictions.append(datum)
                print(f"{len(predictions)}/{len(rows)} row {record['row']}: {predicted}")

    category_counts = {}
    confusion = {}
    for cat in CATEGORIES:
        subset = [r for r in predictions if r["golden_category"] == cat]
        correct = sum(r["correct"] for r in subset)
        category_counts[cat] = {"correct": correct, "total": len(subset),
                                "accuracy": correct / len(subset) if subset else None}
        confusion[cat] = dict(Counter(r["predicted_category"] for r in subset))
    correct = sum(r["correct"] for r in predictions)
    metrics = {"correct": correct, "total": len(predictions), "accuracy": correct / len(predictions),
               "categories": category_counts, "confusion_matrix": confusion}
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(f"Accuracy {correct}/{len(predictions)} = {correct / len(predictions):.2%}")
    if args.mode == "cascade":
        print("For cascade escalated/non-escalated accuracy: join request_id with service logs.")


if __name__ == "__main__":
    main()
