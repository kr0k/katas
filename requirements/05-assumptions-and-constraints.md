# 05 · Assumptions & Constraints

The judges cannot talk to us, so we state what we assumed. Each assumption is tagged with what changes if it is wrong.

## Given constraints (from the brief)
- Wi-Fi coverage on the estate is patchy.
- Cloud services may be used; a way to get data from the estate to the cloud is our problem.
- There is budget for MQTT-capable hardware throughout the park.
- 40 rides, 55 enclosures, 200+ animals, ~5,000 visitors/day today, ≥15,000 target in 3 years.

## Assumptions

| # | Assumption | If wrong… |
| --- | --- | --- |
| A1 | **Greenfield.** No legacy ticketing or animal records system to integrate; paper records exist and can be digitised once. | Add an integration/anti-corruption layer per legacy system; timeline extends. |
| A2 | **Cellular coverage exists** at a few points on the estate (enough for a backhaul link). | Fall back to a fixed line or satellite for backhaul; store-and-forward design already tolerates intermittent uplink. |
| A3 | **A veterinarian is available** (staff or on call) to act as the human in the loop for welfare alerts, for the hours in the [human roles table](../hld/ai-platform/README.md#humans-in-the-loop-who-does-what) (2 h/week in Phase 1 rising to ~8 h/week in Phase 3). | Review queue routes to head keeper; escalation to external vet; confidence thresholds set more conservatively; Phase 3 per-animal vision delayed. |
| A4 | **Staff have smartphones or can be issued rugged devices** that work on the local network. | Add fixed kiosks/radios for alerts. |
| A5 | **EU jurisdiction (GDPR applies).** | Privacy design is GDPR-grade regardless; other regimes are generally less strict. |
| A6 | **Seasonality is strong** (summer peaks, winter troughs). Forecasting models need ≥ 1 year of data to be reliable; until then, heuristics. | If flat, forecasting matures faster. |
| A7 | **Cameras can be installed in enclosures** without harming animals; some species (e.g. nocturnal) need infrared. | Fall back to sensor-only monitoring (scales, water, movement) for those enclosures. |
| A8 | **Team size ≤ 5 engineers** plus ops/keeper staff. | Managed services preferred over self-hosting throughout. |
| A9 | **Visitors mostly arrive as families** with children. | Companion persona and pass structure adjust; architecture does not. |
| A10 | **Historic rides cannot be heavily instrumented** (heritage constraints); only non-invasive sensors (cycle counters, vibration). | Ride maintenance analytics (FR-2.5) stays a COULD. |
| A11 | **Individuals in group enclosures cannot be reliably re-identified by camera.** Per-animal monitoring (S1) therefore covers solitary animals and animals with tags, rings or collars — roughly 35 of the 55 enclosures; group enclosures (meerkats, aviary, fish) are monitored per enclosure. | If re-identification proves accurate enough in the Phase 3+ spike ([`TODOS.md`](../TODOS.md)), per-animal monitoring extends to groups; the architecture does not change, the feature extractor and baselines do. |
| A12 | **An HR / rostering system exists or will be procured** by the estate. We import staff, skills, certifications and availability from it and export approved staffing plans to it; labour rules (max hours, breaks, required certifications) are policy configuration we own. | Park Operations keeps a minimal staff register itself; roster export becomes a spreadsheet; payroll stays out of scope either way. |

## Out of scope
- Ride control systems and their certification.
- Payroll and HR beyond importing staff/skills/availability and exporting staffing plans (A12).
- Physical security (CCTV for theft) — only animal enclosure cameras are in scope.
