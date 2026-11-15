# Assignment 2 cascade rule — pre-benchmark design
Status: DESIGN, not yet runtime validated. Memory residency is a hard prerequisite; do not benchmark until `ollama ps` confirms both models remain resident on official PC1 with unchanged RAM and CPU allocation.

## Fixed candidate pair
- First stage: `llama3.2:3b` (small, fastest A1 sequential p50).
- Second stage: `llama3.1:8b` (large, highest A1 overall golden accuracy).
- Both are frozen Assignment 1 tags/digests; do not introduce new models or change the classification prompt.
- Both stages use exactly `app.services.classifier.build_prompt` and the existing parser. Only their model tags differ.
- Return exactly the final category through POST /tickets and store only the final classification.

## Signal
Category predicted by the small model. The true golden category is NEVER consulted during routing. Predictive precision of category outputs is assessed only using odd-row (tuning) tickets. Unknown / unusable first-stage responses propagate an error, rather than silently alter the prompt or use undeclared fallback.

## Two frozen settings
- **Setting A, conservative**: accept the small answer iff it is exactly `Mortgage`; otherwise escalate.
- **Setting B, broader**: accept the small answer iff it is exactly `Mortgage` or `Bank account or service`; otherwise escalate.
Both settings are fixed before A2 benchmarking. This uses a single first-stage call plus a second-stage call for escalations. No cache, no reclassification prompt, no alternative classifier.

## Tuning-only evidence and rationale
Existing A1 small-model predictions on the odd-row tuning subset show:
- `Mortgage` 14 correct / 15 predictions (93.3% predicted-label precision).
- `Bank account or service` 10 / 14 (71.4%).
- `Credit reporting` 19 / 37 (51.4%) and `Debt collection` 4 / 10 (40%) were not accepted.
- `Money transfer or service` 2/2 is too few examples for a robust acceptance rule.
These are retrospective A1 outputs on the tuning rows, not new A2 measurements or test-set tuning.

## Reproducibility
Every successful POST /tickets log should record: mode, first_model, final_model, escalated, escalation_setting, predicted_category, duration_ms and request_id. A2 experiments must also capture raw JTL and service-log evidence, and use identical prompt, versions and settings across configurations. Record and verify simultaneous model residency with `ollama ps` and hardware limits before any cascade benchmark.

## Important restriction
A2 requires the golden-set split, escalation rule, and prediction record to be committed before the first A2 benchmark. Do not change these files after benchmarking begins; if residency fails, document the infeasibility and assess a smaller Assignment 1 model pair without pretending the original pair was tested.
