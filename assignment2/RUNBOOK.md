# Assignment 2 single-day execution runbook

This is a team execution plan, not a claim that tests ran. All generated A2 code is on branch `assignment2-implementation`. The immutable split was committed first; escalation design and prediction record were committed before any new benchmark.

## Current A2 reference
- 180 A1 golden tickets: 88 odd-row tuning; 92 even-row test.
- A1 best overall: `llama3.1:8b`; previously saved even-row predictions show 77/92 (83.70%) and overall threshold 73.70% (at least 68/92). Category thresholds must each be applied independently.
- Current cascade: `llama3.2:3b` -> `llama3.1:8b`. Rule A accepts only Mortgage; Rule B accepts Mortgage or Bank account or service.
- Fixed A2 speed workload: `assignment2/speed_workload_rows.csv` and `jmeter/data/a2_speed_narratives.tsv`. Three calibration rows 7203,7409,7555 and three warmups 7389,7643,7631, all outside golden and speed workload.
- **No new A2 empirical results have been measured by ChatGPT.**

## PC1: preparation
1. Pull the branch, activate project Python 3.12 virtual environment and run `python -m pytest -q`.
2. Confirm exactly the same four model tags/digests as A1, prompt and seven categories. Verify actual PC1 model availability and Ollama version and compare with original runtime records; historical model provenance alone does not establish identity. Capture `ollama list`, `ollama show`, exact digests, `ollama ps`, `docker stats` and full CPU/RAM allocations.
3. The Assignment 1 repo points its Docker API at host Ollama; determine and document how Ollama will be restarted and how the host Ollama cache is cleared. Restarting `docker compose` alone does NOT restart host Ollama.
4. Start the API with Docker: `docker compose up --build`. Use `docker compose ps`. Ensure Docker has no additional CPU/RAM compared to A1.
5. For memory-residency verification, send distinct CPU-only requests to `llama3.2:3b` and `llama3.1:8b` at the same Ollama instance, with the same inference options as A1; immediately run `ollama ps`, and again after a few routed tickets. Both must be present, resident and reporting CPU-only; record timestamps/screenshots. If not, do NOT benchmark a model-loading cascade as a valid two-model cascade. Try a permitted smaller pair and predeclare it before benchmarking or report infeasibility.
6. Check your `.env`. For single-model configs use `CLASSIFICATION_MODE=single` and `OLLAMA_MODEL=<tag>`. For cascade use `CLASSIFICATION_MODE=cascade`, `CASCADE_SMALL_MODEL=llama3.2:3b`, `CASCADE_LARGE_MODEL=llama3.1:8b`, and `CASCADE_SETTING=A` or `B`. Restart/recreate API after changing env, and preserve request logs. Set timeouts consistently before all experiments.

## Recheck A1 accuracy reuse (optional, conditional)
Run `python -m scripts.a2_analyze_predictions` to generate `assignment2/a1_prediction_reuse_analysis.json`.
Existing A1 full-set results cannot be presented as A2 accuracy. The script subsets even rows only. Reuse only if same prompt, model digest, Ollama version and machine as A1; otherwise re-run each single model via A2 accuracy runner.

## Accuracy tests (first)
Execute the same 92 even-row tickets via POST /tickets for all four single-model configurations and both cascades, or reuse valid single-model prediction records as above.

Example for single model:
```powershell
# Set CLASSIFICATION_MODE=single, OLLAMA_MODEL=llama3.1:8b, restart API
.\.venv\Scripts\python.exe -m scripts.a2_accuracy_test --name llama31_single --mode single --model llama3.1:8b --api-url http://localhost:8000
```
Example for cascade:
```powershell
# Set CLASSIFICATION_MODE=cascade, CASCADE_SETTING=A, restart API
.\.venv\Scripts\python.exe -m scripts.a2_accuracy_test --name cascade_A --mode cascade --small-model llama3.2:3b --large-model llama3.1:8b --setting A --api-url http://localhost:8000
.\.venv\Scripts\python.exe -m scripts.a2_log_analysis --mode accuracy --config cascade_A --log logs/service.log
```
Repeat setting B. Score overall, seven per-category accuracies (counts and percentages), confusion matrices and escalation/accepted group accuracy. Any failed requests count incorrect. Do not change rule based on test-set outcomes.

## Speed protocol
1. Restart Ollama on PC1; standard warm-up; send three distinct typical calibration rows **7203, 7409, 7555**, one at a time through the top model; record measured elapsed times (seconds) and row numbers. The middle time is S.
2. On PC2, after synchronizing the exact branch/workload, run `python -m scripts.a2_speed_plan --timings TIME1 TIME2 TIME3 --host PC1_IP`. **Replace TIME1 etc. with actual timings**. It creates `assignment2/a2_speed_plan.json` and prints all JMeter commands. S seconds -> 1 arrival per 2S seconds, run max(5,S) minutes, HTTP timeout max(300,10S) sec, drain at least 60 sec longer than timeout.
3. Every configuration uses identical arrival rate, duration, workload order and open-loop plan. For each of the 3 repetitions: restart actual Ollama, verify cleared cache and no loaded models, send the three fixed warm-up tickets (7389,7643,7631), ensure both cascade models loaded, `GET /stats` before, run one JMeter command, let all requests finish, `GET /stats` after, archive request logs and raw .jtl.
4. Speed-test the top model, all other SINGLE models that passed both test accuracy limits, and both cascade settings regardless of accuracy. Nonqualifying small single models need not be speed-tested.
5. Make `assignment2/speed/<config>/` before launching. Run `python -m scripts.a2_speed_metrics --config <name> --duration-s <duration>` after each configuration has its three runs, and `python -m scripts.a2_log_analysis --mode speed --config <name> --log logs/service.log`.
6. Report all run sample counts (sent/completed/errored/unfinished). Unfinished status requires reconciling JTL, service logs and GET /stats deltas. Give run-level p50, mean and spread; pooled p95 from about 90 successful samples with n; throughput, error rate, cascade escalation fraction from logs. Do not report p99.
7. Compare A2 rate with the client's A1 peak rate; a slower test rate doesn't establish peak-capacity compliance.

## Slide order (maximum eight)
1 cover, reference model and floors; 2 cascade design and both rules; 3 environment / calibration S / open-loop method; 4 all configurations' overall and per-category accuracy with counts and pass/fail; 5 all speed-tested configs p50-per-run/pooled-p95/throughput/errors and cascade escalation; 6 one accuracy-vs-latency trade-off chart with overall floor; 7 predictions versus results and fastest qualifying recommendation; 8 limitations, bibliography, model licences, AI disclosure.

## Submission / integrity
- Submit `Group07_A2.pptx` via xSiTe by **Friday 27 Nov 2026 at 23:59**; group filename should use the actual group number as required by the brief (this repo is P2-7).
- Include `assignment2/prediction_record.md`, `assignment2/escalation_rule.md`, `assignment2/speed_workload_rows.csv` with submission.
- Keep raw JTLs, timestamped complete request logs and reproducible run metadata in the repository. All figures on slides 4–7 must trace to actual evidence.
- AI declaration: tools assisted with design/code/tests/slide drafting; humans must check rule choice, run experiments and defend the recommendation. Never claim experiments were executed on PC1/PC2 unless they were.
