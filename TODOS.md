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

**What:** Landscape review of 3-5 attraction-ticketing products against the full criteria table of the "Ticketing platform: adopt, not build" ADR: offline gate validation with signed credentials, local ledger and reconciliation; season/family passes with a group counter; `GateEntered` with `persons_admitted`; webhooks/events within seconds; price API with checkout lock; **timed-entry slots and a daily cap with an API returning effective cap and sold count, plus pass-holder slot reservations on capacity-managed days carried in the credential**; **POS included or per-transaction export/webhook with the FR-2.6 fields**; **upgrade credit voucher** (once per ticket scanned in today, redeemable within 7 days, void on refund, pass starts on the visit date); **signed webhooks** (HMAC-SHA256, signed-at window, re-signed retries with backoff on 429, key rotation); **vendor sandbox** covering webhooks incl. replay and backlog, cap/reservation API and voucher; GDPR export/delete; open-data exit; PCI scope at the vendor; price at 15,000/day. Output: alternatives table in the ADR, go/no-go on the "build it ourselves" fallback, and a **fallback matrix**: for each criterion no vendor meets, what changes in Phase 0 scope, staffing and the TCO table (e.g. no POS export → daily totals per outlet and A13's fallback; no upgrade credit → the flywheel's second lever becomes a manual desk process; no cap API → cap enforced by closing online sales manually).

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

## Business case

### Exit survey design for the anonymous repeat estimate

**What:** Specify the quarterly exit survey that requirements/05 A14 and requirements/06 ¹ rely on: questions (visited in the last 12 months? group size? how did you arrive?), sample size and stratification (≈ 400 answers per quarter for ±5 points on the repeat share; by day type and ticket type), staffing at the exits, and how the self-reported estimate is combined with identified households (pass or account) into one repeat-share figure with a stated error.

**Why:** Anonymous day-ticket visitors cannot be linked across visits, so the survey is the only source of the repeat share for roughly half the guests in year 1 and of the party size (A9). Without a sampling design the "~10%" carries no interval and the season-1 re-issue of requirements/08 would feed noise into the cohort model.

**Context:** The same questionnaire yields car share and parking turns for A14. Bias towards loyal respondents must be estimated (e.g. by comparing the identified-household subsample with the survey). Hours go into the human-roles table.

**Effort:** S
**Priority:** P3
**Depends on:** requirements/08 §0 definitions (done); Phase 0 exit staffing.

### Estate-level P&L at the Y3 run rate

**What:** One table in `scripts/business_case.py`, alongside the platform payback: revenue from the cohort model minus every cost in requirements/08 §5 — parking or park-and-ride, F&B seating, gate lanes, marketing at a measured customer-acquisition cost per channel, step staffing at the estate's FTE cost, and the platform — once the site survey and procurement have turned the orders of magnitude into prices.

**Why:** requirements/08 is deliberately the platform's payback, not an estate P&L; but the Countess's question (G1) is whether the estate pays at 15,000 a day, and that question needs an owner and a trigger rather than a footnote.

**Context:** Inputs: price per parking space or park-and-ride contract, price per F&B seat, FTE cost, CAC by channel, vendor fees from the evaluation. Trigger: Phase 2 entry, together with the season-1 re-issue of requirements/08 (§6). Risk: read as a promise of profit — label it a scenario with the same assumption → measured-by discipline.

**Effort:** M
**Priority:** P3
**Depends on:** LoRaWAN/site survey TODO; ticketing vendor evaluation TODO; season-1 measured values.

## Infrastructure

### LoRaWAN site survey and measured SF distribution

**What:** Before buying sensors: deploy 1-2 test gateways and 10-20 test nodes at the estate edges; measure real spreading-factor distribution, RSSI/SNR and packet loss. Replace the "70% SF7-9" assumption in the capacity check with measured values; fix gateway count and placement. Same visit verifies A2 (cellular coverage).

**Why:** The airtime calculation stands on an SF assumption; a 4x airtime error (SF7 -> SF10) changes gateway count and battery life (ADR-0002 promises >= 2 years).

**Context:** Capacity check row is marked "assumption until site survey". The LoRaWAN network server container collects the survey metrics. Output: updated capacity row + gateway map in hld/core/edge-and-connectivity.md.

**Effort:** S (plan) / M (field work)
**Priority:** P2
**Depends on:** Physical access to the estate; LoRaWAN network server container.

## Completed
