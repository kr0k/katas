# ADR-0009 — Anonymous footfall counting, no visitor identification

**Status:** accepted · **Date:** 2026-09-05
**Serves:** FR-2.1, FR-5.3, NFR-PRV-1, NFR-PRV-2, R6
**Related:** ADR-0004, ADR-0006, ADR-0012

## Context
"Understanding which parts of the park are popular" is, technically, tracking people. Families are the audience; GDPR applies (A5); and reputational damage from perceived surveillance would undo any analytics gain. We also have cameras in enclosures that inevitably see visitors.

## Decision
1. Zone popularity and queue lengths are measured with **anonymous counting sensors** (LiDAR / thermal / IR beam counters) at zone boundaries and queue lines. They emit **counts**, never images or identifiers.
2. **No face recognition, no Wi-Fi/Bluetooth MAC tracking, no re-identification** anywhere in the system. Dwell time is derived from in/out counts, not from following individuals.
3. Enclosure cameras **mask visitor regions at the edge** before features or clips are produced (ADR-0006); raw video is not stored centrally.
4. **Personal data exists only with opt-in** (account for companion/nudges) and is held in Ticketing & Guest Engagement with purpose limitation, retention limits and export/delete on request. Companion sessions without an account are ephemeral.
5. The companion's *itinerary adherence* metric uses the visitor's **own device location with consent**, never sensors.
6. Signage and the privacy notice explain counting; a DPIA is completed before go-live.
7. **Personal-data lifecycle and erasure.** Opt-in personal data (account, companion sessions tied to an account, nudge preferences and delivery address) lives only in the Guest Engagement module and the adopted ticketing platform ([ADR-0012](ADR-0012-ticketing-platform-adopt-not-build.md)). Everything else refers to the person by a **pseudonymous subject id**; events never carry personal fields ([ADR-0004](ADR-0004-event-driven-backbone.md) §6). The few personal fields that must travel in events are encrypted with a **per-subject key** held in Guest Engagement. **Erasure** = delete the account record, call the ticketing platform's delete API, delete the subject's key (crypto-shredding of every encrypted field in the immutable log and the lakehouse), and emit `SubjectErased`; consumers drop the subject from read models, the feature store and golden/eval sets within 7 days; an **erasure audit query** over all stores proves zero remaining references before the request is closed (GDPR allows 30 days). **Retention:** companion sessions without an account are ephemeral (end of day); with an account, 12 months unless erased earlier.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| CCTV analytics with person re-identification | Rich paths and dwell time | Biometric processing; consent impossible at scale; reputational risk | R6, GDPR |
| Wi-Fi/Bluetooth probe tracking | Cheap | Device identifiers are personal data; randomised MACs make it unreliable anyway | Both legal and technical weakness |
| Ticket QR scans at every zone | Precise, tied to consent | Friction for visitors; queues at every zone entrance | Experience |
| Anonymous counters (chosen) | Privacy by design; simple devices; sufficient for staffing and investment decisions | Less granular than paths | — |

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
