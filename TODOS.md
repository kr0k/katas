# TODOS

## Architecture

### Heritage assessment per ride, before any sensor is fitted

**What:** Walk all 40 rides with the conservation officer and the certified engineer and record, per ride, which of the four non-invasive sensor classes may be fitted and how (cycle counter, clamp-on current, surface temperature, run-hours from the controller). Output: an instrumentable count, a fitting method per ride, and the refusals with their reasons.

**Why:** A19 assumes roughly half the forty can take sensors, and [S8](hld/scenarios/ride-condition-monitoring/README.md)'s whole coverage and its CAPEX line follow from that number. Below about ten instrumented rides the capability is not worth its sensors and the threshold rules stand alone ([SP-11](hld/architecture-evaluation.md#sensitivity-points)).

**Context:** Vibration spectra are out of scope by A10 and should not be re-litigated here; the question is only which of the four classes each ride can take. The result also fixes the ride-sensor line in the [cost model](appendix/cost-model.md).

**Effort:** S (plan) / M (field work)
**Priority:** P2 — before Phase 1 procurement
**Depends on:** Conservation officer's availability; certified engineer; the Phase 0 site visit.

### Token support as a ticketing-vendor criterion, and the issuance process

**What:** Add passive RFID as a credential form factor to the vendor evaluation below — can the platform issue, validate offline and revoke a token against the same credential as a QR code, and does its POS take a token tap settled by card-on-file? Separately, design the gate process: issuance, return, recycling and re-keying, hygiene, and what happens when a family loses one mid-visit.

**Why:** [ADR-0018](adrs/ADR-0018-visitor-token-and-anonymised-paths.md) treats the token as a second form factor for the vendor's credential rather than a second ticketing system, and that only holds if the vendor supports it. The gate process is a queue the estate now owns, and it is the most likely place for the token to fail in practice rather than in design.

**Effort:** S (criterion) / M (process)
**Priority:** P1 — the criterion is part of the vendor evaluation; the process before Phase 0 go-live
**Depends on:** Ticketing vendor evaluation; DPIA update for the tap consent.

### Line-of-sight survey for the remote enclosures

**What:** As part of the Phase 0 site survey: identify which enclosures lie beyond LoRaWAN and Wi-Fi reach, and for each, whether a directional bridge has Fresnel clearance with a margin for vegetation growth and new structures. Output: the remote-site count, the bridge count and placement, and the list that falls to delay-tolerant pickup.

**Why:** A17 is an assumption with a 4-to-8 range, and it decides whether the estate operates two delivery channels or three ([SP-9](hld/architecture-evaluation.md#sensitivity-points), [ADR-0019](adrs/ADR-0019-reach-for-remote-enclosures.md) §4). Below two no-line-of-sight sites the pickup collector is not bought at all.

**Effort:** S (plan) / M (field work)
**Priority:** P2 — same visit as the LoRaWAN survey below
**Depends on:** Physical access to the estate; A18's decision on the land train.

### Per-animal re-identification in group enclosures (Phase 3+)

**What:** Research spike: can individuals in group enclosures be identified (tags/rings + CV, or re-ID models) accurately enough for per-animal baselines? Defines the entry criterion for S1 Phase 3.

**Why:** S1 was split into per-animal (solitary/tagged) and per-enclosure (group) modes because animal re-identification is an open research problem (occlusion, low inter-identity variation). Full S1 value ("this bird has eaten less for three days") needs identity.

**Context:** Pick 2 enclosures (meerkats, aviary), collect 2 weeks of footage, measure re-ID accuracy with and without tags. Entry threshold: identity accuracy >= 0.95 over a daily window. Literature: RoVF (IJCV 2025), polar-bear zoo behaviour study (PMC 2022).

**Effort:** L
**Priority:** P3
**Depends on:** S1 Phase 2 vision in production; golden set with identity labels; keeper-hours budget (human roles table).

### Ticketing platform vendor evaluation — prerequisite for Phase 0

**What:** Landscape review of 3-5 attraction-ticketing products against the 13 must-have criteria in the "Ticketing platform: adopt, not build" ADR — offline gate validation, family/season passes, `GateEntered` with `persons_admitted`, webhooks within seconds, price API with checkout lock, timed-entry slots and cap API, POS export with the FR-2.6 fields, upgrade credit voucher, signed webhooks, vendor sandbox, GDPR export/delete, open-data exit, PCI scope at the vendor, price at 15,000/day.

**Output:** an alternatives table in the ADR, a go/no-go on the build-it-ourselves fallback, and a **fallback matrix** — for each criterion no vendor meets, what changes in Phase 0 scope, staffing and the TCO table. For example: no POS export → daily totals per outlet and A13's fallback; no upgrade credit → the flywheel's second lever becomes a desk process; no cap API → the cap is enforced by closing online sales by hand.

**Why:** Adopt-not-build was accepted on criteria, not on market facts, and six of the thirteen may not be offered together. If the combination is rare the fallback triggers, changing Phase 0 scope, R9 and the payback arithmetic.

**Context:** ADR-0011 becomes a product requirement; requirements/08 §1 and §3 depend on the cap and the credit. 2-3 days; feeds the TCO table and the season-1 re-issue of requirements/08.

**Effort:** M
**Priority:** P1 — prerequisite for Phase 0
**Depends on:** Ticketing ADR written (done); requirements/08 published.

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
