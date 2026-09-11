# ADR-0023 — Rules first, model second: the cold-start policy

**Status:** accepted · **Date:** 2026-09-11
**Serves:** NFR-RES-2, NFR-VER-1, OKR 5.3, A6, R7
**Related:** ADR-0007, ADR-0008, ADR-0016, ADR-0022

## Context
Every scenario in this proposal has the same year-one problem: the data it needs does not exist yet.
Forecasting wants a season of footfall (A6). Welfare anomaly detection wants per-animal baselines and
labelled clips. Price elasticity wants a year of sales at varying prices. Ride condition monitoring
wants run-in data. The roadmap already sequences the models behind the data, but sequencing alone
leaves a gap: between the sensor going live and the model being promoted, the estate has the
instrumentation and none of the benefit, and there is nothing for the eventual model to be compared
against.

The failure this prevents is the usual one — a model promoted on a thin golden set, beating nothing in
particular, and then defended because it exists.

## Decision
1. **Every AI capability ships as a deterministic rule first, in production, doing the real job.** Not
   a placeholder and not a stub: a documented rule with an owner, a threshold and an alert, used by the
   people who will later use the model.
2. **That rule is permanently the capability's fallback** (NFR-RES-2). It does not get deleted when the
   model arrives; it keeps running, which is what makes the kill switch
   ([ADR-0008](ADR-0008-ai-evaluation-and-production-monitoring.md) §7) and GD-10 possible.
3. **A model is promoted only if it beats its own rule** on the capability's golden set, on the metric
   in the [thresholds table](../hld/ai-platform/README.md#thresholds-and-cadences-source-of-truth) —
   not merely if it clears an absolute threshold. "Beats the same weekday last week, adjusted for
   season" is a harder and more honest bar than "MAPE ≤ 25%".
4. **The rule's period is what builds the golden set.** Every decision the rule triggers is reviewed by
   the human who would have reviewed a model's, with the same reason codes, so the labels accumulate as
   a side effect of the job rather than as a labelling project (R13).
5. **The rule defines the capability's interface.** Consumers subscribe to the capability, not to the
   rule or to the model, so promotion changes nothing downstream — the same principle as capability
   addressing in [ADR-0005](ADR-0005-model-gateway-and-provider-independence.md).
6. **Where a rule genuinely cannot do the job, the capability waits** rather than shipping a model on
   insufficient data. Per-animal vision has no rule equivalent; it stays in Phase 3 behind its golden
   set, and nothing pretends otherwise.
7. **The comparison is kept after promotion.** The rule keeps running in the background and its error
   is reported alongside the model's, monthly. A model that stops beating its rule is a rollback
   candidate, and this has caught more real regressions in practice than drift monitoring does.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Wait for data, ship nothing | No premature model; no rule to maintain | A year of instrumentation with no benefit, no labels accumulating, and no baseline for the model to beat | Wastes the year that matters most |
| Ship the model early on a small golden set | The capability looks complete sooner | A model validated on too little data, with nothing to compare it against, and a team invested in defending it | The failure this ADR exists for |
| Rule as a temporary scaffold, deleted on promotion | Less to maintain long-term | Deletes the fallback, which NFR-RES-2 requires and the kill switch depends on; and removes the ongoing comparison of §7 | Loses the degradation story |
| Buy a general-purpose model to bridge the gap | Immediate capability | No API knows this estate's animals or its Tuesdays; and it still produces no labels of our own | Accuracy and lock-in |
| Rule first, model must beat it, rule stays (chosen) | Benefit from day one; an honest promotion bar; the fallback is proven in production rather than assumed | Two implementations of every capability, permanently | — |

## Consequences
**Positive:** the degradation ladder is real rather than designed — every fallback has been the primary
path for a season; the promotion bar is a comparison against something that works; labels arrive from
ordinary work.
**Negative:** two implementations per capability, for good; the rule's period sets expectations that a
model then has to exceed, and sometimes it will not, which means some capabilities stay rules forever —
an outcome this ADR treats as success and a reader may treat as failure.

| Risk | Mitigation |
| --- | --- |
| The rule is good enough and the model never justifies itself | That is a result, not a problem: the capability stays deterministic, the phase gate records why, and the budget goes elsewhere |
| The rule is written to be easy to beat | The rule's owner is the domain expert who uses it, not the engineer promoting the model; its error is published from the day it ships |
| Two implementations drift apart | They share the capability's interface, its golden set and its monitoring; the monthly comparison in §7 is what detects divergence |

## How we will know this was right
Every production capability has a fallback that has actually run in production; every promotion cites
its rule's score on the same window; and at least one capability is consciously left as a rule because
the model did not earn promotion.
