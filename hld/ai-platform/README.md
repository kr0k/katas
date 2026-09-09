# AI Platform

Shared infrastructure every AI scenario uses. It answers two questions once, rather than per scenario: how we cope with a fast-changing AI landscape, and how we know the AI works.

Three parts, and the third is thin on purpose: **agents** are a model plus typed tools that *propose* into approvals that already exist → [agents.md](agents.md), [ADR-0013](../../adrs/ADR-0013-role-agents-on-typed-tools.md). They add no deployable and about 1% of generative spend.

Two halves, easy to confuse. **Model governance** (registry, evaluation, monitoring) covers *every* model we run — rented, own, cloud, edge or batch. The **inference gateway** is a runtime proxy for *hosted* models only, and we adopt it rather than build it. → [ADR-0005](../../adrs/ADR-0005-model-gateway-and-provider-independence.md)

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
    Agents["🤖 Agents<br/>ops-copilot · companion · ask-the-estate<br/>typed tools · step & token budget"]

    Ops & Welfare & Guest --> Res
    Cons --> Res
    Agents --> Res
    Agents -. "reads via tools" .-> Ops & Welfare & Guest
    Agents -. "proposals" .-> HITL
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
- **Budgets:** per-capability monthly budget; alerts at 70/90%; at 100% switch to the downgrade path rather than fail. The budget is the *last* line: an anonymous caller is stopped by the BFF's inference quota first (NFR-SEC-3), so abuse cannot degrade the service for paying visitors.
- **Fallback chain:** provider A → provider B → open-weight model on **managed hosting** (not self-hosted — R9) → non-AI fallback (returned as a typed "no AI available" response the service knows how to handle: a rule, a template, or a documented human procedure).
- **Tracing:** every call emits `capability`, `model_version`, `latency`, `tokens`, `cost`, `confidence` to OpenTelemetry.
- **Guardrails:** input/output schema validation, PII scrubbing on the way out to external providers, output filters for the companion.

We do not build any of that. Routes, budgets and fallback chains are declarative configuration, portable between gateways of this class.

→ [ADR-0005](../../adrs/ADR-0005-model-gateway-and-provider-independence.md)

### What a capability declares

The capability is the unit every consumer calls, so its registry entry is the contract — and one field in it is what keeps the delivery phases honest.

| Field | Why it is there |
| --- | --- |
| `implementation: rule \| model` | **A capability served by a deterministic rule is still a capability.** S1 begins as feed-scale thresholds, S3 as "the same weekday last week, adjusted for season" — behind the same names their consumers already call, so the switch to a model changes nothing outside the registry |
| `promotion trigger` | What must be true before a model replaces the rule: the labelled volume required, the threshold it must beat from the [thresholds table](#thresholds-and-cadences-source-of-truth), and the shadow duration. A capability without one drifts either into rules forever or into a model promoted on enthusiasm |
| `must beat` | The named baseline, which is the rule itself — not a paper metric. S3's forecast is promoted only if it beats the heuristic it replaces |
| `fallback` | The rule does not retire when the model arrives; it becomes the last rung of the fallback chain ([ADR-0005](../../adrs/ADR-0005-model-gateway-and-provider-independence.md) §4). Promotion changes which implementation is primary, never whether a deterministic path exists |
| `owner` | The domain lead who owns the golden set and the bands (vet, ops manager, guest team) |

This is why the [delivery roadmap](../../README.md#delivery-roadmap-what-we-build-when-and-what-we-buy) is an architectural mechanism rather than a project plan: a phase gate is a promotion trigger that has not fired yet, and the rule that is live meanwhile is the same artefact the fallback chain will keep afterwards.

### Capability → runtime path

| Capability (examples) | Model kind | Runtime path | Governed by |
| --- | --- | --- | --- |
| `answer-question`, `plan-visit`, `summarise-daily-welfare-report`, `summarise-estate-day`, nudge wording | Rented generative; open-weight on managed hosting as downgrade | Capability resolver → **inference gateway** → provider or managed endpoint | Registry · eval gate · monitoring |
| `detect-feeding-anomaly`, `score-enclosure-activity` | Own tabular / time-series, cloud | AI consumer on the backbone → **own model endpoint** (managed hosting); no gateway | same |
| `extract-enclosure-features`, `mask-visitors`, `count-piranha`, `flag-aggressive-behaviour` (tier-1 advisory) | Own vision, edge | **Edge inference node**; artifact pulled from the registry over the downlink ([ADR-0006](../../adrs/ADR-0006-edge-vs-cloud-inference.md)); node reports version and confidence stats | same |
| `forecast-zone-footfall`, `estimate-price-elasticity` | Own tabular, batch | **Scheduled batch job** in the GPU/batch workers; results published as events | same |
| `agent:ops-copilot`, `agent:companion` tool-selection, `ask-the-estate` | Rented generative; tool calls resolve to reads and commands, not to models | Capability resolver → **inference gateway**, with the agent's tool whitelist, step and token budget applied per task ([agents](agents.md)) | Registry · eval gate · monitoring · **plus** the agent's own version, rolled back separately from the model |

The gateway is on the path of the first row only. The other three rows never touch a hosted provider and never depend on the gateway — but they cannot be promoted or served without passing through governance.

## What the generative capabilities cost

Generative spend is the one platform cost that grows with success — five-fold between today and the target run rate — so it is budgeted per capability rather than in total.

| Figure | Consequence for the design |
| --- | --- |
| ≈ €34,600 a year at 15,000 visitors/day — ≈ €0.04 per companion household visit, ≈ €0.01 per visitor-day | Inside the €50k line in the [cost model](../../requirements/04-non-functional-requirements.md#cost-model-tco-50) with a 44% overrun absorbed, at ≈ 0.04% of revenue against NFR-COST-1's 2% ceiling. Squeezing AI spend buys nothing; a worst-case price move is caught by the per-capability budget rather than by the line |
| Planning and re-planning ≈ 90% of the bill | Routing is tiered, and a re-plan touches only the affected stops |
| ≈ €68,000 without the FAQ cache and prompt caching | The caches are a design condition, not an optimisation — the same shape as the [ingestion counterfactual](../core/edge-and-connectivity.md#capacity-check-at-15000-visitorsday-by-traffic-class) |
| Peak day 2.0× an average one | Load is bounded by households present, not by concurrency, so the budget is seasonal rather than a flat twelfth |

Per-request-class arithmetic, tier prices, the counterfactual and the escalation sensitivity: [appendix · generative-AI cost model](../../appendix/generative-cost.md), generated by [`scripts/business_case.py`](../../scripts/business_case.py) and checked by lint.

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
- **Paging policy: a model failure is never a page.** A capability that trips a guardrail falls back to its rule, template or documented human procedure and opens a ticket for its owner in working hours. Only the deterministic safety tier wakes anybody (NFR-AVL-3). This is deliberate — five engineers can be on call for a park, but not for a model.

### Review queue (human in the loop)
Confidence bands per capability decide auto-act / human review / discard-and-learn. Reviewer decisions are captured with reason codes and become training data.

**The queue degrades separately from the model, and the two need different answers.** A rising override rate says the model is getting things wrong; **overdue confirmations** say the people are saturated, which no amount of retraining fixes. Both are monitored: queue depth and the age of the oldest item, per capability, against the review capacity in the [human roles table](#humans-in-the-loop-who-does-what).

Over capacity for three consecutive days, the platform sheds load rather than letting the SLA quietly rot: the medium band's lower bound is raised so that fewer, higher-confidence items reach a human, each shed item is recorded with the confidence that shed it, and a weekly sample of shed items is reviewed to measure what the shedding cost in recall. If that sample turns up a real case that was shed, the shedding stops and the **phase gate slips instead** — at that point the load was the problem, not the threshold (R13, [SP-2](../architecture-evaluation.md#sensitivity-points)).

→ [ADR-0007](../../adrs/ADR-0007-human-in-the-loop-confidence-bands.md)

### Training pipelines
For models we own (enclosure vision, piranha counting, forecasting, pricing): reproducible pipelines from the data platform, producing artifacts registered with lineage. Edge models are exported to a portable format, signed, and pulled by edge nodes through the downlink described in [Edge & connectivity](../core/edge-and-connectivity.md#downlink-cloud--estate).

## Thresholds and cadences (source of truth)

Every number that gates a promotion, trips a guardrail or sets a human cadence lives here. Scenario READMEs, ADR-0008 and the OKRs refer to it; if two numbers disagree, this table wins.

### How the gated metrics are defined

Each gated number names the instrument that produces it, so a gate and its production monitor measure the same thing.

| Metric | Definition |
| --- | --- |
| `calibration error ≤ 0.05` | **Expected calibration error (ECE)** on the capability's golden set over **10 equal-mass bins** of model confidence: ECE = Σ (nᵦ/N) · \|accuracyᵦ − mean confidenceᵦ\|. Equal-mass rather than equal-width, because confidence piles up at the ends and equal-width bins leave the interesting ones nearly empty. The CI job emits a reliability diagram and per-bin counts as build artifacts |
| Per-band calibration | Each of ADR-0007's three bands is checked on its own: \|accuracy − mean confidence\| ≤ 0.05 **within** the medium band, and the high band's accuracy ≥ its lower confidence bound. An aggregate ECE of 0.03 can hide a medium band 15 points optimistic, which is what the vet acts on. **Max deviation of any single bin ≤ 0.10** as well, so one badly-behaved bin cannot be averaged away |
| What happens when calibration fails | The bundle is blocked, and post-hoc calibration is re-fitted and re-measured. Until it passes, the capability is not simply switched off: **its bands shift conservatively** — the medium band's lower bound drops so that more goes to a human and less is auto-acted, at a known cost in review hours. A model whose confidence cannot be trusted is still useful; a model whose confidence is trusted wrongly is not |
| Confidence itself | A calibrated quantity, not a raw model score. Post-hoc calibration (temperature scaling, or isotonic where labels allow) is fitted on a held-out split that is **not** the golden set and shipped inside the versioned bundle, so a model swap re-fits it and the gate re-measures it |
| `factuality ≥ 0.95` | Share of factual claims in a sampled answer that map to a cited knowledge-base record or live-data call. Judged by the LLM-as-judge, calibrated weekly against the guest team's 50 human-reviewed sessions; judge-vs-human disagreement above 10% invalidates the measurement (ADR-0008 §5) |
| `MAPE` | Rolling-origin: refitted at each origin, scored on the next day only, never on data available after the origin |

Production re-measures these from sampled human-labelled data on the same definitions (ADR-0008 §4).

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
| **`agent:ops-copilot`** (Phase 2) | Task success ≥ 0.70 on a 100-task labelled set; tool-error rate ≤ 0.05; 0 instructions followed from retrieved content on the 100-case injection set; 0 duplicate effects under forced retry; step budget respected in every task | Task success below target for two weekly cycles → **agent** rollback (prompt, whitelist, budget), separate from the model bundle; tool-error rate rising → integration triage before any retraining; `open_review` items rejected by the vet > 50% → the tool is rate-limited harder or withdrawn | Weekly: 20 tasks labelled by the ops manager and the guest team | AI platform |
| **`agent:companion`** (Phase 2) | The S4 companion gates, plus: tool-selection accuracy ≥ 0.95 on a labelled set of live-data questions; 0 effectful calls without a typed argument set | As S4, plus duplicate `hold_slot` effects = 0 under forced retry | Within the S4 weekly session review | Guest team |
| **`ask-the-estate`** (Phase 2) | Every answer resolves to a named metric or refuses: fabricated numbers = 0 on a 100-question set including 20 unanswerable ones; the metric definition and window shown with every answer | Any answer without a metric definition → capability off until fixed | Monthly: 10 answers checked against the read model by the ops manager | Ops manager |
| **Review-queue health** — the people, not the model | — | Overdue confirmations > 10% of a week's items, **or** queue depth above the phase's review capacity for 3 consecutive days → alert the capability owner and shed load as described in [review queue](#review-queue-human-in-the-loop); a shed-item sample containing a real case → stop shedding, slip the phase gate | Weekly, read together with the override rate | Vet · Ops manager |
| **Business guardrails** (alert only — no model is rolled back on a business number; every figure comes from a KPI read model that is itself tested with fixture event streams, [hld/core → Verification](../../appendix/data-health-and-verification.md#verification-purchases-cap-and-the-daily-report)) | — | Season-pass renewal: cohort-over-cohort decline > 10 points before month 36 (earliest signal month 24), below 60% after → alert Guest team and management. On-site spend per visitor-day — all guests, `PurchaseRecorded` ÷ Σ `persons_admitted` — 10% below the modelled €6.00 on-site spend per visitor-day, seasonally adjusted (A6) → alert. Pass share of admissions (credential type on `GateEntered`) more than 5 points below the ladder for a quarter → alert management. Contribution per pass visit is **derived** from those two and the A15 parameters by `business_case.py` and labelled *model* — never a raw metric, because purchases carry no subject without consent ([ADR-0009](../../adrs/ADR-0009-visitor-privacy-anonymous-counting.md) §7). Cohort rates (adoption, opt-in, nudge reach, return, pass conversion, pass renewal, account retention — [08 §3](../../appendix/business-case-model.md#3-the-membership-flywheel)) more than 20% below the table for 2 months → alert Guest team | Monthly readout with the OKRs; yearly re-issue of requirements/08 with measured values | Guest team · Management |
| **Platform** | Every production capability has a passing eval and a named non-AI fallback (OKR 5.3) | Budget alerts at 70% / 90%, downgrade at 100% (NFR-COST-1); model swap ≤ 1 day (OKR 5.2) | Monthly shadow run of the secondary provider and the open-weight bundle; quarterly game days GD-9/GD-10 | AI platform |

## Humans in the loop: who does what

Hours per week by role and phase, all of them roles the estate already has. **Labels are a side-effect of the job:** every routine decision — confirm/dismiss, roster edit, price approval, thumbs-down triage — is captured as a label with a reason code. The only standalone labelling work is the initial golden set per capability, and it is bounded.

| Role | AI-related task | Phase 1 | Phase 2 | Phase 3 | Where the label comes from |
| --- | --- | --- | --- | --- | --- |
| Veterinarian (A3) | Review queue: confirm / dismiss with reason | 2 h/wk | 5 h/wk | 8 h/wk | The decision is the label |
| Veterinarian | Initial golden-set labelling (per new capability, bounded) | 4 h/wk for 8 weeks | 4 h/wk for 8 weeks | 2 h/wk for 8 weeks | Explicit, one-off |
| Head keeper | Weekly audits (discards, unflagged hours), tier-1 advisory review, escalations | 1 h/wk | 2 h/wk | 2 h/wk | Audit outcome |
| Keepers | Feeding exceptions; census at maintenance (2 × 4 h/yr); monthly visual audit (30 min) | 1 h/wk | 1 h/wk | 2 h/wk | Ledger entries |
| Ops manager | Approve/edit rosters; own forecast thresholds; approve the Estate daily report's wording between 20:30 and 21:00 (Phases 2–3, +1 h/wk) | 1 h/wk (heuristics) | 3 h/wk | 3 h/wk | Roster edits; report approve / skip |
| Guest team | Review 50 sessions; curate knowledge base; triage thumbs-down | 3 + 5 h/wk | 4 + 5 h/wk | 4 + 5 h/wk | Reviews, KB fixes |
| Ops manager + guest team | **Label 20 agent tasks a week** for task success (ADR-0013) — the only new human cost the agentic layer adds; the copilot's own proposals redistribute review time rather than adding it | — | 1 h/wk | 1 h/wk | The label is the accept / edit / reject |
| Guest team + a contracted translator | **Approve the safety, allergen and price fields per language** (NFR-LNG-1) — a bounded set that changes only when a rule, a price or an animal changes, not a per-answer task | — | 2 h/wk while a language is added, then ≈ 1 h/mo | ≈ 1 h/mo per language | Explicit approval per field and language |
| Management | Out-of-guardrail price approvals; experiment readout | — | — | 1 h/wk | Approval reason codes |
| Platform engineers (of the 5) | Model promotions, game days, on-call; re-issue of [requirements/08](../../requirements/08-business-case.md) with the ops manager (1 day/yr, from Phase 2 entry) | 1 day/quarter + rota | same + 1 day/yr | same + 1 day/yr | — |
| **Total estate-staff hours on AI** | | **≈ 17 h/wk** | **≈ 27 h/wk** | **≈ 26 h/wk** | Phase 2 carries the language-approval spike; it falls away once a language is live |

Workload per role is a tracked metric; a phase gate slips before a role is overloaded (R13, NFR-OPS-1).

## The three kinds of AI and how the platform treats them

| Kind | Examples | Determinism | Pre-release check | Production check |
| --- | --- | --- | --- | --- |
| Classical ML | forecasting, pricing | Deterministic given inputs | Backtests, MAPE/RMSE thresholds; invariant suites for the policy around them | Error vs. actuals, drift, invariant violations = 0 |
| Computer vision | welfare anomalies, piranha count | Probabilistic | Precision/recall on golden footage | Confidence bands, override rate, audits per the thresholds table |
| Generative | companion, report summaries | Non-deterministic | Factuality, safety, format evals; adversarial and indirect-injection sets | Sampled judge + human, thumbs-down, escalation rate |

## The uncertainty questions, answered

| Question | Answer |
| --- | --- |
| Best model today isn't best tomorrow | Change the registry entry, pass the eval gate, promote. No service code changes. Target ≤ 1 day (OKR 5.2). |
| Provider changes prices | Budgets + tiered routing + downgrade path already wired in the gateway config; cost per capability visible daily. |
| Provider shuts down | Named fallback provider passing the same evals; open-weight bundle on managed hosting exercised monthly; prompts/evals/traces are ours; safety paths never depend on a generative provider. |
| The gateway itself is a dependency | It is adopted OSS with declarative config; the resolver isolates services; only hosted generative capabilities depend on it — vision, counting and forecasting never do. |
| How do we know it works? | Nothing is promoted without passing its golden set; shadow before live; guardrails with auto-rollback after — all numbers in one table. |
| How do we know it *stopped* working? | Drift monitors + business-metric guardrails + human override rate, alerting the capability owner. |
| Who does all the reviewing? | Existing estate roles, ≈ 17–26 h/week in total, with labels captured as a side-effect of their normal decisions. |
