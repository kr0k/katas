# 06 · Suggested OKRs

> The brief gives one number (5,000 → 15,000 visitors/day). We propose the rest so that every AI scenario can be judged against a target. "Current" values are **estimates/assumptions**; the first quarter of operation replaces them with measured baselines. Where a 12-month cell reads **base / stretch**, *base* is what the growth model in [08](08-business-case.md) yields under its stated assumptions and *stretch* is the original target; the gap between them is what marketing and a stronger flywheel must close. The forecast does not become the target: the 36-month targets are unchanged, and where the model's year-3 value falls short a note says so.

| Objective | Key result | Current (est.) | Target (12 mo) | Target (36 mo) | Scenario |
| --- | --- | --- | --- | --- | --- |
| **1. Grow attendance and revenue** | 1.1 Average visitors per day (visitor-days) | 5,000 | 6,500 / 8,000 | 15,000 | S5, S4 |
| | 1.2 Returning share of households — pass or opt-in account — with ≥ 2 visits in 12 mo¹ | ~10% | 10% / 25% | 40% — model: ≈ 32%, growth dilutes the flywheel ([08 §3](08-business-case.md#3-the-membership-flywheel)) | S4 |
| | 1.3 Family and season passes as share of admissions (visitor-days admitted on passes ÷ all admissions) | ~20% | 19% / 40% | ≥ 50% — model: ≈ 41% ([08 §2](08-business-case.md#2-where-the-growth-comes-from)) | S4, S5 |
| | 1.4 Revenue per visitor-day (admission + on-site, cash)²; second line: revenue per unique household per year (estimate) | baseline | ≥ baseline | not below baseline; per household +30% | S4, S5 |
| | 1.5 Weekday / weekend attendance ratio³ (fill quiet days) — S5's primary objective | 0.35 | 0.38 / 0.5 | 0.6 | S5, S3 |
| | 1.6 Season-pass renewal rate (households renewing ÷ households whose pass expired)⁴ | n/a | baseline (first cohort) | ≥ 70% (ambitious) | S4, S5 |
| **2. Run the park on data, not guesswork** | 2.1 Zones with live popularity data | 0% | 100% | 100% | Core |
| | 2.2 p90 queue time on top-10 rides | unknown | ≤ 20 min | ≤ 15 min | S3, S4 |
| | 2.3 Forecast accuracy, zone footfall next day (MAPE) | n/a | ≤ 25% | ≤ 15% | S3 |
| | 2.4 Staff hours in zones with no visitors | unknown | −30% | −50% | S3 |
| **3. Healthy animals at lower cost** | 3.1 Time from first anomaly to vet review | days | ≤ 4 h | ≤ 1 h | S1 |
| | 3.2 Veterinary cost per animal per year | baseline | −15% | −30% | S1 |
| | 3.3 Feeding events logged automatically | 0% | 90% | 98% | S1 |
| | 3.4 Piranha population estimate error vs. census of record (full count at planned tank maintenance, ledger-adjusted between censuses) | ±30% (manual count) | ±10% | ±5% | S2 |
| | 3.5 Vet override rate on AI-flagged reviews (proxy for false positives) | n/a | ≤ 40% | ≤ 25% | S1 |
| **4. Keep everyone safe** | 4.1 Safety alert delivery p99 (local) | n/a | ≤ 5 s | ≤ 5 s | Core |
| | 4.2 Safety incidents involving animals | 0 | 0 | 0 | Core |
| **5. Keep the platform affordable and evolvable** | 5.1 AI spend as share of revenue | n/a | ≤ 2% | ≤ 1.5% | AI platform |
| | 5.2 Time to swap a model/provider for a capability | n/a | ≤ 1 day | ≤ 1 day | AI platform |
| | 5.3 AI capabilities with a passing eval suite | n/a | 100% | 100% | AI platform |

¹ Measured per credential and account from the ticketing platform's export and `GateEntered`; anonymous day tickets are covered by a quarterly exit survey — a self-report, not a link across visits — and labelled as an estimate (A14). The growth model works in households; persons only via the party size of 3.5 ([08 §0](08-business-case.md#0-how-to-read-the-numbers)). A household holding both a pass and an account is counted once.
² Primary line: cash revenue from `TicketPurchased` + `PurchaseRecorded` (FR-2.6) ÷ Σ `GateEntered.persons_admitted` — numerator and denominator from the same population, so a growing opt-in share cannot move it. Second line: the same cash ÷ the model's estimate of unique households ([08 §3](08-business-case.md#3-the-membership-flywheel)), reported as an estimate; revenue of identified households ÷ identified households is a segment metric, not this OKR. Admissions never appear as purchases — there is no admission category — so nothing is double-counted. **OKR = year, guardrail = week:** the S5 experiment cannot wait for an annual figure and uses its own weekly operational guardrail — contribution per visitor-day on discounted blocks not below the 0% blocks − 10% ([thresholds table](../hld/ai-platform/README.md#thresholds-and-cadences-source-of-truth)).
³ r = average weekday visitor-days ÷ average weekend-day visitor-days, per open day. Weekly visitor-days = W(5r + 2), W the weekend-day average ([08 §0](08-business-case.md#0-how-to-read-the-numbers)).
⁴ Measured from `PassRenewed` ÷ passes expiring, which exists from Phase 0: the first cohort's renewal is measurable at month 12 and targeted from Phase 3. It covers pass holders only; repeaters without a pass have their own retention rate in the model ([08 §3](08-business-case.md#3-the-membership-flywheel)). Zoo-membership renewal norms are 50–70% ([PassPlay 2026](https://passplay.io/blog/posts/what-museum-and-zoo-members-want-from-membership-in-2026)), so 70% is labelled ambitious.

Each scenario's README states which key results it moves and how we will measure it.
