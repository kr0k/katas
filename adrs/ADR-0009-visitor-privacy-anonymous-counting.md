# ADR-0009 — Anonymous footfall counting, no visitor identification

**Status:** accepted · **Date:** 2026-09-05
**Serves:** FR-2.1, FR-5.3, NFR-PRV-1, NFR-PRV-2, R6
**Related:** ADR-0004, ADR-0006, ADR-0012

## Context
"Understanding which parts of the park are popular" is, technically, tracking people. Families are the audience; GDPR applies (A5); and reputational damage from perceived surveillance would undo any analytics gain. We also have cameras in enclosures that inevitably see visitors.

## Decision
1. Zone popularity and queue lengths are measured with **anonymous counting sensors** (LiDAR / thermal / IR beam counters) at zone boundaries and queue lines. They emit **counts**, never images or identifiers.
2. **No face recognition, no Wi-Fi/Bluetooth MAC tracking, and no re-identification of anonymous visitors** anywhere in the system. To be exact rather than merely reassuring: a household holding a pass or an opt-in account **is** identified — by its own choice, and that is how OKR 1.2 has always been measured — and a durable pass credential ([ADR-0011](ADR-0011-offline-ticket-validation.md) §6) makes that identification useful at a till as well as at a gate. What does not exist is the ability to identify anyone who has *not* opted in, or to reconstruct where any household walked: **readers live at gates, ride entitlement points and tills, never on a zone boundary or a path** (NFR-PRV-3, enforced by an architecture test on the reader registry and drilled as game day GD-25), and counting stays anonymous for every visitor. Dwell time is an **average per zone derived from in/out counts** — occupancy ÷ throughput over a window (Little's law) — never from following individuals. Occupancy (in − out) accumulates counter error, so it is **reset to zero at closing** every day and **reconciled hourly** against gate totals; when the sum of zone occupancies differs from park occupancy by more than 10%, the offending counters are flagged for recalibration.
3. Enclosure cameras **mask visitor regions at the edge** before features or clips are produced (ADR-0006); raw video is not stored centrally.
4. **Personal data exists only with opt-in** (account for companion/nudges) and is held in Ticketing & Guest Engagement with purpose limitation, retention limits and export/delete on request. Companion sessions without an account are ephemeral.
5. The companion's *itinerary adherence* metric uses the visitor's **own device location with consent**, never sensors.
6. Signage and the privacy notice explain counting; a DPIA is completed before go-live.
7. **Personal-data lifecycle and erasure.**
   - **Where it lives:** opt-in personal data (account, companion sessions tied to an account, nudge preferences and delivery address) only in the Guest Engagement module and the adopted ticketing platform ([ADR-0012](ADR-0012-ticketing-platform-adopt-not-build.md)). Everything else refers to a person by a pseudonymous subject id, and events carry no personal fields ([ADR-0004](ADR-0004-event-driven-backbone.md) §6). The few that must travel in events are encrypted with a per-subject key held in Guest Engagement.
   - **Erasure:** delete the account record, call the ticketing platform's delete API, delete the subject's key (crypto-shredding every encrypted field in the immutable log and the lakehouse), emit `SubjectErased`. Consumers drop the subject from read models, feature store and golden sets within 7 days; an erasure audit query over all stores proves zero remaining references before the request is closed. GDPR allows 30 days.
   - **Retention:** companion sessions without an account are ephemeral (end of day); with an account, 12 months unless erased earlier.
   - **Purchase history is a separate consent.** `PurchaseRecorded` (FR-2.6) carries the pseudonymous `visitor_id` only where the account's opt-in covers purchase history and the family paid with the app or the pass; otherwise the event has no subject. Erasure works as above, and the anonymous rows keep amount, category and terminal — everything OKR 1.4 and the daily report need.
8. **Staff data is personal data too.** Names, skills, certifications and availability imported from the HR/rostering system (A12) are processed under the employment basis, live only in Park Operations' roster store, and appear in events as staff ids. They are used for staffing plans and badge checks, nothing else.

What the anonymous counters can and cannot tell us — so nobody asks the dashboard for what it must not know:

| We can | We cannot (and do not want to) |
| --- | --- |
| Occupancy per zone, live and historical | Where a particular family went |
| Queue length and wait time per ride | Per-visitor dwell time or path |
| **Average** dwell per zone (Little's law) | Repeat visitors, from sensors — only from an opt-in account |
| Aggregate flows between adjacent zones (paired counters) | Demographics, group composition, faces, devices |
| Popularity before/after an investment (FR-2.4) | Anything that needs an identifier retained past the day |
| Spend per zone and per visitor-day, from POS terminals (FR-2.6) | What a particular family bought — unless they opted in to purchase history (§7) |
| Spend and visit frequency **per pass-holding household**, from taps at gates and tills under their own opt-in — which is what makes OKR 1.4's second line a measurement rather than a survey estimate | **Where any household walked.** No reader sits on a path, so there is no sequence to reconstruct (NFR-PRV-3) |

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| CCTV analytics with person re-identification | Rich paths and dwell time | Biometric processing; consent impossible at scale; reputational risk | R6, GDPR |
| Wi-Fi/Bluetooth probe tracking | Cheap | Device identifiers are personal data; randomised MACs make it unreliable anyway | Both legal and technical weakness |
| Ticket QR scans at every zone | Precise, tied to consent | Friction for visitors; queues at every zone entrance | Experience |
| RFID/NFC token portals at zone boundaries | A token can be cheap, and taps are unambiguous where they happen | Counts only visitors carrying a working token. Issuing one to everyone daily is a per-visitor cost where counters have none — a €0.15 disposable tag is 30% of the €0.50 [per-visitor ceiling](../requirements/04-non-functional-requirements.md#cost-model-tco-50) — and issuing only to pass holders samples ≈ 20% of admissions today, rising to ≈ 41%, from the segment least like the average visitor. Correcting that bias needs a per-zone carry rate, measurable only with an independent count of everyone in the zone: the counter it would replace. Queue lines have no portal to read, so OKR 2.2 loses its instrument, and OKR 2.4 fails in the dangerous direction — a zone reads zero taps with two hundred people standing in it. Portals on paths also mean physical gateways on 150 boundaries in a heritage park | Circular calibration, a biased sample, and no queue instrument. It would also turn discrete taps at a gate into continuous tracking of identified households, which is the scope creep this ADR answers with no |
| Anonymous counters (chosen) | Privacy by design; simple devices; sufficient for staffing and investment decisions | Less granular than paths | — |

## Consequences
**Positive:** analytics with nothing to leak; simpler compliance; a story the estate can tell proudly.
**Negative:** we cannot answer "where did *this* family go" — and we do not want to; counter accuracy at wide boundaries needs calibration.

| Risk | Mitigation |
| --- | --- |
| Counter drift/miscounts | Periodic manual calibration; in/out reconciliation with gate totals |
| Scope creep toward identification | ADR required; DPIA update; default answer is no. The specific creep to guard is a reader on a zone boundary, which would convert a transaction record into a location history — hence NFR-PRV-3 and its architecture test rather than a promise (R26) |
| Erasure request cannot be honoured against an immutable event log or a trained model's dataset | No personal data in events by construction (CI check); crypto-shredding for the exceptions; `SubjectErased` propagates to features and golden sets; erasure end-to-end test is a game day (GD-11) |

## How we will know this was right
OKR 2.x achieved without any personal-data incident; DPIA passes; visitor survey shows trust in data handling; every erasure request closed within 30 days with a passing audit query.
