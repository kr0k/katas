# ADR-0009 — Anonymous footfall counting, no visitor identification

**Status:** accepted · **Date:** 2026-09-05
**Serves:** FR-2.1, FR-5.3, NFR-PRV-1, NFR-PRV-2, R6
**Related:** ADR-0004, ADR-0006, ADR-0012

## Context
"Understanding which parts of the park are popular" is, technically, tracking people. Families are the audience; GDPR applies (A5); and reputational damage from perceived surveillance would undo any analytics gain. We also have cameras in enclosures that inevitably see visitors.

## Decision
1. Zone popularity and queue lengths are measured with **anonymous counting sensors** (LiDAR / thermal / IR beam counters) at zone boundaries and queue lines. They emit **counts**, never images or identifiers.
2. **No face recognition, no Wi-Fi/Bluetooth MAC tracking, no re-identification** anywhere in the system. Dwell time is an **average per zone derived from in/out counts** — occupancy ÷ throughput over a window (Little's law) — never from following individuals. Occupancy (in − out) accumulates counter error, so it is **reset to zero at closing** every day and **reconciled hourly** against gate totals; when the sum of zone occupancies differs from park occupancy by more than 10%, the offending counters are flagged for recalibration.
3. Enclosure cameras **mask visitor regions at the edge** before features or clips are produced (ADR-0006); raw video is not stored centrally.
4. **Personal data exists only with opt-in** (account for companion/nudges) and is held in Ticketing & Guest Engagement with purpose limitation, retention limits and export/delete on request. Companion sessions without an account are ephemeral.
5. The companion's *itinerary adherence* metric uses the visitor's **own device location with consent**, never sensors.
6. Signage and the privacy notice explain counting; a DPIA is completed before go-live.
7. **Personal-data lifecycle and erasure.**
   - **Where it lives:** opt-in personal data (account, companion sessions tied to an account, nudge preferences and delivery address) only in the Guest Engagement module and the adopted ticketing platform ([ADR-0012](ADR-0012-ticketing-platform-adopt-not-build.md)). Everything else refers to a person by a pseudonymous subject id, and events carry no personal fields ([ADR-0004](ADR-0004-event-driven-backbone.md) §6). The few that must travel in events are encrypted with a per-subject key held in Guest Engagement.
   - **Erasure:** delete the account record, call the ticketing platform's delete API, delete the subject's key (crypto-shredding every encrypted field in the immutable log and the lakehouse), emit `SubjectErased`. Consumers drop the subject from read models, feature store and golden sets within 7 days; an erasure audit query over all stores proves zero remaining references before the request is closed. GDPR allows 30 days.
   - **Retention:** companion sessions without an account are ephemeral (end of day); with an account, 12 months unless erased earlier.
   - **Purchase history is a separate consent.** `PurchaseRecorded` (FR-2.6) carries the pseudonymous `visitor_id` only where the account's opt-in covers purchase history and the family paid with the app or the pass; otherwise the event has no subject. Erasure works as above, and the anonymous rows keep amount, category and terminal — everything OKR 1.4 and the daily report need.
8. **The visitor token does not change §1 or §2.** Anonymous counters remain the **instrument of record** for footfall, occupancy, dwell and queues, because they count everyone and a token counts only its carriers. Taps from the token ([ADR-0018](ADR-0018-visitor-token-and-anonymised-paths.md)) answer a different question — the *order* of a visit — and they reach analytics only after aggregation: zone-to-zone flows and dwell distributions, suppressed below 20 tokens in a cell, weighted to the counter totals so that the sample bias is a published number rather than an assumption. Location is a consent separate from the token, refusing it costs no function, and a `token_id` is a subject under §7 like any other: crypto-shredded on erasure, re-keyed on recycling, never linked across seasons. The "we cannot" column below still holds — a particular family's path is not something this system can reconstruct, because no consumer downstream of aggregation ever sees an individual sequence.
9. **Staff data is personal data too.** Names, skills, certifications and availability imported from the HR/rostering system (A12) are processed under the employment basis, live only in Park Operations' roster store, and appear in events as staff ids. They are used for staffing plans and badge checks, nothing else.

What the anonymous counters can and cannot tell us — so nobody asks the dashboard for what it must not know:

| We can | We cannot (and do not want to) |
| --- | --- |
| Occupancy per zone, live and historical | Where a particular family went |
| Queue length and wait time per ride | Per-visitor dwell time or path |
| **Average** dwell per zone (Little's law) | Repeat visitors, from sensors — only from an opt-in account |
| Aggregate flows between adjacent zones (paired counters), and the order of a visit for the token cohort, weighted and published with its carry rate (§8) | Demographics, group composition, faces, devices — or any individual sequence of taps, which no consumer downstream of aggregation receives |
| Popularity before/after an investment (FR-2.4) | Anything that needs an identifier retained past the day |
| Spend per zone and per visitor-day, from POS terminals (FR-2.6) | What a particular family bought — unless they opted in to purchase history (§7) |

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| CCTV analytics with person re-identification | Rich paths and dwell time | Biometric processing; consent impossible at scale; reputational risk | R6, GDPR |
| Wi-Fi/Bluetooth probe tracking | Cheap | Device identifiers are personal data; randomised MACs make it unreliable anyway | Both legal and technical weakness |
| Ticket QR scans at every zone | Precise, tied to consent | Friction for visitors; queues at every zone entrance | Experience |
| Token taps **instead of** counters | One device class rather than two | The calibration is circular and the queue instrument disappears — argued in full in [ADR-0018](ADR-0018-visitor-token-and-anonymised-paths.md) | Rejected there, and the counters stay |
| Anonymous counters as the instrument of record, **plus** aggregated token taps for order (chosen) | Privacy by design on the number everyone quotes; the path question answered with its error stated rather than not at all | Two instruments and a weighting step to maintain; a visible tracking surface to explain (R23) | — |

## Consequences
**Positive:** analytics with nothing to leak; simpler compliance; a story the estate can tell proudly.
**Negative:** we cannot answer "where did *this* family go" — and we do not want to; counter accuracy at wide boundaries needs calibration.

| Risk | Mitigation |
| --- | --- |
| Counter drift/miscounts | Periodic manual calibration; in/out reconciliation with gate totals |
| Scope creep toward identification | ADR required; DPIA update; default answer is no |
| Erasure request cannot be honoured against an immutable event log or a trained model's dataset | No personal data in events by construction (CI check); crypto-shredding for the exceptions; `SubjectErased` propagates to features and golden sets; erasure end-to-end test is a game day (GD-11) |

## How we will know this was right
OKR 2.x achieved without any personal-data incident; DPIA passes; visitor survey shows trust in data handling; every erasure request closed within 30 days with a passing audit query.
