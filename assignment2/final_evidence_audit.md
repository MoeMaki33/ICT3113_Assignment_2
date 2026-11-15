# ICT3113 A2 — Final Benchmark Evidence Audit

## Request reconciliation
- 12 JMeter runs completed.
- 53 HTTP 201 responses per run.
- 636/636 JMeter request IDs matched service logs.
- 636/636 requests matched database count increases.
- No JMeter errors reported.

## Cascade A
- Escalated: 147/159 (92.45%).
- Accepted: 12/159 (7.55%).
- No saved before/after ollama ps snapshots.
- Request logs confirm both model tags were invoked, but
  continuous simultaneous residency is not independently proven.

## Cascade B
- Escalated: 99/159 (62.26%).
- Accepted: 60/159 (37.74%).
- Both models appeared simultaneously in before/after
  ollama ps snapshots for all three runs.
- Both models reported 100% CPU.

## Final recommendation
Qwen 2.5 7B:
- Accuracy: 74/92 (80.43%).
- Passes overall and all seven category floors.
- Three-run mean p50: 5.751 seconds.
- Pooled p95: 15.578 seconds.
- Fastest accuracy-qualified measured configuration.

## Limitations
- Cascade A residency snapshots are missing.
- Three runs per configuration; results may vary with system load.
- Benchmarks measured performance at a fixed offered load, not peak capacity.
