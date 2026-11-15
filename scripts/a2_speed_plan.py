"""Generate (do NOT run) three identical-condition open-loop JMeter commands.

First measure 3 distinct typical calibration tickets with the top model on PC1
after Ollama restart and warm-up. Use the middle elapsed time S seconds.

Usage:
python -m scripts.a2_speed_plan --timings 12.1 10.7 11.6 --host 192.168.1.170
Those numbers are an EXAMPLE, not observed values.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--timings", type=float, nargs=3, required=True)
    p.add_argument("--host", required=True)
    p.add_argument("--port", type=int, default=8000)
    args = p.parse_args()
    if not all(s > 0 for s in args.timings):
        p.error("All 3 measured elapsed seconds must be positive")
    s = sorted(args.timings)[1]
    duration_s = max(s, 5) * 60
    arrivals_per_hour = 1800 / s
    timeout_s = max(300, 10 * s)
    drain_s = timeout_s + 60
    print(f"S={s:.3f}s, one ticket every {2*s:.3f}s, arrival rate={arrivals_per_hour:.4f}/hour")
    print(f"Run duration={duration_s:.1f}s, response timeout={timeout_s:.1f}s, drain={drain_s:.1f}s")
    print("Calibration rows: assignment2/calibration_warmup_rows.csv (purpose=calibration)")
    print("Workload file: jmeter/data/a2_speed_narratives.tsv (48 fixed non-golden tickets)")
    print("Run from the SEPARATE PC2 machine; ensure identical file/order and use same seed per run across configurations.")
    print("BEFORE EACH RUN: restart Ollama on PC1, warm up with fixed tickets, check ollama ps, GET /stats total.")
    print("AFTER EACH RUN: GET /stats total, reconcile completed count with service logs and JTL.")
    print()
    workload = (ROOT / "jmeter/data/a2_speed_narratives.tsv").resolve()
    jmx = (ROOT / "jmeter/ticket_load_test.jmx").resolve()
    props = (ROOT / "jmeter/results.properties").resolve()
    for setting in ("llama31_single", "qwen25_single", "cascade_A", "cascade_B"):
        print(f"### {setting}")
        for run in range(1, 4):
            dst = (ROOT / "assignment2/speed" / setting)
            cmd = (
                f'jmeter -n -t "{jmx}" -q "{props}" '
                f'-l "{dst / ("run-" + str(run) + ".jtl")}" -j "{dst / ("run-" + str(run) + ".jmeter.log")}" '
                f'-Jhost={args.host} -Jport={args.port} -Jprotocol=http '
                f'-Jrate={arrivals_per_hour:.8f} -Jduration_s={duration_s:.3f} '
                f'-Jdrain_s={drain_s:.3f} -Jtimeout_ms={int(timeout_s*1000)} '
                f'-Jsearch_schedule=pause(1s) -Jseed={311300+run} '
                f'-Jdata_file="{workload}"'
            )
            print(cmd)
        print()
    plan = {
        "calibration_rows": [7203, 7409, 7555],
        "calibration_timings_seconds": args.timings,
        "S_seconds": s, "arrival_interval_s": 2*s, "arrival_rate_per_hour": arrivals_per_hour,
        "duration_seconds": duration_s, "response_timeout_seconds": timeout_s,
        "drain_seconds": drain_s, "host": args.host,
        "note": "Commands are generated from operator measurements, not executed. Directory creation, restart, warm-up, stats checks, and log preservation remain operator responsibilities.",
    }
    output = ROOT / "assignment2/a2_speed_plan.json"
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite the frozen speed plan: {output}")
    output.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded calibration measurements and plan in {output}")


if __name__ == "__main__":
    main()
