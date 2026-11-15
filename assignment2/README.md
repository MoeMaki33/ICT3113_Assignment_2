# ICT3113 Assignment 2 — Fast Triage Within an Accuracy Floor

Assignment 2 deadline: 27 Nov 2026 23:59 Singapore time, worth 20%. This folder intentionally preserves the Assignment 1 repository evidence. **Do not overwrite A1 results, prompt, labels or prediction files.**

## Required sequence
1. **Frozen split:** `golden_split.csv`, odd original row numbers to tuning (88), even to held-out A2 test (92). This was committed first.
2. **Before A2 benchmark:** commit `escalation_rule.md` and `prediction_record.md`. Check actual same-PC1 residency of both cascade models; if they do not fit, report failure and select an allowable smaller pair before starting tests.
3. **Implement:** configuration modes `single` and `cascade`; setting `A` or `B`. The POST interface and classifier prompt must stay unchanged.
4. **Accuracy:** score every model and each of two cascade settings on even-row tickets, comparing against top-model overall minus 10 percentage points and each category minus 15 percentage points. Show correct/total counts, confusion matrices, and escalated vs accepted accuracy. Reuse A1 single-model prediction rows ONLY if model digest, prompt, machine and Ollama version are unchanged.
5. **Speed:** first measure 3 different typical tickets after restart/warm-up on top model, and take middle elapsed time S seconds. Send one ticket per 2S seconds for max(S,5) minutes. Test all accuracy-passing single models, and BOTH cascade settings even if they fail. Three open-loop runs per configuration with fixed non-golden rows, restarts, warm-ups, drain, JTL and reconciled service logs. Record p50 per run, pooled p95, achieved throughput, error rate and escalation fraction. Never reuse A1 speed numbers.
6. **Decision:** recommend fastest measured configuration that passes both test-set accuracy limits.

## Technical note
Original repo runs Ollama on Windows host, not in its compose file. Ollama host restart and `ollama ps` verification are equivalent only when they demonstrably clear prompt cache and keep both model processes resident; record the exact commands and any differences from the assignment's container wording. PC1 (i7-10510U, 15.8 GB RAM) is SUT; PC2 (Ryzen 5800X3D) is separate JMeter load generator.

No A2 benchmark results have been recorded by this preparation. Statements about performance remain predictions until measured.
