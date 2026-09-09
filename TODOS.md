# TODOS

## Architecture

### Ride downtime analytics spike (Phase 4+)

**What:** Spike, not a scenario: on cycle counters alone, can downtime and scheduling analytics beat the current maintenance calendar? Entry threshold before any model: 12 months of `RideStatusChanged` and cycle counts, and a measurable baseline (unplanned downtime hours per ride per season). Predictive maintenance on vibration stays out until A10 is retested per ride.

**Why:** The scope question is now answered in the submission — [requirements/05 "Out of scope"](requirements/05-assumptions-and-constraints.md#out-of-scope) states why the 40 rides carry one event and no AI (A10 blocks the instrumentation; ride safety is certified inspection, with no tier-1 equivalent), and the roadmap carries FR-2.5 at Phase 4+. What remains is the analytics itself.

**Effort:** M
**Priority:** P3
**Depends on:** 12 months of ride status events; A10 retested per ride; roadmap Phase 4+ entry.

### Per-animal re-identification in group enclosures (Phase 3+)

**What:** Research spike: can individuals in group enclosures be identified (tags/rings + CV, or re-ID models) accurately enough for per-animal baselines? Defines the entry criterion for S1 Phase 3.

**Why:** S1 was split into per-animal (solitary/tagged) and per-enclosure (group) modes because animal re-identification is an open research problem (occlusion, low inter-identity variation). Full S1 value ("this bird has eaten less for three days") needs identity.

**Context:** Pick 2 enclosures (meerkats, aviary), collect 2 weeks of footage, measure re-ID accuracy with and without tags. Entry threshold: identity accuracy >= 0.95 over a daily window. Literature: RoVF (IJCV 2025), polar-bear zoo behaviour study (PMC 2022).

**Effort:** L
**Priority:** P3
**Depends on:** S1 Phase 2 vision in production; golden set with identity labels; keeper-hours budget (human roles table).

### Ticketing platform vendor evaluation — prerequisite for Phase 0

**What:** Landscape review of 3-5 attraction-ticketing products against the 16 must-have criteria in the "Ticketing platform: adopt, not build" ADR — offline gate validation, family/season passes, `GateEntered` with `persons_admitted`, webhooks within seconds, price API with checkout lock, timed-entry slots and cap API, POS export with the FR-2.6 fields, upgrade credit voucher, signed webhooks, vendor sandbox, GDPR export/delete, open-data exit, PCI scope at the vendor, price at 15,000/day, and the three credential criteria — closed-loop cashless card-on-file with an offline floor limit, tap emitting `PurchaseRecorded`, and revocation with re-issue within 60 s.

**Output:** an alternatives table in the ADR, a go/no-go on the build-it-ourselves fallback, and a **fallback matrix** — for each criterion no vendor meets, what changes in Phase 0 scope, staffing and the TCO table. For example: no POS export → daily totals per outlet and A13's fallback; no upgrade credit → the flywheel's second lever becomes a desk process; no cap API → the cap is enforced by closing online sales by hand.

**Why:** Adopt-not-build was accepted on criteria, not on market facts, and nine of the sixteen may not be offered together. If the combination is rare the fallback triggers, changing Phase 0 scope, R9 and the payback arithmetic.

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

### Export the mermaid diagrams to SVG for the video

**What:** Have CI write an SVG per mermaid block into `diagrams/exports/`, alongside the render check that already runs.

**Why:** [`video/`](video/README.md) is a real deliverable and the semi-final video cannot show a GitHub-rendered mermaid block — a slide needs a file. The same applies to any PDF or printed version of the submission.

**Context:** `scripts/check_mermaid.py` already installs and drives `@mermaid-js/mermaid-cli` in its own CI job, so producing an SVG is a flag on a call that is already being made rather than a new tool or a new job. Keep the exports out of the lint gate: they are build output, not content, so a stale export must not be able to fail the docs job.

**Effort:** S
**Priority:** P3
**Depends on:** Nothing.

### Bump the CI actions off Node.js 20

**What:** Update `actions/checkout` and `astral-sh/setup-uv` in [`.github/workflows/lint.yml`](.github/workflows/lint.yml) to versions that target a supported Node runtime.

**Why:** The failure mode is the dangerous shape: when GitHub stops force-running these actions on Node 24, the workflow does not go red — it stops running, and with it the gate that checks every link, id, count and derived number across 50 files. A gate that disappears is worse than one that fails.

**Context:** Observed on run 34355341654 on this branch: *"Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout@v4, astral-sh/setup-uv@v5."* Both jobs pass today. Bump the two actions and confirm both jobs still pass; the `mermaid` job is the fragile one because it installs a Chromium at run time. Deliberately kept out of the content branch so the architecture diff stays readable.

**Effort:** S
**Priority:** P2
**Depends on:** Nothing.

## Completed
