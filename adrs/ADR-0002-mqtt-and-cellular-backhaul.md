# ADR-0002 — MQTT on the estate, LoRaWAN for sensors, cellular backhaul

**Status:** accepted · **Date:** 2026-09-05
**Serves:** FR-2.1, FR-3.1, NFR-RES-1, NFR-SEC-1
**Related:** ADR-0001

## Context
Hundreds of small sensors across a large estate with patchy Wi-Fi; a budget for MQTT-capable devices; cameras that produce far more data than any wireless link can carry; and a need to get events to the cloud.

## Decision
1. **MQTT** is the messaging protocol for all device telemetry and local events (the brief's device budget assumes it; it is lightweight, supports QoS and persistent sessions, and every IoT cloud ingests it).
2. **Transport is chosen per device class:** wired Ethernet/PoE for gates and cameras; Wi-Fi where coverage exists; **LoRaWAN** for battery sensors and counters spread over the grounds, with a LoRaWAN gateway bridging into the MQTT broker.
3. **Backhaul is cellular** (two operators, automatic failover) carrying the MQTT bridge over TLS. Fixed line or satellite is the fallback if coverage assumptions fail.
4. **Cameras never use MQTT or the backhaul:** RTSP on an isolated VLAN to edge nodes only.
5. Device identity by **per-device X.509 certificates**, mutual TLS, topic ACLs per device class.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Wi-Fi everywhere (densify APs) | One network | Expensive across a sprawling estate; power needed at every AP; still fragile outdoors | Cost; does not fix backhaul |
| Per-device cellular (NB-IoT/LTE-M) direct to cloud | No local broker | Recurring SIM cost per device; no local tier; violates ADR-0001 | Cost, resilience |
| HTTP polling instead of MQTT | Simple | No persistent sessions, heavier on battery devices, worse for patchy links | Poorer fit |
| Zigbee/BLE mesh | Cheap devices | Short range; mesh reliability over hundreds of metres outdoors is poor | Range |

## Consequences
**Positive:** sensors run for years on batteries; one broker abstracts transport diversity; bandwidth to the cloud is a few Mbps.
**Negative:** two radio technologies to operate; LoRaWAN payloads are tiny (fine for readings, not for images); cellular has recurring cost.

| Risk | Mitigation |
| --- | --- |
| LoRaWAN interference / collisions at scale | Duty-cycle planning; ADR (adaptive data rate); gateway redundancy |
| Cellular outage on both operators | Store-and-forward (ADR-0001); fixed-line fallback where available |
| Certificate lifecycle burden | Automated issuance/rotation via the GitOps pipeline |

## How we will know this was right
Sensor uptime ≥ 99%; battery replacement interval ≥ 2 years; backhaul utilisation < 30% of capacity at 15,000 visitors/day.
