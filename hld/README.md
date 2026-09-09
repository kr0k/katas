# High Level Design

## How the HLD is organised

- [`core/`](core/README.md) — the foundation every AI scenario stands on: edge devices, MQTT, backhaul, event backbone, business services, data platform.
- [`ai-platform/`](ai-platform/README.md) — shared AI infrastructure: inference gateway (adopted OSS) and model governance — registry, evaluation, monitoring. Read this for "dealing with uncertainty" and "does it work".
- [`../appendix/`](../appendix/README.md) — calculations and specifications the design references but does not contain: business case, generative cost, daily-report spec, ticketing rules, data-health runbooks, LoRaWAN airtime.
- [`architecture-evaluation.md`](architecture-evaluation.md) — the ATAM-style evaluation of the whole thing: quality-attribute scenarios with response measures, the architectural styles we rejected and why, sensitivity points, trade-off points, risks and non-risks.
- [`scenarios/`](scenarios/) — one folder per AI use case. Each has the same structure: *Problem → Why AI → Solution → Containers → Diagram → Data → Validation → ADRs*.

## Delivery phases

The full roadmap with entry gates and the build-vs-adopt table lives in the [README](../README.md#delivery-roadmap-what-we-build-when-and-what-we-buy). How it maps onto the HLD:

| Phase | `core/` | `ai-platform/` | `scenarios/` |
| --- | --- | --- | --- |
| 0 · Foundation | Everything: edge tier, ticketing platform integration, event backbone, business monolith, data platform, game days | — | — (data capture only) |
| 1 · Data & rules | Anonymous counters complete · spend ingestion (`PurchaseRecorded`) · [Estate daily report](core/README.md#estate-daily-report) as a template | Inference gateway (adopted), registry and eval gate (thin) | S1 feeding-by-scale · S3 live dashboard · S4 FAQ |
| 2 · Models on data | Edge compute N+1 · daily report phrased by the S1 drafter capability · [requirements/08](../requirements/08-business-case.md) re-issued with season-1 values | Monitoring, shadow mode, golden sets per capability | S1 activity anomalies + vision in shadow · S3 forecasting · S4 planning |
| 3 · Optimisation | — | — | S2 counting · S5 pricing experiment · S4 nudges and pass-upgrade prompt · S1 per-animal vision |

Each scenario README carries a **Phase** line in its header.

## Diagram legend (used in every diagram)

| Shape / style | Meaning |
| --- | --- |
| Rectangle | Software component / service we build or configure |
| Rectangle with `☁️` / `🏰` boundary | Deployment zone: cloud vs. on the estate |
| Stadium (rounded) | External system / SaaS provider |
| Cylinder | Data store |
| Dashed arrow | Asynchronous event / message |
| Solid arrow | Synchronous call (HTTP/gRPC) |
| 🤖 | Component that contains AI inference |
| 👤 | Human decision point |

We use Mermaid so the diagrams render in GitHub and stay in version control next to the decisions they illustrate. Where a diagram has custom shapes, its own legend is added below it.

## C4 · Level 1 — System context

```mermaid
flowchart LR
    Visitor["👨‍👩‍👧 Visitor / Family"]
    Countess["👑 Countess & management"]
    Staff["👩‍⚕️ Vet, keepers, ops staff"]
    System["Von Digitalis Estate Platform"]
    Pay(["Payment provider"])
    LLM(["LLM / vision providers"])
    Msg(["Email / push provider"])
    Weather(["Weather & events data"])
    TixSaaS(["Ticketing & POS platform (SaaS)<br/>or a separate POS behind the same anti-corruption layer"])
    HR(["HR / rostering system"])

    Visitor -- "buys tickets, uses companion" --> System
    Countess -- "reads the daily report and dashboards, sets base price, pass price & guardrails" --> System
    Staff -- "reviews alerts, logs treatments, runs the park" --> System
    System <-- "sales, entries, passes, purchases / prices, caps, erasure" --> TixSaaS
    TixSaaS --> Pay
    System <-- "staff, skills, availability / approved plans" --> HR
    System --> LLM
    System --> Msg
    Weather --> System
```

## C4 · Level 2 — Containers

See [core/README.md](core/README.md#container-view) for the full container view and [ai-platform/README.md](ai-platform/README.md) for the AI containers.

## Bounded contexts

| Context | Owns | Publishes events | Consumes events |
| --- | --- | --- | --- |
| **Ticketing & Access** (anti-corruption layer to the ticketing platform, [ADR-0012](../adrs/ADR-0012-ticketing-platform-adopt-not-build.md)) | tickets, passes, **on-site purchases**, gate validations, capacity cap, timed-entry slots and pass-holder reservations, upgrade vouchers, accounts (opt-in) — as our events over the vendor's data | `TicketPurchased`, `GateEntered` (with `persons_admitted`), `GateExited`, `PassRenewed`, `PurchaseRecorded` (an auditable commerce event: transaction id, type, net + tax + currency, category, terminal, time, optional pseudonymous visitor id — FR-2.6), `PriceUpdated`, `CapacityCapChanged` (ops decision with reason code) | `PriceRecommended` (applies it within guardrails), `SubjectErased` |
| **Park Operations** | zones, rides, footfall, queues, staffing plans, labour rules, **the Estate daily report** (a read model — it publishes no event) | `ZoneOccupancyUpdated`, `QueueLengthUpdated`, `RideStatusChanged`, `StaffingPlanApproved` | `GateEntered/Exited`, telemetry, `EnclosureStatusChanged`; for the daily report: `TicketPurchased`, `PassRenewed`, `PurchaseRecorded`, `CapacityCapChanged`, `ReviewDecided`, `TreatmentStarted/Closed` — facts and human decisions, never model output |
| **Animal Welfare** | animals, enclosures, feeding, health reviews, treatments, population ledger and estimates | `FeedingRecorded`, `WelfareAnomalyDetected`, `ReviewDecided`, `TreatmentStarted`, `TreatmentClosed`, `EnclosureStatusChanged` (keeper decision: on/off show), `PopulationEstimated`, `SafetyAlertRaised` | enclosure telemetry |
| **Guest Engagement** | companion sessions, itineraries, nudges, pricing recommendations, per-subject keys | `ItineraryCreated`, `NudgeSent`, `PriceRecommended`, `SubjectErased` | `QueueLengthUpdated`, `RideStatusChanged`, `TicketPurchased`, `PriceUpdated`, `EnclosureStatusChanged` (e.g. "the sloth is off show today") |

**Why the boundaries sit where they do.** Each context is dominated by a different one of the estate's [driving characteristics](../requirements/04-non-functional-requirements.md#driving-characteristics-the-ones-that-shape-the-architecture), which is the reason there are four of them and not one module or fourteen services: a boundary is drawn where the characteristics diverge, so that each side can be built and degraded on its own terms.

| Context | Dominant characteristic | What the boundary therefore buys |
| --- | --- | --- |
| **Ticketing & Access** | Resilience to connectivity loss (plus a local need for transactional consistency the others do not have) | Admission survives an outage on signed credentials and a local ledger, while money and PCI scope stay with the vendor — neither of which the other three contexts should inherit |
| **Park Operations** | Analysability, at a cost that does not grow with attendance | Read models rebuilt by replay, forecasting in scheduled batches, and no model on a request path |
| **Animal Welfare** | Safety, then accuracy | The tier-0 rules stay deterministic and local, structurally separated from every model; confidence bands and evidence travel with each opinion |
| **Guest Engagement** | Evolvability of the AI layer, then cost-efficiency | Capabilities are addressed by name so a model can be swapped, degraded or switched off without the visitor-facing surface changing |

Contexts communicate only through events on the backbone or through published read models — no shared databases. This matters for the AI additions: a scenario can be switched off, replaced or degraded without touching the others.

### Rule: probabilistic events do not cross into visitor-facing contexts

This is the boundary that makes embedding AI in a business process safe rather than reckless, so it is stated once here and enforced in code. `WelfareAnomalyDetected` is a model's opinion; what Guest Engagement may act on is `EnclosureStatusChanged`, a keeper's decision. `PriceRecommended` is a model's opinion; what visitors see is `PriceUpdated`, after the policy engine and, where needed, management. The forecast never leaves Park Operations; `StaffingPlanApproved` does. Contract tests fail a visitor-facing context that subscribes to an AI-output topic ([ADR-0004](../adrs/ADR-0004-event-driven-backbone.md) §9).

Its complement is the reason the [process table](../README.md#where-ai-sits-in-the-working-day) has a column for the AI being off: a model may inform a decision, and a human or a rule commits it. Nothing downstream of a model is load-bearing on its own.
