# Appendix · Cost model (TCO, ±50%)

Order-of-magnitude CAPEX and OPEX so that NFR-COST-2 can be checked and the Countess can see what she is buying. Procurement figures, not architecture: every number is an assumption to be replaced by a quote. The architectural constraint it serves is the per-visitor ceiling in [requirements/04](../requirements/04-non-functional-requirements.md#cost-model-tco-50), and the [business-case model](business-case-model.md) uses this table as its OPEX curve.

Order-of-magnitude figures so that NFR-COST-2 can be checked and so the Countess sees what she is buying. All numbers are assumptions to be replaced by quotes. The business case — payback, growth, what the estate must fund besides the platform — is in [08](../requirements/08-business-case.md), which uses this table as a curve: **OPEX(V) ≈ €595k fixed + €0.177 per visitor-day**, within ≈ 2% of both columns below, so that every cumulative figure there follows the ladder rather than two end points.

**CAPEX** (one-off, mostly Phase 0–1)

| Component | Estimate | Phase |
| --- | --- | --- |
| 2 GPU-class edge servers (N+1) | €16k | 0 |
| Broker witness + LoRaWAN server host, UPS, rack, PoE switching | €25k | 0 |
| Gate readers (6), if not supplied by the ticketing platform | €12k | 0 |
| Cameras, 110 incl. IR (55 primary in Phase 0, 55 secondary later) | €44k | 0 / 2 |
| Enclosure sensors (300 × €150) and anonymous counters (150 × €600, LiDAR/thermal) | €135k | 0–1 |
| LoRaWAN gateways (3) | €5k | 0 |
| DECT base stations and 40 handsets/pagers | €15k | 0 |
| Cabling, installation, site survey | €60k | 0 |
| Token readers (≈ 40: rides, outlets, zone boundaries) + issuance and encoding at the gates | €25k | 0 |
| Directional radio bridges (4 links, incl. mast, power and survey) | €12k | 0–1 |
| Ride condition sensors (≈ 20 instrumentable rides × ≈ €600: cycle counter, current clamp, 2 temperature probes, radio node) | €12k | 1 |
| Delay-tolerant pickup collector on the land train (one unit for the estate) | €8k | 1 |
| **Total CAPEX** | **≈ €367k** (≈ €73k/yr over 5 years) | |

The last four lines are what the merged AI portfolio added: ≈ €57k, or 18% on the original CAPEX. The land train itself is **not** here — it is an estate asset bought out of the accessibility and capacity case (A18), and the platform pays only for the collector it carries ([ADR-0020](../adrs/ADR-0020-internal-transport-and-autonomy.md) §1).

**OPEX** (per year)

| Component | At 5,000/day | At 15,000/day | Notes |
| --- | --- | --- | --- |
| Cloud: event backbone, databases, object storage, IoT ingestion, own-model hosting | €40k | €70k | Ingestion itself ≈ $600/yr ([capacity table](../hld/core/edge-and-connectivity.md#capacity-check-at-15000-visitorsday-by-traffic-class)) |
| Hosted LLMs + open-weight endpoint (planned spend) | €10k | €50k | **Token arithmetic behind the €50k: ≈ €34,800/yr** of model calls at 15,000/day, leaving a 44% overrun before the line is exceeded, so the top of the ±50% price band is not inside it ([generative cost](generative-cost.md)). Phase 1 runs FAQ answers only; day planning arrives in Phase 2, which is what grows the line. Cap is 2% of revenue (≈ €600k at €30M); the plan sits far below the cap |
| Cellular (2 operators) + fixed-line fallback + per-remote-site critical-class links | €6k | €6k | Each remote enclosure keeps its own cellular link for the critical class alone, which is kilobytes a day ([ADR-0019](../adrs/ADR-0019-reach-for-remote-enclosures.md)) |
| Visitor tokens: replacement stock, issuance and hygiene | €12k | €30k | Scales with admissions; tokens are returned and recycled, so this is loss and cleaning rather than a tag per visitor |
| Metric layer, agent traces and token-tap storage | €5k | €12k | Observability and storage on top of the base cloud line; the agents' own token spend is inside the LLM line at ≈ €508/yr |
| Ticketing platform fees (assumed €0.15/ticket or 1.5–3% of ticket revenue) | €225k | €675k | Largest line after the team; a selection criterion in [ADR-0012](../adrs/ADR-0012-ticketing-platform-adopt-not-build.md) |
| Team: 5 engineers, loaded | €500k | €500k | Does not grow with attendance — the point of adopt-not-build |
| Hardware maintenance and spares (10% of CAPEX) | €37k | €37k | |
| **Total OPEX** | **≈ €860k** | **≈ €1.39M** | |

**Per visitor** (CAPEX/5 + OPEX ÷ visitors/yr at 300 open days): ≈ **€0.62** at 5,000/day, ≈ **€0.33** at 15,000/day — inside NFR-COST-2 with the ±50% band. Ticketing fees and the team are ~82% of the total; the AI is not the expensive part, and the four agents are ≈ €508 of it.

