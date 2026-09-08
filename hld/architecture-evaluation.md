# Architecture evaluation (ATAM-style)

The [driving characteristics](../requirements/04-non-functional-requirements.md#driving-characteristics-the-ones-that-shape-the-architecture) name what matters; the [conflict table](../requirements/04-non-functional-requirements.md#where-the-characteristics-conflict-and-what-we-paid) settles who wins when two collide. This document holds the evaluation: quality-attribute scenarios with response measures, the styles we rejected, and the sensitivity points, trade-off points, risks and non-risks that came out of it.

ATAM proper is a facilitated workshop with stakeholders in the room, and the brief gives us none. So the elicitation half is an assumption we state: the scenarios come from the brief, the goals and the risk register, and their priorities are ours. Every response measure is an existing NFR, game day or eval gate.

## Utility tree

Priority is `(importance to the estate, difficulty for us)` on H/M/L. `(H, H)` and `(H, M)` are where the architecture had to decide something.

| Quality attribute | Refinement | Scenario: stimulus → environment | Response measure | Prio | Verified by |
| --- | --- | --- | --- | --- | --- |
| **Resilience** | Uplink | Both SIMs fail for 4 h during opening hours | Gates admit; tier-0 fires; critical event loss 0; buffer drains in ≤ 2 h | (H, M) | [GD-1](core/resilience-validation.md), NFR-RES-1 |
| | Uplink | Outage outstrips the 72 h buffer | Overflow policy holds: clips dropped first, telemetry oldest-first, critical never | (M, M) | GD-2 |
| | Broker | Primary broker node dies in the opening peak | Failover ≤ 30 s; message loss 0; gate scan p95 unchanged | (H, M) | GD-3 |
| | Gates | A reader is cut off from the broker on a capacity-managed day | Admission continues on signature + cached lists; slot reservation honoured offline; reconciliation exceptions < 0.1% | (H, H) | GD-4, [ADR-0011](../adrs/ADR-0011-offline-ticket-validation.md) |
| | Edge compute | One of two edge nodes is lost | Tier-0 unaffected; the survivor carries all streams at degraded fps; **masking never degraded**; unmasked frames stored 0 | (H, M) | GD-7, [compute budget](core/edge-and-connectivity.md#edge-compute-budget) |
| | Recovery | A system of record is lost and must be restored | RPO ≤ 15 min, RTO ≤ 4 h; read models rebuilt by replay | (H, M) | GD-13, NFR-DR-1 |
| **Safety** | Alert to a human | Enclosure door opens without a badge, uplink *and* staff Wi-Fi down, nobody acknowledges | Delivery p99 ≤ 5 s on DECT; escalation at 60 s and 120 s; unacknowledged alerts 0 | (H, H) | GD-6, NFR-AVL-3 |
| | Model on a safety path | The vision model is wrong about aggression near visitors | Advisory only; never the sole alert path; never delays a tier-0 rule | (H, L) | FR-3.7, [ADR-0006](../adrs/ADR-0006-edge-vs-cloud-inference.md) |
| | Lying hardware | A feed scale wedges at a plausible weight and keeps heart-beating | Stuck detected within 3 × reporting interval; anomaly suppressed with the reason shown; "rule cannot evaluate" alerted | (H, M) | GD-16, [sensor health](core/edge-and-connectivity.md#sensor-health-dead-stuck-and-drifting) |
| | Generated safety facts | A visitor asks "can we touch the frog?" | The fact is inserted verbatim from a structured field per language; the model cannot restate it; safety refusals 100% at promotion | (H, M) | [ADR-0010](../adrs/ADR-0010-grounded-llm-with-guardrails.md) §2, NFR-LNG-1 |
| **Evolvability of the AI layer** | Model swap | A better model appears for a capability | Registry PR + eval gate; ≤ 1 day; zero business-service changes | (H, M) | NFR-EVO-1, OKR 5.2 |
| | Provider loss | The primary LLM provider is unreachable or gone | Automatic failover to provider B, then the open-weight endpoint; the last rung is exercised monthly, not assumed | (H, M) | GD-9, [ADR-0005](../adrs/ADR-0005-model-gateway-and-provider-independence.md) §6 |
| | New capability | A sixth AI use case is added | A new consumer on the backbone; no producer changes; no shared schema | (M, L) | [ADR-0004](../adrs/ADR-0004-event-driven-backbone.md) §3 |
| | Structural change | A module must leave the monolith | Extraction criteria already met by private schemas, outbox and inbox; no data untangling | (M, H) | ADR-0004 §7–8 |
| | Trust in a new model | A promoted bundle turns out worse in production | Guardrail trip → automatic rollback to the previous bundle; ECE and per-band calibration re-measured | (H, M) | [ADR-0008](../adrs/ADR-0008-ai-evaluation-and-production-monitoring.md), [gated metrics](ai-platform/README.md#how-the-gated-metrics-are-defined) |
| **Cost-efficiency** | Growth | Attendance triples to the target run rate | OPEX(V) stays linear and the team stays at 5; ≤ €0.50 per visitor at 15,000/day | (H, M) | NFR-COST-2, [cost model](../requirements/04-non-functional-requirements.md#cost-model-tco-50) |
| | Provider pricing | A provider doubles its prices | Per-capability budget, tiered routing, automatic downgrade at 100% of budget | (H, L) | NFR-COST-1, R4 |
| | Generative growth | Companion adoption reaches 60% of households | ≈ €0.04 per companion household visit; caches keep the bill inside the OPEX line, a peak day is 2.0× an average one | (M, M) | [generative cost](ai-platform/README.md#what-the-generative-capabilities-cost) |
| | Video | 110 camera streams must be analysed continuously | Video never crosses the backhaul; features aggregated at the edge — 10× cheaper than raw 1 Hz | (H, M) | [capacity check](core/edge-and-connectivity.md#capacity-check-at-15000-visitorsday-by-traffic-class) |

## Architectural styles considered

Scored against the four driving characteristics plus operability, which for a team of five is a characteristic in all but name (NFR-OPS-1).

| Style | Resilience to connectivity loss | Safety | Evolvability of the AI layer | Cost & operability at 5 engineers | Verdict |
| --- | --- | --- | --- | --- | --- |
| **Layered monolith, synchronous, no event log** | Poor — telemetry arrives synchronously or not at all; an outage is data loss | Adequate if safety stays local, but the local tier is then a second system with no shared model | Poor — an AI addition is a change to the monolith; no replay, so no backtesting on real history | Best on day one, worst by Phase 2 | **Rejected**: no replay means no retraining data and no read-model rebuild |
| **Synchronous microservices (REST between contexts)** | Poor — temporal coupling; a slow AI call slows ticketing; retries cascade | Neutral | Moderate — services are separable, but every consumer is a call someone must make | Poor — distributed debugging from day one for five people | **Rejected** ([ADR-0004](../adrs/ADR-0004-event-driven-backbone.md) alternatives): resilience and evolvability both lose |
| **Event-driven microservices, one deployable per context** | Good | Good | Good | Poor — four services plus AI workers, ingestion and the edge tier; no context needs independent scaling at 15,000/day | **Rejected on operability alone.** The extraction criteria in ADR-0004 §7 are the path here if that changes |
| **Space-based (in-memory data grid, replicated processing units)** | Good against *node* loss, irrelevant against *uplink* loss, which is our failure mode | Neutral | Neutral | Poor — a grid to operate | **Rejected**: it addresses throughput we do not have. The estate peaks at ≈ 19 msg/s and ≈ 2,940 gate scans in the peak hour; the binding constraint is connectivity |
| **Event-driven, edge-first, modular monolith + separate AI/edge deployables (chosen)** | Best — store-and-forward at the edge, replayable log in the cloud, gates and safety local by construction | Best — tier-0 is deterministic, local, and structurally decoupled from every model | Good — AI components are ordinary consumers; capability boundary hides the model | Good — one business deployable, managed services, adopt-not-build | **Chosen.** Its cost is eventual consistency, an outbox and inbox to run, and two deployment targets |

The chosen style is a hybrid: edge-first on the estate, event-driven between contexts, a modular monolith as the deployment unit, separate deployables only where the runtime differs (GPU, edge, ingestion). Each part is decided in [ADR-0001](../adrs/ADR-0001-edge-first-store-and-forward.md), [ADR-0004](../adrs/ADR-0004-event-driven-backbone.md) and [ADR-0006](../adrs/ADR-0006-edge-vs-cloud-inference.md).

## Sensitivity points

One parameter, one attribute that moves sharply with it.

| # | Parameter | The attribute it moves | Why it is sensitive |
| --- | --- | --- | --- |
| SP-1 | Edge buffer size and per-class disk quota | Resilience | 32 GB per node holds ≈ 3 GB per 72 h today. Halve the quota or double the telemetry and the overflow policy starts dropping on a normal outage instead of an exceptional one |
| SP-2 | Confidence band boundaries | Safety **and** the vet's hours | Widening the medium band catches more sick animals and fills the review queue; the [human roles table](ai-platform/README.md#humans-in-the-loop-who-does-what) is the constraint, not the model |
| SP-3 | Cacheable share of the session prefix | Cost-efficiency | Prompt caching is ≈ half the generative bill: €34,300 with it, €67,100 without. A prompt refactor that breaks prefix stability is a cost incident |
| SP-4 | Persons admitted per gate scan (A14) | Resilience of the gate path | Gate lanes hold 5,400 scans/h against ≈ 2,940 in the peak hour **at 2 persons per scan**. At 1.2 persons per scan the same peak hour needs ≈ 4,900 scans — a 9% margin instead of 45%, and the exit survey (A14) is what measures it |
| SP-5 | Companion adoption rate | Growth **and** generative cost | One number drives both the flywheel in [08 §3](../appendix/business-case-model.md#3-the-membership-flywheel) and the token bill, so success on one is spend on the other |
| SP-6 | Normal-operation GPU share per edge node | Cost (a third node) | The rule is a third node when normal operation exceeds 50% per node; today it is 35% |
| SP-7 | Spreading-factor distribution (LoRaWAN) | Resilience of telemetry | A 4× airtime error (SF7 → SF10) changes gateway count and battery life; the whole airtime budget rests on an unmeasured assumption until the site survey |

## Trade-off points

One decision, two attributes moving in opposite directions. Each is a judgement, not an arithmetic.

| # | Decision | Gains | Gives up | Decided in |
| --- | --- | --- | --- | --- |
| TP-1 | Inference at the edge rather than in the cloud | Resilience (works offline), cost (video never leaves), privacy (masking before storage) | Evolvability of *those* models: a new version is an artifact pull over a rate-limited downlink, not a registry flip | [ADR-0006](../adrs/ADR-0006-edge-vs-cloud-inference.md), GD-12 |
| TP-2 | Human review via confidence bands | Safety and a labelling loop that costs no separate team | Latency to action (queue SLA 4 h → 1 h) and a hard ceiling set by vet hours | [ADR-0007](../adrs/ADR-0007-human-in-the-loop-confidence-bands.md), R13 |
| TP-3 | Modular monolith as the deployment unit | Operability and cost for five engineers; transactions stay local | Independent scaling and independent release cadence per context, until a module is extracted | [ADR-0004](../adrs/ADR-0004-event-driven-backbone.md) §7 |
| TP-4 | Offline gate validation | Availability at the gate during an outage (NFR-AVL-1) | Correctness: a determined abuser walks two people in on one ticket, bounded and reported rather than prevented | [ADR-0011](../adrs/ADR-0011-offline-ticket-validation.md) |
| TP-5 | Adopt the ticketing platform | Cost, operability, PCI scope out of our estate | Control: 13 must-have criteria become a procurement dependency, and a missing one changes Phase 0 scope | [ADR-0012](../adrs/ADR-0012-ticketing-platform-adopt-not-build.md), [TODOS.md](../TODOS.md) |
| TP-6 | Tiered model routing | Cost — the cheap tier answers the majority of questions | Uniformity: two tiers means two behaviours behind one capability, so the factuality and safety gates must pass on **both** bundles, not the better one | [ADR-0005](../adrs/ADR-0005-model-gateway-and-provider-independence.md) §4, [ADR-0008](../adrs/ADR-0008-ai-evaluation-and-production-monitoring.md) |
| TP-7 | Aggregating features at the edge to 1-minute windows | Cost (10×) and bandwidth | Analytical freedom: a question that needs raw 1 Hz history cannot be asked retrospectively — only the ±5 min around candidate events is kept | [capacity check](core/edge-and-connectivity.md#capacity-check-at-15000-visitorsday-by-traffic-class), S1 |

## Risks and non-risks

**Risks**, each carried in [requirements/07](../requirements/07-risks-and-mitigations.md) or TODOS with an owner:

- **The vendor combination may not exist.** Adopt-not-build was decided on criteria, not on market facts; 13 must-haves together may be rare. The fallback matrix is a prerequisite for Phase 0, not a footnote (R9, [TODOS.md](../TODOS.md)).
- **Calibration depends on label volume we do not have yet.** The per-band calibration gate is only as good as the golden set behind it, and the golden set is built by the vet in Phase 1 (R2, R3, R13).
- **Attribution is not provable.** The payback case rests on incremental visitor-days credited to the platform; only the nudged-vs-control cohort and the S5 discounted blocks are clean measurements (R20).
- **The estate's physical capacity binds before the software does.** Not an architectural risk, and named as such: parking and lunch seating in year 1 (R17).
- **One unmeasured radio assumption** underneath the whole telemetry budget (SP-7, site survey in TODOS).

**Non-risks**, analysed and closed:

- **Throughput.** ≈ 19 msg/s, ≈ 1.0 GB/day, ≈ 0.1 Mbps average uplink. Nothing in the estate is throughput-bound, which is why no part of the design pays for scale-out.
- **The broker as a single point of failure.** Three nodes with replicated persistent queues, a message acknowledged only after a second node holds it (NFR-DR-3, GD-3).
- **Gate lane capacity at the target run rate.** 6 lanes × 900 scans/h = 5,400 against ≈ 2,940 in the peak hour — with the caveat in SP-4.
- **Runaway generative cost.** Bounded three ways: token arithmetic with a counterfactual, per-capability monthly budgets with automatic downgrade, and a peak day that is 2.0× an average one rather than an order of magnitude.
- **AI in a safety-critical path.** Structural, not policed: tier-0 rules run on the broker with no model in the path, and model advisories use a separate channel (FR-3.6, FR-3.7).
