# Edge & Connectivity

Patchy Wi-Fi is the constraint that shapes everything on the estate. This document is the detailed view.

## Device classes and how they talk

| Device class | Examples | Protocol | Volume | Power / link |
| --- | --- | --- | --- | --- |
| **Gate readers** | QR/NFC at 4–6 entry points | MQTT over Wi-Fi/Ethernet to local broker | ~3,000 scans/h at opening | Wired where possible |
| **Anonymous counters** | LiDAR / thermal / IR beam counters at zone boundaries and queue lines | MQTT (small payloads) | 1 msg / 30 s / device, ~150 devices | Battery + LoRaWAN, or PoE |
| **Enclosure sensors** | feed scales, water quality (pH, temp, turbidity), climate, door contacts | MQTT (small payloads) | 1 msg / min / sensor, ~300 sensors | LoRaWAN or Wi-Fi; door contacts wired |
| **Cameras** | 1–2 per enclosure, IR for nocturnal | RTSP to edge node (never MQTT, never cloud) | 55–110 streams | Wired PoE |
| **Edge inference nodes** | 1–2 small GPU servers in the estate server room | Publish results/clips via MQTT | events only | Mains + UPS |
| **Staff devices** | phones/rugged handhelds | Local Wi-Fi + push over local broker; DECT/radio as last resort | | |

## Why two link types

- **Wi-Fi/Ethernet** where there is power and coverage (gates, cameras, server room).
- **LoRaWAN** for low-bandwidth sensors and counters spread across a large estate: kilometre-range, years of battery, does not care about Wi-Fi coverage. A LoRaWAN gateway on the main building bridges into the MQTT broker.
- **Cellular** for the backhaul to the cloud (primary); a second SIM from another operator as failover. If cellular is unavailable (assumption A2 wrong), the same bridge runs over fixed line or satellite.

## Store-and-forward

```mermaid
sequenceDiagram
    participant D as Device
    participant B as Local MQTT broker
    participant C as Cloud ingestion
    D->>B: publish (QoS 1, persistent)
    Note over B: Message stored to disk
    alt Uplink up
        B->>C: bridge forwards (QoS 1)
        C-->>B: ack → message released
    else Uplink down
        Note over B: Retain ≥ 24 h (sized for 72 h)
        B->>B: keep queuing; local consumers still served
    end
    Note over C: Idempotent ingest: dedupe on (device_id, seq)
```

- Devices number their messages; the cloud de-duplicates on `(device_id, seq)`. Ordering is per device, not global — consumers are written for that.
- Local consumers (gate service, safety alerting, dashboards' local cache) subscribe to the same broker, so the estate keeps working while the bridge queues.
- Broker runs as an HA pair; storage sized for 72 h of full telemetry (≈ a few GB — telemetry is small; video never leaves the estate as a stream).

## What stays local, always

| Function | Why local | Depends on cloud? |
| --- | --- | --- |
| Gate validation | Visitors must get in | No — allow-list synced when possible ([ADR-0011](../../adrs/ADR-0011-offline-ticket-validation.md)) |
| Safety alerts (door open, aggressive-behaviour flag, water out of band) | Seconds matter; poisonous animals | No — rule-based on broker |
| Piranha counting | 24/7 video, no bandwidth to ship it | No — edge model; results synced later |
| Anomaly pre-filter & visitor masking | Reduce video to events; privacy | No |
| Live local dashboard for ops | Staff need to see the park while uplink is down | No (read-only cache) |

## Security

- Per-device X.509 certificates; mutual TLS to the broker; topic ACLs per device class.
- Bridge to cloud over TLS with certificate pinning.
- Cameras on an isolated VLAN reachable only by the edge nodes.
- Firmware/OTA through the same GitOps pipeline as software.

## Capacity check at 15,000 visitors/day

- Gate scans: ~15,000 in + 15,000 out; peak 3,000/h → 1/s. Trivial for the broker.
- Telemetry: ~450 devices × 2 msg/min ≈ 15 msg/s. Trivial.
- Video: 110 streams × 2 Mbps ≈ 220 Mbps on the camera VLAN, processed locally. Never crosses the backhaul.
- Backhaul: telemetry + events + occasional clips ≈ a few Mbps. Fits cellular with margin.

The system is not bandwidth- or throughput-bound; it is **connectivity-reliability-bound**, which is exactly what store-and-forward solves.
