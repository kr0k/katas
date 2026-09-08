# Appendix · Ticketing rules the platform executes

Three things the [business-case model](business-case-model.md) asks the foundation to carry. None changes deployment units, safety tiers or gate validation; all three live in the Ticketing & Access anti-corruption layer and are executed by the adopted platform ([ADR-0012](../adrs/ADR-0012-ticketing-platform-adopt-not-build.md)).

These are vendor-executed business rules, not architectural decisions. What the architecture fixes is in [hld/core → Ticketing & Access additions](../hld/core/README.md#ticketing--access-additions-purchases-cap-and-upgrade-credit): where the layer sits, what it publishes, and which invariants hold.

Three things the business case ([requirements/08](../requirements/08-business-case.md)) asks the foundation to carry. None changes deployment units, safety tiers or gate validation; all three live in the anti-corruption layer and are executed by the adopted platform ([ADR-0012](../adrs/ADR-0012-ticketing-platform-adopt-not-build.md)).

### On-site spend (FR-2.6)

The POS — the ticketing platform's own or a separate system (A13) — posts each transaction as a signed webhook. The anti-corruption layer then:

- **Verifies the signature.** HMAC-SHA256 over the raw body with a key id, constant-time compare, and a signed-at timestamp accepted within 5 minutes. Every retry is re-signed. Mutual TLS is welcome as transport but is not replay protection; keys are short-lived vendor-published ones, or a rotatable secret with an overlap window.
- **Drops duplicates** on transaction id for 7 days, the same window as device events ([ADR-0001](../adrs/ADR-0001-edge-first-store-and-forward.md)), so a re-signed backlog after our own outage is accepted while a captured payload is not.
- **Runs a runtime value deny-list** (PAN/Luhn, e-mail, phone) over every field and rejects the event with an incident on a match. The schema-registry CI check cannot see runtime values, so this is the only place it can be caught.
- **Writes `PurchaseRecorded` to the outbox:** transaction id, type (sale / refund / void / correction), net + tax + currency, category without an admission category, terminal, time. The pseudonymous `visitor_id` travels only under the purchase-history consent ([ADR-0009](../adrs/ADR-0009-visitor-privacy-anonymous-counting.md) §7). Terminal-to-zone mapping belongs to Park Operations, not here; an unknown terminal lands in an "unmapped" bucket and alerts rather than being dropped.

Every night the day's totals are reconciled against the vendor's end-of-day figures. A difference above 1% marks the day's spend *provisional* on every read model and produces an exceptions report for finance.

**Backpressure slows, never drops.** Above the rate limit the layer answers HTTP 429 with Retry-After and the vendor retries with backoff (an ADR-0012 criterion), so a burst drains at our pace with zero loss — the sandbox test replays one hour of backlog in ≤ 10 minutes. The dead-letter queue holds only invalid events (signature, schema, PII) and has no quota for valid ones.

### Timed entry and daily cap (FR-1.7)

The default cap is GitOps policy config under the management role. A day-level change by the ops manager — usually proposed by the daily report from the S3 forecast — carries a reason code, goes through the vendor's cap API, and is published as `CapacityCapChanged` with the audit fields fixed in [hld/core](../hld/core/README.md#ticketing--access-additions-purchases-cap-and-upgrade-credit).

- The cap applies to **unsold tickets only**; gate validation is untouched.
- Pass holders hold no date-specific ticket, so on capacity-managed days they **reserve a free timed slot**. The reservation travels as an attribute of the signed credential and is validated offline like the signature ([ADR-0011](../adrs/ADR-0011-offline-ticket-validation.md)); an unreserved pass is admitted only while the downlink cap snapshot has room.
- Concurrent edits are last-write-wins, both events published, with a UI warning. The vendor API returns the effective cap and the sold count; *sold > cap* raises an oversell alert, never a gate refusal.

A cap redistributes arrivals and adds no capacity ([requirements/08 §1](business-case-model.md#1-capacity-reality-check)).

### Upgrade credit voucher (P-I7)

A day ticket scanned in today (`GateEntered`, until the operational day closes) can be turned **once per ticket id** into a credit voucher for its price, redeemable against a season pass within 7 days, at home or at the desk. The pass starts on the visit date, so the visit counts as a pass visit.

- A refund of the ticket voids an unredeemed voucher; once redeemed, the ticket is not refundable — it is absorbed by the pass.
- The vendor executes the rules; the prompt is ours. The companion shows it only to day-ticket holders without a pass, using the ticket id as idempotency key; offline it reads "available at the exit and at the gate POS". The gate POS makes the same offer, and the next-day nudge reminds about an outstanding voucher without creating new eligibility.
- A pass keeps one price for everyone: the voucher is a rule, not a personal price.

