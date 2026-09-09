# ADR-0008 — AI evaluation gate and production monitoring

**Status:** accepted · **Date:** 2026-09-05
**Serves:** NFR-VER-1, NFR-OBS-1, OKR 5.3, R11
**Related:** ADR-0005, ADR-0007

## Context
"Verifying deterministic solutions is easy — GenAI is non-deterministic. How will you know if your AI-driven functionality starts misbehaving in production?" We have classical ML, vision and generative capabilities; each needs a fit-for-purpose answer, but the *process* should be one.

## Decision
**One promotion process for every capability**, with capability-specific metrics.

1. **Golden dataset** per capability, owned by the domain lead, versioned with the bundle:
   - welfare: labelled clips/time series per species group;
   - piranha: manually counted multi-view frame sets;
   - forecasting: historical footfall with rolling-origin splits;
   - pricing: historical sales weeks;
   - companion: Q&A pairs with expected facts, planning scenarios with hard constraints, adversarial prompts.
2. **CI evaluation gate**: a candidate bundle is scored on its golden set and must meet the capability's thresholds — all of them in the [thresholds & cadences table](../hld/ai-platform/README.md#thresholds-and-cadences-source-of-truth), each with a named instrument ([definitions](../hld/ai-platform/README.md#how-the-gated-metrics-are-defined)) — **with no regression** against the current production bundle. Calibration is gated as ECE over 10 equal-mass bins **and per confidence band**, with the reliability diagram kept as a build artifact. **Deterministic components on AI paths** (pricing policy engine, staffing optimiser, gate rules) get **invariant suites**: property-based tests over generated inputs with a violations = 0 gate, and the same invariants checked in production by an independent validator.
3. **Shadow mode** before live: candidate runs on live traffic in parallel; outputs compared; disagreements sampled for human review. Minimum 2 weeks for welfare/companion, 1 forecasting cycle for forecasting.
4. **Production monitoring**, three layers:
   - *Technical:* latency, error rate, cost, token use per capability (gateway tracing).
   - *Model:* input drift (feature/image statistics), output drift (confidence histograms, class mix), calibration on sampled human-labelled data — the same ECE definition and the same per-band check as the gate, so the two numbers are comparable.
   - *Business guardrails:* vet override rate, forecast MAPE vs. actuals, companion thumbs-down/escalation/ungrounded-block rate, pricing conversion drop. Each has a threshold and an **automatic rollback** to the previous production bundle plus an alert to the owner.
5. **Non-deterministic outputs** (companion): sampled **LLM-as-judge** for factuality and safety against the KB, calibrated weekly by a human reviewing 50 sessions; judge disagreement with humans is itself monitored.
6. **Delayed ground truth** is joined back where it exists (treatments ↔ flags; actual footfall ↔ forecast; census of record and the births/deaths/transfers ledger ↔ population estimates) to compute real-world accuracy monthly. Ground truth must be measurably better than the target it scores: a ±30% visual audit cannot score a ±10% estimate, so S2 uses a census at planned tank maintenance as its reference.
7. **Human override rate is the leading indicator, and it has two different meanings.** A rise means either the model is degrading or the people are saturating, and the responses diverge: sustained above its threshold for two review cycles with queue depth normal is a **model** signal and rolls the bundle back to its predecessor; the same rise with the queue over capacity is a **staffing** signal and goes to [review-queue health](../hld/ai-platform/README.md#review-queue-human-in-the-loop) instead. Trust falls before any business metric moves, which is what makes this the earliest signal available — and reading it wrong retrains a model that was never wrong.
8. **Kill switch & deterministic fallback** for every capability, tested in game days GD-9 and GD-10 of the [resilience validation catalogue](../hld/core/resilience-validation.md) — the same catalogue that verifies the non-AI foundation.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Manual QA before release only | Low effort | Non-deterministic systems drift after release; no signal in production | Fails NFR-VER-1: nothing watches the model after release |
| Rely on provider dashboards | Zero build | Provider-shaped, not capability-shaped; gone when the provider goes; no business guardrails | Independence |
| Full MLOps platform product | Rich | Cost and learning curve for a team of 5; still needs our golden sets and guardrails | Start lean; revisit at scale |
| Golden sets + gate + shadow + guardrails (chosen) | Fits all three AI kinds; owned by domain leads | Golden-set curation is ongoing work | — |

## Consequences
**Positive:** nothing unproven reaches visitors or animals; misbehaviour is detected by business impact, not by complaints; rollbacks are automatic.
**Negative:** golden sets need care and feeding; shadow mode doubles inference cost temporarily; judges (LLM or human) add latency to feedback loops.

| Risk | Mitigation |
| --- | --- |
| Golden set stale (new species, new rides) | Golden-set refresh is part of every domain change; drift monitors flag distribution shift |
| Guardrail thresholds too tight → rollback storms | Thresholds set from shadow data; hysteresis; owner acknowledgement before re-promotion |
| LLM-as-judge shares the model's blind spots | Human calibration weekly; judge from a different provider than the generator |

## How we will know this was right
100% of production capabilities have a passing eval and a documented fallback (OKR 5.3); time from misbehaviour to rollback measured in minutes; monthly real-world accuracy reports exist for every capability.
