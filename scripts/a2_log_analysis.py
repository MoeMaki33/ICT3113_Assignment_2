"""A2 evidence reconciliation: join request IDs in A2 CSV/JTL to service logs.

Usage:
  python -m scripts.a2_log_analysis --mode accuracy --config cascade_A --log logs/service.log
  python -m scripts.a2_log_analysis --mode speed --config cascade_A --log logs/service.log

Accuracy test outputs provide golden_category and correct. Speed outputs provide
row IDs from JTL, but NOT golden labels; only speed escalation fraction is reported.
The script does not invent requests missing from either source.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_logs(path):
    logs = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            req_id = record.get("request_id")
            if req_id:
                if req_id in logs:
                    raise ValueError(f"Duplicate request_id in service logs: {req_id}")
                logs[req_id] = record
    return logs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", required=True, choices=["accuracy", "speed"])
    p.add_argument("--config", required=True)
    p.add_argument("--log", required=True, type=Path)
    args = p.parse_args()

    logs = read_logs(args.log)
    if args.mode == "accuracy":
        path = ROOT / "assignment2/accuracy" / args.config / "predictions.csv"
        inputs = read_csv(path)
    else:
        inputs = []
        for run in (1, 2, 3):
            path = ROOT / "assignment2/speed" / args.config / f"run-{run}.jtl"
            inputs.extend(r for r in read_csv(path) if r.get("label") == "POST /tickets")

    present = []
    missing = []
    for record in inputs:
        request_id = record.get("request_id")
        if not request_id or request_id not in logs:
            missing.append(request_id or "NO_REQUEST_ID")
            continue
        present.append((record, logs[request_id]))
    cascade = [(src, entry) for src, entry in present if entry.get("classification_mode") == "cascade"]
    escalation_count = sum(entry.get("escalated") is True for _, entry in cascade)
    report = {
        "configuration": args.config,
        "mode": args.mode, "input_requests": len(inputs), "matched_log_requests": len(present),
        "missing_log_requests": len(missing), "missing_ids": missing[:100],
        "log_status_codes": dict(Counter(str(entry.get("status_code")) for _, entry in present)),
        "cascade_matched": len(cascade),
        "cascade_escalated": escalation_count,
        "cascade_accepted": sum(entry.get("escalated") is False for _, entry in cascade),
        "cascade_escalation_fraction": escalation_count/len(cascade) if cascade else None,
        "first_models": dict(Counter(entry.get("first_model") for _, entry in present)),
        "final_models": dict(Counter(entry.get("final_model") for _, entry in present)),
    }
    if args.mode == "accuracy" and cascade:
        splits = {}
        for escalated in (False, True):
            group = [(src, ent) for src, ent in cascade if ent.get("escalated") is escalated]
            correct = sum(src["correct"].lower() == "true" for src, _ in group)
            splits[str(escalated)] = {
                "count": len(group), "correct": correct, "accuracy": correct/len(group) if group else None
            }
        report["cascade_group_accuracy"] = splits
    target = (ROOT / "assignment2" / args.mode / args.config / "log_reconciliation.json")
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite {target}")
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
