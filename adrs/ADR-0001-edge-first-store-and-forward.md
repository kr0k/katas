# ADR-0001 — Edge-first architecture with store-and-forward

**Status:** accepted · **Date:** 2026-09-05
**Serves:** FR-1.4, FR-3.6, NFR-AVL-1, NFR-AVL-3, NFR-RES-1, NFR-RES-2
**Related:** ADR-0002, ADR-0006, ADR-0011

## Context
Wi-Fi on the estate is patchy and the uplink to any cloud will fail — for minutes, sometimes hours. Yet visitors must get through the gates, staff must be alerted when an enclosure door opens, and telemetry must not be lost. The brief allows cloud services but makes getting data off the estate our problem.

## Decision
The estate runs a **local tier** that is sufficient for safety, access and data capture on its own; the cloud tier adds analytics, AI and visitor-facing services.

1. A local **MQTT broker (HA pair)** is the hub for every device. Messages are persisted (QoS 1) and **bridged to the cloud when the uplink is up**; buffered otherwise, sized for 72 h.
2. **Gate validation** and **safety alerting** are local services subscribing to the broker; they never call the cloud on the critical path.
3. **Edge inference nodes** process video locally and publish features/events, so video never needs the backhaul.
4. Cloud ingestion is **idempotent** (dedupe on device id + sequence); consumers tolerate late and out-of-order data.
5. Every capability declares its place on a **degradation ladder** (cloud+AI → cloud → estate-only).

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Cloud-first, devices publish directly to a cloud IoT service | Simplest; fully managed | Gates and alerts fail with the uplink; video cannot be shipped; per-device cellular is expensive | Violates NFR-AVL-1/3 |
| Fully on-premise (no cloud) | No uplink dependency | Team of 5 runs databases, ML, web at scale; visitors' web/mobile still needs internet; no elastic compute for training | Operability (NFR-OPS-1) and cost |
| Edge-first (chosen) | Local resilience; cloud for what cloud is good at | Two tiers to operate; some duplication (local cache of read models) | — |

## Consequences
**Positive:** estate functions during outages; bandwidth needs are tiny; privacy improves (video stays local); AI additions inherit the same asynchronous, eventually-consistent model as everything else.
**Negative:** two deployment targets; on-site hardware to maintain (broker pair, edge nodes, UPS); eventual consistency means the cloud view may lag reality during outages.

| Risk | Mitigation |
| --- | --- |
| Local hardware failure | HA broker pair; UPS; spare edge node; monitoring from the cloud with "last seen" alerts |
| Buffer overflow in a long outage | 72 h sizing (telemetry is small); oldest non-critical telemetry dropped first; gate and safety events prioritised |
| Divergence between local and cloud state | Idempotent ingest; reconciliation jobs; conflict rules documented per stream |

## How we will know this was right
Gate availability during uplink outages (target 99.9%); zero telemetry loss in quarterly failover drills; safety alert p99 ≤ 5 s measured locally. Revisit if the estate gets reliable fibre and cellular redundancy — then the local tier can shrink, but safety and gates should stay local regardless.
