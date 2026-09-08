# Appendix · Estate daily report specification

The product specification of FR-2.7: information architecture, states, the evening timeline and the report's own verification cases. The architectural part — a read model in Park Operations, numbers inserted verbatim, phrasing by an LLM only after human approval — is in [hld/core → Estate daily report](../hld/core/README.md#estate-daily-report).

**Evening timeline.** Numbers are final at 21:00, so the ops manager approves wording, not numbers:

1. **20:30** — a draft is rendered from the 20:30 snapshot, every figure a slot.
2. **20:30–21:00** — the ops manager approves the wording. Offline, the button is disabled with the reason shown.
3. **21:00** — the final snapshot's numbers go verbatim into the approved slots, the verbatim check runs on the final text, freshness is evaluated, the report is sent.

If the rule set picks a different recommendation at 21:00 than at 20:30, the template wording is sent instead of the approved phrase.

**Information architecture** — one screen, top to bottom, no charts (they are one tap away in the ops dashboard); mobile first, with an e-mail copy of the same text:

| # | Block | Lines | Source |
| --- | --- | --- | --- |
| 1 | **Tomorrow's recommendation** and the one number furthest from forecast, large | Chosen by a fixed rule set — *forecast below the quiet-day threshold → quiet-day offer on*; *parking within 10% of its limit → cap proposed*; *rain forecast → staffing to covered zones*; otherwise "no change" — and only phrased by the LLM | S3 forecast, capacity model, weather |
| 2 | **Guests and spend** | Visitor-days vs. forecast; weekday/weekend ratio to date (OKR 1.5); spend per visitor-day and total (FR-2.6); top-3 and bottom-3 zones by spend | `GateEntered`, `PurchaseRecorded`, forecast |
| 3 | **Animals** | Reviews decided today (confirmed / dismissed); animals under treatment (opened / closed) — human decisions, never anomaly scores | `ReviewDecided`, `TreatmentStarted/Closed` |
| 4 | **Passes and queues** | Passes sold, renewals (OKR 1.6); p90 queue on the top-10 rides (OKR 2.2) | `TicketPurchased`, `PassRenewed`, `QueueLengthUpdated` |
| 5 | **Tomorrow** | Forecast visitor-days; approved staffing; **days until parking binds** at the current attendance trend — computed from the A14 parameters and labelled as a model | forecast, `StaffingPlanApproved`, capacity model |
| — | **Footer = freshness** | snapshot id · freshness at 21:00 (p95 ingest delay, uplink buffer state) · provisional flags · template version · phrasing model version or "template" | read model, [edge metrics](../hld/core/edge-and-connectivity.md#capacity-check-at-15000-visitorsday-by-traffic-class) |

**States and rules**

| State | When | What the Countess sees |
| --- | --- | --- |
| SUCCESS | Fresh at 21:00 (below), verbatim check passed on the final numbers, wording approved between 20:30 and 21:00 | Full report, phrased |
| SUCCESS (template) | No wording approved by 21:00, phrasing unavailable, or the recommendation changed between the 20:30 draft and 21:00 | Full report, template wording; approve after 21:00 is logged as "sent as template" and no phrasing is sent later |
| PARTIAL (provisional) | **Not fresh at 21:00** — freshness = p95(ingested_at − event_time) over the day's events ≤ 15 min **and** the broker's uplink buffer empty, both metrics [Edge & connectivity](../hld/core/edge-and-connectivity.md#capacity-check-at-15000-visitorsday-by-traffic-class) already collects (recency of the last event is *not* the measure: the park closes at 18:00) — or the day's spend reconciliation failed | Report marked *provisional* by symbol **and** word (never colour alone) in the header and footer; **re-issued at 07:00** |
| PARTIAL (template only) | Post-generation check finds a number that is not in the read model, or a read-model number missing from the text | Template wording sent; alert to the platform owner; the phrasing bundle is a rollback candidate |
| EMPTY | Closed day | Short variant: animals, treatments, tomorrow |
| FIRST SEASON | No prior-year comparison or no forecast yet | "first season — baseline" / "heuristic" labels instead of blanks |
| ERROR | Not delivered after 3 retries | Dashboard banner and a "report not delivered" alert; the snapshot is still in the archive |

Approval is **idempotent per date**; offline, the approve button is disabled with the reason shown (GD-15). Every report is archived behind SSO with **3-year retention**, snapshot and text together; approve and skip decisions are logged with the snapshot id.

