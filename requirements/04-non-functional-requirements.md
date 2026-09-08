# 04 · Non-Functional Requirements & Architectural Characteristics

## Driving characteristics (the ones that shape the architecture)

We chose four. Everything else is important but does not drive structure.

| Characteristic | Why it drives the design | Where it shows up |
| --- | --- | --- |
| **Resilience to connectivity loss** | Wi-Fi is patchy; the uplink will fail. Gates, safety alerts and data capture must work offline. | Edge-first design, store-and-forward, offline validation → [ADR-0001](../adrs/ADR-0001-edge-first-store-and-forward.md), [ADR-0011](../adrs/ADR-0011-offline-ticket-validation.md) |
| **Safety** | Poisonous animals + historic rides + families. Safety paths must be deterministic and local. | FR-3.6 tier-0 rules bypass cloud and ML; FR-3.7 model advisories only add to them → [ADR-0006](../adrs/ADR-0006-edge-vs-cloud-inference.md) |
| **Evolvability of the AI layer** | Models and providers will change faster than the estate. | Inference gateway; model governance (registry, evals, monitoring) → [ADR-0005](../adrs/ADR-0005-model-gateway-and-provider-independence.md) |
| **Cost-efficiency** | A poor estate with a small team. Cloud and AI spend must be bounded and visible. | Tiered model routing, per-capability budgets, edge inference for high-volume streams, adopt-not-build → [ADR-0005](../adrs/ADR-0005-model-gateway-and-provider-independence.md), [ADR-0006](../adrs/ADR-0006-edge-vs-cloud-inference.md), [ADR-0012](../adrs/ADR-0012-ticketing-platform-adopt-not-build.md) |

## Where the characteristics conflict, and what we paid

Four driving characteristics named side by side read as if they were compatible. They are not: **Resilience and Cost-efficiency pull in opposite directions on every line of the CAPEX table**, and a submission that does not say which one wins where has not made the decision, only listed the words.

**The order of precedence when two of them collide is Safety → Resilience → Evolvability of the AI layer → Cost-efficiency.** It is not a tie-break we invented for this table; it is the order the ADRs already resolve conflicts in, and it is why the numbers below look the way they do.

| Conflict | Who wins, and where exactly | What it cost | Decided in |
| --- | --- | --- | --- |
| **Safety vs. Cost-efficiency** | Safety, without argument. Alert delivery does not share a channel with anything else: DECT base stations and 40 handsets exist **only** because Wi-Fi and smartphones are not dependable enough for a poisonous-animal alert. | €15k CAPEX for a redundant delivery channel carrying ~100 messages a day — the worst cost-per-message in the estate, and the one line we would not cut. | [ADR-0001](../adrs/ADR-0001-edge-first-store-and-forward.md) §2, NFR-AVL-3, [alert chain](../hld/core/edge-and-connectivity.md#safety-alerts-from-sensor-to-a-human) |
| **Safety vs. Evolvability of the AI layer** | Safety, by **decoupling** rather than by compromise. Tier-0 rules never call a model, so the AI layer is free to change weekly precisely because nothing safety-critical is downstream of it. The AI layer's evolvability is *bought* by the safety layer's rigidity. | Some detection is deliberately duplicated: a tier-1 model advisory covers ground a rule already covers, and may never replace it (FR-3.7). We run two mechanisms where one would be cheaper. | [ADR-0006](../adrs/ADR-0006-edge-vs-cloud-inference.md), FR-3.6 / FR-3.7, [ADR-0005](../adrs/ADR-0005-model-gateway-and-provider-independence.md) §8 |
| **Resilience vs. Cost-efficiency** | Resilience wins **only where an outage stops the estate** — gates, safety, data capture: N+1 edge compute, a three-node broker with replicated queues, two SIMs from two operators, multi-zone event storage. Cost-efficiency wins **everywhere else**, and it wins hard: video never crosses the backhaul, features are aggregated at the edge, high-volume inference runs on our own models, generative calls are tiered and budgeted. | Redundancy that does nothing on a good day: the **second** edge server (≈ €8k of the €16k N+1 line), the witness node and UPS inside the €25k edge line, and the second operator's SIM in OPEX. Against it: edge aggregation is a **10× saving** on the same workload (≈ $50 vs. ≈ $520 a month, [capacity check](../hld/core/edge-and-connectivity.md#capacity-check-at-15000-visitorsday-by-traffic-class)) and adopt-not-build keeps the team flat at 5 while attendance triples. | [ADR-0001](../adrs/ADR-0001-edge-first-store-and-forward.md), [ADR-0002](../adrs/ADR-0002-mqtt-and-cellular-backhaul.md) §3, [ADR-0006](../adrs/ADR-0006-edge-vs-cloud-inference.md), [ADR-0012](../adrs/ADR-0012-ticketing-platform-adopt-not-build.md) |
| **Resilience vs. correctness (consistency)** | Resilience, with the loss **bounded, priced and admitted**: during an uplink outage a gate admits on signature plus local ledger, so a determined abuser can walk two people in on one ticket. We took that over refusing families at the gate. | The exceptions report, and a named upper bound on the abuse window rather than a guarantee against it. | [ADR-0011](../adrs/ADR-0011-offline-ticket-validation.md) §5 and its consequences |
| **Evolvability of the AI layer vs. Cost-efficiency** | Evolvability, but only in the **governance** half. The registry, eval gate, shadow runs and the monthly exercise of the secondary provider and open-weight bundle all cost inference money to keep a swap honest. The **runtime** half refuses to pay: we adopt an OSS gateway instead of building one. | Shadow mode roughly doubles a capability's inference cost for its 2-week window, and the monthly fallback exercise is spend that produces no user value. Both sit inside NFR-COST-1's budgets. | [ADR-0005](../adrs/ADR-0005-model-gateway-and-provider-independence.md) §6, [ADR-0008](../adrs/ADR-0008-ai-evaluation-and-production-monitoring.md) §3 |
| **Cost-efficiency vs. everything, at the top level** | Cost-efficiency loses the argument about *what* to build and wins the argument about *how* to build it. It never removes a capability; it decides that we adopt ticketing, adopt the gateway, adopt managed services, and self-host nothing. | ≈ 85% of OPEX is ticketing fees and the team — the two lines cost-efficiency cannot cut without changing what the estate is. The AI is not the expensive part, so squeezing it further would buy nothing. | [Cost model](#cost-model-tco-50), NFR-COST-2, R9 |

This table is the summary. The evaluation behind it — the utility tree of quality-attribute scenarios with their response measures, the architectural styles we rejected (including space-based, and why it solves a problem we do not have), the sensitivity and trade-off points, and the risks and **non-risks** — is in [hld/architecture-evaluation.md](../hld/architecture-evaluation.md).

## Full NFR list

| ID | NFR | Target |
| --- | --- | --- |
| NFR-AVL-1 | Gate validation availability (local) | 99.9% during opening hours, independent of uplink |
| NFR-AVL-2 | Ticket purchase availability (cloud) | 99.9% (ticketing platform SLA, [ADR-0012](../adrs/ADR-0012-ticketing-platform-adopt-not-build.md)) |
| NFR-AVL-3 | Safety alert delivery **to a human** | ≤ 5 s from sensor to a DECT handset/pager on the local network, no cloud dependency; **acknowledged by a human within 60 s** or escalated (head keeper, then all staff); measured end to end to the acknowledgement; unacknowledged alerts per day = 0 |
| NFR-RES-1 | Telemetry buffering during uplink loss | ≥ 24 h at edge without data loss (sized for 72 h, per traffic class) |
| NFR-RES-2 | Degraded mode | Every AI capability has a **non-AI fallback** — a rule-based system or a documented human procedure; loss of AI never blocks a core function |
| NFR-SCL-1 | Peak load | 15,000 visitors/day on average; a peak day ≈ 29,400 visitor-days with ≈ 5,900 arrivals and ≈ 2,940 gate scans in the peak hour (2 persons per scan, A14 — [capacity check](08-business-case.md#1-capacity-reality-check)); 40 rides + 55 enclosures streaming telemetry |
| NFR-SCL-2 | Camera ingest | 55 enclosures × 1–2 cameras; pre-filtered at edge; only 1-minute feature windows and event clips leave the estate |
| NFR-PRF-1 | Companion response time, **by request class** | FAQ answer: p95 ≤ 3 s complete. Day planning: first token ≤ 2 s, first stop suggestion ≤ 5 s, full plan ≤ 15 s (p95, streamed); re-plan after a closure ≤ 5 s. Verified by a load test at 500 concurrent sessions before each promotion |
| NFR-PRF-2 | Dashboard freshness | Live view ≤ 60 s behind reality when uplink is up |
| NFR-ACC-1 | **Digital accessibility of visitor-facing surfaces** (companion, kiosks, purchase flow) | WCAG 2.2 level AA on the pages and flows a visitor uses: keyboard-navigable, screen-reader-labelled, contrast ≥ 4.5:1, no colour-only meaning, target size and focus visible. Automated axe-core checks in CI gate every release; one manual screen-reader pass per phase; the companion's answers must be usable read aloud — no meaning carried by layout or emoji alone (the same rule the [daily report](../hld/core/README.md#estate-daily-report) already follows for *provisional*) |
| NFR-LNG-1 | **Languages of the companion and the purchase flow** | UI, knowledge base and companion answers in the estate's national language plus English at launch, plus the two largest inbound-visitor languages from Phase 2 (chosen from the exit survey, A14). **Safety- and money-critical facts are looked up per language, never machine-translated at answer time**: age/height limits, "may I touch/feed", allergens, prices and hours exist as human-approved fields per language, so the model composes around them in the visitor's language but cannot restate them ([ADR-0010](../adrs/ADR-0010-grounded-llm-with-guardrails.md) §2). A language with no approved safety field for a subject falls back to the info point rather than to a translation |
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
| Hosted LLMs + open-weight endpoint (planned spend) | €10k | €50k | **Token arithmetic behind the €50k: ≈ €34,300/yr** of model calls at 15,000/day, plus the standing open-weight endpoint and the ±50% headroom — [what the generative capabilities cost](../hld/ai-platform/README.md#what-the-generative-capabilities-cost). Phase 1 runs FAQ answers only; day planning arrives in Phase 2, which is what grows the line. Cap is 2% of revenue (≈ €600k at €30M); the plan sits far below the cap |
| Cellular (2 operators) + fixed-line fallback | €4k | €4k | |
| Ticketing platform fees (assumed €0.15/ticket or 1.5–3% of ticket revenue) | €225k | €675k | Largest line after the team; a selection criterion in [ADR-0012](../adrs/ADR-0012-ticketing-platform-adopt-not-build.md) |
| Team: 5 engineers, loaded | €500k | €500k | Does not grow with attendance — the point of adopt-not-build |
| Hardware maintenance and spares (10% of CAPEX) | €30k | €30k | |
| **Total OPEX** | **≈ €810k** | **≈ €1.33M** | |

**Per visitor** (CAPEX/5 + OPEX ÷ visitors/yr at 300 open days): ≈ **€0.58** at 5,000/day, ≈ **€0.31** at 15,000/day — inside NFR-COST-2 with the ±50% band. Ticketing fees and the team are ~85% of the total; the AI is not the expensive part.

## Architectural style

**Event-driven, edge-first, with bounded contexts** (Ticketing & Access, Park Operations, Animal Welfare, Guest Engagement) communicating through an event backbone. The four contexts are deployed as **one modular monolith** with private schemas and an outbox; AI components are **separate** consumers and producers on the same backbone, so they inherit the same asynchrony, retry and degradation properties as everything else — this is how we keep the "architectural characteristics of the additions" consistent with the base system ([ADR-0004](../adrs/ADR-0004-event-driven-backbone.md)).
