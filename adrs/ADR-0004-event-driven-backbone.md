# ADR-0004 — Event-driven backbone between bounded contexts

**Status:** accepted · **Date:** 2026-09-05
**Serves:** NFR-RES-2, NFR-EVO-1, NFR-SCL-1, NFR-OPS-1, NFR-PRV-1, FR-5.1, FR-5.3
**Related:** ADR-0001, ADR-0005, ADR-0009, ADR-0012

## Context
Four bounded contexts (Ticketing & Access, Park Operations, Animal Welfare, Guest Engagement), telemetry arriving asynchronously from an intermittently connected estate, and AI components that must be added, replaced or switched off without disturbing the rest. The judges ask whether the AI additions share the architectural characteristics of the base system.

## Decision
1. Contexts communicate through a **durable, replayable event backbone** (managed streaming; topics per context; schema registry). No shared databases.
2. Events are **facts** (`GateEntered`, `FeedingRecorded`, `WelfareAnomalyDetected`, `PriceRecommended`), versioned with a schema registry; consumers are tolerant to additive change.
3. **AI components are ordinary consumers and producers** on the backbone. A scoring model consumes `FeedingRecorded` and produces `WelfareAnomalyDetected`; it can be replaced by a new version (or a rule) without producers or other consumers noticing.
4. **Synchronous calls** are reserved for user-facing request/response (BFF → services) and for the inference gateway (a service asks a question and needs an answer now).
5. Every AI decision is itself an event with `model_version`, `confidence`, inputs reference — this **is** the audit log (FR-5.1) and the retraining dataset.
6. **No personal data in events.** Events carry pseudonymous subject ids (a random `visitor_id` issued at account creation; ticket and session ids), never names, e-mail addresses, phone numbers, device identifiers or free text about a person. The schema registry's **CI check rejects** any field tagged `pii` or matching a deny-list unless it is declared `encrypted`. The few unavoidable personal fields (a companion transcript kept for evaluation, a nudge delivery address) are encrypted with a **per-subject key**; erasure deletes the key (**crypto-shredding**), so the immutable log stays immutable and unreadable for that subject. A `SubjectErased` event tells every consumer to drop or re-key the subject in read models, the feature store and golden sets ([ADR-0009](ADR-0009-visitor-privacy-anonymous-counting.md) §7).
7. **Deployment unit ≠ context boundary.** The four business contexts ship as **one modular monolith**: one deployable, one runtime, a **private schema per module** (no cross-module table access — enforced by a fitness function in CI), each module publishing through a **transactional outbox** to the backbone. AI consumers, the IoT ingestion path and GPU/batch workers are **separate deployables** on the same backbone. A module is extracted only when it meets one of these criteria: it needs to scale independently (> 3× the others), its release cadence blocks the others, it needs a different runtime (GPU), or a different team owns it. None applies at 15,000 visitors/day; a team of five deploys one business thing.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Synchronous microservices (REST between contexts) | Familiar | Temporal coupling; a slow AI call slows ticketing; hard to add consumers; retries and outages cascade | Resilience, evolvability |
| One deployable per context (event-driven microservices) | Isolation; independent scaling | Four services plus AI workers, ingestion and edge for a team of five; no context needs independent scaling at 15,000/day; distributed debugging from day one | NFR-OPS-1 — extraction criteria (§7) let us get here later if needed |
| Modular monolith with a **shared** schema | Simplest deploy; joins across contexts | Shared schema couples contexts; AI and GPU workloads do not fit in one runtime | Coupling — we take the monolith, not the shared schema |
| Event-driven contexts inside a modular monolith, AI as separate consumers (chosen) | Loose coupling with one business deployable; replay for retraining; natural fit with MQTT ingest; GPU workloads outside the monolith | Eventual consistency; outbox relay to run; module discipline needs CI enforcement | — |

## Consequences
**Positive:** adding an AI consumer is a deployment, not a change request; outages are isolated; history is replayable to backtest new models on real data; the business tier is one deployable a small team can watch.
**Negative:** eventual consistency must be explained to users ("dashboard may lag 60 s"); debugging spans the monolith, AI consumers and the edge; schema governance is real work; the monolith couples module release cadence until a module is extracted.

| Risk | Mitigation |
| --- | --- |
| Schema breaking changes | Registry with compatibility checks in CI |
| Duplicate/out-of-order events | Idempotent consumers keyed on event id; per-source ordering guarantees only |
| Hidden coupling via event content | Events carry ids and facts, not another context's internal model; consumer-driven contract tests |
| Module boundaries erode inside the monolith | Fitness function in CI: no cross-schema access, no imports across modules except published interfaces; extraction criteria reviewed quarterly |
| Personal data leaks into an event | Schema-registry CI check with `pii` tags and deny-list; erasure end-to-end test in the game-day catalogue (GD-11) |

## How we will know this was right
Time to add a new AI consumer to production (target: days, no producer change); zero cascading incidents across contexts; retraining pipelines run from replayed events without bespoke exports; zero cross-module schema access found by the fitness function; an erasure request leaves zero references in the audit query.
