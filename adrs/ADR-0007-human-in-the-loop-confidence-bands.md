# ADR-0007 — Human in the loop via confidence bands

**Status:** accepted · **Date:** 2026-09-05
**Serves:** FR-3.3, FR-3.5, FR-5.1, OKR 3.1, 3.5, R2, R3
**Related:** ADR-0006, ADR-0008

## Context
Vision and anomaly models produce probabilities, not diagnoses. Acting on every flag would exhaust the veterinarian; ignoring low-confidence flags could miss a sick animal. We need a standard, auditable way to decide when AI acts alone, when a human decides, and when a signal is discarded — and a way for human decisions to improve the model.

## Decision
1. Every probabilistic capability defines **three confidence bands** with actions, configured per species group and anomaly type:
   - **High:** auto-act within a bounded scope (record an observation, adjust a baseline, log a feeding). Never auto-act on treatment or safety.
   - **Medium:** route to a **review queue** with an SLA (welfare: 4 h, target 1 h), prioritised by species risk. Reviewer sees clip, sensor trace, baseline, model rationale; decides *Confirm (finding)* / *Dismiss (reason code)*.
   - **Low:** discard from the queue but **retain for learning**; a weekly random sample is human-reviewed to catch false negatives.
2. Bands are **policy, not code**: owned by the domain lead (vet), versioned, changeable without a deployment.
3. **Reviewer decisions are labels.** They flow to the training pipeline and to the evaluation service; the **override rate** per anomaly type is a first-class metric (OKR 3.5) that triggers recalibration when it rises.
4. **Full audit trail** per decision: model version, inputs, confidence, band, reviewer, outcome (FR-5.1).
5. The same mechanism is reused wherever AI recommends an action with consequences: staffing plans (manager approves), pricing outside guardrails (management approves), companion escalations (staff).

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Fully automated alerts to keepers | Fast, cheap | Alert fatigue; no calibration loop; unfair to animals and staff when wrong | R3 |
| Human reviews everything | Highest accuracy | Vet time is the scarcest resource; does not scale to 200 animals × 4 dimensions | Cost, OKR 3.1 |
| Single threshold (act / don't) | Simple | No learning from the grey zone; either misses or floods | Learning loop lost |
| Confidence bands + queue (chosen) | Focuses human time where it matters; calibrates itself | Needs calibrated models; queue tooling to build | — |

## Consequences
**Positive:** vet time spent on genuinely ambiguous cases; the model improves from real decisions; every AI-influenced action is explainable after the fact.
**Negative:** requires calibration testing at promotion (ADR-0008); reviewers need training and consistent reason codes; SLAs need staffing.

| Risk | Mitigation |
| --- | --- |
| Model miscalibrated → bands meaningless | Calibration error is a promotion gate; bands re-derived per model version |
| Reviewer inconsistency | Reason-code taxonomy; periodic agreement check on a shared sample |
| Queue backlog at peak | Priority by species risk; escalation to head keeper; band tightened temporarily by policy |

## How we will know this was right
Override rate ≤ 40% then ≤ 25%; time-to-review within SLA ≥ 95%; monthly real-world precision/recall from delayed ground truth improving release over release.
