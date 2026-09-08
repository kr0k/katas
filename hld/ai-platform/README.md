# AI Platform

Shared infrastructure that every AI scenario uses. It exists to answer two of the judges' questions structurally rather than per-scenario: **how do we cope with a fast-changing AI landscape**, and **how do we know the AI works**.

It has two halves that are easy to confuse. **Model governance** (registry, evaluation, monitoring) covers *every* model we run — rented, own, cloud, edge or batch. The **inference gateway** is a runtime proxy for *hosted* models only, and we adopt it rather than build it. → [ADR-0005](../../adrs/ADR-0005-model-gateway-and-provider-independence.md)

## Components

```mermaid
flowchart LR
    subgraph Services["Business monolith modules & AI consumers"]
        Ops["Park Operations"]
        Welfare["Animal Welfare"]
        Guest["Guest Engagement"]
        Cons["🤖 AI consumers / batch workers"]
    end

    subgraph Gov["Model governance — every model"]
        Reg[("Model & prompt registry<br/>versions · eval scores · owners")]
        Eval["Evaluation service<br/>golden sets · CI gate · shadow runs"]
        Mon["AI monitoring<br/>drift · confidence · cost · overrides"]
    end

    subgraph Runtime["Inference runtime"]
        Res["Capability resolver (built, thin)<br/>capability → bundle → route"]
        GW["Inference gateway (adopted OSS)<br/>routing · budgets · fallback · tracing · PII scrub"]
        Own["Own model endpoints<br/>(managed hosting, cloud)"]
        Edge["Edge inference nodes 🏰"]
        Batch["GPU / batch jobs"]
    end

    subgraph Providers["Hosted models"]
        P1(["LLM provider A"])
        P2(["LLM provider B (fallback)"])
        OW(["Open-weight model<br/>(managed hosting, downgrade path)"])
    end

    HITL["Review queue service 👤<br/>confidence bands · SLAs · audit"]
    Train["Training pipelines<br/>(vision & tabular models)"]

    Ops & Welfare & Guest --> Res
    Cons --> Res
    Res --> GW
    GW --> P1 & P2 & OW
    Res --> Own
    Reg --> Res
    Reg -. "deploy" .-> Edge
    Reg -. "deploy" .-> Own
    Reg -. "deploy" .-> Batch
    GW -.-> Mon
    Own -.-> Mon
    Edge -.-> Mon
    Batch -.-> Mon
    Eval --> Reg
    Train --> Reg
    Mon -.-> Eval
    Welfare --> HITL
    HITL -.-> Train
```

## Inference runtime

### Inference gateway (adopted) and capability resolver (built)
Business services request a **capability** (`detect-feeding-anomaly`, `plan-visit`, `forecast-zone-footfall`), never a model. The **capability resolver** — the only runtime code we write here — looks the capability up in the registry and sends the request down its runtime path. For hosted models that path is the **inference gateway**, an open-source LLM gateway (LiteLLM, Portkey, Kong AI Gateway class) configured from Git. It applies:

- **Routing policy:** tiered (small/cheap model first; escalate to a larger one on low confidence or explicit need), or fixed for capabilities where determinism matters.
- **Budgets:** per-capability monthly budget; alerts at 70/90%; at 100% switch to the downgrade path rather than fail.
- **Fallback chain:** provider A → provider B → open-weight model on **managed hosting** (not self-hosted — R9) → non-AI fallback (returned as a typed "no AI available" response the service knows how to handle: a rule, a template, or a documented human procedure).
- **Tracing:** every call emits `capability`, `model_version`, `latency`, `tokens`, `cost`, `confidence` to OpenTelemetry.
- **Guardrails:** input/output schema validation, PII scrubbing on the way out to external providers, output filters for the companion.

We do not build any of that. Routes, budgets and fallback chains are declarative configuration, portable between gateways of this class.

→ [ADR-0005](../../adrs/ADR-0005-model-gateway-and-provider-independence.md)

### Capability → runtime path

| Capability (examples) | Model kind | Runtime path | Governed by |
| --- | --- | --- | --- |
| `answer-question`, `plan-visit`, `summarise-daily-welfare-report`, `summarise-estate-day`, nudge wording | Rented generative; open-weight on managed hosting as downgrade | Capability resolver → **inference gateway** → provider or managed endpoint | Registry · eval gate · monitoring |
| `detect-feeding-anomaly`, `score-enclosure-activity` | Own tabular / time-series, cloud | AI consumer on the backbone → **own model endpoint** (managed hosting); no gateway | same |
| `extract-enclosure-features`, `mask-visitors`, `count-piranha`, `flag-aggressive-behaviour` (tier-1 advisory) | Own vision, edge | **Edge inference node**; artifact pulled from the registry over the downlink ([ADR-0006](../../adrs/ADR-0006-edge-vs-cloud-inference.md)); node reports version and confidence stats | same |
| `forecast-zone-footfall`, `estimate-price-elasticity` | Own tabular, batch | **Scheduled batch job** in the GPU/batch workers; results published as events | same |

The gateway is on the path of the first row only. The other three rows never touch a hosted provider and never depend on the gateway — but they cannot be promoted or served without passing through governance.

## What the generative capabilities cost

We costed LoRaWAN airtime to 0.19 s and IoT ingestion to the dollar. The generative line deserves the same treatment, because it is the only cost in the estate that **grows with success** — five-fold between today and the target run rate — and the only one where a design choice can move it by a factor of two.

Token counts per call and the two tier prices are assumptions (list-price bands, ±50%, replaced by quotes); everything else follows from the attendance ladder, the party size (A9) and the companion adoption rate the cohort model already uses. Generated by [`scripts/business_case.py`](../../scripts/business_case.py) and checked by lint, so it cannot drift from the business case.

<!-- business-case:llm-cost -->
| Request class (capability) | Calls / yr at 15,000/day | Tokens per call: in / of which cached / out | Tier | € / yr |
|---|---|---|---|---|
| `answer-question` — FAQ, small tier | 1,967,143 | 2,000 / 400 / 150 | small | €661 |
| `answer-question` — escalated on low confidence | 347,143 | 2,000 / 400 / 150 | large | €2,500 |
| `plan-visit` — the day plan | 771,429 | 6,000 / 4,500 / 800 | large | €13,800 |
| `plan-visit` — re-plan on a closure or a queue spike | 1,542,857 | 4,000 / 3,500 / 300 | large | €10,900 |
| Nudge wording (Phase 3) | 3,471,429 | 1,500 / 0 / 200 | small | €1,200 |
| LLM-as-judge on a sample | 92,571 | 3,000 / 0 / 100 | large | €972 |
| `summarise-*` report drafters | 900 | 4,000 / 0 / 500 | large | €18 |
| Shadow runs before promotion | — | — | as production | €4,300 |
| **Total, planned spend at the target run rate** |  |  |  | **€34,300 / yr** |
| *Counterfactual: no FAQ cache, no prompt caching* | *6,942,857* | *same tokens, none cached* | *same* | *€67,100 / yr* |
<!-- /business-case:llm-cost -->

**What the arithmetic says.**

- **Planned spend ≈ €34,300 a year at 15,000 visitors/day** — ≈ €0.04 per companion household visit, against ≈ €21 of gross revenue per visitor-day. It is ≈ 0.04% of revenue at that run rate, against the 2% ceiling in NFR-COST-1. The AI is not the expensive part; the [ticketing fees and the team](../../requirements/04-non-functional-requirements.md#cost-model-tco-50) are.
- **It fits the €50k OPEX line, and now we can say why.** The line covers this token spend plus the open-weight fallback endpoint (a managed endpoint has a standing cost even when the fallback is idle) and the headroom the ±50% band demands. The line is a budget, not a forecast: NFR-COST-1 turns it into per-capability monthly budgets, alerts at 70/90% and an automatic downgrade at 100%.
- **The two caches are budget decisions, not optimisations.** Without the daily FAQ cache and without prompt caching of the session prefix, the same traffic costs ≈ €67,100 — over the line rather than inside it. This is the same shape as the [ingestion counterfactual](../core/edge-and-connectivity.md#capacity-check-at-15000-visitorsday-by-traffic-class): the cheap design and the expensive one differ by a factor, not by a rounding.
- **Where it actually goes:** day planning and re-planning are ≈ 90% of the bill, because a plan is a large-tier call with a long input and a long output, and a family triggers three of them. FAQ answers are the cheap majority of calls. That is why tiered routing exists, and why re-planning touches only the affected stops.
- **The bad Saturday.** A peak day (≈ 29,400 visitor-days) costs ≈ €182 of generative spend against ≈ €93 on an average day — **2.0×**, not 10×, because the load is bounded by households present, not by concurrency. Thirty such days would be ≈ €5,400 against a monthly budget of ≈ €2,900 on the yearly average, which is exactly why the budget is monthly **and** seasonal rather than a flat twelfth.
- **If more answers escalate than we assume.** The model routes 15% of FAQ answers to the large tier on low confidence. A Saturday with more first-time families pushes that up; at **40%** escalation the yearly bill rises by ≈ €4,600 — inside the headroom, and visible in the gateway's per-capability cost telemetry before it is visible in an invoice.

## Model governance

Applies to every row of the table above, wherever the model runs.

### Model & prompt registry
Versioned bundles: model reference (external model ID, or our own artifact), prompt template, parameters, eval score, owner, status (`candidate` / `shadow` / `production` / `retired`). Declared in Git and reconciled (GitOps), so a model change is a reviewed pull request. Edge nodes and batch jobs read their *desired version* from the registry; the resolver reads the production bundle for hosted capabilities.

### Evaluation service
- **Golden datasets** per capability, maintained by the domain owner (vet for welfare, ops manager for forecasting, guest team for companion).
- **CI gate:** a candidate bundle must meet the capability's thresholds in the [thresholds & cadences table](#thresholds-and-cadences-source-of-truth) or it cannot be promoted; **no regression** against the current production bundle.
- **Invariant suites** for the deterministic components that sit on AI paths (pricing policy engine, staffing optimiser): property-based tests over generated inputs, violations = 0 gate, same invariants checked in production.
- **Shadow mode:** candidate runs alongside production on live traffic, outputs compared, no user impact.
- **LLM-as-judge** with human calibration sample for open-ended outputs.

→ [ADR-0008](../../adrs/ADR-0008-ai-evaluation-and-production-monitoring.md)

### AI monitoring
- Input drift (feature distributions, image statistics), output drift (confidence histograms, class balance), and **business-metric guardrails** (vet override rate, forecast error, companion thumbs-down rate, pricing floor hits) with the thresholds in the table below.
- Automatic rollback to the previous production bundle when a guardrail trips — for hosted bundles via the gateway route, for edge and batch models via the registry's desired version.

### Review queue (human in the loop)
Confidence bands per capability decide auto-act / human review / discard-and-learn. Reviewer decisions are captured with reason codes and become training data.

→ [ADR-0007](../../adrs/ADR-0007-human-in-the-loop-confidence-bands.md)

### Training pipelines
For models we own (enclosure vision, piranha counting, forecasting, pricing): reproducible pipelines from the data platform, producing artifacts registered with lineage. Edge models are exported to a portable format, signed, and pulled by edge nodes through the downlink described in [Edge & connectivity](../core/edge-and-connectivity.md#downlink-cloud--estate).

## Thresholds and cadences (source of truth)

Every number that gates a promotion, trips a guardrail or sets a human cadence lives here. Scenario READMEs, ADR-0008 and the OKRs refer to this table; if two numbers disagree, this one wins and the other is a bug.

### How the gated metrics are defined

A threshold nobody can compute is not a gate. Three of the numbers below are ambiguous unless we say which instrument produces them.

- **`calibration error ≤ 0.05`** is the **expected calibration error (ECE)** on the capability's golden set over **10 equal-mass bins** of the model's confidence: ECE = Σ (nᵦ/N) · |accuracyᵦ − mean confidenceᵦ|. Equal-mass, not equal-width, because confidence distributions pile up at the ends and equal-width bins would leave the interesting bins nearly empty. The CI job also emits a **reliability diagram** and the per-bin counts as build artifacts, so a passing aggregate with two bad bins is visible in review rather than averaged away.
- **The bands are gated separately from the aggregate.** ADR-0007's three bands are what a vet actually acts on, so each band is checked on its own: |accuracy − mean confidence| ≤ 0.05 **within** the medium band, and the high band's accuracy must be ≥ its lower confidence bound. An aggregate ECE of 0.03 with a medium band that is 15 points optimistic passes the average and fails the vet; this is the check that catches it.
- **Confidence is a calibrated quantity, not a raw softmax score.** Post-hoc calibration (temperature scaling, or isotonic regression where enough labels exist) is fitted on a **held-out split that is not the golden set** and shipped **inside the versioned bundle** — so a model swap re-fits it and the gate re-measures it. An uncalibrated model can pass recall and precision and still make the bands meaningless, which is exactly the failure ADR-0007 is exposed to.
- **`factuality ≥ 0.95`** is the share of factual claims in a sampled answer that map to a cited knowledge-base record or live-data call, judged by the LLM-as-judge and calibrated weekly against the guest team's 50 human-reviewed sessions; judge-vs-human disagreement above 10% invalidates the measurement before it invalidates the model (ADR-0008 §5).
- **`MAPE`** is rolling-origin: the model is refitted at each origin and scored on the next day only, never on data available after the origin.

Production **re-measures the same metrics on the same definitions** from sampled human-labelled data (ADR-0008 §4); a gate and its monitor that disagree on the instrument are two different numbers wearing one name.

| Capability | Promotion gate (pre-release) | Production guardrail → action | Human cadence | Owner |
| --- | --- | --- | --- | --- |
| **S1 feeding anomaly** — `detect-feeding-anomaly` (Phase 1) | Recall ≥ 0.90 on "missed meal" against the feed-scale golden set; precision ≥ 0.60; calibration error ≤ 0.05; 2-week shadow | Vet override rate > 40% (12 mo) / > 25% (36 mo) → alert owner, auto-tighten band; real-world precision/recall from treatments computed monthly | Review-queue SLA 4 h → 1 h. Weekly: 20 low-confidence discards + 10 random *unflagged* hours reviewed by a keeper | Vet |
| **S1 activity / posture / social anomalies** — `score-enclosure-activity` (Phase 2) | Shadow-only for 4 weeks; then recall ≥ 0.90 on "lethargy", precision ≥ 0.60, calibration ≤ 0.05 on the golden set accumulated during Phases 1–2 (≥ 200 clips per class) | As above; **treatments without a prior flag** ≤ 30% by Phase 3 | As above | Vet |
| **S1 visitor masking** — `mask-visitors` | Unmasked person regions = 0 on a 500-frame staged golden set (staff volunteers in frame); over-masking ≤ 10% of animal area | Unmasked frames stored = 0 — any occurrence is a rollback and an incident | Monthly review of 200 sampled stored clips | AI platform |
| **S1 tier-1 advisory** — `flag-aggressive-behaviour` | Recall ≥ 0.80 on staged and archival aggression clips; delivered as advisory only (FR-3.7) | Advisory precision from keeper feedback < 0.30 → retune bands | Weekly review of the week's advisories by the head keeper | Head keeper |
| **S2 piranha count** — `count-piranha` | Detector precision/recall ≥ 0.95 on 50 multi-view frame sets; bias correction seeded from the same set | Census error > 10% (12 mo) / > 5% (36 mo) → retrain; ledger-adjusted drift outside the CI for 7 days → inspection | Census ≥ 2 per year at planned maintenance; visual audit monthly (sanity check only) | Keeper + vet |
| **S3 footfall forecast** — `forecast-zone-footfall` | Rolling-origin next-day MAPE ≤ 25% (12 mo) → ≤ 15% (36 mo) **and** beats the "same weekday last week × seasonal factor" heuristic; one forecasting cycle in shadow | 3-day rolling MAPE > target + 5 points → alert; input drift (new ride, closure) → retrain flag | Weekly retrain; daily forecast-vs-actual per zone | Ops manager |
| **S3 staffing optimiser** (deterministic) | Hard-constraint violations = 0 in property-based tests | Violations = 0 on every proposal, checked by an independent validator before it is shown | Ops manager approves every plan; edits logged as labels | Ops manager |
| **S4 companion** — `answer-question`, `plan-visit` | Factuality ≥ 0.95; constraint violations 0; safety refusals 100%; **indirect prompt-injection resistance 100%** on a 100-case set; **ungrounded-block false positives ≤ 5%** on 300 answerable questions; NFR-PRF-1 latency budgets met in a 500-session load test; offline itinerary end-to-end test passes; **per-language safety-field fidelity 100% and unapproved-language handoff 100%** (NFR-LNG-1); **read-aloud meaning preserved on 20 cases** (NFR-ACC-1); 2-week shadow | Thumbs-down > 5%; ungrounded-block rate doubling week-on-week; judge/human disagreement > 10%; any safety-critical wrong statement → rollback + alert | Weekly: 50 sessions reviewed by the guest team; knowledge base curated daily by ops | Guest team |
| **S5 pricing** — `estimate-price-elasticity` + policy engine | Backtest: contribution on held-out weeks ≥ fixed pricing; invariant violations = 0 in property-based tests, incl. the contribution constraint with the A15 parameters | Conversion drop > 10% vs. control → revert to fixed price; **weekly: contribution per visitor-day on discounted blocks < 0% blocks − 10% → pause that discount level**; complaint rate > 0.5% of buyers → review; floor/ceiling hit frequency monitored; invariant violations = 0 | Management approves every out-of-guardrail price; monthly readout vs. fixed-price counterfactual; year-1 experiment readout after one season | Management |
| **LLM drafters** — `summarise-daily-welfare-report`, `summarise-estate-day` | Inserted figures verbatim = 100% and invented numbers = 0 on the "numeric fidelity" set (200 snapshots); format and tone evals; a human approves the wording before anything is sent (for the estate day: the ops manager between 20:30 and 21:00, numbers inserted verbatim at 21:00) | Post-generation verbatim check on the final numbers fails → template-only sent + alert, bundle is a rollback candidate; approval rate and edits per report tracked weekly | Weekly sample of 10 reports by the owner (vet for the welfare briefing, ops manager for the estate day) | Vet · Ops manager |
| **Business guardrails** (alert only — no model is rolled back on a business number; every figure comes from a KPI read model that is itself tested with fixture event streams, [hld/core → Verification](../core/README.md#verification-purchases-cap-and-the-daily-report)) | — | Season-pass renewal: cohort-over-cohort decline > 10 points before month 36 (earliest signal month 24), below 60% after → alert Guest team and management. On-site spend per visitor-day — all guests, `PurchaseRecorded` ÷ Σ `persons_admitted` — 10% below the modelled €6.00 on-site spend per visitor-day, seasonally adjusted (A6) → alert. Pass share of admissions (credential type on `GateEntered`) more than 5 points below the ladder for a quarter → alert management. Contribution per pass visit is **derived** from those two and the A15 parameters by `business_case.py` and labelled *model* — never a raw metric, because purchases carry no subject without consent ([ADR-0009](../../adrs/ADR-0009-visitor-privacy-anonymous-counting.md) §7). Cohort rates (adoption, opt-in, nudge reach, return, pass conversion, pass renewal, account retention — [08 §3](../../requirements/08-business-case.md#3-the-membership-flywheel)) more than 20% below the table for 2 months → alert Guest team | Monthly readout with the OKRs; yearly re-issue of requirements/08 with measured values | Guest team · Management |
| **Platform** | Every production capability has a passing eval and a named non-AI fallback (OKR 5.3) | Budget alerts at 70% / 90%, downgrade at 100% (NFR-COST-1); model swap ≤ 1 day (OKR 5.2) | Monthly shadow run of the secondary provider and the open-weight bundle; quarterly game days GD-9/GD-10 | AI platform |

## Humans in the loop: who does what

The AI does not run itself, and the estate has no spare team to run it. This table is the answer to "who reviews all this?" — hours per week, by role and phase, all of them roles the estate already has. **Rule: labels are a side-effect of the job.** Every routine decision — confirm/dismiss, roster edit, price approval, thumbs-down triage — is captured as a label with a reason code. The only standalone labelling work is the initial golden set per capability, and it is bounded.

| Role | AI-related task | Phase 1 | Phase 2 | Phase 3 | Where the label comes from |
| --- | --- | --- | --- | --- | --- |
| Veterinarian (A3) | Review queue: confirm / dismiss with reason | 2 h/wk | 5 h/wk | 8 h/wk | The decision is the label |
| Veterinarian | Initial golden-set labelling (per new capability, bounded) | 4 h/wk for 8 weeks | 4 h/wk for 8 weeks | 2 h/wk for 8 weeks | Explicit, one-off |
| Head keeper | Weekly audits (discards, unflagged hours), tier-1 advisory review, escalations | 1 h/wk | 2 h/wk | 2 h/wk | Audit outcome |
| Keepers | Feeding exceptions; census at maintenance (2 × 4 h/yr); monthly visual audit (30 min) | 1 h/wk | 1 h/wk | 2 h/wk | Ledger entries |
| Ops manager | Approve/edit rosters; own forecast thresholds; approve the Estate daily report's wording between 20:30 and 21:00 (Phases 2–3, +1 h/wk) | 1 h/wk (heuristics) | 3 h/wk | 3 h/wk | Roster edits; report approve / skip |
| Guest team | Review 50 sessions; curate knowledge base; triage thumbs-down | 3 + 5 h/wk | 4 + 5 h/wk | 4 + 5 h/wk | Reviews, KB fixes |
| Management | Out-of-guardrail price approvals; experiment readout | — | — | 1 h/wk | Approval reason codes |
| Platform engineers (of the 5) | Model promotions, game days, on-call; re-issue of [requirements/08](../../requirements/08-business-case.md) with the ops manager (1 day/yr, from Phase 2 entry) | 1 day/quarter + rota | same + 1 day/yr | same + 1 day/yr | — |
| **Total estate-staff hours on AI** | | **≈ 17 h/wk** | **≈ 24 h/wk** | **≈ 25 h/wk** | |

Workload per role is a tracked metric; a phase gate slips before a role is overloaded (R13, NFR-OPS-1).

## The three kinds of AI and how the platform treats them

| Kind | Examples | Determinism | Pre-release check | Production check |
| --- | --- | --- | --- | --- |
| Classical ML | forecasting, pricing | Deterministic given inputs | Backtests, MAPE/RMSE thresholds; invariant suites for the policy around them | Error vs. actuals, drift, invariant violations = 0 |
| Computer vision | welfare anomalies, piranha count | Probabilistic | Precision/recall on golden footage | Confidence bands, override rate, audits per the thresholds table |
| Generative | companion, report summaries | Non-deterministic | Factuality, safety, format evals; adversarial and indirect-injection sets | Sampled judge + human, thumbs-down, escalation rate |

## Answering the judges directly

| Question | Answer |
| --- | --- |
| Best model today isn't best tomorrow | Change the registry entry, pass the eval gate, promote. No service code changes. Target ≤ 1 day (OKR 5.2). |
| Provider changes prices | Budgets + tiered routing + downgrade path already wired in the gateway config; cost per capability visible daily. |
| Provider shuts down | Named fallback provider passing the same evals; open-weight bundle on managed hosting exercised monthly; prompts/evals/traces are ours; safety paths never depend on a generative provider. |
| The gateway itself is a dependency | It is adopted OSS with declarative config; the resolver isolates services; only hosted generative capabilities depend on it — vision, counting and forecasting never do. |
| How do we know it works? | Nothing is promoted without passing its golden set; shadow before live; guardrails with auto-rollback after — all numbers in one table. |
| How do we know it *stopped* working? | Drift monitors + business-metric guardrails + human override rate, alerting the capability owner. |
| Who does all the reviewing? | Existing estate roles, ≈ 17–25 h/week in total, with labels captured as a side-effect of their normal decisions. |
