# ADR-0004 — Event-driven backbone between bounded contexts

**Status:** accepted · **Date:** 2026-09-05 (revised 2026-09-08)
**Serves:** NFR-RES-2, NFR-EVO-1, NFR-SCL-1, NFR-OPS-1, NFR-PRV-1, FR-5.1, FR-5.3
**Related:** ADR-0001, ADR-0005, ADR-0009, ADR-0012

## Context
Four bounded contexts (Ticketing & Access, Park Operations, Animal Welfare, Guest Engagement), telemetry arriving asynchronously from an intermittently connected estate, and AI components that must be added, replaced or switched off without disturbing the rest. The judges ask whether the AI additions share the architectural characteristics of the base system.

## Decision
1. Contexts communicate through a **durable, replayable event backbone** (managed streaming; topics per context; schema registry). No shared databases.
2. Events are **facts** (`GateEntered`, `PurchaseRecorded`, `FeedingRecorded`, `TreatmentStarted`, `WelfareAnomalyDetected`, `PriceRecommended`), versioned with a schema registry; consumers are tolerant to additive change. A commerce fact carries what an auditor needs — transaction id, type (sale / refund / void / correction), net, tax, currency — so a read model can be reconciled against the vendor's books (FR-2.6).
3. **AI components are ordinary consumers and producers** on the backbone. A scoring model consumes `FeedingRecorded` and produces `WelfareAnomalyDetected`; it can be replaced by a new version (or a rule) without producers or other consumers noticing.
4. **Synchronous calls** are reserved for user-facing request/response (BFF → services) and for the inference gateway (a service asks a question and needs an answer now).
5. Every AI decision is itself an event with `model_version`, `confidence`, inputs reference — this **is** the audit log (FR-5.1) and the retraining dataset. The same pattern covers **human decisions that change prices, capacity or financial parameters**: `PriceUpdated` and `CapacityCapChanged` carry who, when, why (reason code), old and new value; finance parameters and the default cap are GitOps policy config, so their history is the Git log.
6. **No personal data in events.** Events carry pseudonymous subject ids (a random `visitor_id` issued at account creation; ticket and session ids), never names, e-mail addresses, phone numbers, device identifiers or free text about a person. The schema registry's **CI check rejects** any field tagged `pii` or matching a deny-list unless it is declared `encrypted`. The few unavoidable personal fields (a companion transcript kept for evaluation, a nudge delivery address) are encrypted with a **per-subject key**; erasure deletes the key (**crypto-shredding**), so the immutable log stays immutable and unreadable for that subject. A `SubjectErased` event tells every consumer to drop or re-key the subject in read models, the feature store and golden sets ([ADR-0009](ADR-0009-visitor-privacy-anonymous-counting.md) §7).
7. **Deployment unit ≠ context boundary.** The four business contexts ship as **one modular monolith**: one deployable, one runtime, a **private schema per module** (no cross-module table access — enforced by a fitness function in CI), each module publishing through a **transactional outbox** to the backbone. AI consumers, the IoT ingestion path and GPU/batch workers are **separate deployables** on the same backbone. A module is extracted only when it meets one of these criteria: it needs to scale independently (> 3× the others), its release cadence blocks the others, it needs a different runtime (GPU), or a different team owns it. None applies at 15,000 visitors/day; a team of five deploys one business thing.
8. **Consumer-side idempotency is an inbox, specified symmetrically to the outbox.** A consumer applies an event's effect and records `(consumer_id, event_id)` as handled **in one local transaction**; effects that cannot join that transaction (vendor API, e-mail, push) carry an idempotency key derived from the same `event_id`. The CI fitness function that forbids cross-module schema access also fails a subscription handler that writes without its inbox row. Per-consumer keys, windows and the bounded failure this admits are in [hld/core → consumer-side idempotency](../hld/core/README.md#consumer-side-idempotency-the-inbox).
9. **Probabilistic events stay inside their context.** An AI output is a fact about a model, not about the world: `WelfareAnomalyDetected`, `PriceRecommended`, a forecast. Such events never cross into a **visitor-facing** context. What crosses is the **decision** a human or a policy made from them: Animal Welfare publishes `EnclosureStatusChanged` (keeper decides the sloth is off show) and Guest Engagement consumes that, never the anomaly; Guest Engagement publishes `PriceRecommended`, Ticketing & Access applies it within the guardrails and publishes `PriceUpdated`; Park Operations publishes `StaffingPlanApproved`, not the raw forecast. The bounded-context table in [hld/README.md](../hld/README.md#bounded-contexts) is the reference.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Synchronous microservices (REST between contexts) | Familiar | Temporal coupling; a slow AI call slows ticketing; hard to add consumers; retries and outages cascade | Resilience, evolvability |
| One deployable per context (event-driven microservices) | Isolation; independent scaling | Four services plus AI workers, ingestion and edge for a team of five; no context needs independent scaling at 15,000/day; distributed debugging from day one | NFR-OPS-1 — extraction criteria (§7) let us get here later if needed |
| Modular monolith with a **shared** schema | Simplest deploy; joins across contexts | Shared schema couples contexts; AI and GPU workloads do not fit in one runtime | Coupling — we take the monolith, not the shared schema |
| Event-driven contexts inside a modular monolith, AI as separate consumers (chosen) | Loose coupling with one business deployable; replay for retraining; natural fit with MQTT ingest; GPU workloads outside the monolith | Eventual consistency; outbox relay to run; module discipline needs CI enforcement | — |

## Consequences
**Positive:** adding an AI consumer is a deployment, not a change request; outages are isolated; history is replayable to backtest new models on real data; the business tier is one deployable a small team can watch.
**Negative:** every consumer owns an inbox table and the discipline to write it in the effect's transaction; eventual consistency must be explained to users ("dashboard may lag 60 s"); debugging spans the monolith, AI consumers and the edge; schema governance is real work; the monolith couples module release cadence until a module is extracted.

| Risk | Mitigation |
| --- | --- |
| Schema breaking changes | Registry with compatibility checks in CI |
| Duplicate/out-of-order events | Idempotent consumers keyed on event id — for device events derived from `(device_id, boot_id, seq)` at ingestion ([ADR-0001](ADR-0001-edge-first-store-and-forward.md) §4); **inbox row in the same transaction as the effect**, enforced by the same fitness function as the outbox (§8, [table](../hld/core/README.md#consumer-side-idempotency-the-inbox)); per-source ordering guarantees only |
| A probabilistic AI event leaks into a visitor-facing context | §9 rule; consumer-driven contract tests fail on a visitor-facing context subscribing to an AI-output topic |
| Hidden coupling via event content | Events carry ids and facts, not another context's internal model; consumer-driven contract tests |
| Module boundaries erode inside the monolith | Fitness function in CI: no cross-schema access, no imports across modules except published interfaces; extraction criteria reviewed quarterly |
| Personal data leaks into an event | Schema-registry CI check with `pii` tags and deny-list; erasure end-to-end test in the game-day catalogue (GD-11) |

## How we will know this was right
Time to add a new AI consumer to production (target: days, no producer change); zero cascading incidents across contexts; retraining pipelines run from replayed events without bespoke exports; zero cross-module schema access found by the fitness function; an erasure request leaves zero references in the audit query.
