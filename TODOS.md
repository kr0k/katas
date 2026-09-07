# TODOS

## Architecture

### Ride operations & maintenance domain

**What:** Decide where ride operations & maintenance live in the architecture: a sixth scenario (predictive maintenance from vibration/cycle counters, FR-2.5) or an explicit "why rides are only `RideStatusChanged` in this submission" paragraph.

**Why:** G6 makes ride safety non-negotiable and 40 historic rides are half the attraction, yet rides get one event and no AI. A10 limits instrumentation; 05 excludes ride control systems but not maintenance analytics. Judges will ask "what about the rides?".

**Context:** Rides appear in C4 L1, Park Operations ("zones, rides"), the companion ("Is the Ferris wheel OK for a 4-year-old") and queue counters. Missing: state telemetry, downtime analytics, link to safety. Start with a paragraph in requirements/05 "Out of scope" and a "Phase 4+" row in the roadmap. Do not add a sixth scenario before submission (scope decision of the 2026-09-07 review: five scenarios stand).

**Effort:** M
**Priority:** P3
**Depends on:** Delivery roadmap (README); A10.

### Per-animal re-identification in group enclosures (Phase 3+)

**What:** Research spike: can individuals in group enclosures be identified (tags/rings + CV, or re-ID models) accurately enough for per-animal baselines? Defines the entry criterion for S1 Phase 3.

**Why:** S1 was split into per-animal (solitary/tagged) and per-enclosure (group) modes because animal re-identification is an open research problem (occlusion, low inter-identity variation). Full S1 value ("this bird has eaten less for three days") needs identity.

**Context:** Pick 2 enclosures (meerkats, aviary), collect 2 weeks of footage, measure re-ID accuracy with and without tags. Entry threshold: identity accuracy >= 0.95 over a daily window. Literature: RoVF (IJCV 2025), polar-bear zoo behaviour study (PMC 2022).

**Effort:** L
**Priority:** P3
**Depends on:** S1 Phase 2 vision in production; golden set with identity labels; keeper-hours budget (human roles table).

### Ticketing platform vendor evaluation — prerequisite for Phase 0

**What:** Landscape review of 3-5 attraction-ticketing products against the full criteria table of the "Ticketing platform: adopt, not build" ADR: offline gate validation with signed credentials, local ledger and reconciliation; season/family passes with a group counter; `GateEntered` with `persons_admitted`; webhooks/events within seconds; price API with checkout lock; **timed-entry slots and a daily cap with an API returning effective cap and sold count**; **POS included or per-transaction export/webhook with the FR-2.6 fields**; **same-day upgrade credit** (once per ticket, valid today, void on refund, 7-day validity); **signed webhooks with replay protection**; **vendor sandbox** covering webhooks, cap API and credit; GDPR export/delete; open-data exit; PCI scope at the vendor; price at 15,000/day. Output: alternatives table in the ADR, go/no-go on the "build it ourselves" fallback, and a **fallback matrix**: for each criterion no vendor meets, what changes in Phase 0 scope, staffing and the TCO table (e.g. no POS export → daily totals per outlet and A13's fallback; no upgrade credit → the flywheel's second lever becomes a manual desk process; no cap API → cap enforced by closing online sales manually).

**Why:** Adopt-not-build was accepted on criteria, not on market facts. The business-case review added six criteria the market may not offer together; if the combination is rare, the fallback triggers and changes Phase 0, R9 and the payback arithmetic in requirements/08.

**Context:** ADR-0011 becomes a product requirement; requirements/08 §1 and §3 depend on the cap and the credit. 2-3 days; feeds the TCO table and the season-1 re-issue of requirements/08.

**Effort:** M
**Priority:** P1 — prerequisite for Phase 0
**Depends on:** Ticketing ADR written (done); requirements/08 published.

### Design review of the Estate daily report

**What:** Run `/plan-design-review` on the Estate daily report specification in hld/core (information architecture, states, footer, approval semantics) and on the two companion prompts it adds (quiet-day offer, upgrade-to-pass). Output: a reviewed one-screen layout for mobile and e-mail, copy for the provisional / first-season / closed-day states, and the recommendation wording per rule.

**Why:** The report is the one surface where all five scenarios meet the person who pays; a one-screen, no-chart, provisional-by-word design was decided but not designed. Colour-only provisional marking and chart creep are the two ways it goes wrong.

**Context:** Spec in hld/core/README.md "Estate daily report"; IA fixed to five blocks and a freshness footer; template auto-sends at 21:00, phrasing optional.

**Effort:** S
**Priority:** P3 (becomes P1 before the Phase 1 build)
**Depends on:** requirements/08 and the hld/core report section landing (done).

## Infrastructure

### LoRaWAN site survey and measured SF distribution

**What:** Before buying sensors: deploy 1-2 test gateways and 10-20 test nodes at the estate edges; measure real spreading-factor distribution, RSSI/SNR and packet loss. Replace the "70% SF7-9" assumption in the capacity check with measured values; fix gateway count and placement. Same visit verifies A2 (cellular coverage).

**Why:** The airtime calculation stands on an SF assumption; a 4x airtime error (SF7 -> SF10) changes gateway count and battery life (ADR-0002 promises >= 2 years).

**Context:** Capacity check row is marked "assumption until site survey". The LoRaWAN network server container collects the survey metrics. Output: updated capacity row + gateway map in hld/core/edge-and-connectivity.md.

**Effort:** S (plan) / M (field work)
**Priority:** P2
**Depends on:** Physical access to the estate; LoRaWAN network server container.

## Completed
