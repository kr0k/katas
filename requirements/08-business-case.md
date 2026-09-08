# 08 · Business Case & Growth (summary)

What the growth arithmetic concluded, and which of its outputs the architecture depends on. The arithmetic itself — attendance ladder, capacity constraints, cohort model, payback simulation — is a financial model rather than an architectural artifact, so it lives in [appendix · business-case model](../appendix/business-case-model.md), generated from one assumptions block by [`scripts/business_case.py`](../scripts/business_case.py) and checked by lint on every push.

## The four findings

1. **The estate's physical capacity binds before the software does.** A 15,000 daily average means a peak summer Saturday near 29,400 people; parking as assumed holds 15,000 of them and lunch seating 13,636, so both bind in the first ladder year. Gates hold well past the target. → [capacity reality check](../appendix/business-case-model.md#1-capacity-reality-check)
2. **The platform's savings never pay for it.** They cover ≈ 14% of running cost, so payback rests on growth: **years 4–7**, the early end requiring 36% of the year-2-to-year-3 growth to be credited to the platform, which no phase before Phase 3 can deliver. → [does the platform pay back](../appendix/business-case-model.md#4-does-the-platform-pay-back)
3. **Growth comes from three levers, and the platform owns the mechanics of two.** Quiet-day pricing (S5), weekday fill by pass holders (S4 nudges) and repeat visits (S4 companion → account → pass). The third — new audiences — is marketing's, and the model credits the platform with none of it. → [the membership flywheel](../appendix/business-case-model.md#3-the-membership-flywheel)
4. **Everything is conditional on the ticketing-vendor evaluation** ([TODOS.md](../TODOS.md), a Phase 0 prerequisite). Without a capacity API and an upgrade credit, the second lever becomes a desk process and the payback window moves right.

## What the architecture takes from it

The model touches the architecture at three points, and only these three:

| Input | Where it lands |
| --- | --- |
| Peak day ≈ 29,400 visitor-days, peak hour ≈ 5,880 arrivals, ≈ 2,940 gate scans | NFR-SCL-1, and the [edge capacity check](../hld/core/edge-and-connectivity.md#capacity-check-at-15000-visitorsday-by-traffic-class) that sizes the broker, buffer and ingestion |
| Platform cost ceiling: ≤ €1.00 per visitor at 5,000/day, ≤ €0.50 at 15,000/day; AI ≤ 2% of revenue | NFR-COST-1, NFR-COST-2, and the [cost model](04-non-functional-requirements.md#cost-model-tco-50) |
| The growth rates and what measures each one | The events they are computed from (`GateEntered.persons_admitted`, `ItineraryCreated`, `NudgeSent`, `PassRenewed`, `PurchaseRecorded`) and the business guardrails in the [thresholds table](../hld/ai-platform/README.md#thresholds-and-cadences-source-of-truth) |

Nothing else in the model changes a component, a boundary or a decision. Every figure is an assumption until season 1; the model is re-issued once with measured values at Phase 2 entry ([owner and trigger](../appendix/business-case-model.md#6-owner-trigger-and-re-issue)).
