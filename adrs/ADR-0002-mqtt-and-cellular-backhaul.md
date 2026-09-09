# ADR-0002 — MQTT on the estate, LoRaWAN for sensors, cellular backhaul

**Status:** accepted · **Date:** 2026-09-05 (revised 2026-09-07)
**Serves:** FR-2.1, FR-3.1, NFR-RES-1, NFR-SEC-1, NFR-DR-3
**Related:** ADR-0001

## Context
Hundreds of small sensors across a large estate with patchy Wi-Fi; a budget for MQTT-capable devices; cameras that produce far more data than any wireless link can carry; and a need to get events to the cloud. The broker in the middle must survive a node failure without losing gate and safety events, and the two radio technologies need two identity schemes because LoRaWAN devices cannot do TLS.

## Decision
1. **MQTT** is the messaging protocol for all device telemetry and local events (the brief's device budget assumes it; it is lightweight, supports QoS and persistent sessions, and every IoT cloud ingests it).
2. **Transport is chosen per device class:** wired Ethernet/PoE for gates, cameras and anything safety-related; Wi-Fi where coverage exists; **LoRaWAN** for battery sensors and counters spread over the grounds. The **transport rule**: LoRaWAN only for devices sending ≤ 1 message/min with ≤ 20-byte payloads at SF7–SF10; everything else is wired. Three LoRaWAN gateways (assumption until the site survey) feed a **LoRaWAN network/application server** that runs as a container on the estate and republishes decoded payloads into the broker.
3. **The broker is a cluster, not a pair.** A cluster-capable MQTT broker with **replicated persistent sessions and queues** (EMQX / HiveMQ / VerneMQ class), three nodes on UPS — one per edge server plus a witness on the LoRaWAN server host — behind one DNS name. A message is acknowledged to a device only when a second node holds it. Single-writer brokers (Mosquitto class) are excluded: they cannot replicate a persisted queue, so a failover during an outage would start with an empty buffer.
4. **Three traffic classes** (critical / telemetry / clips), each with its own queue, disk quota and bridge connection, drained critical-first after an outage and dropped clips-first if a quota fills ([Edge & connectivity → Traffic classes](../hld/core/edge-and-connectivity.md#traffic-classes)). "Priority" is therefore a property we configure, not one we hope the broker has.
5. **Gate behaviour on broker failover:** readers reconnect through the DNS name within 30 s; during those seconds they admit on signature and cached lists ([ADR-0011](ADR-0011-offline-ticket-validation.md) §5); their queued entries are delivered on reconnect from the persistent session. No gate ever blocks on the broker.
6. **Backhaul is cellular** (two operators, automatic failover) carrying the MQTT bridge over TLS, one connection per traffic class and direction. Fixed line or satellite is the fallback if coverage assumptions fail.
7. **Cameras never use MQTT or the backhaul:** RTSP on an isolated VLAN to edge nodes only.
8. **Reach is a separate question from coverage.** PoE stops at 100 m and the estate is large, so an enclosure beyond that distance from a switch is not served by the transport rule alone. One rule decides it: the default is **single-mode fibre with a media converter** back to the edge tier, inside the cabling line of the [cost model](../appendix/cost-model.md); a **local inference node at the enclosure** is the exception, taken where fibre cannot be laid, because then only events cross the link instead of a video stream. The count of such enclosures is an output of the site survey ([TODOS.md](../TODOS.md)), and if it exceeds two the [edge compute budget](../hld/core/edge-and-connectivity.md#edge-compute-budget) is re-sized before purchase rather than after.
9. **Device identity by transport class:** per-device **X.509 certificates and mutual TLS** for every IP-connected device, with topic ACLs per class; per-device **DevEUI/AppKey with OTAA join** for LoRaWAN devices, session keys derived at join and decrypted only inside the estate's network/application server, which re-publishes under its own X.509 identity ([Edge & connectivity → Security](../hld/core/edge-and-connectivity.md#security-identity-by-transport-class)).

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Wi-Fi everywhere (densify APs) | One network | Expensive across a sprawling estate; power needed at every AP; still fragile outdoors | Cost; does not fix backhaul |
| Per-device cellular (NB-IoT/LTE-M) direct to cloud | No local broker | Recurring SIM cost per device; no local tier; violates ADR-0001 | Cost, resilience |
| HTTP polling instead of MQTT | Simple | No persistent sessions, heavier on battery devices, worse for patchy links | Poorer fit |
| Zigbee/BLE mesh | Cheap devices | Short range; mesh reliability over hundreds of metres outdoors is poor | Range |
| Single-writer broker in an active-passive pair (Mosquitto + floating IP) | Simplest; tiny footprint | Persisted queue lives on one node; failover during an outage loses the buffer or needs shared storage we would have to run | Fails the 72 h buffer promise on the day it matters |
| Cluster-capable broker with replicated queues (chosen) | Node failure is a reconnect; classes and quotas are configuration | Heavier to run; three nodes on-site; commercial editions for some features | — |
| One LoRaWAN gateway | Cheapest | ≈ 14% channel load at full sensor count, above the 10% we allow; no receive diversity at the estate edges | Collision loss; see airtime budget |
| **Delay-tolerant pickup by a vehicle** ("data mule"): a vehicle on its round collects buffered data from remote enclosures and uploads it where there is signal | No uplink to pay for per enclosure; the right answer where a link genuinely cannot exist | It solves bandwidth and coverage, and neither is our constraint. The whole backhaul is ≈ 0.1 Mbps, and the only bulky delay-tolerant payload is ≈ 140 MB of clips a day for the entire estate ([capacity check](../hld/core/edge-and-connectivity.md#capacity-check-at-15000-visitorsday-by-traffic-class)). Against an OPEX of €810k–1.33M it would save on the order of €4k a year — less than the ±50% band on the figure it saves from — while adding a delivery mode to operate, a dependency on a vehicle's route, and a missed-round failure mode | **Operability for a team of five**, which is the same test that rejected event-driven microservices in the [styles matrix](../hld/architecture-evaluation.md#architectural-styles-considered). Our payload is small because inference happens where the data is; moving data to compute is the opposite bet and only one of the two can be taken |
| **Directional radio bridges** (PtP/PtMP) to remote zones | Real-time and high throughput with no monthly cellular bill | Throughput we do not need at 0.1 Mbps aggregate. Needs line of sight, a survey and periodic re-alignment; vegetation growth, weather on long links and new structures in the beam all break it; and one bridge is a single point of failure for its zone | Buys the wrong attribute. Reach is answered by fibre or a local node (§8), and the critical class by cellular |
| **A vehicle-mounted mesh, or an autonomous shuttle as the carrier** | Would combine visitor transport with data collection | Certification and liability in a place with children and venomous animals; the hardest component in the proposal to verify, for the smallest team; and once delay-tolerant pickup is rejected there is no data-transport reason for the vehicle either | Safety and verification cost, on top of no remaining need |

## Consequences
**Positive:** sensors run for years on batteries; one broker abstracts transport diversity; bandwidth to the cloud is a few Mbps; a broker node can die at opening time without a lost scan.
**Negative:** two radio technologies and two identity schemes to operate; LoRaWAN payloads are tiny (fine for readings, not for images); cellular has recurring cost; a three-node broker cluster and a LoRaWAN server are more to run than a single broker.

| Risk | Mitigation |
| --- | --- |
| LoRaWAN interference / collisions at scale | Transport rule; ≤ 10% channel load per gateway; three gateways; ADR (adaptive data rate); SF histogram and per-gateway loss as metrics; site survey before purchase ([airtime budget](../hld/core/edge-and-connectivity.md#lorawan-airtime)) |
| Cellular outage on both operators | Store-and-forward (ADR-0001); fixed-line fallback where available |
| Certificate lifecycle burden | Automated issuance/rotation via the GitOps pipeline; 90-day certs |
| AppKey extracted from a stolen or opened sensor | Per-device keys, never shared; tamper switch raises a critical event; device de-registered at the join server; secure-element sensors preferred at accessible locations (R15) |
| Broker cluster split-brain during a power event | Three nodes with quorum; witness on a separate UPS; game day GD-3 |

## How we will know this was right
Sensor uptime ≥ 99%; battery replacement interval ≥ 2 years; backhaul utilisation < 30% of capacity at 15,000 visitors/day; LoRaWAN channel load ≤ 10% per gateway in the survey and in operation; broker failover with zero message loss in game day GD-3.
