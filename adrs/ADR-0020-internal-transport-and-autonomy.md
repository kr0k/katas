# ADR-0020 — Internal transport: a manned land train now, and where autonomy stops

**Status:** accepted · **Date:** 2026-09-11
**Serves:** FR-1.9, NFR-ACC-1, A18, R21, R24
**Related:** ADR-0017, ADR-0019

## Context
The estate is sprawling, and at 15,000 visitors a day that is not only a comfort problem. Families with
small children, elderly visitors and anyone with reduced mobility cannot reach the remote enclosures at
all today, which quietly removes a third of the collection from a third of the audience — and the
remote enclosures are exactly where [ADR-0019](ADR-0019-reach-for-remote-enclosures.md) wants a
delay-tolerant collector to pass.

Both needs point at a vehicle on a fixed route. The interesting question is not whether to have one;
the estate arguably needs it regardless of this platform. It is how much autonomy to put in it, in a
place with children, poisonous animals and a team of five engineers.

## Decision
1. **A manned electric land train on a fixed route, leased off the shelf, from season 1.** It is an
   estate asset rather than a platform component: the estate pays for it out of the accessibility and
   capacity case, not out of the platform's CAPEX ([cost model](../appendix/cost-model.md)).
2. **It carries the data-mule collector** — a ruggedised buffer-and-upload unit, the platform's only
   contribution to the vehicle ([ADR-0019](ADR-0019-reach-for-remote-enclosures.md) §3). The route is
   planned so that every mule-served site is passed at least three times a day.
3. **The driver stays.** No autonomy in this submission, and the reason is stated rather than implied:
   a low-speed autonomous shuttle is a **safety case**, not a feature. It needs an operational design
   domain, a certified platform, an insurer, a teleoperation desk and disengagement statistics before
   anyone removes the driver — and it would be the hardest component in the proposal to verify, owned
   by the smallest team, in the one environment where a mistake involves a child.
4. **What would have to be true to revisit it**, written down now so that a future "let's automate the
   train" is a decision rather than a drift: a certified low-speed platform procured with its safety
   case; a geofenced route with no crossing of visitor flow at speed; a safety driver through a full
   season with a measured disengagement rate; an insurer who prices it; and a sixth engineer, or an
   operator who runs it for us. Until all five hold, the class stays outside the risk framework's high
   band ([ADR-0017](ADR-0017-ai-risk-classes-and-proportional-controls.md) §5).
5. **The route's own AI is modest and already exists.** Departure frequency comes from the S3 footfall
   forecast, and the companion reads the timetable — no new model. The vehicle's positions are an
   ordinary telemetry stream, which is also how the mule's rounds are monitored.
6. **The mule does not depend on the vehicle being autonomous, and the vehicle does not depend on the
   mule.** Either can be removed without the other changing: the collector could ride a utility cart,
   and the train runs whether or not anything is collected.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Driverless shuttle from day one | Removes the driver's OPEX; a genuinely novel AI application | An unverifiable safety case at this team size, in an environment with children and venomous animals; vendor lock-in is physical, not contractual; insurance and liability unresolved | Safety and verification cost |
| Supervised autonomy with a safety driver, season 1 | The autonomy V&V statistics start accumulating now | Pays for the autonomy platform *and* the driver, for a benefit that only arrives when the driver leaves; the five preconditions in §4 are unmet anyway | Cost before benefit |
| No vehicle; remote enclosures stay walk-only | Nothing to buy or run | Accessibility gap stays; the mule loses its carrier and every no-line-of-sight site falls back to per-site cellular | Removes a need the estate already has |
| Utility cart for the mule, no passenger vehicle | Cheapest data answer | Solves nothing for visitors; a vehicle on a route is needed either way | Half the value for most of the cost |
| Manned train now, autonomy behind stated preconditions (chosen) | Accessibility and data pickup from season 1; the autonomy question stays open and honest | The driver's OPEX stays; the most eye-catching AI application in the neighbouring proposal is deliberately not taken | — |

## Consequences
**Positive:** the remote collection becomes reachable for the visitors least able to walk to it; the
mule gets a carrier without the platform buying a vehicle; the autonomy decision is documented with its
exit conditions instead of being quietly dropped.
**Negative:** a driver is a recurring cost the estate carries, and we are explicitly declining the AI
application that would remove it; a fixed route constrains where mule-served sites can be; and this is
the place a judge may reasonably say the proposal was too conservative.

| Risk | Mitigation |
| --- | --- |
| The route changes and a mule-served site falls off it | Route and mule-served sites are one configuration with one owner; a route change re-runs the channel decision in [ADR-0019](ADR-0019-reach-for-remote-enclosures.md) §4 for the affected sites |
| Autonomy is added later without the safety case (R24) | §4's five preconditions are the gate, and [ADR-0017](ADR-0017-ai-risk-classes-and-proportional-controls.md) §5 places the class outside scope until they hold |
| The estate never buys the train, and the mule has no carrier | A18 states the dependency; if it fails the collector is not purchased, and the thin-link site it existed for ([ADR-0019](ADR-0019-reach-for-remote-enclosures.md) §4) sends its clips over its own cellular link and accepts the overage, or the same unit rides a utility cart — §6 keeps the two purchases independent for exactly this reason |

## How we will know this was right
Mule-served sites passed three times a day through a season; step-free access measured to every
enclosure on the route; and the autonomy preconditions reviewed once a year, with the answer recorded
either way.
