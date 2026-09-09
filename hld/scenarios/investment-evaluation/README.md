# S7 · Investment evaluation

> "We have no real idea what parts of the estate are most popular, so it's difficult to know where to invest." S3 answers the first half. This answers the second — and it is the only scenario whose most common correct output is "we cannot tell you."

**Moves:** OKR 2.5 (investments with a measured effect and a stated interval within two quarters)
**Process:** [P4 · the 21:00 review and the commercial call](../../../README.md#where-ai-sits-in-the-working-day), quarterly rather than weekly
**Phase:** 3 — needs the investment register from Phase 0 (FR-2.9) and at least a year of zone history — see [roadmap](../../../README.md#delivery-roadmap-what-we-build-when-and-what-we-buy)
**ADRs:** [ADR-0008](../../../adrs/ADR-0008-ai-evaluation-and-production-monitoring.md) (how a method with no ground truth is still evaluated), [ADR-0004](../../../adrs/ADR-0004-event-driven-backbone.md) (the register is a fact, the estimate is a model output and stays inside Park Operations)

## The gap this closes

FR-2.4 has always said the platform correlates investments with changes in popularity, and until now
nothing sat underneath it. A before-and-after chart is not an answer: a refurbished enclosure that
reopened in April will show more visitors in May whether or not the refurbishment mattered, because May
has better weather than April. The estate would then congratulate itself and spend the next €200k the
same way.

**The prerequisite is not a model, it is a register.** You cannot evaluate investments nobody recorded,
and today nobody records them — hence FR-2.9, which is Phase 0 and costs a form. That ordering matters:
the register has to exist for a year before the method has anything to work on.

## Why a rule cannot do this

The question is counterfactual — what would this zone have done *without* the investment — and no rule
produces a counterfactual. The method is ordinary applied statistics rather than anything exotic:

- **Difference-in-differences** against comparable zones that saw no investment in the same window, on
  the daily zone-occupancy and spend-per-zone series S3 and the [data platform](../../core/README.md#data-platform)
  already produce.
- **A pre-trend test on every control.** A control zone whose trajectory already diverged before the
  work started is disqualified; this is the check that separates a result from a coincidence.
- **Synthetic control** where no single comparable zone exists — a weighted combination of others fitted
  on the pre-period.
- **Seasonality and calendar** from the same features S3 forecasts with, so the two never disagree
  about what a normal Tuesday in May looks like.

Classical, deterministic given its inputs, and therefore tested like software rather than gated on a
confidence band. There is no generative model anywhere in this scenario; the quarterly readout reuses the
existing `summarise-*` drafter under its human-approval rules, or a template.

## The output, and why refusal is the interesting part

Each evaluation returns an **effect estimate with an interval**, the counterfactual it rests on, the
controls used, and the assumptions that would invalidate it — or the verdict **cannot attribute**, when:

- another investment, a new ride or a marketing push overlapped the window;
- no control zone passes its pre-trend test;
- the interval is wider than the effect size, which is a real answer and not a failure;
- the register entry is incomplete.

**We expect "cannot attribute" to be the majority verdict in the first years**, because a small estate
makes a few large investments at once and that is exactly the condition under which causal inference
cannot work. Saying so is the point. A capability that always produces a number would be producing
numbers, not findings — and management deciding where the next €200k goes is better served by "we
genuinely cannot separate these two things, so stagger the next two openings" than by a confident
estimate built on a disqualified control.

That advice — **stagger investments so they can be measured** — is the scenario's real contribution, and
it costs nothing to act on.

## Containers

| Container | Responsibility | AI? |
| --- | --- | --- |
| Investment register | The record: what, where, when it opened, cost, zones touched (FR-2.9). A read model in Park Operations, written by a human | No |
| Evaluation job | Quarterly batch: assemble the panel, fit controls, run the pre-trend test, estimate, or refuse | Classical ML / statistics |
| Quarterly readout | Effect, interval, counterfactual, assumptions, verdict — into the commercial call | Wording only, via the existing drafter |

No new deployable: the job runs in the existing batch workers, and the estimate stays inside Park
Operations as a model output ([ADR-0004](../../../adrs/ADR-0004-event-driven-backbone.md) §9) — what
crosses to management is the readout a human presents.

## Validation & verification

A causal estimate has no ground truth to score against, which is exactly why it needs stricter process
discipline than a forecast does, not looser:

| Check | How | Gate |
| --- | --- | --- |
| **Placebo tests** | Run the method on windows where nothing was invested | Significant "effects" found ≤ the false-positive rate the interval implies |
| **Pre-trend test** | Every control, every evaluation | A failed control is never used; failures are reported with the verdict |
| **Back-test on a known change** | A zone closed for a season is a large, unambiguous negative effect | The method recovers it, direction and rough magnitude |
| **Invariant suite** | Property-based tests on the panel assembly: no leakage of post-period data into the pre-period, no zone used as its own control | Violations = 0 |
| **Sensitivity** | Re-run with each control dropped in turn | An effect that survives only one control specification is reported as fragile |

**Kill gate:** if two full years of evaluations return *cannot attribute* for every investment, the
estate's investment cadence is too clustered for any method to work, and the capability goes — the useful
residue is the staggering advice, which does not need software to deliver.

## Degradation ladder

1. **Cloud + AI:** estimates with intervals, quarterly.
2. **Cloud without AI:** the register and the raw before-and-after series, presented without a causal
   claim — which is honestly most of the value, since the register is the part that did not exist.
3. **Estate-only:** nothing, and nothing is needed; this is a quarterly analytical job.
