# ADR-0022 — Ride condition monitoring: the model flags, a certified human clears

**Status:** accepted · **Date:** 2026-09-11
**Serves:** FR-2.5, FR-2.9, NFR-AVL-1, A10, A19, R24
**Related:** ADR-0001, ADR-0002, ADR-0016, ADR-0017, ADR-0023

## Context
Forty rides from the eighteenth century are the estate's other expensive asset, and until now they
appear in this architecture as a status event and a queue counter. That was a defensible boundary: the
instrumentation predictive maintenance normally wants — vibration spectra at rate, load cycles, motor
current — mostly cannot be fitted to heritage machinery (A10), and ride safety is certified mechanical
inspection, a domain where a model has no standing at all.

Two things make the boundary worth reopening. First, an unplanned closure is not only a repair bill: it
pushes its queue onto neighbouring rides, which the forecast then reads as demand, and it is the single
most visible thing that can go wrong on a peak day. Second, "cannot be instrumented" turns out to be
per ride rather than per estate — a cycle counter, a clamp-on current sensor and a surface temperature
probe are non-invasive, and on a meaningful share of the forty they can be fitted without touching
protected fabric.

The danger is the obvious one. A model that predicts a bearing failure sounds very much like a model
that says a ride is safe, and those are different claims with different consequences.

## Decision
1. **Only non-invasive telemetry, fitted per ride after a heritage assessment** (A19): cycle counter,
   clamp-on current, surface temperature at bearings and motors, and a run-hours clock. Where a ride
   cannot take even these, it stays as it is today — a status event and a counter — and the scenario
   simply does not cover it.
2. **The output is a condition flag with its evidence, never a verdict.** The capability produces "this
   ride's current and temperature signature has diverged from its own run-in baseline" together with
   the traces that say so. It does not produce a remaining-useful-life number, because a heritage
   ride has no fleet to estimate one from.
3. **AI never clears a ride, and the interface says so.** A flag opens an inspection item for the
   certified engineer; only that engineer changes ride status. There is no automatic band at any
   confidence — this is the high risk class and the 100:1 row of the cost-of-error matrix
   ([ADR-0016](ADR-0016-cost-of-error-sets-the-bands.md) §3,
   [ADR-0017](ADR-0017-ai-risk-classes-and-proportional-controls.md) §4).
4. **The statutory inspection schedule is untouched.** Condition monitoring adds inspections; it never
   removes, delays or re-times one. A ride that the model thinks is fine is inspected exactly as often
   as it is today.
5. **Rules first, model second** ([ADR-0023](ADR-0023-rules-first-model-second.md)): Phase 1 is
   thresholds on current and temperature against the ride's own run-in data, which is all that is
   available before a season of history exists. A model is promoted only after twelve months of
   `RideStatusChanged` and cycle counts, and only if it beats the threshold rule on the same window.
6. **Sensor health is part of the capability, not an afterthought.** The stuck, dead and drifting
   detectors of the [sensor health](../hld/core/edge-and-connectivity.md#sensor-health-dead-stuck-and-drifting)
   rules apply here, because a drifting current clamp and a degrading motor look alike; a flag whose
   only evidence is an unhealthy sensor is suppressed and shown as such.
7. **Closures feed the rest of the estate as facts.** `RideStatusChanged` already reaches the forecast,
   the companion and the daily report; a condition flag is a model output and stays inside Park
   Operations under the probabilistic-events rule ([HLD](../hld/README.md#bounded-contexts)).

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Leave rides out of scope, as before | Honest about A10; nothing to build; the smallest surface | Leaves the most visible failure on a peak day entirely unmanaged, and the neighbouring proposal is right that some of the forty can be instrumented | The boundary was drawn per estate, not per ride |
| Full predictive maintenance with RUL estimates | The industry-standard shape; a number a manager can plan against | No fleet to estimate a distribution from, no vibration spectra on most rides, and a remaining-life number is exactly the claim that gets confused with a safety clearance | Data and risk |
| Model-assisted clearance — AI narrows what the inspector checks | The largest labour saving | A model influencing the scope of a statutory inspection is a model influencing certification; there is no tier-1 equivalent for a ride | Certification |
| Vibration spectra on all forty | The signal predictive maintenance actually wants | Requires mounting to protected fabric on most rides (A10); a heritage assessment would refuse | A10 |
| Non-invasive telemetry, condition flags, human clearance (chosen) | Fits the constraint; adds inspections rather than replacing them; the safety claim stays with the person who may make it | Covers only part of the forty; weaker signal than a fleet operator would accept; a new device class to maintain | — |

## Consequences
**Positive:** the first data the estate has ever had about how its rides behave; unplanned downtime
becomes measurable, which is the precondition for reducing it; the forecast stops being surprised by a
closure it could have seen coming.
**Negative:** a new sensor class across forty assets, each needing a heritage assessment; coverage will
be partial and uneven, so the metric is per instrumented ride rather than per estate; and the whole
capability is worthless in year one by construction — it has nothing to compare against until a season
of baselines exists.

| Risk | Mitigation |
| --- | --- |
| A flag is read as a safety clearance, or its absence as one (R24) | §3 and §4, stated on the ride screen itself and in the inspection item; the capability's own name is *condition*, not *safety* |
| Heritage damage from fitting a sensor | §1 — non-invasive classes only, per-ride assessment before any fitting, refusal is a normal outcome |
| Alert fatigue on the engineer | The 100:1 row biases toward recall, but the [roles table](../hld/ai-platform/README.md#humans-in-the-loop-who-does-what) bounds the hours; a threshold that exceeds them is narrowed and the shortfall recorded |
| A drifting sensor produces a phantom degradation | §6 — sensor health suppresses it and says which device, the same rule S1 applies to a wedged feed scale (GD-16) |

## How we will know this was right
Unplanned downtime hours per instrumented ride per season falling against the first season's baseline;
zero rides opened or closed on a model's output; flags whose inspection found nothing trending down as
the baselines mature; and a decision, after two seasons, on whether the capability earns its sensors.
