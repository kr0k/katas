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
be there, and its output — feature windows, clips, a tier-1 advisory — has to get back. The naive
answer, a cellular gateway per remote site, is linear in sites and permanent in OPEX for something
most of whose traffic could wait an hour.

So the question is not throughput. It is: for a remote site, which delivery channel per traffic class,
and at what site count does each stop being the cheapest.

## Decision
1. **Choose the channel per traffic class, per site** — never one channel for a site.

   | Traffic class at a remote site | Channel | Why |
   | --- | --- | --- |
   | **Critical** — tier-0 alerts, acknowledgements, device health | **Cellular**, always, at every remote site regardless of what else it has | A venomous-animal alert may not wait for a vehicle or for a bridge to re-align. The class is tiny — kilobytes a day — so per-site cellular for the critical class alone is cheap |
   | **Telemetry** — sensor readings, 1-minute feature windows | **Radio bridge** where line of sight exists, otherwise the same cellular link | Small, continuous, wanted inside the hour |
   | **Clips** — S1 event clips with their raw feature window, S2 sample frames | **Delay-tolerant pickup** where a bridge is not possible | The bulky class, and the one that genuinely tolerates hours |

2. **A directional radio bridge (PtP/PtMP) is the first choice for a remote site with line of sight.**
   It is a one-off cost with no monthly bill, it is real-time, and it carries an edge node's whole
   output with room to spare. It is chosen for **reach at a fixed point**, not for throughput we do not
   need.
3. **Delay-tolerant pickup — a data mule — carries the clip class where there is no line of sight.**
   The collector rides the estate's land train ([ADR-0020](ADR-0020-internal-transport-and-autonomy.md)),
   pulls the site's clip buffer over the local link as it passes, and uploads at a stop with
   connectivity. It reuses the store-and-forward machinery already in place: the same per-class
   queues, the same `(device_id, boot_id, seq)` idempotency key, the same at-least-once contract
   ([ADR-0001](ADR-0001-edge-first-store-and-forward.md) §4). A missed round is a delay, never a loss —
   the site's buffer is sized for three days of rounds, and a site missed twice raises an ops ticket.
4. **The break-even is a site count, and it is small.** A cellular gateway carrying an enclosure's full
   traffic costs roughly €400 a year in subscription and data; a bridge is ≈ €3k once and shares one
   backhaul; the mule collector is ≈ €8k once for the whole estate. Above **two to three** no-line-of-
   sight remote sites the mule is cheaper than per-site cellular for the clip class; below that it is
   not worth the operating mode and we buy cellular. **The site survey decides this, not this
   document** ([TODOS.md](../TODOS.md)): today we assume four to eight remote sites, of which three to
   five have line of sight (A17).
5. **Nothing about this changes the safety tier.** Tier-0 rules run on the local broker at the site,
   as everywhere else; reach affects when the cloud finds out, never whether a keeper is paged
   (FR-3.6).
6. **One abstraction above the channels.** A traffic class is published to the broker and a transport
   policy decides the path. No producer knows whether its clip left by bridge, by mule or by cellular,
   which is what keeps three channels from becoming three code paths.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Cellular gateway at every remote site, all classes | Simple, uniform, real-time | Linear OPEX for a payload that is mostly clips, which tolerate hours; a permanent bill for an occasional need | Cost, at more than two or three sites |
| Extend Wi-Fi or mesh across the whole estate | One network to reason about | Trenching and masts in a heritage park; dead zones would remain anyway; the capital is better spent on the cameras themselves | Cost and heritage constraints |
| Radio bridges everywhere, no mule | One extra channel instead of two | Line of sight cannot be built to every enclosure — foliage, artificial rock, buildings, rides; a bridge that is the only path to a zone is a single point of failure for it | Physics, and SPOF |
| Mule only, no bridges | Cheapest per site | Telemetry that should arrive in a minute arrives in an hour; the clip class is not the only class | Wrong latency for the middle class |
| Drones for pickup | No route dependency | Noise and stress near venomous and nervous animals; flight regulation over a public site; a new craft to operate | Welfare and regulation |
| Per-class channel selection with a survey-set threshold (chosen) | Each class pays for what it needs; the critical class never depends on a vehicle | Three delivery modes to operate and monitor; the mule adds a route dependency and a missed-round failure mode | — |

## Consequences
**Positive:** remote enclosures get cameras at all, which is what the welfare scenario needs to cover
more than the easy half of the estate; the recurring bill stays with the class that needs real time.
**Negative:** three delivery modes on a team of five, which is the real price here; the mule's latency
is minutes to hours and the clip's freshness metric has to say so; a radio bridge is an outdoor asset
with an alignment and a survey life-cycle (R21); the whole channel mix is a site-survey assumption
until Phase 0 measures it.

| Risk | Mitigation |
| --- | --- |
| Line of sight lost to vegetation growth, weather or a new structure (R21) | Fresnel clearance and a growth margin in the survey; link budget monitored per bridge with an alert on margin loss; no bridge is the sole path for the critical class; re-alignment is a scheduled operation, not an incident |
| A mule round is missed and clips age out | Buffer sized for three rounds; missed-round counter per site; a site missed twice raises a ticket and falls back to cellular for its clip class until fixed (GD-19) |
| Three channels become three code paths | Decision 6: one transport policy, one publisher contract; a producer that names a channel fails review |
| The survey shows one remote site, and the mule is unjustified | The threshold in decision 4 is the trigger — below it we buy cellular and the collector is not purchased at all |

## How we will know this was right
Every remote enclosure reports its critical class inside the NFR-AVL-3 budget; clip freshness at
mule-served sites inside its stated hours with zero loss after a missed round; bridge link margin above
its floor through a full growing season; and the cost per remote site below the per-site cellular
line it replaced.
