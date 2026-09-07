# 04 · Non-Functional Requirements & Architectural Characteristics

## Driving characteristics (the ones that shape the architecture)

We chose four. Everything else is important but does not drive structure.

| Characteristic | Why it drives the design | Where it shows up |
| --- | --- | --- |
| **Resilience to connectivity loss** | Wi-Fi is patchy; the uplink will fail. Gates, safety alerts and data capture must work offline. | Edge-first design, store-and-forward, offline validation → [ADR-0001](../adrs/ADR-0001-edge-first-store-and-forward.md), [ADR-0011](../adrs/ADR-0011-offline-ticket-validation.md) |
| **Safety** | Poisonous animals + historic rides + families. Safety paths must be deterministic and local. | FR-3.6 tier-0 rules bypass cloud and ML; FR-3.7 model advisories only add to them → [ADR-0006](../adrs/ADR-0006-edge-vs-cloud-inference.md) |
| **Evolvability of the AI layer** | Models and providers will change faster than the estate. | Inference gateway; model governance (registry, evals, monitoring) → [ADR-0005](../adrs/ADR-0005-model-gateway-and-provider-independence.md) |
| **Cost-efficiency** | A poor estate with a small team. Cloud and AI spend must be bounded and visible. | Tiered model routing, per-capability budgets, edge inference for high-volume streams, adopt-not-build → [ADR-0005](../adrs/ADR-0005-model-gateway-and-provider-independence.md), [ADR-0006](../adrs/ADR-0006-edge-vs-cloud-inference.md), [ADR-0012](../adrs/ADR-0012-ticketing-platform-adopt-not-build.md) |

## Full NFR list

| ID | NFR | Target |
| --- | --- | --- |
| NFR-AVL-1 | Gate validation availability (local) | 99.9% during opening hours, independent of uplink |
| NFR-AVL-2 | Ticket purchase availability (cloud) | 99.9% (ticketing platform SLA, [ADR-0012](../adrs/ADR-0012-ticketing-platform-adopt-not-build.md)) |
| NFR-AVL-3 | Safety alert delivery **to a human** | ≤ 5 s from sensor to a DECT handset/pager on the local network, no cloud dependency; **acknowledged by a human within 60 s** or escalated (head keeper, then all staff); measured end to end to the acknowledgement; unacknowledged alerts per day = 0 |
| NFR-RES-1 | Telemetry buffering during uplink loss | ≥ 24 h at edge without data loss (sized for 72 h, per traffic class) |
| NFR-RES-2 | Degraded mode | Every AI capability has a **non-AI fallback** — a rule-based system or a documented human procedure; loss of AI never blocks a core function |
| NFR-SCL-1 | Peak load | 15,000 visitors/day on average; a peak day ≈ 29,000 with ≈ 5,900 gate scans in the peak hour ([capacity check](08-business-case.md#1-capacity-reality-check)); 40 rides + 55 enclosures streaming telemetry |
| NFR-SCL-2 | Camera ingest | 55 enclosures × 1–2 cameras; pre-filtered at edge; only 1-minute feature windows and event clips leave the estate |
| NFR-PRF-1 | Companion response time, **by request class** | FAQ answer: p95 ≤ 3 s complete. Day planning: first token ≤ 2 s, first stop suggestion ≤ 5 s, full plan ≤ 15 s (p95, streamed); re-plan after a closure ≤ 5 s. Verified by a load test at 500 concurrent sessions before each promotion |
| NFR-PRF-2 | Dashboard freshness | Live view ≤ 60 s behind reality when uplink is up |
| NFR-SEC-1 | Device identity, **by transport class** | IP devices: per-device X.509 certificate, mutual TLS to the broker, 90-day rotation, TPM/secure element on edge nodes and gate readers. LoRaWAN devices: per-device DevEUI/AppKey with OTAA join, session keys derived at join, keys never shared, de-registration on tamper ([ADR-0002](../adrs/ADR-0002-mqtt-and-cellular-backhaul.md)) |
| NFR-SEC-2 | Payment data | Never touches estate systems (PCI scope at the ticketing platform / payment provider) |
| NFR-PRV-1 | Visitor privacy | Footfall counting is anonymous (no faces, no device IDs retained); GDPR-compliant opt-in for accounts; no personal data in events; erasure completed ≤ 30 days with a passing audit query ([ADR-0009](../adrs/ADR-0009-visitor-privacy-anonymous-counting.md)) |
| NFR-PRV-2 | Camera footage | Enclosure cameras point at animals; visitor areas in frame are masked at edge before anything is stored |
| NFR-OBS-1 | Observability | Traces, metrics and logs for every service and every AI call (model, version, tokens, cost, confidence) |
| NFR-EVO-1 | Model replaceability | Swap a model/provider for a capability in ≤ 1 day with no service code change |
| NFR-VER-1 | AI verification | No model/prompt version reaches production without passing its evaluation suite; the non-AI foundation is verified by the [game-day catalogue](../hld/core/resilience-validation.md) |
| NFR-COST-1 | AI spend | Per-capability monthly budget with alerts at 70% / 90% and automatic downgrade at 100%; total AI spend ≤ 2% of revenue (OKR 5.1) |
| NFR-COST-2 | **Platform cost per visitor** | Total cost of ownership (CAPEX depreciated over 5 years + OPEX including ticketing fees and the team) ≤ €1.00 per visitor at 5,000/day and ≤ €0.50 at 15,000/day, reported quarterly — see [cost model](#cost-model-tco-50) |
| NFR-OPS-1 | Operability | Deployable and runnable by a team of ≤ 5 engineers; GitOps for all infrastructure; AI review and labelling work absorbed by existing estate roles within the hours of the [human roles table](../hld/ai-platform/README.md#humans-in-the-loop-who-does-what) — no separate labelling or operations team |
| NFR-DR-1 | **Systems of record** — welfare records, population ledger, staffing plans, accounts and per-subject keys, ticketing (at the platform, as a selection criterion) | RPO ≤ 15 min (point-in-time recovery), RTO ≤ 4 h; restore tested quarterly in game day GD-13 |
| NFR-DR-2 | **Event log and lakehouse** | RPO 0 for acknowledged events (replicated managed streaming, multi-zone); read models and feature store are rebuilt by replay, RTO ≤ 8 h; models, prompts and golden sets versioned in Git and object storage, RPO ≤ 1 day |
| NFR-DR-3 | **Edge buffer** | Every message replicated to a second broker node before acknowledgement; loss of one node or disk loses nothing; broker cluster failover ≤ 30 s (GD-3) |

## Cost model (TCO, ±50%)

Order-of-magnitude figures so that NFR-COST-2 can be checked and so the Countess sees what she is buying. All numbers are assumptions to be replaced by quotes. The business case — payback, growth, what the estate must fund besides the platform — is in [08](08-business-case.md), which uses this table as a curve: **OPEX(V) ≈ €580k fixed + €0.165 per visitor-day**, within ≈ 2% of both columns below, so that every cumulative figure there follows the ladder rather than two end points.

**CAPEX** (one-off, mostly Phase 0–1)

| Component | Estimate | Phase |
| --- | --- | --- |
| 2 GPU-class edge servers (N+1) | €16k | 0 |
| Broker witness + LoRaWAN server host, UPS, rack, PoE switching | €25k | 0 |
| Gate readers (6), if not supplied by the ticketing platform | €12k | 0 |
| Cameras, 110 incl. IR (55 primary in Phase 0, 55 secondary later) | €44k | 0 / 2 |
| Enclosure sensors (300 × €150) and anonymous counters (150 × €600, LiDAR/thermal) | €135k | 0–1 |
| LoRaWAN gateways (3) | €5k | 0 |
| DECT base stations and 40 handsets/pagers | €15k | 0 |
| Cabling, installation, site survey | €60k | 0 |
| **Total CAPEX** | **≈ €310k** (≈ €62k/yr over 5 years) | |

**OPEX** (per year)

| Component | At 5,000/day | At 15,000/day | Notes |
| --- | --- | --- | --- |
| Cloud: event backbone, databases, object storage, IoT ingestion, own-model hosting | €40k | €70k | Ingestion itself ≈ $600/yr ([capacity table](../hld/core/edge-and-connectivity.md#capacity-check-at-15000-visitorsday-by-traffic-class)) |
| Hosted LLMs + open-weight endpoint (planned spend) | €10k | €50k | Cap is 2% of revenue (≈ €600k at €30M); the plan sits far below the cap |
| Cellular (2 operators) + fixed-line fallback | €4k | €4k | |
| Ticketing platform fees (assumed €0.15/ticket or 1.5–3% of ticket revenue) | €225k | €675k | Largest line after the team; a selection criterion in [ADR-0012](../adrs/ADR-0012-ticketing-platform-adopt-not-build.md) |
| Team: 5 engineers, loaded | €500k | €500k | Does not grow with attendance — the point of adopt-not-build |
| Hardware maintenance and spares (10% of CAPEX) | €30k | €30k | |
| **Total OPEX** | **≈ €810k** | **≈ €1.33M** | |

**Per visitor** (CAPEX/5 + OPEX ÷ visitors/yr at 300 open days): ≈ **€0.58** at 5,000/day, ≈ **€0.31** at 15,000/day — inside NFR-COST-2 with the ±50% band. Ticketing fees and the team are ~85% of the total; the AI is not the expensive part.

## Architectural style

**Event-driven, edge-first, with bounded contexts** (Ticketing & Access, Park Operations, Animal Welfare, Guest Engagement) communicating through an event backbone. The four contexts are deployed as **one modular monolith** with private schemas and an outbox; AI components are **separate** consumers and producers on the same backbone, so they inherit the same asynchrony, retry and degradation properties as everything else — this is how we keep the "architectural characteristics of the additions" consistent with the base system ([ADR-0004](../adrs/ADR-0004-event-driven-backbone.md)).
