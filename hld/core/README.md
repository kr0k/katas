# Core Platform (non-AI foundation)

The foundation the AI scenarios stand on: edge tier, connectivity, ticketing, event backbone, data platform.

## Design principles

1. **Edge-first.** Anything that keeps people safe or lets them in works on the estate's local network without the cloud. → [ADR-0001](../../adrs/ADR-0001-edge-first-store-and-forward.md)
2. **Events, not calls.** Contexts exchange facts through an event backbone; consumers can be added (e.g. an AI model) without changing producers. Deployment is a separate question: the four business contexts ship as **one modular monolith**, AI consumers and batch workers as separate deployables. → [ADR-0004](../../adrs/ADR-0004-event-driven-backbone.md)
3. **Managed where it doesn't differentiate — adopted where it is a commodity.** Databases, message brokers, object storage and model hosting are managed services; ticketing is an adopted platform; the team of five builds business logic and models. → [ADR-0003](../../adrs/ADR-0003-cloud-provider-selection.md), [ADR-0012](../../adrs/ADR-0012-ticketing-platform-adopt-not-build.md)
4. **Open protocols at the boundaries.** MQTT, HTTPS, OpenTelemetry, Parquet/Iceberg — so we can leave.
5. **Broken on purpose, on a schedule.** A game-day catalogue with metrics and owners verifies the foundation, as evaluation gates verify the AI. → [Resilience validation](resilience-validation.md)

## Container view

```mermaid
flowchart TB
    subgraph Estate["🏰 Estate — local network"]
        direction TB
        GateDev["Gate readers<br/>(QR/NFC — ticketing platform's or ours)"]
        Counters["Footfall / queue counters<br/>(LiDAR/IR, anonymous)"]
        Encl["Enclosure sensors<br/>(scales, water, climate, door contacts, PIR/beam)"]
        Cams["Enclosure cameras"]
        EdgeAI["🤖 Edge inference nodes (2, N+1)<br/>visitor masking · S1 features (1-min windows) · S2 counting<br/>tier-1 safety advisory"]
        LNS["LoRaWAN network server<br/>(join server, decode → MQTT)"]
        Broker["MQTT broker cluster (3 nodes)<br/>replicated queues per traffic class<br/>retained downlink snapshots"]
        GateSvc["Gate validation<br/>(local, offline-capable)"]
        Rules["Tier-0 safety rules<br/>(deterministic, no ML)"]
        Pager["DECT handsets / pagers<br/>(primary alert channel, ack)"]
        StaffDev["Staff smartphones<br/>(secondary, local Wi-Fi)"]

        GateDev <--> GateSvc
        GateSvc -.-> Broker
        Broker -. "allow/revocation<br/>snapshots" .-> GateSvc
        Counters -. "LoRaWAN" .-> LNS
        Encl -. "LoRaWAN / wired" .-> LNS
        Encl -.-> Broker
        LNS -.-> Broker
        Cams --> EdgeAI
        EdgeAI -.-> Broker
        Broker -.-> Rules
        Rules --> Pager
        Rules --> StaffDev
        Pager -. "ack" .-> Broker
        EdgeAI -. "advisory" .-> StaffDev
    end

    subgraph Cloud["☁️ Cloud"]
        direction TB
        Ingest["IoT ingestion gateway<br/>(device auth, schema validation, dedupe;<br/>bridge terminates here, both directions)"]
        Bus["Event backbone<br/>(topics per context, schema registry)"]
        Ingest -.-> Bus

        subgraph Mono["Business monolith — one deployable, four modules"]
            Tix["Ticketing & Access<br/>(anti-corruption layer to the ticketing platform and POS)"]
            Ops["Park Operations<br/>+ Estate daily report (read model)"]
            Welfare["Animal Welfare"]
            Guest["Guest Engagement"]
        end
        Bus -.-> Mono
        Mono -. "outbox" .-> Bus

        subgraph Workers["Separate deployables"]
            AICons["🤖 AI consumers<br/>(S1 anomaly scoring)"]
            Batch["🤖 GPU / batch workers<br/>(training · S3 forecasts · S5 elasticity)"]
        end
        Bus -.-> AICons
        AICons -.-> Bus
        Batch -.-> Bus

        Down["Downlink publisher<br/>lists · policies · desired model versions"]
        Down -.-> Ingest

        API["API gateway / BFF"]
        Web["Visitor web & mobile"]
        OpsUI["Ops & vet dashboards"]
        Countess["👑 Countess & management<br/>daily report (mobile, e-mail copy)"]
        Web --> API
        OpsUI --> API
        Countess --> API
        API --> Mono

        subgraph DataP["Data platform"]
            Raw[("Raw / bronze")]
            Cur[("Curated / silver-gold")]
            Feat[("Feature store")]
            Vec[("Knowledge base<br/>(vector + structured)")]
            Store[("Object storage<br/>(model artifacts, signed)")]
        end
        Bus -.-> Raw --> Cur --> Feat
        Cur --> Vec

        AIP["🤖 AI platform<br/>(see ai-platform/)"]
        Mono --> AIP
        AICons --> AIP
        Batch --> AIP
        Feat --> AIP
        Vec --> AIP
        AIP --> Store
        AIP -.-> Down
        Tix -.-> Down
    end

    TixSaaS(["Ticketing platform (SaaS)<br/>catalogue · checkout · passes · credentials · accounts<br/>timed entry & daily cap · upgrade credit"])
    POS(["POS / commerce<br/>(the platform's own, or a separate system — A13)"])
    Pay(["Payment provider"])
    POS -. "purchases: signed webhooks" .-> Tix
    POS --> Pay
    HR(["HR / rostering system<br/>staff · skills · certifications · availability"])
    Ops <-- "import staff data / export approved plans" --> HR

    Broker -. "uplink: MQTT bridge over cellular<br/>critical → telemetry → clips" .-> Ingest
    Ingest -. "downlink: retained snapshots + sequenced deltas" .-> Broker
    Store -. "model artifacts: HTTPS pull,<br/>rate-limited, off-hours, resumable" .-> EdgeAI
    Tix <-- "API / webhooks" --> TixSaaS
    TixSaaS --> Pay
```

Legend: see [hld/README.md](../README.md#diagram-legend-used-in-every-diagram). Both directions of the bridge are designed: uplink (store-and-forward) and downlink (retained snapshots, model pull) are described in [Edge & connectivity](edge-and-connectivity.md#downlink-cloud--estate).

## Containers

| Container | Responsibility | Runs where | Notes |
| --- | --- | --- | --- |
| **Gate validation** | Verifies the ticket signature offline, checks the local used-ledger, applies allow/revocation snapshots arriving over the downlink; records entry/exit; reconciles with the cloud when connected | Estate | Vendor readers/SDK that pass [ADR-0011](../../adrs/ADR-0011-offline-ticket-validation.md), or our readers with the vendor SDK ([ADR-0012](../../adrs/ADR-0012-ticketing-platform-adopt-not-build.md) §3) |
| **MQTT broker cluster** | Local pub/sub for all devices; three nodes with replicated persistent queues, one queue and bridge connection per traffic class; bridges uplink when connected; holds retained downlink snapshots for reconnecting consumers | Estate | Cluster-capable broker class → [ADR-0002](../../adrs/ADR-0002-mqtt-and-cellular-backhaul.md) §3; 72 h buffer sized in [Edge & connectivity](edge-and-connectivity.md#capacity-check-at-15000-visitorsday-by-traffic-class); 32 GB per node |
| **LoRaWAN network server** | Join server and network/application server for battery sensors and counters: OTAA joins, per-device session keys, payload decode, republish into per-device MQTT topics; collects SF histogram and per-gateway loss | Estate | OSS container (ChirpStack class); three gateways → [ADR-0002](../../adrs/ADR-0002-mqtt-and-cellular-backhaul.md) |
| **Edge inference nodes** | Mask visitors in frame; extract S1 features and aggregate them to 1-minute windows (raw 1 Hz only around events, with the clip); count piranhas (S2); raise tier-1 safety advisories | Estate | Two GPU-class servers sized N+1 with a degradation rule ([compute budget](edge-and-connectivity.md#edge-compute-budget)); models pulled from object storage, rate-limited and off-hours → [ADR-0006](../../adrs/ADR-0006-edge-vs-cloud-inference.md) |
| **Tier-0 safety rules** | Deterministic, no ML, no cloud: enclosure door contact open without keeper badge; water/climate out of band; PIR/beam motion in a dry zone → DECT handsets/pagers within seconds, smartphones in parallel; acknowledgement within 60 s or escalation to head keeper, then all staff | Estate | FR-3.6; NFR-AVL-3 is measured on this path, to a human ack ([alert chain](edge-and-connectivity.md#safety-alerts-from-sensor-to-a-human)). Tier-1 model advisories (FR-3.7) come from the edge node, use the secondary channel and only add to it |
| **IoT ingestion gateway** | Terminates the MQTT bridge in both directions: authenticates, validates schemas and de-duplicates uplink; delivers downlink snapshots | Cloud | Managed IoT service |
| **Event backbone** | Durable topics per bounded context; schema registry whose CI check rejects personal-data fields; replayable | Cloud | Managed streaming → [ADR-0004](../../adrs/ADR-0004-event-driven-backbone.md) |
| **Business monolith** | One deployable, four modules with private schemas and a transactional outbox to the backbone — [modules below](#modules-of-the-business-monolith) | Cloud | Serverless containers; extraction criteria → [ADR-0004](../../adrs/ADR-0004-event-driven-backbone.md) |
| **AI consumers** | Stateless consumers that score events with our own models (S1 anomaly scoring against baselines) and publish results back | Cloud | Separate deployable: scales with event rate, released with model promotions, not with the monolith |
| **GPU / batch workers** | Training pipelines; scheduled S3 forecasts; S5 elasticity estimation | Cloud | Managed batch/GPU; bursty, scheduled |
| **Downlink publisher** | Publishes retained snapshots and sequenced deltas of allow/revocation lists, policy parameters (bands, prices, hours) and desired edge model versions to the bridge | Cloud | [Edge & connectivity → Downlink](edge-and-connectivity.md#downlink-cloud--estate) |
| **API gateway / BFF** | AuthN/Z, rate limiting, aggregation for web/mobile/dashboards | Cloud | |
| **Data platform** | Lakehouse: raw → curated → features; knowledge base for the companion; object storage for signed model artifacts | Cloud | Open table format for portability |
| **Ticketing platform (SaaS)** | External: catalogue, checkout and payments, passes, credentials, opt-in accounts, timed-entry slots, daily cap and pass-holder reservations, upgrade credit vouchers, sales reconciliation | Vendor | [ADR-0012](../../adrs/ADR-0012-ticketing-platform-adopt-not-build.md); PCI scope stays here |
| **POS / commerce** | External: F&B, retail and parking sales on the estate; per-transaction webhooks or export with the FR-2.6 fields; end-of-day totals for reconciliation | Vendor (the ticketing platform's own POS, or a separate system — A13) | Behind the same anti-corruption layer; never card data (NFR-SEC-2); R16 |
| **Estate daily report** | Read model inside Park Operations: one screen of "how was today" for the Countess at 21:00, numbers verbatim, one rule-selected recommendation for tomorrow; optional phrasing by the S1 drafter capability after ops-manager approval | Cloud (monolith) | FR-2.7; not an AI scenario — [details below](#estate-daily-report) |

### Modules of the business monolith

| Module | Owns |
| --- | --- |
| **Ticketing & Access** | Anti-corruption layer: vendor and POS webhooks → our events including `PurchaseRecorded`, behind signature, replay and PII checks ([purchases, cap and upgrade credit](#ticketing--access-additions-purchases-cap-and-upgrade-credit)). Outbound: `PriceUpdated`, cap settings and erasure to the vendor API; gate list deltas to the downlink |
| **Park Operations** | Zone and ride model; occupancy and queue read models including average dwell; staffing plans; labour-rule policy store; adapter to the HR/rostering system (A12); the [Estate daily report](#estate-daily-report) read model |
| **Animal Welfare** | Animal and enclosure registry; feeding log; review queue; treatments, published as `TreatmentStarted` / `TreatmentClosed`; population ledger and estimates |
| **Guest Engagement** | Companion sessions; itineraries; nudges including the pass-upgrade prompt; pricing recommendation orchestration; per-subject key store |

## Deployment units

Deployment unit ≠ bounded context ([ADR-0004](../../adrs/ADR-0004-event-driven-backbone.md)). Six things are deployed:

| Unit | Contains | Why it is separate |
| --- | --- | --- |
| Business monolith | Four context modules, outbox relay, APIs behind the BFF | One thing to deploy and watch for a team of five; transactions stay inside a module; modules talk through events or published interfaces only |
| AI consumers | S1 scoring (more as scenarios arrive) | Scale with event rate; restart and roll back on model promotion without touching the monolith |
| GPU / batch workers | Training, forecasts, elasticity | Different runtime (GPU), bursty and scheduled |
| IoT ingestion + downlink publisher | Bridge termination both ways | Managed IoT service; must keep running while the monolith deploys |
| Edge tier | Broker cluster, gate validation, tier-0 rules, edge inference nodes, LoRaWAN network server and gateways, DECT base stations | On the estate; reconciled by GitOps from the same repositories |
| Ticketing platform | SaaS | Adopted, not deployed ([ADR-0012](../../adrs/ADR-0012-ticketing-platform-adopt-not-build.md)) |

A module leaves the monolith only when it meets an extraction criterion in ADR-0004 (independent scaling, blocking release cadence, different runtime, different owning team). Nothing at 15,000 visitors/day meets one today.

## Data platform

- **Raw:** every event as received, immutable, partitioned by day — the audit trail and the source for retraining.
- **Curated:** zone occupancy per 5 min, queue lengths, feeding per animal per day, enclosure climate, ticket sales, pass usage; **spend per zone per day** — Park Operations maps `pos_terminal_id` → zone in its own policy config, so the `PurchaseRecorded` event never carries another context's zone model; **daily report snapshots**, one per date, kept 3 years.
- **Feature store:** the same features served to training and to online inference (footfall lags, weather, calendar, per-animal baselines) so models are not trained on one thing and served another.
- **Knowledge base:** structured facts (animals, rides, opening hours, safety rules, prices) plus curated narrative content; the *only* source the companion may cite → [ADR-0010](../../adrs/ADR-0010-grounded-llm-with-guardrails.md).
- **Personal data: none here by construction.** Events carry pseudonymous subject ids, never names, contacts or device identifiers; the schema registry's CI check enforces it ([ADR-0004](../../adrs/ADR-0004-event-driven-backbone.md) §6). The few unavoidable personal fields are encrypted with a per-subject key and **crypto-shredded** on erasure; a `SubjectErased` event removes the subject from read models, the feature store and golden sets ([ADR-0009](../../adrs/ADR-0009-visitor-privacy-anonymous-counting.md) §7).

## Consumer-side idempotency: the inbox

At-least-once delivery means every consumer eventually sees a duplicate: after a broker failover, an ingestion retry, a replay, or a re-signed vendor backlog. The outbox side is specified in [ADR-0004](../../adrs/ADR-0004-event-driven-backbone.md) §7; this is the consuming mirror.

**The invariant.** A consumer applies an event's effect and records it as handled in **one local transaction**. That record is the inbox: `(consumer_id, event_id)` plus a handled-at timestamp, in the module's private schema. `event_id` is the derived id every consumer keys on — UUIDv5 over `(device_id, boot_id, seq)` for device events ([ADR-0001](../../adrs/ADR-0001-edge-first-store-and-forward.md) §4), the transaction id for POS webhooks, the backbone's event id otherwise. Payload content is never a dedup key.

| Consumer | Key it dedupes on | Window | The effect, and why a replay is harmless |
| --- | --- | --- | --- |
| Monolith modules (read models: occupancy, queues, spend, welfare timeline, [daily report](#estate-daily-report)) | `(module, event_id)`, private schema | 7 days, as the ingestion window | Effect and inbox row commit together. Outside the window the read model is rebuilt by replay — a full recompute, not an increment |
| AI consumers (S1 anomaly scoring) | `(capability, bundle_version, event_id)` | 7 days | Same window scored twice yields the same `WelfareAnomalyDetected`. The bundle version is in the key so a promoted model re-scores instead of being deduplicated away |
| Guest Engagement on `SubjectErased` | `(consumer, subject_id)` — the subject, not the event | Permanent tombstone | `DELETE` the per-subject key, then re-key read models, feature store and golden sets by subject id. A second delivery finds nothing and is a no-op; GD-11's audit query proves it |
| Ticketing & Access on vendor and POS webhooks | `transaction_id` (POS), credential id + operation (ticketing) | 7 days | Signature verified, then dedup *before* the outbox write, so a replay never becomes an event ([purchases](#ticketing--access-additions-purchases-cap-and-upgrade-credit), GD-14) |
| Downlink publisher | Snapshot id + sequence number | Latest snapshot | Retained snapshots are idempotent: a consumer re-applies the snapshot it holds and detects gaps by sequence ([downlink](edge-and-connectivity.md#downlink-cloud--estate)) |

**Effects that leave the transaction.** A vendor API call, e-mail or push cannot join a local transaction. Sequence: write the inbox row as *in-flight* with an idempotency key derived from `event_id` and commit; make the external call with that key; commit *done*. A crash between the call and the second commit repeats the call with the same key and the receiver collapses it — hence "accepts an idempotency key on writes" as a vendor criterion ([ADR-0012](../../adrs/ADR-0012-ticketing-platform-adopt-not-build.md)). An external effect can therefore happen twice only if the receiver ignores the key, which the fallback matrix covers.

**Enforcement.** The fitness function that forbids cross-module schema access also fails a subscription handler that writes without an inbox row in the same transaction. Every consumer's tests replay their fixture stream twice and assert identical read-model state and side-effect counts. GD-8 measures `idempotency violations = 0` after an outage and replay; GD-11 covers the erasure tombstone.

## Ticketing & Access additions: purchases, cap and upgrade credit

The business case asks the foundation to carry three things. All are executed by the adopted platform and enter our world through the Ticketing & Access anti-corruption layer; none changes a deployment unit, a safety tier or gate validation.

| What | What the architecture fixes | Executed by |
| --- | --- | --- |
| **On-site spend (FR-2.6)** | POS transactions arrive as signed webhooks; the layer verifies the signature, dedupes on transaction id for 7 days, rejects any event whose runtime values hit the PII deny-list, and writes `PurchaseRecorded` to the outbox with no subject unless purchase-history consent covers it ([ADR-0009](../../adrs/ADR-0009-visitor-privacy-anonymous-counting.md) §7). Backpressure answers 429 and slows the vendor; the dead-letter queue holds only invalid events | POS: the ticketing platform's own or a separate system (A13) |
| **Timed entry and daily cap (FR-1.7)** | The cap is policy config, applied through the vendor API and published as `CapacityCapChanged` (who / when / why / old / new). It acts on unsold tickets only; gate validation is untouched. Pass holders reserve a timed slot carried as a credential attribute, validated offline ([ADR-0011](../../adrs/ADR-0011-offline-ticket-validation.md)) | Vendor cap and reservation API |
| **Upgrade credit voucher (P-I7)** | An invariant, not a price: one voucher per ticket id, idempotency key = ticket id, and a pass keeps one price for everyone. The companion and the gate POS surface it; the vendor enforces the rules | Vendor |

Full rules, field lists, reconciliation and failure handling: [appendix · ticketing rules](../../appendix/ticketing-rules.md).

## Estate daily report

**FR-2.7**: at 21:00 the Countess receives one phone screen of "how was today", promised in [requirements/01](../../requirements/01-business-goals-and-drivers.md).

Architecturally it is a **read model inside Park Operations** over facts and human decisions already on the backbone — `GateEntered` (with `persons_admitted`), `TicketPurchased`, `PassRenewed`, `PurchaseRecorded`, `CapacityCapChanged`, `ReviewDecided`, `TreatmentStarted` / `TreatmentClosed`, `QueueLengthUpdated`, plus the S3 forecast and `StaffingPlanApproved` from inside the module. It publishes no event and is not an AI scenario:

- Numbers are **inserted verbatim** from the read model; a post-generation check fails the send if a number in the text is not in the model.
- The recommendation comes from a **fixed rule set**, not a model.
- The optional phrasing reuses the S1 drafter as `summarise-estate-day` under the same verbatim-numbers rule and human approval ([ADR-0010](../../adrs/ADR-0010-grounded-llm-with-guardrails.md) §2). What the ops manager approves is wording, never numbers.

Information architecture, the five delivery states, the 20:30–21:00 timeline and the report's own test cases are product specification: [appendix · estate daily report](../../appendix/estate-daily-report.md).

## Business data health and verification

Purchases and the daily report are business data and get the same treatment as the sensors: a metric with a threshold and a one-line runbook, tests at every level, and a flag order that reaches the Countess last. Both are operational detail rather than architecture — [appendix · data health, verification and rollout](../../appendix/data-health-and-verification.md). The architectural claims they back up are that **KPI read models are tested, not trusted** (fixture event streams with known answers, same formulas as the model) and that a **reconciliation gap marks the day provisional** rather than silently adjusting a number.

## Cross-cutting

- **Identity:** visitors (optional accounts), staff (SSO, roles: keeper / vet / ops / management), devices by transport class — X.509 + mutual TLS for IP devices, DevEUI/AppKey with OTAA for LoRaWAN devices ([Edge & connectivity → Security](edge-and-connectivity.md#security-identity-by-transport-class)).
- **Audit of human decisions:** the same pattern as AI decisions (FR-5.1). Finance parameters (A15) and the default capacity cap are GitOps policy config under the management role, so their history is the Git log; day-level cap changes by the ops manager carry a reason code and are published as `CapacityCapChanged` (who / when / why / old / new); report approve and skip are logged with the snapshot id; out-of-guardrail price approvals already carry reason codes (S5).
- **Observability:** OpenTelemetry everywhere; AI calls carry `capability`, `model_version`, `confidence`, `cost` attributes.
- **Infrastructure as code & GitOps:** everything — including model versions in the registry — is declared in Git and reconciled.
- **Degradation ladder:** (1) cloud + AI, (2) cloud without AI (rules/heuristics), (3) estate-only (gates, safety, buffering). Every scenario names where it sits on this ladder.
- **Resilience validation:** sixteen scripted game days with expected behaviour, metric, cadence and owner → [resilience-validation.md](resilience-validation.md).
