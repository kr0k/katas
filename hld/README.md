# High Level Design

## How the HLD is organised

- [`core/`](core/README.md) — the foundation every AI scenario stands on: edge devices, MQTT, backhaul, event backbone, business services, data platform.
- [`ai-platform/`](ai-platform/README.md) — shared AI infrastructure: model gateway, registry, evaluation, monitoring. Read this for "dealing with uncertainty" and "does it work".
- [`scenarios/`](scenarios/) — one folder per AI use case. Each has the same structure: *Problem → Why AI → Solution → Containers → Diagram → Data → Validation → ADRs*.

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

    Visitor -- "buys tickets, uses companion" --> System
    Countess -- "reads dashboards, sets pricing guardrails" --> System
    Staff -- "reviews alerts, logs treatments, runs the park" --> System
    System --> Pay
    System --> LLM
    System --> Msg
    Weather --> System
```

## C4 · Level 2 — Containers

See [core/README.md](core/README.md#container-view) for the full container view and [ai-platform/README.md](ai-platform/README.md) for the AI containers.

## Bounded contexts

| Context | Owns | Publishes events | Consumes events |
| --- | --- | --- | --- |
| **Ticketing & Access** | tickets, passes, gate validations, accounts (opt-in) | `TicketPurchased`, `GateEntered`, `GateExited`, `PassRenewed` | `PriceUpdated` |
| **Park Operations** | zones, rides, footfall, queues, staffing plans | `ZoneOccupancyUpdated`, `QueueLengthUpdated`, `RideStatusChanged`, `StaffingPlanProposed` | `GateEntered/Exited`, telemetry |
| **Animal Welfare** | animals, enclosures, feeding, health reviews, population estimates | `FeedingRecorded`, `WelfareAnomalyDetected`, `ReviewDecided`, `PopulationEstimated`, `SafetyAlertRaised` | enclosure telemetry |
| **Guest Engagement** | companion sessions, itineraries, nudges, pricing recommendations | `ItineraryCreated`, `NudgeSent`, `PriceRecommended` | `QueueLengthUpdated`, `TicketPurchased`, `WelfareAnomalyDetected` (e.g. "the sloth is off show today") |

Contexts communicate only through events on the backbone or through published read models — no shared databases. This matters for the AI additions: a scenario can be switched off, replaced or degraded without touching the others.
