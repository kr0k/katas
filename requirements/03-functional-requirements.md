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
| FR-1.8 | A **visitor token** (passive RFID wristband or card) is issued with every admission, included in the price and optional to take: it validates at gates and ride entrances offline, pays at estate outlets by card-on-file, and links the tokens bought together so that a lost child is a lookup rather than a search. It carries a pseudonymous `token_id` and nothing else, and is re-keyed when recycled → [ADR-0018](../adrs/ADR-0018-visitor-token-and-anonymised-paths.md) | SHOULD |
| FR-1.9 | Internal transport on a fixed route with step-free access to the remote enclosures, publishing its position as ordinary telemetry; the companion surfaces the timetable and departure frequency follows the S3 forecast → [ADR-0020](../adrs/ADR-0020-internal-transport-and-autonomy.md) | COULD |

## FR-2 · Park Operations & Analytics

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-2.1 | Collect **anonymous footfall and queue-length** telemetry per zone/ride via MQTT devices | MUST |
| FR-2.2 | Ops dashboard: live and historical popularity per zone, ride and enclosure; **average dwell time per zone derived from in/out counts** (occupancy ÷ throughput — Little's law; no individual is followed, see [ADR-0009](../adrs/ADR-0009-visitor-privacy-anonymous-counting.md)); queue length | MUST |
| FR-2.3 🤖 | Forecast visitor flow per zone at 30-min granularity for the next 7 days and **recommend staffing** → [S3](../hld/scenarios/visitor-flow-forecasting/README.md) | SHOULD |
| FR-2.4 🤖 | Estimate what an investment (new ride, refurbished enclosure) actually changed, against a synthetic control of comparable zones, with an interval — and say so when the effect cannot be told apart from the season → [S6](../hld/scenarios/operations-copilot/README.md) | SHOULD |
| FR-2.5 🤖 | Ride telemetry (cycles, current, bearing temperature, run hours) feeds **condition-based** maintenance: the capability flags a ride for inspection with its evidence and a certified human decides, on top of the unchanged statutory schedule → [S8](../hld/scenarios/ride-condition-monitoring/README.md) | SHOULD |
| FR-2.6 | Ingest **on-site purchases** from the POS as auditable `PurchaseRecorded` events: `transaction_id`, type (sale / refund / void / correction), net amount + tax + currency, category (F&B / retail / parking / other — **no admission category**: gate-POS ticket sales stay `TicketPurchased`, so nothing is double-counted), `pos_terminal_id`, time; the pseudonymous `visitor_id` only where the opt-in explicitly covers purchase history ([ADR-0009](../adrs/ADR-0009-visitor-privacy-anonymous-counting.md) §7), otherwise no subject; never card data (NFR-SEC-2). Reconciled daily against the vendor's end-of-day totals | MUST |
| FR-2.7 | **Estate daily report** — one screen of "how was today" for the Countess at 21:00, a read model over existing events with every number inserted verbatim; the optional phrasing reuses the S1 daily-summary drafter under its human-approval rules → [Core](../hld/core/README.md#estate-daily-report) | SHOULD |
| FR-2.8 🤖 | **Ask the estate**: a question in plain language is resolved against a named metric with its dimensions and window, answered with the metric's definition alongside the number, or **refused with the name of the metric it looked for** — never answered by a query invented over raw tables → [S6](../hld/scenarios/operations-copilot/README.md) | SHOULD |
| FR-2.9 | Instrumented rides report cycle count, motor current, bearing and motor surface temperature and run hours on the telemetry class; sensors are non-invasive and fitted only after a per-ride heritage assessment (A10, A19) | SHOULD |
| FR-2.10 | **Zone-path analytics** from visitor-token taps: taps are aggregated into zone-to-zone flows and dwell distributions before they reach analytics, suppressed below 20 tokens in a cell, and **weighted to the anonymous counter totals** so that the carry rate is measured and published rather than assumed; a zone below a 15% carry rate reports "paths not representative" instead of a figure → [ADR-0018](../adrs/ADR-0018-visitor-token-and-anonymised-paths.md) | SHOULD |

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
| FR-3.8 🤖 | **Collection condition**: the carnivorous plant house is monitored on the same IoT classes, the same anomaly capability and the same review queue as an enclosure, and a detected feeding event becomes a scheduled demonstration on the day's programme → [S1](../hld/scenarios/animal-welfare-monitoring/README.md) | COULD |

## FR-4 · Guest Engagement & Growth

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-4.1 🤖 | **Guest companion**: a conversational assistant (mobile/web, kiosks) that plans a family's day, suggests the next stop based on live queues, and answers questions about animals and rides → [S4](../hld/scenarios/guest-companion/README.md) | SHOULD |
| FR-4.2 🤖 | Personalised **return-visit nudges** (new animal born, seasonal event, unfinished "collection") for opted-in visitors → [S4](../hld/scenarios/guest-companion/README.md) | SHOULD |
| FR-4.3 🤖 | **Demand-aware family pass pricing** within guardrails set by the estate → [S5](../hld/scenarios/dynamic-family-passes/README.md) | COULD |
| FR-4.4 🤖 | Post-visit feedback is clustered into **named themes with counts, trends and verbatim quotes** — never a sentiment score — and each theme resolves to the zone, ride or enclosure it is about → [S7](../hld/scenarios/content-and-visitor-voice/README.md) | SHOULD |
| FR-4.5 🤖 | **Content drafting**: highlight candidates are mined from the activity features the welfare pipeline already computes, and a caption is drafted around verbatim species facts. Nothing publishes without the curator, and there is no automated publish path → [S7](../hld/scenarios/content-and-visitor-voice/README.md) | COULD |
| FR-4.6 | The token and the account are one profile: a household recognised by either sees the same history, and either may be erased on its own → [ADR-0018](../adrs/ADR-0018-visitor-token-and-anonymised-paths.md) | SHOULD |
| FR-4.7 🤖 | Personalisation for a token or account holder changes **what the companion suggests**, never what it asserts: visit history and declined suggestions shape the route and the nudge, while safety, price and allergen facts stay verbatim from approved fields → [S4](../hld/scenarios/guest-companion/README.md) | SHOULD |

## FR-5 · Platform & Governance (cross-cutting)

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-5.1 | All AI decisions are logged with model version, inputs, confidence and outcome — **and so are human decisions that change prices, capacity or financial parameters** (who, when, why, old and new value) (auditability) | MUST |
| FR-5.2 | Any AI model or provider can be replaced without changing business services | MUST |
| FR-5.3 | Visitor tracking is anonymous by default; personal data only with explicit opt-in | MUST |
| FR-5.4 | An AI **agent** reaches a service only through typed, least-privilege tools; every tool call is a span in one trace with its arguments, outcome, cost and bundle version; effectful calls are idempotent on a business key; and a human commits anything that moves money, a roster, a price or an animal's care → [ADR-0013](../adrs/ADR-0013-stakeholder-agents-on-typed-tools.md) | MUST |
