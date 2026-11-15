"""A2: calculate p50 per JMeter run and pooled p95 across 3 runs.

Usage: python -m scripts.a2_speed_metrics --config cascade_A --duration-s 360
Reads assignment2/speed/<config>/run-{1,2,3}.jtl.
Does not fabricate missing runs or counts; all 3 JTL files are mandatory.
"""
import argparse
import csv
import json
from collections import Counter
from math import ceil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def percentile(values, p):
    if not values:
        return None
    data = sorted(values)
    return data[max(0, min(len(data) - 1, ceil(len(data) * p) - 1))]


def load_jtl(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = [x for x in csv.DictReader(f) if x.get("label") == "POST /tickets"]
    if not rows:
        raise ValueError(f"No POST /tickets samples in {path}")
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--duration-s", required=True, type=float)
    args = p.parse_args()
    if args.duration_s <= 0:
        p.error("Duration must be positive")
    root = ROOT / "assignment2" / "speed" / args.config
    if not root.exists():
        raise FileNotFoundError(root)
    all_success = []
    run_summaries = []
    for i in (1, 2, 3):
        path = root / f"run-{i}.jtl"
        samples = load_jtl(path)
        successful = [r for r in samples if r.get("success", "").lower() == "true"
                      and r.get("responseCode") == "201"]
        failed = [r for r in samples if r not in successful]
        elapsed = [float(r["elapsed"]) / 1000 for r in successful]
        all_success.extend(elapsed)
        counts = Counter(r.get("responseCode", "") for r in samples)
        run_summaries.append({
            "run": i, "sent_samples": len(samples), "completed_successful": len(successful),
            "errors": len(failed), "error_rate": len(failed)/len(samples),
            "p50_s": percentile(elapsed, .50),
            "throughput_successful_per_sec": len(successful)/args.duration_s,
            "response_codes": dict(counts),
            "unique_request_ids": len({r.get("request_id") for r in samples if r.get("request_id")}),
            "note": "Reconcile GET /stats delta and service log to identify sent-but-unfinished requests; JTL samples alone cannot prove their count."
        })
    p50s = [r["p50_s"] for r in run_summaries]
    result = {
        "configuration": args.config, "method": "JMeter POST samples; nearest-rank percentiles",
        "runs": run_summaries,
        "mean_p50_s": sum(p50s)/len(p50s) if all(x is not None for x in p50s) else None,
        "spread_p50_s": max(p50s)-min(p50s) if all(x is not None for x in p50s) else None,
        "pooled_p95_s": percentile(all_success, .95),
        "pooled_p95_sample_count": len(all_success),
        "do_not_report_p99": True,
        "caution": "Escalation fraction, unfinished requests and GET /stats completion deltas need separate service logs / operator run metadata."
    }
    dest = root / "a2_metrics.json"
    if dest.exists():
        raise FileExistsError(f"Refusing to overwrite {dest}")
    dest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
