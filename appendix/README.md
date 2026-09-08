# Appendix

Work the architecture rests on but does not consist of: financial modelling, product specification, vendor rules, radio planning, capacity arithmetic and operational runbooks. Each document is referenced from the place in the architecture that uses its conclusion, and each states which architectural claim it supports.

| Document | What it holds | Whose work it is | Referenced from |
| --- | --- | --- | --- |
| [Business-case model](business-case-model.md) | Attendance ladder, capacity constraints, cohort growth model, payback simulation, market sanity check | Finance / product | [requirements/08](../requirements/08-business-case.md) summary; NFR-SCL-1 and NFR-COST-2 take three figures from it |
| [Generative-AI cost model](generative-cost.md) | Token arithmetic per request class, tier prices, cache counterfactual, escalation sensitivity | Capacity planning | [AI platform → what the generative capabilities cost](../hld/ai-platform/README.md#what-the-generative-capabilities-cost) |
| [Estate daily report specification](estate-daily-report.md) | Information architecture, five delivery states, the 20:30–21:00 timeline, report test cases | Product / UX | [hld/core → Estate daily report](../hld/core/README.md#estate-daily-report), FR-2.7 |
| [Ticketing rules the platform executes](ticketing-rules.md) | Webhook signing and reconciliation, cap and reservation mechanics, upgrade-credit rules (P-I7) | Vendor product rules | [hld/core → Ticketing & Access additions](../hld/core/README.md#ticketing--access-additions-purchases-cap-and-upgrade-credit), [ADR-0012](../adrs/ADR-0012-ticketing-platform-adopt-not-build.md) |
| [Business data health, verification and rollout](data-health-and-verification.md) | Metric thresholds with runbooks, test levels, feature-flag order | SRE / QA | [hld/core](../hld/core/README.md#business-data-health-and-verification), GD-4, GD-14, GD-15 |
| [Cost model (TCO)](cost-model.md) | Line-by-line CAPEX and OPEX at both run rates, per-visitor cost | Procurement / finance | [requirements/04 → cost model](../requirements/04-non-functional-requirements.md#cost-model-tco-50), NFR-COST-2 |
| [LoRaWAN airtime budget](lorawan-airtime.md) | Spreading-factor distribution, channel load, duty cycle, gateway count, battery life | Radio planning | [Edge & connectivity → LoRaWAN airtime](../hld/core/edge-and-connectivity.md#lorawan-airtime) |

Two of these are generated from [`scripts/business_case.py`](../scripts/business_case.py) — the business-case model and the generative-cost model — and `uv run scripts/lint_docs.py` fails if a table or a quoted figure drifts from the model. The rest are assumptions until the Phase 0 site survey and the ticketing-vendor evaluation ([TODOS.md](../TODOS.md)).
