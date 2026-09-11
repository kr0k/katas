# ADR-0018 — Visitor token: personal at the tap, anonymous in the analytics

**Status:** accepted · **Date:** 2026-09-11
**Serves:** FR-1.3, FR-1.8, FR-2.10, FR-4.7, NFR-PRV-1, NFR-PRV-3, R23
**Related:** ADR-0009, ADR-0011, ADR-0012, ADR-0013, ADR-0015

## Context
Three unrelated problems point at the same missing object.

A credential that lives only in a phone is fragile exactly where the estate is weakest: the battery
dies, the Wi-Fi is patchy (the constraint the whole architecture is built around), and a share of
families arrive without a usable smartphone at all. Second, the flywheel in
[08 §3](../appendix/business-case-model.md#3-the-membership-flywheel) rests on recognising a returning
household, and today the only way to be recognised is to open an account in an app. Third, the
anonymous counters of [ADR-0009](ADR-0009-visitor-privacy-anonymous-counting.md) answer "how many are
in this zone" but structurally cannot answer "where do families go after the piranha tank" — the
question behind FR-2.4 and behind half the Countess's investment decisions.

A physical token answers all three, and it brings the objection that killed it as a *counting* device:
only people carrying a working token are seen, and pass holders are not a random sample of visitors. A
design that ignores that bias produces confident, wrong heat maps.

## Decision
1. **Issue a passive RFID token — a wristband or a card — with every admission**, included in the
   price and optional to take. It carries a **pseudonymous `token_id`** and nothing else; it is
   returned or recycled at exit, and a recycled token is re-keyed, so a token is not a person across
   seasons.
2. **Four uses, three of them offline.**
   - **Access:** tap at the gate and at ride entrances, validated offline against the reader's cached
     lists exactly as a QR credential is ([ADR-0011](ADR-0011-offline-ticket-validation.md)). The
     token is a second form factor for the same credential, not a second ticketing system.
   - **Cashless:** tap to pay at estate outlets, settled by card-on-file at the payment provider. The
     token holds **no stored value and no card data** — PCI scope stays where
     [ADR-0012](ADR-0012-ticketing-platform-adopt-not-build.md) put it.
   - **Family link:** tokens in one purchase are linked, which is what turns a lost child from a
     search into a lookup at the nearest reader.
   - **Paths:** taps at zone-boundary readers, which is decision 3.
3. **Path analytics are built on the token cohort and calibrated against the counters, which remain
   the instrument of record.** Counter totals answer *how many*; taps answer *in what order*. Per zone
   and hour, the tap cohort is weighted to the counter total, so the **carry rate is measured rather
   than assumed**, and the weighting error is published with the figure. A zone whose carry rate falls
   below 15% is reported as "paths not representative" instead of being drawn.
4. **Personal at the tap, anonymous before the analytics.** Taps are recorded under `token_id` and
   used in real time only by capabilities the holder opted into — the companion's next-stop
   suggestion, the lost-child lookup. Everything that reaches Park Operations, the metric layer or the
   daily report is **aggregated first**: zone-to-zone flows and dwell distributions, suppressed below
   **k = 20 tokens** in a cell, with no path shorter than a zone published at all. The raw tap stream
   is retained 30 days for reconciliation and then aggregated away.
5. **Location is its own consent, and refusing it costs nothing.** Access, cashless and the family link
   work without it. The tap record for a holder who declined carries the zone and the hour but no
   `token_id`, which makes it a counter reading and nothing more.
6. **Everything in [ADR-0009](ADR-0009-visitor-privacy-anonymous-counting.md) still holds.** No faces,
   no device tracking, no re-identification across seasons; `token_id` is a subject under §7, so
   erasure crypto-shreds it and `SubjectErased` clears it from read models, the feature store, the
   agent memory tiers and golden sets.
7. **Readers are placed, not scattered:** gates, ride entrances, points of sale, and the boundaries of
   the twelve zones the investment question is actually asked about — not every path in a heritage
   park.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| App only, no token | Nothing to issue, clean, zero hardware | Fails on a dead battery and for families without a smartphone; leaves the path question unanswerable and the flywheel dependent on account creation | The estate's own constraints |
| Token for access only, no taps for analytics | Keeps the privacy story maximally simple | Pays for the readers and throws away the answer to FR-2.4; the counters still cannot order a visit | Buys the cost without the benefit |
| Taps as the counting instrument, replacing counters | One device class instead of two | Counts only token carriers, and the carry rate can only be measured against an independent count of everyone — the counter it would have replaced. Queue lines have no portal to tap, so OKR 2.2 loses its instrument entirely | Circular calibration; this is the version we reject |
| Wi-Fi or Bluetooth probe tracking | No hardware to issue | Device identifiers are personal data, randomised MACs make them unreliable, and it is tracking without a tap anyone can see | [ADR-0009](ADR-0009-visitor-privacy-anonymous-counting.md) |
| Token for identity and paths, counters for totals (chosen) | Each instrument used for what it can measure; bias becomes a measured, published number | Two instruments and a weighting step; hardware, issuance and hygiene logistics; a visible tracking surface to explain | — |

## Consequences
**Positive:** a credential that survives a dead battery and patchy Wi-Fi; recognition of a returning
household without requiring an app; the first honest answer to "what did this investment change",
with its error stated; a materially faster lost-child procedure.
**Negative:** CAPEX for readers and OPEX for tokens and hygiene (both in the
[cost model](../appendix/cost-model.md)); a visible surface that can be read as surveillance (R23) and
must be explained in signage, not in a privacy policy; issuance and return at the gate is a queue we
now own; and the weighting in decision 3 is a real statistical procedure someone has to maintain.

| Risk | Mitigation |
| --- | --- |
| Perceived as tracking; opt-in rate collapses (R23) | Location is a separate, refusable consent (§5); the token is physically visible and removable, unlike a device identifier; signage at every reader; DPIA updated before the first tap |
| Carry rate too low or too biased to weight | §3 publishes the rate and refuses the figure below 15% rather than drawing a pretty map; the quarterly exit survey (A14) is the independent check on who carries one |
| Token becomes a second ticketing system | It is a form factor for the vendor's credential, and the vendor's support for it is a selection criterion ([TODOS.md](../TODOS.md)) |
| Re-identification creep — "just link taps to the account" | Aggregation before analytics is enforced in the metric layer ([ADR-0015](ADR-0015-metric-layer-and-estate-twin.md)), not in each consumer; k = 20 is policy config with a named owner |

## How we will know this was right
Token carry rate above 40% of admissions with the weighting error inside ±10 points; a measurable
before-and-after for at least one investment in the first season (FR-2.4); lost-child resolution time
down against the manual baseline; and no privacy incident, with the DPIA and the erasure audit query
(GD-11, GD-20) passing each quarter.
