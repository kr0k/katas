# High Level Design

## How the HLD is organised

- [`core/`](core/README.md) — the foundation every AI scenario stands on: edge devices, MQTT, backhaul, event backbone, business services, data platform.
- [`ai-platform/`](ai-platform/README.md) — shared AI infrastructure: inference gateway (adopted OSS) and model governance — registry, evaluation, monitoring. Read this for "dealing with uncertainty" and "does it work".
- [`scenarios/`](scenarios/) — one folder per AI use case. Each has the same structure: *Problem → Why AI → Solution → Containers → Diagram → Data → Validation → ADRs*.

## Delivery phases

The full roadmap with entry gates and the build-vs-adopt table lives in the [README](../README.md#delivery-roadmap-what-we-build-when-and-what-we-buy). How it maps onto the HLD:

| Phase | `core/` | `ai-platform/` | `scenarios/` |
| --- | --- | --- | --- |
| 0 · Foundation | Everything: edge tier, ticketing platform integration, event backbone, business monolith, data platform, game days | — | — (data capture only) |
| 1 · Data & rules | Anonymous counters complete | Inference gateway (adopted), registry and eval gate (thin) | S1 feeding-by-scale · S3 live dashboard · S4 FAQ |
| 2 · Models on data | Edge compute N+1 | Monitoring, shadow mode, golden sets per capability | S1 activity anomalies + vision in shadow · S3 forecasting · S4 planning |
| 3 · Optimisation | — | — | S2 counting · S5 pricing experiment · S4 nudges · S1 per-animal vision |

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
    TixSaaS(["Ticketing platform (SaaS)"])
    HR(["HR / rostering system"])

    Visitor -- "buys tickets, uses companion" --> System
    Countess -- "reads dashboards, sets base price & guardrails" --> System
    Staff -- "reviews alerts, logs treatments, runs the park" --> System
    System <-- "sales, entries, passes / prices, erasure" --> TixSaaS
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
| **Ticketing & Access** (anti-corruption layer to the ticketing platform, [ADR-0012](../adrs/ADR-0012-ticketing-platform-adopt-not-build.md)) | tickets, passes, gate validations, accounts (opt-in) — as our events over the vendor's data | `TicketPurchased`, `GateEntered`, `GateExited`, `PassRenewed`, `PriceUpdated` | `PriceRecommended` (applies it within guardrails), `SubjectErased` |
| **Park Operations** | zones, rides, footfall, queues, staffing plans, labour rules | `ZoneOccupancyUpdated`, `QueueLengthUpdated`, `RideStatusChanged`, `StaffingPlanApproved` | `GateEntered/Exited`, telemetry, `EnclosureStatusChanged` |
| **Animal Welfare** | animals, enclosures, feeding, health reviews, population ledger and estimates | `FeedingRecorded`, `WelfareAnomalyDetected`, `ReviewDecided`, `EnclosureStatusChanged` (keeper decision: on/off show), `PopulationEstimated`, `SafetyAlertRaised` | enclosure telemetry |
| **Guest Engagement** | companion sessions, itineraries, nudges, pricing recommendations, per-subject keys | `ItineraryCreated`, `NudgeSent`, `PriceRecommended`, `SubjectErased` | `QueueLengthUpdated`, `RideStatusChanged`, `TicketPurchased`, `PriceUpdated`, `EnclosureStatusChanged` (e.g. "the sloth is off show today") |

Contexts communicate only through events on the backbone or through published read models — no shared databases. This matters for the AI additions: a scenario can be switched off, replaced or degraded without touching the others.

**Rule: probabilistic events do not cross into visitor-facing contexts.** `WelfareAnomalyDetected` is a model's opinion; what Guest Engagement may act on is `EnclosureStatusChanged`, a keeper's decision. `PriceRecommended` is a model's opinion; what visitors see is `PriceUpdated`, after the policy engine and, where needed, management. The forecast never leaves Park Operations; `StaffingPlanApproved` does. Contract tests fail a visitor-facing context that subscribes to an AI-output topic ([ADR-0004](../adrs/ADR-0004-event-driven-backbone.md) §8).
