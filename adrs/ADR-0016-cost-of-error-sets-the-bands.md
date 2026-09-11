# ADR-0016 — The cost of an error sets the confidence bands

**Status:** accepted · **Date:** 2026-09-11
**Serves:** FR-3.2, FR-3.3, FR-3.7, FR-4.3, NFR-VER-1, OKR 3.5, R2, R3
**Related:** ADR-0007, ADR-0008, ADR-0017, ADR-0022

## Context
[ADR-0007](ADR-0007-human-in-the-loop-confidence-bands.md) gives every probabilistic capability three
bands and a review queue, but it does not say where a boundary comes from. In practice the numbers in
the [thresholds table](../hld/ai-platform/README.md#thresholds-and-cadences-source-of-truth) were set
per capability by argument, and an argument does not transfer: when a sixth capability arrives, or when
the vet's hours change, there is nothing to re-derive from. Worse, a band set "at 0.9, as is
conventional" quietly asserts that a false positive and a false negative cost the same, which in this
estate is never true. A dismissed alert costs a keeper ten minutes. A missed one can cost a rare
animal.

## Decision
1. **Every capability declares a cost-of-error row before its bands are set**: what a false negative
   costs, what a false positive costs, the approximate ratio between them, and who owns the judgement.
   The row is policy config next to the bands, versioned in Git.
2. **The ratio sets the direction of the bias, not the number.** A high false-negative cost lowers the
   escalation boundary — more goes to a human — and a symmetric cost allows a higher automatic band.
   The exact boundary is then fitted on the golden set to hit the capability's recall and precision
   targets, and re-fitted when the model version changes.
3. **The matrix, as it stands today** (ratios are estimates, re-stated with the owner each season):

   | Capability domain | A miss costs | A false alarm costs | ≈ FN:FP | What the bands do |
   | --- | --- | --- | --- | --- |
   | Ride condition (S8, [ADR-0022](ADR-0022-ride-condition-monitoring.md)) | An injury, and the estate's licence | An inspection slot | ≈ 100:1 | No automatic band at all: the model flags, a certified human clears |
   | Animal welfare (S1) | A rare or venomous animal dies; treatment cost multiplies | Keeper and vet minutes | ≈ 20:1 | Recall maximised; medium band deliberately wide; the vet decides |
   | Safety advisory (FR-3.7) | Nothing — the tier-0 rule is the guarantee | Staff walk to an enclosure for no reason | ≈ 1:1 on its own path | Advisory only; it may never delay or replace a rule |
   | Content and brand (S7) | A post the estate has to apologise for | A discarded draft | ≈ 5:1 | Nothing publishes without the curator |
   | Pricing (S5) | Revenue left on the table | A family feels treated unfairly | ≈ 1:3 — **inverted** | Guardrails bind harder than the model; management approves anything outside them |
   | Companion suggestion (S4) | A mediocre next stop | A mediocre next stop | ≈ 1:1 | Automatic, with a thumbs-down loop |

4. **An inverted ratio is stated as such.** Pricing is the case where the false positive is the
   expensive one — a family that feels singled out costs more than a quiet day priced too high — and
   the bands are set in the opposite direction from every other row. Writing the matrix down is what
   makes that visible.
5. **A capability whose ratio cannot be argued does not get an automatic band.** If nobody can say what
   a miss costs, everything goes to a human until somebody can.
6. **The matrix is reviewed when the cost changes, not when the model does** — a new species, a change
   in the vet's hours, a licensing change. Model changes re-fit the boundary; cost changes re-derive
   it.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| One global threshold, 0.9 everywhere | Trivial to explain and to implement | Asserts symmetric costs, which is wrong in five of the six rows above; floods the vet or starves them depending on the capability | It is the convention this ADR replaces |
| Per-capability numbers set by argument, as today | Already in the thresholds table and working | Nothing to re-derive from when a capability, a season or a staffing level changes; the reasoning lives in a meeting rather than the repository | Does not transfer |
| Expected-cost optimisation against measured euro costs | Principled; would give a number rather than a direction | Needs euro costs per outcome that the estate does not have and will not have in season 1 | Precision the data cannot support |
| Declared ratios setting the direction, golden set setting the number (chosen) | Honest about which part is judgement and which is measurement; survives a staffing change | The ratios are estimates and will be argued about | — |

## Consequences
**Positive:** each band has a stated reason a reviewer can disagree with; the inverted pricing row stops
being a surprise; a new capability starts from a question rather than a convention.
**Negative:** the ratios are assumptions dressed in numbers, and a reader may take ≈ 20:1 more literally
than it deserves — hence the explicit re-statement each season; the matrix is one more artefact with an
owner.

| Risk | Mitigation |
| --- | --- |
| The ratio is taken as measurement rather than judgement | Every row is labelled an estimate and carries its owner; only the direction is load-bearing |
| The band derived from a ratio floods the review queue (R3) | The [human roles table](../hld/ai-platform/README.md#humans-in-the-loop-who-does-what) is the binding constraint: a band that exceeds the owner's hours is narrowed and the shortfall recorded, rather than the hours being assumed |
| Calibration makes the band meaningless | Bands are only interpretable on a calibrated score; the ECE gate and the per-band check in [ADR-0008](ADR-0008-ai-evaluation-and-production-monitoring.md) remain a precondition |

## How we will know this was right
A new capability's bands are derivable from its row without reopening the argument; the vet's override
rate falls toward its target while the queue stays inside the roles table; and a change in staffing
produces a band change through this document rather than an ad-hoc edit.
