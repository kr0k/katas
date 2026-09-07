# ADR-0004 — Event-driven backbone between bounded contexts

**Status:** accepted · **Date:** 2026-09-05
**Serves:** NFR-RES-2, NFR-EVO-1, NFR-SCL-1, FR-5.1
**Related:** ADR-0001, ADR-0005

## Context
Four bounded contexts (Ticketing & Access, Park Operations, Animal Welfare, Guest Engagement), telemetry arriving asynchronously from an intermittently connected estate, and AI components that must be added, replaced or switched off without disturbing the rest. The judges ask whether the AI additions share the architectural characteristics of the base system.

## Decision
1. Contexts communicate through a **durable, replayable event backbone** (managed streaming; topics per context; schema registry). No shared databases.
2. Events are **facts** (`GateEntered`, `FeedingRecorded`, `WelfareAnomalyDetected`, `PriceRecommended`), versioned with a schema registry; consumers are tolerant to additive change.
3. **AI components are ordinary consumers and producers** on the backbone. A scoring model consumes `FeedingRecorded` and produces `WelfareAnomalyDetected`; it can be replaced by a new version (or a rule) without producers or other consumers noticing.
4. **Synchronous calls** are reserved for user-facing request/response (BFF → services) and for the model gateway (a service asks a question and needs an answer now).
5. Every AI decision is itself an event with `model_version`, `confidence`, inputs reference — this **is** the audit log (FR-5.1) and the retraining dataset.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Synchronous microservices (REST between contexts) | Familiar | Temporal coupling; a slow AI call slows ticketing; hard to add consumers; retries and outages cascade | Resilience, evolvability |
| Modular monolith with shared DB | Simple deploy | Shared schema couples contexts; AI workloads (GPU, bursty) do not fit; scaling is all-or-nothing | AI workload fit |
| Event-driven (chosen) | Loose coupling; replay for retraining; natural fit with MQTT ingest | Eventual consistency; more moving parts; needs schema discipline | — |

## Consequences
**Positive:** adding an AI consumer is a deployment, not a change request; outages are isolated; history is replayable to backtest new models on real data.
**Negative:** eventual consistency must be explained to users ("dashboard may lag 60 s"); debugging spans services; schema governance is real work.

| Risk | Mitigation |
| --- | --- |
| Schema breaking changes | Registry with compatibility checks in CI |
| Duplicate/out-of-order events | Idempotent consumers keyed on event id; per-source ordering guarantees only |
| Hidden coupling via event content | Events carry ids and facts, not another context's internal model; consumer-driven contract tests |

## How we will know this was right
Time to add a new AI consumer to production (target: days, no producer change); zero cascading incidents across contexts; retraining pipelines run from replayed events without bespoke exports.
