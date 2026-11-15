# ICT3113 — Financial Complaint Ticket Triage (Assignments 1 & 2)

**Module:** ICT3113 Performance Optimisation and Design  
**Team:** P2-7 (Group 07)  
**Current focus:** **Assignment 2 — Fast Triage Within an Accuracy Floor**  
**Stack:** Python 3.12, FastAPI, SQLite, Docker Compose, local Ollama (CPU-only), Apache JMeter 5.6.3

> **Assignment 2 result:** **Qwen 2.5 7B** is the fastest **accuracy-qualified** configuration tested: **74/92 (80.43%)** held-out accuracy, **5.751 s** mean of three run-level POST p50 latencies, **15.578 s** pooled POST p95, and **159/159 successful** load-test requests. Both evaluated cascades failed at least one per-category accuracy floor. This is a recommendation **within the A2 comparison**, not a claim of production readiness or peak throughput compliance.

## Project overview

The service automatically routes financial-services complaint narratives into exactly seven categories using locally hosted language models. The client requires complaints to stay on its own infrastructure and the evaluated server is CPU-only. The original Assignment 1 API, prompt and golden labels were retained for a controlled Assignment 2 comparison.

Categories: **Credit reporting**, **Debt collection**, **Mortgage**, **Credit card**, **Bank account or service**, **Consumer loan**, **Money transfer or service**.

```text
Client / separate JMeter load generator (PC2)
                   |
                   v
             FastAPI on PC1
             POST /tickets
                   |
              Mode selector
               /       \
        Single model   Two-stage cascade
           |          Small: llama3.2:3b
           |             |
           |        Category-based routing
           |           /         \
           |        Accept     Escalate to
           |        small      llama3.1:8b
           \___________|__________/
                       |
                SQLite storage
                       |
                 HTTP 201 result

GET /search   -> search saved tickets
GET /stats    -> counts by classified category
```

**Implementation:** A request is classified synchronously before storage and response. Neither assignment uses a prediction cache, asynchronous queue, batching, or an additional classifier. The original category prompt and output parser are shared by the single and cascade paths. Request logs capture model routing, escalation, durations and request IDs without storing full complaint narratives in the structured log.

## Assignment 2 design

### Frozen evaluation and decision criteria

The Assignment 1 adjudicated golden set has **180 tickets**. Original source-row parity defines the immutable A2 split:

- **Odd original row numbers:** 88 tuning tickets (used only to design the routing rule).
- **Even original row numbers:** 92 held-out test tickets (used for final A2 accuracy).
- The A1 **highest-accuracy model**, `llama3.1:8b`, is the reference regardless of the A1 operating recommendation. Its previously recorded even-row prediction result was **77/92 (83.70%)**.
- **Overall floor:** reference test accuracy minus **10 percentage points** = **73.70%**.
- **Every category floor:** the corresponding reference category accuracy minus **15 percentage points**. Passing overall accuracy alone is insufficient; all seven categories must also pass.
- A failed classification is counted as incorrect. Due to small denominators, results are reported with correct/total counts, not just percentages.

The frozen split, rule and prospective predictions were committed before new A2 benchmarking. See [golden split](assignment2/golden_split.csv), [escalation rule](assignment2/escalation_rule.md) and [prediction record](assignment2/prediction_record.md). Do **not** edit these pre-registered artifacts to match the observed results.

### Two-stage cascade

The first stage runs **`llama3.2:3b`**; escalations run **`llama3.1:8b`** using the same prompt. Routing depends only on the *first model's predicted category*, never the true label.

| Frozen setting | Accept the first-stage prediction when… | Otherwise |
|---|---|---|
| **Cascade A — conservative** | Predicted category is exactly **Mortgage** | Call `llama3.1:8b` |
| **Cascade B — broader** | Predicted category is **Mortgage** or **Bank account or service** | Call `llama3.1:8b` |

An escalated request invokes both models in sequence; an accepted request invokes only the small model. The HTTP interface still returns and stores **one final category**. [Implementation](app/services/cascade.py).

### A2 accuracy results — held-out 92 tickets

All six configurations were evaluated fresh, as the observed A2 Ollama version differed from Assignment 1. The figures below are **A2 test-set measurements**, not the original A1 full-set scores.

| Configuration | Correct / 92 | Accuracy | All floors met? | Main failed floors |
|---|---:|---:|---|---|
| **Llama 3.1 8B** (`llama3.1:8b`) | **76/92** | **82.61%** | **Yes** | — |
| **Qwen 2.5 7B** (`qwen2.5:7b`) | **74/92** | **80.43%** | **Yes** | — |
| Cascade A | 74/92 | 80.43% | **No** | Consumer loan: 9/13 |
| Cascade B | 68/92 | 73.91% | **No** | Consumer loan: 9/13; Money transfer or service: 6/11 |
| Gemma 2 2B (`gemma2:2b`) | 59/92 | 64.13% | **No** | Overall; Consumer loan; Money transfer |
| Llama 3.2 3B (`llama3.2:3b`) | 54/92 | 58.70% | **No** | Overall; Credit card; Consumer loan; Money transfer |

**Accuracy-floor detail** (derived from the frozen reference predictions on the even-row split):

| True category | Test n | Reference correct | Category floor |
|---|---:|---:|---:|
| Credit reporting | 17 | 15/17 | 73.24% |
| Debt collection | 8 | 4/8 | 35.00% |
| Mortgage | 15 | 13/15 | 71.67% |
| Credit card | 13 | 11/13 | 69.62% |
| Bank account or service | 15 | 12/15 | 65.00% |
| Consumer loan | 13 | 11/13 | 69.62% |
| Money transfer or service | 11 | 11/11 | 85.00% |

**Note:** The reference floor is based on the frozen A1 test predictions (77/92); a fresh A2 run of Llama 3.1 scored 76/92. Category denominators are small, especially Debt collection (n=8), so a one-ticket difference can change pass/fail.

Complete correct counts, per-category accuracy, confusion matrices, raw predictions and timestamps are in [A2 accuracy evidence](assignment2/accuracy/). Cascade accuracy-stage splits are available in the [log reconciliation outputs](assignment2/accuracy/).

## Assignment 2 CPU-only performance benchmark

### Test environment and fixed load

- **PC1 (system under test):** Intel Core i7-10510U, 4 cores / 8 threads, approximately 15.8 GB RAM; Windows 11; Docker-hosted FastAPI plus **Ollama 0.40.16 on the Windows host**. The model tags/digest prefixes were checked against A1. CPU-only execution was checked using `ollama ps` and `num_gpu: 0`. Docker restart alone **does not restart host Ollama**.
- **PC2 (separate generator):** Ryzen 7 5800X3D desktop, Java 17, Apache JMeter **5.6.3**. This avoided running load generation on PC1.
- **Calibration:** following Ollama restart and warm-up, three distinct non-golden tickets (rows **7203**, **7409**, **7555**) through the reference model took **2.5438**, **2.8175**, **3.1268** seconds. Middle value **S = 2.8175 s**.
- **Identical offered load for every configuration:** one random open-loop arrival per **2S = 5.635 s** on average, equivalent to **638.864 tickets/hour**, over **300 seconds**, followed by **360 seconds drain**. HTTP response timeout **300 seconds**.
- **Workload:** fixed 48 non-golden narratives in [the speed row list](assignment2/speed_workload_rows.csv), sent from [the JMeter TSV](jmeter/data/a2_speed_narratives.tsv). Warm-up rows **7389**, **7643**, **7631** were distinct from the measured workload. Each of four configurations was run **three times** with predeclared seeds **311301, 311302, 311303**.
- Speed was measured for the two accuracy-qualified single models and **both cascades regardless of accuracy outcome**. The nonqualifying Gemma and Llama 3.2 single models were scored for accuracy but not speed-tested.
- Figures use **successful POST /tickets** responses: p50 for **each run**, the mean and range of three run p50s, and **pooled p95 from 159 successful samples** per configuration. **No p99 is used for A2**.

### Measured A2 latency and reliability

| Configuration | Run 1 p50 | Run 2 p50 | Run 3 p50 | Mean p50 | p50 spread | Pooled p95 | Successful |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Qwen 2.5 7B** | 5.875 s | 5.603 s | 5.774 s | **5.751 s** | 0.272 s | **15.578 s** | 159/159 |
| Llama 3.1 8B | 7.066 s | 6.020 s | 6.428 s | 6.505 s | 1.046 s | 17.248 s | 159/159 |
| Cascade B | 7.699 s | 6.071 s | 9.958 s | 7.909 s | 3.887 s | 30.587 s | 159/159 |
| Cascade A | 10.463 s | 16.558 s | 26.199 s | 17.740 s | 15.736 s | 57.664 s | 159/159 |

All **12 JMeter runs** had **53 HTTP 201 responses and zero recorded JMeter errors each**, for **636/636** successful recorded requests. The observed completed throughput was **53/300 = 0.1767 tickets/s (636 tickets/hour equivalent)** in every run, measured against the five-minute arrival window, **not** the eleven-minute schedule including drain. Offered load and measured throughput at this rate do not establish peak capacity.

### Escalation and evidence reconciliation

| Configuration | Escalated at speed test | Accepted at first stage |
|---|---:|---:|
| Cascade A | **147/159 (92.45%)** | 12/159 (7.55%) |
| Cascade B | **99/159 (62.26%)** | 60/159 (37.74%) |

Every one of the **636 JMeter request IDs matched a service-log record** with HTTP 201, and the database count increased by **53 on each of the 12 runs**. The logs confirm first/final model tags and escalation routing. For **Cascade B**, saved `ollama ps` snapshots before and after *each* run show **both models simultaneously resident at 100% CPU**. Cascade A's before/after residency snapshots are **missing**; request logs establish invocation of both models but do **not** independently establish continuous simultaneous residency.

Traceable artifacts: [raw JMeter files and statistics](assignment2/speed/), [calibration timings](assignment2/calibration_results.json), [speed plan](assignment2/a2_speed_plan.json), [final evidence audit](assignment2/final_evidence_audit.md), [runbook](assignment2/RUNBOOK.md). The benchmark has per-run `run-1.jtl` through `run-3.jtl`, `a2_metrics.json`, `log_reconciliation.json`, and saved PC1 statistics/log snapshots.

## Decision: fastest qualifying configuration

**Recommend Qwen 2.5 7B for the measured Assignment 2 fixed-load operating point.**

- It **passes the held-out overall floor and all seven category floors**.
- Its **5.751 s mean run-level p50** is approximately **11.6% lower** than the Llama 3.1 8B reference's **6.505 s**; pooled p95 is also lower (15.578 vs 17.248 s).
- It trades **2.17 percentage points of held-out accuracy** for lower measured latency (80.43% vs 82.61%).
- **Cascade A** fails Consumer loan accuracy and has high 92.45% escalation; **Cascade B** fails Consumer loan and Money transfer accuracy even though it escalates only 62.26%.
- Neither cascade is faster than Qwen at the tested arrival rate; Cascade A has incomplete residency evidence.
- This conclusion addresses **A2's relative accuracy-floor decision**, not all of A1's production requirements. No measured peak capacity, long-term reliability or new hardware capacity is claimed.

The frozen [prediction record](assignment2/prediction_record.md) correctly anticipated Qwen as fastest qualifying. Cascade A escalation was predicted at 80% vs **92.45% actual**; B was predicted at 65% vs **62.26% actual**. Predicted cascade latencies were approximate and were not achieved consistently, especially for Cascade A.

## Setup and execution

### Requirements

Install **Python 3.12**, **Docker Desktop**, **Ollama**, and Git on PC1. For formal benchmarking, use **JMeter 5.6.3** and **Java 17** on a **separate PC2**. Do not place the load generator on the CPU under test.

```powershell
git clone https://github.com/MoeMaki33/ICT3113_Assignment_2.git
cd ICT3113_Assignment_2
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Fetch the four frozen model tags (verify model digests when reproducing the study):

```powershell
ollama pull llama3.1:8b
ollama pull qwen2.5:7b
ollama pull llama3.2:3b
ollama pull gemma2:2b
ollama list
```

Run host Ollama and set `OLLAMA_URL=http://host.docker.internal:11434` in `.env` when running the API through Docker. A standalone Python API instead connects to `http://localhost:11434`.

**Single-model example:**

```dotenv
CLASSIFICATION_MODE=single
OLLAMA_MODEL=qwen2.5:7b
```

**Cascade example:**

```dotenv
CLASSIFICATION_MODE=cascade
CASCADE_SMALL_MODEL=llama3.2:3b
CASCADE_LARGE_MODEL=llama3.1:8b
CASCADE_SETTING=A
```

Restart/recreate the API when changing its `.env` configuration. Keep CPU/RAM allocations, model versions, inference parameters, prompt and performance-test schedule fixed for a reproducible comparison.

```powershell
docker compose up -d --build
docker compose exec api printenv CLASSIFICATION_MODE
ollama ps
.\.venv\Scripts\python.exe -m pytest -q
```

API usage:

```powershell
$body = @{ narrative = "I dispute a charge on my credit card." } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/tickets -ContentType application/json -Body $body
Invoke-RestMethod http://localhost:8000/stats
Invoke-RestMethod "http://localhost:8000/search?q=charge"
```

| Endpoint | Description |
|---|---|
| `POST /tickets` | Synchronously classify, save and return ID/category (HTTP 201 on success) |
| `GET /search?q=...` | Search stored tickets |
| `GET /stats` | Return seven category counts |

Classification backend failures return HTTP 502 and are not stored as successful tickets.

### Reproduce / inspect the A2 evaluation

```powershell
# Accuracy: send only the frozen even-row tickets (requires a correctly configured live API).
.\.venv\Scripts\python.exe -m scripts.a2_accuracy_test --name NEW_RUN_NAME --mode single --model qwen2.5:7b --api-url http://localhost:8000

# Inspect existing raw results, without rerunning experiments.
Get-Content assignment2\accuracy\qwen25_single\metrics.json
Get-Content assignment2\speed\qwen25_single\a2_metrics.json

# JMeter schedule generator: the timing arguments below are the observed A2 calibration.
# Run on PC2, with its own checked-out copy of the repository; substitute the PC1 host IP.
py -3 -m scripts.a2_speed_plan --timings 2.5438 2.8175 3.1268 --host PC1_IP

# Compute 3-run latency metrics from saved JTLs.
.\.venv\Scripts\python.exe -m scripts.a2_speed_metrics --config qwen25_single --duration-s 300

# Join speed JTL request IDs with PC1's complete service log.
.\.venv\Scripts\python.exe -m scripts.a2_log_analysis --mode speed --config cascade_B --log logs/service.log
```

**Important:** A2 scripts refuse to overwrite frozen output paths. The speed-plan generator must be run in a fresh workspace or after explicitly choosing how to preserve the existing `assignment2/a2_speed_plan.json`; the metric and log-analysis commands likewise refuse to overwrite their already-committed output files. See the [complete execution runbook](assignment2/RUNBOOK.md) for the restart, warm-up, simultaneous residency and before/after log procedures.

## Repository navigation

| Directory / file | Contents |
|---|---|
| [`app/`](app/) | FastAPI service, SQLite persistence, single-model classifier, cascade routing and structured request logs |
| [`tests/`](tests/) | API, service and cascade unit/integration tests |
| [`assignment2/`](assignment2/) | Frozen A2 split/rules/predictions, calibration, accuracy, speed and audit evidence |
| [`assignment2/accuracy/`](assignment2/accuracy/) | All six 92-ticket classifications, category metrics, confusion matrices and request logs |
| [`assignment2/speed/`](assignment2/speed/) | Twelve JMeter runs, raw JTLs, p50/p95 summaries, request reconciliation and PC1 snapshots |
| [`jmeter/`](jmeter/) | Fixed open-loop JMeter plan and narrative TSV |
| [`scripts/`](scripts/) | A1 utilities and A2 accuracy, benchmark plan, metrics and log-join scripts |
| [`docs/`](docs/) and [`results/`](results/) | Original **Assignment 1** reports, requirements, 180-ticket accuracy and mixed-load/stress evidence |
| [`data/`](data/) | Team dataset, adjudicated golden set, local data and labels |

## Assignment 1 (historical baseline — distinct methodology)

Assignment 1 evaluated all four models on **180 golden tickets**, using **mixed ticket/search load** and distinct R1–R4 criteria. Its full-set accuracy was: **Llama 3.1 8B 152/180 (84.4%)**, **Qwen 2.5 7B 145/180 (80.6%)**, **Gemma 2 2B 121/180 (67.2%)**, **Llama 3.2 3B 109/180 (60.6%)**.

A1 found that no model had demonstrated simultaneous compliance with all its requirements; Qwen was the leading accuracy-qualified candidate for optimisation. That **A1 operational conclusion and its speed figures must not be confused with A2**: A2 uses only even-row accuracy, new accuracy floors, the fixed five-minute open-loop benchmark, and newly measured three-run p50/pooled p95.

For the original analyses and constraints, refer to [A1 test playbook](docs/test_playbook.md), [A1 recommendation](docs/recommendation.md), [A1 requirements](docs/requirements_evaluation.md) and [A1 prediction comparison](docs/prediction_vs_results.md).

## Limitations, integrity and sources

- The Cascade A model-residency snapshots are missing; continuous joint residency for A is therefore not independently verified. Cascade B has saved before/after CPU residency evidence for all three runs.
- The same fixed-rate, five-minute offered-load window does **not** prove peak sustainable throughput. The benchmark was run three times per configuration and may vary with background CPU/RAM conditions.
- Small per-category held-out sample sizes make floor comparisons sensitive to individual classification outcomes. Report counts alongside percentages; do not tune routing to the held-out set.
- Historical A1 observations use different runs, workload and Ollama version and are not recycled as A2 speed results.
- Full prompt, complaint narratives and model raw responses are intentionally absent from structured service logs. Keep `.env`, credentials, backup ZIPs and private raw-data copies out of public commits.
- AI-assisted code/document drafting must be disclosed in the assignment submission; measurements attributed to PC1/PC2 are the team's actual recorded outputs, not AI-generated benchmark data.

The dataset originates from the course-provided extract of the [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/), with the group's assigned original rows 7000–7999. Model and licensing references: [model documentation](docs/models.md) and [references](docs/references.md). Assignment 2 formal submission requires the team presentation (maximum eight slides) and supporting frozen rule, prediction record and workload-row list; this repository provides the reproducibility evidence.
