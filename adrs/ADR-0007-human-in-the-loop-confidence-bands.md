# ADR-0007 — Human in the loop via confidence bands

**Status:** accepted · **Date:** 2026-09-05
**Serves:** FR-3.3, FR-3.5, FR-5.1, OKR 3.1, 3.5, R2, R3
**Related:** ADR-0006, ADR-0008

## Context
Vision and anomaly models produce probabilities, not diagnoses. Acting on every flag would exhaust the veterinarian; ignoring low-confidence flags could miss a sick animal. We need a standard, auditable way to decide when AI acts alone, when a human decides, and when a signal is discarded — and a way for human decisions to improve the model.

## Decision
0. **A band is derived from what an error costs, not chosen by convention.** The table below is the input; 0.9 is an output, and for some capabilities the answer is that no band is defensible at all.
1. Every probabilistic capability defines **three confidence bands** with actions, configured per species group and anomaly type:
   - **High:** auto-act within a bounded scope (record an observation, adjust a baseline, log a feeding). Never auto-act on treatment or safety.
   - **Medium:** route to a **review queue** with an SLA (welfare: 4 h, target 1 h), prioritised by species risk. Reviewer sees clip, sensor trace, baseline, model rationale; decides *Confirm (finding)* / *Dismiss (reason code)*.
   - **Low:** discard from the queue but **retain for learning**; a weekly random sample is human-reviewed to catch false negatives.
2. Bands are **policy, not code**: owned by the domain lead (vet), versioned, changeable without a deployment.
3. **Reviewer decisions are labels.** They flow to the training pipeline and to the evaluation service; the **override rate** per anomaly type is a first-class metric (OKR 3.5) that triggers recalibration when it rises.
4. **Full audit trail** per decision: model version, inputs, confidence, band, reviewer, outcome (FR-5.1).
5. The same mechanism is reused wherever AI recommends an action with consequences: staffing plans (manager approves), pricing outside guardrails (management approves), companion escalations (staff).
6. **Every model output crossing a module boundary is a typed record**, never a bare number: `{value, confidence, evidence, capability, bundle_id}`. The `evidence` field is what makes review real rather than a blind approval — a clip window and bounding box for vision, the cited knowledge-base record for the companion, factor contributions for a forecast, the sensor trace for an anomaly. A reviewer who cannot see why cannot be accountable for the decision, and an audit after the fact needs the same field ([ADR-0004](ADR-0004-event-driven-backbone.md) §10, FR-5.1).

## What an error costs, and what that sets

Units are ours: the vet's minutes come from the [human roles table](../hld/ai-platform/README.md#humans-in-the-loop-who-does-what), the money from the [cost model](../appendix/cost-model.md). The ratios are arguments, not measurements — season 1 replaces them with observed outcomes, and that is exactly why they are written down where they can be challenged.

| Capability | A false negative costs | A false positive costs | Implied ratio | What that sets |
| --- | --- | --- | --- | --- |
| **Welfare anomaly** (feeding, activity) | An illness found days late: treatment instead of prevention, and at worst an animal the collection cannot replace. OKR 3.2 is the line it moves | ≈ 15–20 minutes of veterinary review, out of the 2 → 8 h/week the roles table budgets | ≈ **20:1** | Promotion needs recall ≥ 0.90 while precision ≥ 0.60 is accepted: a 40% false-flag rate is affordable, a 10% miss rate is close to the ceiling of what the weekly audit of unflagged hours can still catch |
| **Aggression near visitors** (tier-1) | Unbounded — the cost is a person | Staff walk to an enclosure for nothing | **No ratio exists**, so no band is defensible | The capability is advisory only and never the sole alert path (FR-3.7). A deterministic tier-0 rule owns the outcome and the model may only add to it |
| **Piranha count** | The population drifts unseen between censuses | A census that disagrees with the ledger, and a stock take nobody trusts | ≈ **symmetric** | Precision and recall both ≥ 0.95, and the estimate is published as an interval rather than a point |
| **Visitor masking** | An unmasked frame of a family in storage — a personal-data incident (A5) and the one failure that cannot be walked back | Animal area masked away, so one frame loses its features | Asymmetric **and irreversible on one side** | Not a band but a gate: unmasked person regions = 0, over-masking ≤ 10% is the price paid for it, and a stream is dropped rather than stored unmasked |
| **Companion safety facts** | A family is told they may touch a venomous animal | An answer is refused that could have been given | Irreversible against merely inconvenient | Not a band either: safety facts are inserted verbatim from a human-approved field per language and the model may not restate them ([ADR-0010](ADR-0010-grounded-llm-with-guardrails.md) §2, NFR-LNG-1); refusal is the default |
| **Staff protocol answers** | A keeper acts on a wrong or stale procedure during a bite, an escape or a quarantine | A refusal where an approved document existed: a keeper walks to the folder, mildly annoyed | Irreversible against trivial | Not a band: steps are inserted verbatim from the approved document, the citation is mandatory, and no approved document produces a refusal with a name to call ([ADR-0010](ADR-0010-grounded-llm-with-guardrails.md) §7) |
| **Footfall forecast** | An under-staffed zone: queues, and OKR 2.2 missed | An over-staffed zone: idle hours, against OKR 2.4 | ≈ **2:1** against under-staffing | The optimiser is asked for plans that err high, and the ops manager's edits are the label |
| **Quiet-day pricing** | Margin given away on a day that would have filled anyway | An empty Wednesday, which is the whole point of S5 | Asymmetric at the floor | Not a confidence band but a hard invariant on contribution per visitor-day, with the weekly guardrail pausing a discount level rather than a model |

Two conclusions the table forces. **Where one side is unbounded or irreversible, the answer is not a stricter threshold but a different mechanism** — advisory-only, verbatim insertion, or a zero gate. And **the sensitive parameter is the ratio, not the boundary**: the bands move when the argument about cost moves, which is why they are policy owned by the vet rather than constants in code (§2).

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Fully automated alerts to keepers | Fast, cheap | Alert fatigue; no calibration loop; unfair to animals and staff when wrong | R3 |
| Human reviews everything | Highest accuracy | Vet time is the scarcest resource; does not scale to 200 animals × 4 dimensions | Cost, OKR 3.1 |
| Single threshold (act / don't) | Simple | No learning from the grey zone; either misses or floods | Learning loop lost |
| Bands chosen by convention (0.9 / 0.7 because those are the usual numbers) | No argument to have; quick to write down | The boundary then encodes nobody's judgement about what an error costs, so it cannot be defended when the vet asks why 0.9, and it hides the cases where no threshold is defensible at all | Replaced by the cost-of-error table above, which makes the ratio the reviewable artefact |
| Confidence bands + queue (chosen) | Focuses human time where it matters; calibrates itself | Needs calibrated models; queue tooling to build | — |

## Consequences
**Positive:** vet time spent on genuinely ambiguous cases; the model improves from real decisions; every AI-influenced action is explainable after the fact.
**Negative:** requires calibration testing at promotion, per band and not only in aggregate (ADR-0008); reviewers need training and consistent reason codes; SLAs need staffing.

| Risk | Mitigation |
| --- | --- |
| Model miscalibrated → bands meaningless | Calibration error is a promotion gate — **ECE over 10 equal-mass bins, plus a per-band check** so an aggregate cannot hide an optimistic medium band, and confidence is a post-hoc-calibrated quantity shipped in the bundle, not a raw model score ([how the gated metrics are defined](../hld/ai-platform/README.md#how-the-gated-metrics-are-defined)); bands re-derived per model version |
| Reviewer inconsistency | Reason-code taxonomy; periodic agreement check on a shared sample |
| Queue backlog at peak | Priority by species risk; escalation to head keeper; band tightened temporarily by policy |

## How we will know this was right
Override rate ≤ 40% then ≤ 25%; time-to-review within SLA ≥ 95%; monthly real-world precision/recall from delayed ground truth improving release over release.
