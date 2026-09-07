# ADR-0012 — Ticketing platform: adopt, not build

**Status:** accepted · **Date:** 2026-09-07
**Serves:** FR-1.1, FR-1.2, FR-1.3, FR-1.4, FR-1.5, FR-1.6, FR-1.7, FR-2.6, NFR-AVL-1, NFR-AVL-2, NFR-OPS-1, NFR-SEC-2, R9, R16
**Related:** ADR-0003, ADR-0004, ADR-0011

## Context
Ticketing, family and season passes, checkout, refunds, gate credentials and fraud control are a commodity: every attraction of this size runs them, and specialised products exist. Our team is ≤ 5 engineers (A8, NFR-OPS-1) and the estate's differentiators are elsewhere — the edge tier, the welfare models, the companion. The one requirement that is not commodity is [ADR-0011](ADR-0011-offline-ticket-validation.md): gates must validate tickets while the uplink is down. Building ticketing ourselves to get offline validation would put one or two engineers permanently on PCI scope, refund edge cases and pass rules. Buying a product that cannot validate offline would violate NFR-AVL-1.

## Decision
1. **Adopt an attraction-ticketing platform (SaaS)** for catalogue, checkout and payments, single and family/season passes, opt-in visitor accounts, gate credentials, on-site POS (or a separate POS behind the same layer — A13) and sales reconciliation. The Ticketing & Access context in our monolith becomes an **anti-corruption layer**: an adapter that turns vendor webhooks into our events (`TicketPurchased`, `GateEntered`, `GateExited`, `PassRenewed`, `PurchaseRecorded`, `CapacityCapChanged`) and our commands (`PriceUpdated`, capacity cap and timed-entry settings, GDPR erasure) into vendor API calls. Domain events, read models and the event backbone stay ours ([ADR-0004](ADR-0004-event-driven-backbone.md)).
2. **ADR-0011 is the specification, not a build plan.** Its signed-credential, local-ledger, reconcile-later design is the **acceptance test** a vendor must pass. Selection criteria, all must-have:

   | Criterion | Why |
   | --- | --- |
   | Offline gate validation with signed credentials, a local used-ledger and later reconciliation, on the vendor's readers or ours | FR-1.3, FR-1.4, NFR-AVL-1 ([ADR-0011](ADR-0011-offline-ticket-validation.md)) |
   | Family/season passes with a configurable group, per-day usage limits, renewals | FR-1.2 |
   | Webhooks or event export for every sale, entry, exit, refund and pass change, within seconds | Our events and analytics depend on them; `GateEntered` feeds Park Operations |
   | Price API with a price lock for an open checkout session | S5 `PriceUpdated`; fairness rule "never reprice mid-checkout" |
   | GDPR export and delete APIs; EU hosting | FR-5.3, NFR-PRV-1, A5, [ADR-0009](ADR-0009-visitor-privacy-anonymous-counting.md) |
   | Bulk data export in open formats; documented exit | [ADR-0003](ADR-0003-cloud-provider-selection.md) exit assessment |
   | PCI-DSS scope entirely at the vendor | FR-1.5, NFR-SEC-2 |
   | Published pricing that fits at 15,000 visitors/day; SLA ≥ 99.9% for online sales | NFR-AVL-2, NFR-COST-1 |
   | **Timed-entry slots with a daily capacity cap**, settable by ops through an API that returns the effective cap and the sold count | FR-1.7; the [capacity check](../requirements/08-business-case.md#1-capacity-reality-check) — parking binds in year 1 and the gates in year 3 |
   | **POS / F&B included, or a separate POS** with per-transaction webhooks or export carrying the FR-2.6 fields (transaction id, type, net + tax + currency, category, terminal, time, optional pseudonymous visitor id) | FR-2.6, OKR 1.4, A13; the [Estate daily report](../hld/core/README.md#estate-daily-report) |
   | **Same-day upgrade of a ticket to a season pass with the ticket price credited** — once per ticket id, only for a ticket valid today, voided if the ticket is refunded, credit valid 7 days. This is the platform invariant **P-I7**: a pass has one price for everyone; the credit is a rule the vendor executes, not a personal price | Second lever of the [flywheel](../requirements/08-business-case.md#3-the-membership-flywheel); S5 only references it |
   | **Signed webhooks** (HMAC or mutual TLS) with timestamp and transaction-id replay protection; our API keys in the secret store, rotated via GitOps | Sales and purchase events feed the OKRs and the daily report; R16 |
   | **Vendor sandbox** covering webhooks, the cap API and the upgrade credit | Integration tests and the staged rollout in [hld/core → Verification](../hld/core/README.md#verification-purchases-cap-and-the-daily-report) |
   | `GateEntered` carries **`persons_admitted`** — the number of people admitted on the scan | Visitor-days are counted from it ([requirements/08 §0](../requirements/08-business-case.md#0-how-to-read-the-numbers), [ADR-0011](ADR-0011-offline-ticket-validation.md) §2) |

   The vendor evaluation in [TODOS.md](../TODOS.md) inherits every row of this table and is a prerequisite for Phase 0.
3. **Gate hardware is the vendor's problem to fit our network:** readers must run on the estate's local network and cache keys and lists as ADR-0011 §5 describes; if the vendor's readers cannot, we run their validation SDK on our own reader hardware.
4. **Fallback is bounded and pre-decided.** If the vendor evaluation ([TODOS.md](../TODOS.md)) finds no product meeting the offline criterion, we adopt a platform for sales and passes and **build gate validation ourselves** exactly as ADR-0011 describes, against the vendor's ticket data. That is why ADR-0011 stays a full design and not a bullet list.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Build ticketing in-house | Full control; offline validation guaranteed by design | 1–2 engineers permanently on a commodity; PCI, refunds, fraud, pass rules are all ours; Phase 0 grows by months | NFR-OPS-1, R9 |
| Generic e-commerce platform + our gates | Cheap, well known | No passes, no gate credentials, no offline story; we build the hard part anyway | Only solves the easy half |
| Attraction-ticketing platform (chosen) | Commodity handled by people who do only that; PCI and refunds off our plate; Phase 0 shrinks to integration | Vendor dependency; offline behaviour bounded by what the market offers; their data model, not ours | — |

## Consequences
**Positive:** Phase 0 delivers ticketing in weeks; the team spends its time on the estate-specific system; PCI scope, fraud and refunds sit with the vendor; ADR-0011 becomes a checklist we can hand to procurement.
**Negative:** a vendor now sits on the critical path of NFR-AVL-2 (online sales); the offline guarantee is only as good as the vendor's implementation until proven in a game day; the anti-corruption layer is real code to maintain.

| Risk | Mitigation |
| --- | --- |
| Vendor offline mode weaker than ADR-0011 | Offline criterion tested on the estate before contract signature; game day GD-4/GD-5 ([resilience validation](../hld/core/resilience-validation.md)); fallback build pre-decided (§4) |
| Vendor lock-in | Export and exit criteria; domain events are ours via the anti-corruption layer; no vendor identifiers leak into other contexts |
| Vendor pricing scales badly with attendance | Price at 15,000/day is a selection criterion; exit assessment names a second vendor |
| Vendor outage | Gates keep validating offline (criterion 1); online sales degrade to the vendor's SLA; gate POS sells on-site |
| Upgrade credit applied twice, or kept after the ticket is refunded | P-I7 is tested as a property (double upgrade, refund after upgrade, expired credit) against the vendor sandbox before go-live and reconciled daily with `TicketPurchased`; violations = 0 or the prompt is switched off ([hld/core → Verification](../hld/core/README.md#verification-purchases-cap-and-the-daily-report)) |
| Purchase webhooks carry card data or are replayed | Runtime PII deny-list in the anti-corruption layer rejects the event and opens an incident; signature, timestamp and transaction-id checks drop replays; game day GD-14 |

## How we will know this was right
Ticketing live in Phase 0 within weeks, not months; zero engineers assigned to ticketing after go-live; gate availability meets [ADR-0011](ADR-0011-offline-ticket-validation.md)'s 99.9% on the vendor's stack in quarterly game days; the vendor evaluation TODO closed with an alternatives table in this ADR. Revisit if the evaluation finds no offline-capable vendor (fallback §4) or if vendor cost exceeds the in-house estimate at 15,000/day.
