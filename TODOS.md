# TODOS

## Architecture

### Ride operations & maintenance domain

**What:** Decide where ride operations & maintenance live in the architecture: a sixth scenario (predictive maintenance from vibration/cycle counters, FR-2.5) or an explicit "why rides are only `RideStatusChanged` in this submission" paragraph.

**Why:** G6 makes ride safety non-negotiable and 40 historic rides are half the attraction, yet rides get one event and no AI. A10 limits instrumentation; 05 excludes ride control systems but not maintenance analytics. Judges will ask "what about the rides?".

**Context:** Rides appear in C4 L1, Park Operations ("zones, rides"), the companion ("Is the Ferris wheel OK for a 4-year-old") and queue counters. Missing: state telemetry, downtime analytics, link to safety. Start with a paragraph in requirements/05 "Out of scope" and a "Phase 4+" row in the roadmap. Do not add a sixth scenario before submission (scope decision D4, 2026-09-07).

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

### Ticketing platform vendor evaluation

**What:** Landscape review of 3-5 attraction-ticketing products against the criteria in the "Ticketing platform: adopt, not build" ADR (offline gate validation with signed credentials + reconciliation, season/family passes with group counter, webhooks/events, GDPR export/delete, open-data exit, price at 15,000/day). Output: alternatives table in the ADR and go/no-go on the "build it ourselves" fallback.

**Why:** Adopt-not-build was accepted on criteria, not on market facts. If offline validation is rare among vendors, the fallback triggers and changes Phase 0 and R9.

**Context:** ADR-0011 becomes a product requirement. 1-2 days; feeds the TCO table.

**Effort:** M
**Priority:** P2
**Depends on:** Ticketing ADR written.

## Infrastructure

### LoRaWAN site survey and measured SF distribution

**What:** Before buying sensors: deploy 1-2 test gateways and 10-20 test nodes at the estate edges; measure real spreading-factor distribution, RSSI/SNR and packet loss. Replace the "70% SF7-9" assumption in the capacity check with measured values; fix gateway count and placement. Same visit verifies A2 (cellular coverage).

**Why:** The airtime calculation stands on an SF assumption; a 4x airtime error (SF7 -> SF10) changes gateway count and battery life (ADR-0002 promises >= 2 years).

**Context:** Capacity check row is marked "assumption until site survey". The LoRaWAN network server container collects the survey metrics. Output: updated capacity row + gateway map in hld/core/edge-and-connectivity.md.

**Effort:** S (plan) / M (field work)
**Priority:** P2
**Depends on:** Physical access to the estate; LoRaWAN network server container.

## Completed
