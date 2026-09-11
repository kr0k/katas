# The AI portfolio: twenty-three applications, eight scenarios, one platform

This page is the inventory. It exists because "how much AI is in this?" and "why *that* AI?" are two
different questions, and the scenario folders answer the second one well and the first one not at all.

## The lens: where AI has to earn its place

The brief's existential goal is profitability — the alternative is the gnome business. Animal welfare
is the estate's *product* and its most expensive asset, but it is a cost-avoidance story, not a revenue
one. The revenue arithmetic is three factors, and the portfolio is arranged against them:

> **Profit ≈ attendance × spend per visitor-day × repeat rate**

| Factor | What moves it here | Who is credited |
| --- | --- | --- |
| **Attendance** | Quiet-day pricing (S5), content that reaches households marketing has not (S7), capacity that does not collapse on a peak day (S3, FR-1.7) | Mostly marketing and the estate. The platform claims none of the new-audience growth (R18) and measures all of it |
| **Spend per visitor-day** | Shorter queues leave more of the day for food and retail (S3, S4); the companion's route passes commercial zones; the token makes paying a tap (ADR-0018) | Shared, and only the S5 discounted blocks and the S4 nudge cohort are cleanly attributable (R20) |
| **Repeat rate** | Recognising a returning household at all (ADR-0018), nudges worth acting on (S4), a day that was worth repeating (S1, S3, S8) | The flywheel in [08 §3](../../appendix/business-case-model.md#3-the-membership-flywheel), which is the platform's actual growth bet |

Welfare sits underneath all three rather than inside one: a collection that is visibly healthy is the
product, and a dead rare animal is a reputational and financial event, not a line in a maintenance
budget.

## The inventory

AI class drives verification, so it is a column: **classical** is deterministic given its inputs and
tested like software; **CV** is probabilistic and gets bands and a human; **generative** is
non-deterministic and gets grounding, guardrails and continuous evaluation; an **agent** is an
orchestrator over the other three ([ADR-0013](../../adrs/ADR-0013-stakeholder-agents-on-typed-tools.md)).
Every row has a deterministic fallback, because loss of AI may never block a core function (NFR-RES-2).

| # | Application | Class | Runs | Scenario | Phase | Risk | Fallback when it is off |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Feeding anomaly from scale and sensor series | classical | cloud | [S1](../scenarios/animal-welfare-monitoring/README.md) | 1 | High | Feed-scale threshold rule |
| 2 | Enclosure activity, posture and social anomaly | CV | edge → cloud | [S1](../scenarios/animal-welfare-monitoring/README.md) | 2 | High | Keeper round; rule 1 |
| 3 | Per-animal vision for solitary and tagged animals | CV | edge → cloud | [S1](../scenarios/animal-welfare-monitoring/README.md) | 3 | High | Per-enclosure mode |
| 4 | Tier-1 safety advisory: aggression, out-of-zone | CV | edge | [S1](../scenarios/animal-welfare-monitoring/README.md) | 2 | High | Tier-0 rules, which are the guarantee anyway |
| 5 | Visitor masking before anything is stored | CV | edge | [S1](../scenarios/animal-welfare-monitoring/README.md) | 1 | High | Stream dropped rather than stored unmasked |
| 6 | Plant-house feeding-event detection | CV | edge | [S1](../scenarios/animal-welfare-monitoring/README.md), [ADR-0024](../../adrs/ADR-0024-plant-collection-on-the-welfare-pipeline.md) | 3 | Low | Curator schedules demonstrations by hand |
| 7 | Welfare daily briefing drafter | generative | gateway | [S1](../scenarios/animal-welfare-monitoring/README.md) | 2 | Low | Template with the same figures |
| 8 | Piranha detect-track-count with an interval | CV | edge | [S2](../scenarios/piranha-population-counting/README.md) | 3 | Medium | Census of record and the ledger |
| 9 | Zone footfall forecasting | classical | batch | [S3](../scenarios/visitor-flow-forecasting/README.md) | 2 | Medium | Same weekday last week × season |
| 10 | Staffing optimiser under labour rules | classical (solver) | batch | [S3](../scenarios/visitor-flow-forecasting/README.md) | 2 | Medium | Heuristic roster |
| 11 | Zone-path weighting from token taps | classical | batch | [S3](../scenarios/visitor-flow-forecasting/README.md), [ADR-0018](../../adrs/ADR-0018-visitor-token-and-anonymised-paths.md) | 2 | Medium | Counter totals alone |
| 12 | Companion FAQ answering, grounded | generative | gateway | [S4](../scenarios/guest-companion/README.md) | 1 | Medium | FAQ cache, then the info point |
| 13 | Day planning and re-planning | generative | gateway | [S4](../scenarios/guest-companion/README.md) | 2 | Medium | Printed map and the cached itinerary |
| 14 | Return-visit nudge wording | generative | gateway | [S4](../scenarios/guest-companion/README.md) | 3 | Medium | Plain offer mail |
| 15 | Price elasticity estimation | classical | batch | [S5](../scenarios/dynamic-family-passes/README.md) | 3 | Medium | Fixed prices |
| 16 | `agent:ops-copilot` | agent | monolith | [S6](../scenarios/operations-copilot/README.md) | 2 | Medium | Dashboards and the protocol folder |
| 17 | `agent:animal` | agent | monolith | [S6](../scenarios/operations-copilot/README.md) | 3 | Medium | The review queue as it is today |
| 18 | `agent:management` — ask the estate | agent | monolith | [S6](../scenarios/operations-copilot/README.md) | 3 | Low | The daily report and a dashboard |
| 19 | Investment effect estimation with an interval | classical | batch | [S6](../scenarios/operations-copilot/README.md) | 3 | Medium | Before-and-after read off a chart |
| 20 | Highlight mining from activity features | CV | edge | [S7](../scenarios/content-and-visitor-voice/README.md) | 3 | Medium | The curator watches footage |
| 21 | Caption drafting around verbatim facts | generative | gateway | [S7](../scenarios/content-and-visitor-voice/README.md) | 3 | Medium | The curator writes it |
| 22 | Feedback theme clustering with quotes | classical + generative | batch | [S7](../scenarios/content-and-visitor-voice/README.md) | 2 | Low | Reading the sentences |
| 23 | Ride condition flagging from non-invasive telemetry | classical | cloud | [S8](../scenarios/ride-condition-monitoring/README.md) | 3 | High | Threshold rule on the ride's run-in baseline |

Two things fall out of the table. **Five of the twenty-three are generative** — 7, 12, 13, 14 and 21,
with the naming half of 22 as a sixth — and none of them decides anything; they phrase, plan, answer
and draft. And **seven run at the edge** — 2, 3, 4, 5, 6, 8 and 20 — which is what keeps 110 camera
streams off a 0.1 Mbps backhaul and is the reason the inference gateway is on the path of only one
column.

## Reuse, which is why twenty-three is affordable

The portfolio is wide because the expensive parts are shared, not because twenty-three things were
built.

- **One camera pipeline serves four purposes.** The edge node's masking and activity features feed
  welfare (2, 3, 4), the plant house (6) and content mining (20). A highlight is an excursion in a
  feature that welfare already computes; the marginal cost of application 20 is a caption.
- **One forecast serves three.** Footfall (9) drives the roster (10), the companion's routing (13) and
  the land train's departure frequency, and the cap in FR-1.7 reads the same numbers.
- **One anomaly capability serves two biologies.** The plant house is an enclosure with different
  baselines ([ADR-0024](../../adrs/ADR-0024-plant-collection-on-the-welfare-pipeline.md)).
- **One metric layer serves everything that asks a question** — dashboards, the daily report, the
  feature store and `agent:management` resolve the same named metric
  ([ADR-0015](../../adrs/ADR-0015-metric-layer-and-estate-twin.md)).
- **One review queue, one band mechanism, one audit trail** for every probabilistic output, whichever
  scenario produced it ([ADR-0007](../../adrs/ADR-0007-human-in-the-loop-confidence-bands.md)).

## Why each one is AI at all

Every candidate had to answer why a rule or a query would not do, and several failed that test and are
rules today — live zone popularity is a counter and a dashboard, ticket validation is a signature, the
daily report's recommendation is a fixed rule set, and the staffing optimiser is a solver with hard
constraints rather than a model. The rows above survived for a specific reason each:

| Application | Why deterministic logic is not enough |
| --- | --- |
| Welfare anomalies (1–3) | The signal is a deviation from *this animal's* own baseline across four dimensions; a fixed threshold either misses the quiet cases or floods the vet |
| Piranha count (8) | Small, fast, self-occluding subjects in water; nobody can count them by rule, and the manual census is twice a year |
| Footfall forecast (9) | Weather, calendar, events and season interact; the heuristic is the baseline it must beat, not a substitute |
| Companion (12–13) | Open-ended natural language over an estate-specific corpus, with a plan that must respond to live queues |
| Elasticity (15) | Demand response is a fitted relationship, and the policy engine around it is deliberately deterministic |
| Agents (16–18) | The task is multi-step lookup and synthesis; each individual step is a rule, and the composition is not |
| Investment effect (19) | Separating an investment from the season needs a counterfactual, which is a model whether or not anyone calls it one |
| Highlight mining (20) | "Interesting" is a pattern over motion features, and it is exactly the kind of judgement nobody can write down |
| Ride condition (23) | Degradation shows as a joint drift across current, temperature and cycles — the pattern, not any single threshold |

## What the portfolio deliberately does not contain

Stated here so that the absences read as decisions rather than oversights.

| Not built | Why | Where it is argued |
| --- | --- | --- |
| A driverless shuttle | A safety case this team cannot carry, in the one place where a mistake involves a child; the preconditions to revisit it are written down | [ADR-0020](../../adrs/ADR-0020-internal-transport-and-autonomy.md) §3–4 |
| A model that clears a ride for operation | Certification is a human's to give; the model flags, an engineer clears | [ADR-0022](../../adrs/ADR-0022-ride-condition-monitoring.md) §3 |
| Face recognition or device tracking | Anonymous counting is the instrument of record; the token is a visible, removable, refusable alternative | [ADR-0009](../../adrs/ADR-0009-visitor-privacy-anonymous-counting.md), [ADR-0018](../../adrs/ADR-0018-visitor-token-and-anonymised-paths.md) |
| Per-person pricing | A fairness risk the estate cannot absorb; pricing moves by day and load only | [S5](../scenarios/dynamic-family-passes/README.md) |
| Automated publishing of any content | One bad post about a venomous animal costs more than a season of them earns | [ADR-0021](../../adrs/ADR-0021-content-drafting-with-a-publish-gate.md) §2 |
| A sentiment score | It aggregates away the only part anyone can act on | [ADR-0025](../../adrs/ADR-0025-feedback-themes-not-scores.md) |
| Remaining-useful-life estimates for rides | No fleet to fit a distribution against, and the number is too easily read as a safety claim | [ADR-0022](../../adrs/ADR-0022-ride-condition-monitoring.md) |
| A simulating digital twin | Nothing in the brief needs one; the twin here is a set of gold projections | [ADR-0015](../../adrs/ADR-0015-metric-layer-and-estate-twin.md) §4 |
| Per-animal re-identification in group enclosures | An open research problem; a Phase 3+ spike with an entry threshold | A11, [TODOS.md](../../TODOS.md) |

## Kill gates

Breadth without an exit is how a portfolio becomes a maintenance burden. Four applications carry an
explicit gate at which they are switched off rather than defended:

| Application | Gate | When |
| --- | --- | --- |
| Caption drafting (21) | Curator's unedited-acceptance rate below 40% | End of the first season it runs |
| Feedback themes (22) | No costed change traceable to a theme | End of each season |
| Plant feeding detection (6) | The demonstration draws no audience | End of the first season it runs |
| Ride condition (23) | Flags never precede an inspection finding | After two seasons of baselines |

Everything else is gated the ordinary way: a capability whose model never beats its rule stays a rule
([ADR-0023](../../adrs/ADR-0023-rules-first-model-second.md)), and one whose guardrail trips rolls back
to its fallback ([ADR-0008](../../adrs/ADR-0008-ai-evaluation-and-production-monitoring.md) §7).
