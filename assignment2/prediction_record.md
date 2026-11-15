# Assignment 2 predictions — committed before A2 benchmark
Date written: 2026-11-15. **Prospective hypotheses, not measured A2 outcomes.** Never edit after the first A2 benchmark.

## Reference and baseline information
Assignment 1 full-golden results (180): Llama 3.1 8B 152/180 (84.4%), Qwen 2.5 7B 145/180 (80.6%), Gemma 2 2B 121/180 (67.2%), Llama 3.2 3B 109/180 (60.6%). A2 top-model reference MUST be Llama 3.1 8B, regardless of the A1 recommendation. Even-row test-set accuracy limits must be recomputed and checked before scoring. A1 speed results are NOT A2 benchmark results.

## Specific forecasts
1. **Expected fastest qualifying configuration:** `qwen2.5:7b` alone, subject to test-set accuracy qualification and new common-rate speed measurements. Its A1 mixed-load p95 was 77.689s vs 97.311s for the top 8B model; these old results are not reusable as A2 results.
2. **Cascade pair:** `llama3.2:3b` first, `llama3.1:8b` for escalated tickets, if both fit resident simultaneously (not yet verified).
3. **Cascade Setting A (accept Mortgage only):** forecast escalation 80% of tickets, test-set overall accuracy 80%, warm median latency approximately 14 seconds.
4. **Cascade Setting B (accept Mortgage or Bank account or service):** forecast escalation 65%, test-set overall accuracy 76%, warm median latency approximately 12 seconds.
5. **Expected largest error risk:** Consumer loan and Money transfer or service if incorrectly accepted from small-model predictions; settings A/B largely escalate those predictions. Bank account or service is the more likely category to lose accuracy between A and B. For A/B, some credit-reporting complaints may be misclassified as accepted Mortgage or Bank account, hurting the true Credit reporting category.
6. **Expected bottleneck:** CPU-only Ollama inference, with cascade expense dominated by frequent second-stage calls. Both settings may fail to beat a qualifying single model, even if they satisfy accuracy floors.

## Methodological guardrails
The estimates above are intentionally falsifiable; do not change them after measurement. The number of escalations, accuracy, median latency, and category losses will be compared with actual post-freeze A2 tests. The exact A2 speed-test arrival rate and duration come from three NEW top-model typical-ticket timings as the assignment requires; no invented S value is included here. Before a run, record actual software versions, unchanged digests, Ollama memory allocation, and the 3 source row numbers used to derive S.
