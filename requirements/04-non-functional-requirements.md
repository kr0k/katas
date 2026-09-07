# 04 · Non-Functional Requirements & Architectural Characteristics

## Driving characteristics (the ones that shape the architecture)

We chose four. Everything else is important but does not drive structure.

| Characteristic | Why it drives the design | Where it shows up |
| --- | --- | --- |
| **Resilience to connectivity loss** | Wi-Fi is patchy; the uplink will fail. Gates, safety alerts and data capture must work offline. | Edge-first design, store-and-forward, offline validation → [ADR-0001](../adrs/ADR-0001-edge-first-store-and-forward.md), [ADR-0011](../adrs/ADR-0011-offline-ticket-validation.md) |
| **Safety** | Poisonous animals + historic rides + families. Safety paths must be deterministic and local. | FR-3.6 tier-0 rules bypass cloud and ML; FR-3.7 model advisories only add to them → [ADR-0006](../adrs/ADR-0006-edge-vs-cloud-inference.md) |
| **Evolvability of the AI layer** | Models and providers will change faster than the estate. | Inference gateway; model governance (registry, evals, monitoring) → [ADR-0005](../adrs/ADR-0005-model-gateway-and-provider-independence.md) |
| **Cost-efficiency** | A poor estate with a small team. Cloud and AI spend must be bounded and visible. | Tiered model routing, per-capability budgets, edge inference for high-volume streams → [ADR-0005](../adrs/ADR-0005-model-gateway-and-provider-independence.md), [ADR-0006](../adrs/ADR-0006-edge-vs-cloud-inference.md) |

## Full NFR list

| ID | NFR | Target |
| --- | --- | --- |
| NFR-AVL-1 | Gate validation availability (local) | 99.9% during opening hours, independent of uplink |
| NFR-AVL-2 | Ticket purchase availability (cloud) | 99.9% |
| NFR-AVL-3 | Safety alert delivery | ≤ 5 s end-to-end on the local network, no cloud dependency |
| NFR-RES-1 | Telemetry buffering during uplink loss | ≥ 24 h at edge without data loss |
| NFR-RES-2 | Degraded mode | Every AI capability has a deterministic fallback; loss of AI never blocks a core function |
| NFR-SCL-1 | Peak load | 15,000 visitors/day; ~3,000 gate scans/hour at opening; 40 rides + 55 enclosures streaming telemetry |
| NFR-SCL-2 | Camera ingest | 55 enclosures × 1–2 cameras; pre-filtered at edge; only events/clips leave the estate |
| NFR-PRF-1 | Companion response time | p95 ≤ 3 s for grounded answers |
| NFR-PRF-2 | Dashboard freshness | Live view ≤ 60 s behind reality when uplink is up |
| NFR-SEC-1 | Device identity | Per-device certificates; mutual TLS to broker |
| NFR-SEC-2 | Payment data | Never touches estate systems (PCI scope at provider) |
| NFR-PRV-1 | Visitor privacy | Footfall counting is anonymous (no faces, no device IDs retained); GDPR-compliant opt-in for accounts |
| NFR-PRV-2 | Camera footage | Enclosure cameras point at animals; visitor areas in frame are masked at edge |
| NFR-OBS-1 | Observability | Traces, metrics and logs for every service and every AI call (model, version, tokens, cost, confidence) |
| NFR-EVO-1 | Model replaceability | Swap a model/provider for a capability in ≤ 1 day with no service code change |
| NFR-VER-1 | AI verification | No model/prompt version reaches production without passing its evaluation suite |
| NFR-COST-1 | AI spend | Per-capability monthly budget with alerts at 70% / 90% and automatic downgrade at 100% |
| NFR-OPS-1 | Operability | Deployable and runnable by a team of ≤ 5 engineers; GitOps for all infrastructure |

## Architectural style

**Event-driven, edge-first, with bounded contexts** (Ticketing & Access, Park Operations, Animal Welfare, Guest Engagement) communicating through an event backbone. The four contexts are deployed as **one modular monolith** with private schemas and an outbox; AI components are **separate** consumers and producers on the same backbone, so they inherit the same asynchrony, retry and degradation properties as everything else — this is how we keep the "architectural characteristics of the additions" consistent with the base system ([ADR-0004](../adrs/ADR-0004-event-driven-backbone.md)).
