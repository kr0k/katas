# ADR-0001 — Edge-first architecture with store-and-forward

**Status:** accepted · **Date:** 2026-09-05
**Serves:** FR-1.4, FR-3.6, NFR-AVL-1, NFR-AVL-3, NFR-RES-1, NFR-RES-2, NFR-DR-3
**Related:** ADR-0002, ADR-0006, ADR-0011

## Context
Wi-Fi on the estate is patchy and the uplink to any cloud will fail — for minutes, sometimes hours. Yet visitors must get through the gates, staff must be alerted when an enclosure door opens, and telemetry must not be lost. The brief allows cloud services but makes getting data off the estate our problem.

## Decision
The estate runs a **local tier** that is sufficient for safety, access and data capture on its own; the cloud tier adds analytics, AI and visitor-facing services.

1. A local **MQTT broker cluster** (three nodes, replicated persistent queues — [ADR-0002](ADR-0002-mqtt-and-cellular-backhaul.md) §3) is the hub for every device. Messages are persisted (QoS 1) in one queue per **traffic class** (critical / telemetry / clips) and **bridged to the cloud when the uplink is up**; buffered otherwise, sized for 72 h, drained critical first.
2. **Gate validation** and **tier-0 safety rules** are local services subscribing to the broker; they never call the cloud on the critical path. Safety alerts are delivered to **DECT handsets/pagers** first and measured to a human acknowledgement (NFR-AVL-3).
3. **Edge inference nodes** process video locally and publish aggregated features and event clips, so video never needs the backhaul.
4. Cloud ingestion is **idempotent**: dedupe on `(device_id, boot_id, seq)` — the boot id makes a reboot or battery swap harmless — and one derived event id that every downstream consumer keys on; consumers tolerate late and out-of-order data.
5. Every capability declares its place on a **degradation ladder** (cloud+AI → cloud → estate-only).
6. **The downlink is designed, not assumed.** State that must reach the estate — ticket allow/revocation lists, rule and policy parameters, desired edge model versions — travels over the same bridge as **retained, sequence-numbered snapshots**, critical class first, so a reconnecting gate or rule engine has the latest state within a minute. Large artifacts (edge models) are **pulled** by edge nodes over HTTPS — resumable, rate-limited, off-hours — never pushed through MQTT ([Edge & connectivity → Downlink](../hld/core/edge-and-connectivity.md#downlink-cloud--estate)).

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Cloud-first, devices publish directly to a cloud IoT service | Simplest; fully managed | Gates and alerts fail with the uplink; video cannot be shipped; per-device cellular is expensive | Violates NFR-AVL-1/3 |
| Fully on-premise (no cloud) | No uplink dependency | Team of 5 runs databases, ML, web at scale; visitors' web/mobile still needs internet; no elastic compute for training | Operability (NFR-OPS-1) and cost |
| Edge-first (chosen) | Local resilience; cloud for what cloud is good at | Two tiers to operate; some duplication (local cache of read models) | — |

## Consequences
**Positive:** estate functions during outages; bandwidth needs are tiny; privacy improves (video stays local); AI additions inherit the same asynchronous, eventually-consistent model as everything else.
**Negative:** two deployment targets; on-site hardware to maintain (broker cluster, edge nodes, LoRaWAN server, DECT base stations, UPS); eventual consistency means the cloud view may lag reality during outages.

| Risk | Mitigation |
| --- | --- |
| Local hardware failure | Three-node broker cluster with replicated queues; UPS; edge nodes sized N+1; monitoring from the cloud with "last seen" alerts |
| Edge buffer lost with a disk | Every message replicated to a second broker node before it is acknowledged (NFR-DR-3); quarterly restore drill GD-13 |
| Buffer overflow in a long outage | 72 h sizing per traffic class (≈ 3 GB at 15,000/day with features aggregated at the edge); per-class disk quotas; clips dropped first, telemetry oldest-first, critical never |
| Readings dropped as duplicates after a reboot or battery swap | `boot_id` in the idempotency key; dedupe drop rate per device as an alerting metric |
| Divergence between local and cloud state | Idempotent ingest; reconciliation jobs; conflict rules documented per stream |
| Reconnect after an outage: uplink drain starves the downlink, gates keep admitting revoked tickets | One bridge connection per direction; critical downlink snapshot delivered first; model pulls paused until the buffer is drained; game day GD-5 |

## How we will know this was right
Gate availability during uplink outages (target 99.9%); zero telemetry loss in quarterly failover drills; safety alert p99 ≤ 5 s measured locally; revocations applied at the gates ≤ 60 s after reconnect. All four are game days GD-1, GD-3, GD-5 and GD-6 in the [resilience validation catalogue](../hld/core/resilience-validation.md). Revisit if the estate gets reliable fibre and cellular redundancy — then the local tier can shrink, but safety and gates should stay local regardless.
