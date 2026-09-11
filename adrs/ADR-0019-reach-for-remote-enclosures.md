# ADR-0019 — Reach for remote enclosures: radio bridge, delay-tolerant pickup, cellular

**Status:** accepted · **Date:** 2026-09-11
**Serves:** FR-3.1, FR-3.6, NFR-RES-1, NFR-SCL-2, A17, R1, R21
**Related:** ADR-0001, ADR-0002, ADR-0006, ADR-0020

## Context
[ADR-0002](ADR-0002-mqtt-and-cellular-backhaul.md) answers the estate's link question in aggregate:
LoRaWAN for small sensors, Wi-Fi or Ethernet where there is power and coverage, cellular for the
backhaul. At ≈ 21 msg/s and ≈ 0.1 Mbps the estate is not bandwidth-bound, and nothing in this ADR
changes that.

The problem it leaves open is **reach at a single site**. The estate is sprawling and some of the 55
enclosures sit beyond the LoRaWAN gateways and well beyond Wi-Fi: no mains for an edge node, no
structure to cable to, heritage rules against trenching. For a battery sensor that is fine — LoRaWAN
was chosen precisely for it. For an enclosure that needs a **camera** it is not: the edge node has to
be there, and its output — feature windows, clips, a tier-1 advisory — has to get back.

The obvious answer is a cellular gateway per remote site, and on money alone it is also the right one:
a remote camera site produces a few megabytes a day, so a link carrying **everything** it makes costs
roughly €400 a year. We say that first because the tempting version of this ADR — "a bridge is a
one-off cost with no monthly bill" — does not survive its own arithmetic at this estate's volumes,
and anyone with a calculator would find that in a minute.

So the question is not throughput and it is not the subscription either. It is: **which remote sites
cellular cannot actually serve**, and what carries their traffic when it cannot.

## Decision
1. **Choose the channel per traffic class, per site** — never one channel for a site.

   | Traffic class at a remote site | Channel | Why |
   | --- | --- | --- |
   | **Critical** — tier-0 alerts, acknowledgements, device health | **Cellular** wherever there is any usable coverage, at every remote site regardless of what else it has; the **bridge** where there is none. **A site with neither cannot host an edge node at all** — it keeps LoRaWAN sensors and the keeper's round until one of the two exists (FR-3.6) | A venomous-animal alert may not wait for a vehicle or for a bridge to re-align. The class is kilobytes a day, so the link it needs is a trickle — but it needs one that exists, and no vehicle may ever be that link |
   | **Telemetry** — sensor readings, 1-minute feature windows | **Cellular** where coverage carries it; the **radio bridge** where it does not | Small, continuous, wanted inside the hour |
   | **Clips** — S1 event clips with their raw feature window, S2 sample frames | **Cellular** where coverage carries it; the **bridge** where there is line of sight; **delay-tolerant pickup** where the link carries the two classes above but not this one, and there is no line of sight | The bulky class, and the only one that genuinely tolerates hours — which is what makes a vehicle an acceptable carrier for it and for nothing else |

2. **A directional radio bridge (PtP/PtMP) is what a site gets when cellular cannot serve it.** A
   heritage estate has dead spots, and a remote enclosure is exactly where one is likely: a valley, a
   tree line, a stone building. Where coverage is absent, too weak for the clip class, or too variable
   to trust a tier-1 advisory to, a bridge with line of sight to the estate's core carries an edge
   node's whole output with room to spare. It is chosen for **reach at a fixed point**, never as a way
   to avoid a subscription.
3. **Delay-tolerant pickup — a data mule — carries the clip class at a thin-link site with no line of
   sight.** The niche is narrow and stated narrowly: a site whose cellular carries alerts and telemetry
   but would be metered into overage by clips, and which no bridge can reach.
   The collector rides the estate's land train ([ADR-0020](ADR-0020-internal-transport-and-autonomy.md)),
   pulls the site's clip buffer over the local link as it passes, and uploads at a stop with
   connectivity. It reuses the store-and-forward machinery already in place: the same per-class
   queues, the same `(device_id, boot_id, seq)` idempotency key, the same at-least-once contract
   ([ADR-0001](ADR-0001-edge-first-store-and-forward.md) §4). A missed round is a delay, never a loss —
   the site's buffer is sized for three days of rounds, and a site missed twice raises an ops ticket.
4. **Neither alternative is bought to save money, and the arithmetic says so plainly.** A cellular
   gateway carrying an enclosure's full traffic is ≈ €400 a year; a bridge is ≈ €3k once, which is
   about seven years of that subscription and does not pay back inside the five-year horizon every
   other figure here uses; the mule collector is ≈ €8k once for the whole estate, which would need
   four no-line-of-sight sites to beat the same subscription — and would not beat it even then,
   because decision 1 keeps the cellular link at every site that has coverage, so the subscription is
   not saved at all. What is bought is **coverage the estate does not otherwise have**, and latency
   for the middle class. The triggers are therefore coverage, not counting:
   - a **bridge** where a remote site's cellular coverage is absent, too weak for the clip class, or
     too variable to carry a tier-1 advisory;
   - the **collector** only if the survey finds a site whose link carries the critical and telemetry
     classes but not the clips, with no line of sight for a bridge. Until it does, it is a conditional
     line in the [cost model](../appendix/cost-model.md) and the operating mode is not started.

   **The site survey decides this, not this document** ([TODOS.md](../TODOS.md)): today we assume four
   to eight remote sites, of which three to five have line of sight (A17), and we do not yet know how
   many have coverage.
5. **Nothing about this changes the safety tier.** Tier-0 rules run on the local broker at the site,
   as everywhere else; reach affects when the cloud finds out, never whether a keeper is paged
   (FR-3.6).
6. **One abstraction above the channels.** A traffic class is published to the broker and a transport
   policy decides the path. No producer knows whether its clip left by bridge, by mule or by cellular,
   which is what keeps three channels from becoming three code paths.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Cellular gateway at every remote site, all classes | Simple, uniform, real-time — and **the cheapest option wherever it works**, which is why it is the default in decision 1 rather than an alternative we rejected | It only works where there is coverage, and a remote enclosure in a heritage park is where coverage is least likely; a metered link is also the wrong place for the clip class to grow | Not rejected: adopted wherever the survey says it reaches |
| Extend Wi-Fi or mesh across the whole estate | One network to reason about | Trenching and masts in a heritage park; dead zones would remain anyway; the capital is better spent on the cameras themselves | Cost and heritage constraints |
| Radio bridges everywhere, no mule | One extra channel instead of two | Line of sight cannot be built to every enclosure — foliage, artificial rock, buildings, rides; a bridge that is the only path to a zone is a single point of failure for it | Physics, and SPOF |
| Mule only, no bridges | One vehicle instead of a mast per site | Telemetry that should arrive in a minute arrives in an hour, and the critical class would depend on a vehicle; the clip class is not the only class | Wrong latency, and a safety dependency we will not take |
| Drones for pickup | No route dependency | Noise and stress near venomous and nervous animals; flight regulation over a public site; a new craft to operate | Welfare and regulation |
| Per-class channel selection, coverage-triggered (chosen) | Each class gets the cheapest channel that can actually carry it; the critical class never depends on a vehicle; nothing extra is bought where cellular reaches | Up to three delivery modes to operate and monitor; the mule adds a route dependency and a missed-round failure mode | — |

## Consequences
**Positive:** remote enclosures get cameras at all, which is what the welfare scenario needs to cover
more than the easy half of the estate; a site that cellular reaches costs the estate one subscription
and nothing else.
**Negative:** up to three delivery modes on a team of five, which is the real price here; the mule's latency
is minutes to hours and the clip's freshness metric has to say so; a radio bridge is an outdoor asset
with an alignment and a survey life-cycle (R21); the whole channel mix is a site-survey assumption
until Phase 0 measures it.

| Risk | Mitigation |
| --- | --- |
| Line of sight lost to vegetation growth, weather or a new structure (R21) | Fresnel clearance and a growth margin in the survey; link budget monitored per bridge with an alert on margin loss; no bridge is the sole path for the critical class; re-alignment is a scheduled operation, not an incident |
| A mule round is missed and clips age out | Buffer sized for three rounds; missed-round counter per site; a site missed twice raises a ticket and pushes its clip class onto its own thin cellular link until the route is fixed — accepting the overage, because a mule-served site has a link by construction (decision 1) and only the clip class was ever kept off it (GD-19) |
| Three channels become three code paths | Decision 6: one transport policy, one publisher contract; a producer that names a channel fails review |
| The survey finds coverage good enough everywhere, and the mule is unjustified | That is the expected outcome and a good one: decision 4 makes the collector conditional, the €8k is not spent, and the operating mode is never started |
| A bridge is justified by habit rather than by coverage | Every bridge names the site's measured signal in the survey record; "no monthly bill" is not an accepted reason, and decision 4 says why |

## How we will know this was right
Every remote enclosure reports its critical class inside the NFR-AVL-3 budget; clip freshness at
mule-served sites, if any exist, inside its stated hours with zero loss after a missed round; bridge
link margin above its floor through a full growing season; and every bridge and collector traceable to
a measured coverage gap in the survey rather than to a cost argument.
