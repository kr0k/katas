# 03 · Functional Requirements

Format: `FR-<domain>.<n>` — **MUST** / **SHOULD** / **COULD**. AI-enabled requirements are marked 🤖 and link to their scenario.

## FR-1 · Ticketing & Access

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-1.1 | Visitors can buy single tickets and **family passes** online (web, mobile) and at the gate | MUST |
| FR-1.2 | Family passes cover a configurable group (e.g. 2 adults + up to 3 children) and can be **multi-visit / seasonal** | MUST |
| FR-1.3 | Tickets are delivered as QR/NFC credentials that work **without the visitor having connectivity** | MUST |
| FR-1.4 | Gates validate tickets **while the estate uplink is down**, with later reconciliation | MUST |
| FR-1.5 | Payments are handled by a PCI-compliant third-party provider; the estate never stores card data | MUST |
| FR-1.6 | Pass holders can opt in to an account for return-visit offers and companion features | SHOULD |
| FR-1.7 | Ops can configure **timed-entry slots and a daily capacity cap** through the ticketing platform, fed by the S3 forecast and the [capacity check](../appendix/business-case-model.md#1-capacity-reality-check); the cap applies to unsold tickets and leaves gate validation unchanged; on capacity-managed days pass holders reserve a free timed slot — an attribute of the credential, validated offline — and unreserved passes are admitted only below the cap; every cap change carries a reason code and is published as `CapacityCapChanged` | SHOULD |

## FR-2 · Park Operations & Analytics

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-1.8 | **Durable pass credential**: a pass-holding household may be issued an NFC card, once, which it keeps — validated offline at gates exactly like any other signed credential, and carrying ride entitlements decremented against the local ledger → [ADR-0011](../adrs/ADR-0011-offline-ticket-validation.md) | COULD |
| FR-1.9 | **Cashless on the estate by tap**, settled against a payment method registered with the PSP — no balance held on the card or by the estate; offline a floor limit applies and above it the visitor pays by their own card → [ADR-0011](../adrs/ADR-0011-offline-ticket-validation.md) | COULD |
| FR-2.1 | Collect **anonymous footfall and queue-length** telemetry per zone/ride via MQTT devices | MUST |
| FR-2.2 | Ops dashboard: live and historical popularity per zone, ride and enclosure; **average dwell time per zone derived from in/out counts** (occupancy ÷ throughput — Little's law; no individual is followed, see [ADR-0009](../adrs/ADR-0009-visitor-privacy-anonymous-counting.md)); queue length | MUST |
| FR-2.3 🤖 | Forecast visitor flow per zone at 30-min granularity for the next 7 days and **recommend staffing** → [S3](../hld/scenarios/visitor-flow-forecasting/README.md) | SHOULD |
| FR-2.4 | Correlate investments (new ride, refurbished enclosure) with changes in popularity | SHOULD |
| FR-2.5 | Ride telemetry (cycles, downtime, faults) feeds maintenance scheduling | COULD |
| FR-2.6 | Ingest **on-site purchases** from the POS as auditable `PurchaseRecorded` events: `transaction_id`, type (sale / refund / void / correction), net amount + tax + currency, category (F&B / retail / parking / other — **no admission category**: gate-POS ticket sales stay `TicketPurchased`, so nothing is double-counted), `pos_terminal_id`, time; the pseudonymous `visitor_id` only where the opt-in explicitly covers purchase history ([ADR-0009](../adrs/ADR-0009-visitor-privacy-anonymous-counting.md) §7), otherwise no subject; never card data (NFR-SEC-2). Reconciled daily against the vendor's end-of-day totals | MUST |
| FR-2.8 🤖 | **Ask the estate**: management asks a question in plain language and it is answered over the estate's *defined metrics* — the occupancy and forecast metrics of [S3](../hld/scenarios/visitor-flow-forecasting/README.md) among them — read-only, with the metric definition and the window shown beside the answer → [agents](../hld/ai-platform/agents.md#ask-the-estate) | COULD |
| FR-2.7 | **Estate daily report** — one screen of "how was today" for the Countess at 21:00, a read model over existing events with every number inserted verbatim; the optional phrasing reuses the S1 daily-summary drafter under its human-approval rules → [Core](../hld/core/README.md#estate-daily-report) | SHOULD |

## FR-3 · Animal Welfare

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-3.1 | Collect enclosure telemetry: camera streams, feed scale weights, water quality, temperature/humidity | MUST |
| FR-3.2 🤖 | Detect **feeding anomalies** (missed meals, reduced intake) per animal/enclosure → [S1](../hld/scenarios/animal-welfare-monitoring/README.md) | MUST |
| FR-3.3 🤖 | Detect **behavioural/health anomalies** (lethargy, abnormal movement, isolation) and raise a review for the veterinarian → [S1](../hld/scenarios/animal-welfare-monitoring/README.md) | MUST |
| FR-3.4 🤖 | Estimate the **jumping piranha population** daily with a stated confidence interval → [S2](../hld/scenarios/piranha-population-counting/README.md) | MUST |
| FR-3.5 | Keeper/vet app: welfare timeline per animal, review queue, feeding log, treatment record | MUST |
| FR-3.6 | **Tier-0 safety alerts** — deterministic rules on local sensors (enclosure door open without a keeper badge, water or climate out of band, motion in a dry zone detected by PIR/beam, gate breach) reach staff within seconds and **do not depend on cloud, machine learning or generative AI** | MUST |
| FR-3.7 🤖 | **Tier-1 safety advisories** — model-assisted detection on camera (aggressive behaviour near visitors, animal outside its normal zone) raises an *advisory* to staff and a clip to the review queue → [S1](../hld/scenarios/animal-welfare-monitoring/README.md). Advisories **add to and never replace** tier-0 rules, and are governed as AI (confidence bands, evaluation gate) | SHOULD |

## FR-4 · Guest Engagement & Growth

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-4.1 🤖 | **Guest companion**: a conversational assistant (mobile/web, kiosks) that plans a family's day, suggests the next stop based on live queues, and answers questions about animals and rides → [S4](../hld/scenarios/guest-companion/README.md) | SHOULD |
| FR-4.2 🤖 | Personalised **return-visit nudges** (new animal born, seasonal event, unfinished "collection") for opted-in visitors → [S4](../hld/scenarios/guest-companion/README.md) | SHOULD |
| FR-4.5 🤖 | **Staff copilot**: a keeper, vet or ops manager asks for an explanation or a draft, and the platform reads defined metrics and evidence and *proposes* — a review to open in [S1](../hld/scenarios/animal-welfare-monitoring/README.md), a roster change in [S3](../hld/scenarios/visitor-flow-forecasting/README.md), a cap change — into the approval surface that already owns that decision → [agents](../hld/ai-platform/agents.md#ops-copilot) | COULD |
| FR-4.3 🤖 | **Demand-aware family pass pricing** within guardrails set by the estate → [S5](../hld/scenarios/dynamic-family-passes/README.md) | COULD |
| FR-4.4 | Post-visit feedback collection and theme analysis | COULD |

## FR-5 · Platform & Governance (cross-cutting)

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-5.1 | All AI decisions are logged with model version, inputs, confidence and outcome — **and so are human decisions that change prices, capacity or financial parameters** (who, when, why, old and new value) (auditability) | MUST |
| FR-5.2 | Any AI model or provider can be replaced without changing business services | MUST |
| FR-5.3 | Visitor tracking is anonymous by default; personal data only with explicit opt-in | MUST |
