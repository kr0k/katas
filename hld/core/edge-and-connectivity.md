# Edge & Connectivity

Patchy Wi-Fi shapes everything on the estate. This is the detailed view.

## Device classes and how they talk

| Device class | Examples | Protocol | Volume | Power / link |
| --- | --- | --- | --- | --- |
| **Gate readers** | QR/NFC at 4–6 entry points | MQTT over Wi-Fi/Ethernet to local broker | ≈ 2,940 scans in the peak hour of a peak day (≈ 5,900 persons at 2 per scan; ≈ 29,400 visitor-days, [capacity check](../../requirements/08-business-case.md#1-capacity-reality-check)); an average day is far lower | Wired where possible |
| **Anonymous counters** | LiDAR / thermal / IR beam counters at zone boundaries and queue lines | MQTT (small payloads) | 1 msg / min / device (in/out deltas), ~150 devices; queue-line counters that need 30 s resolution are PoE | Battery + LoRaWAN, or PoE |
| **Enclosure sensors** | feed scales, water quality (pH, temp, turbidity), climate, door contacts, PIR/beam dry-zone detectors | MQTT (small payloads) | 1 msg / min / sensor, ~300 sensors | LoRaWAN or Wi-Fi; door contacts and PIR/beam wired |
| **Cameras** | 1–2 per enclosure, IR for nocturnal | RTSP to edge node (never MQTT, never cloud) | 55–110 streams | Wired PoE |
| **Edge inference nodes** | 2 GPU servers in the estate server room, sized N+1 | Publish 1-min feature windows, clips, advisories via MQTT; pull model artifacts over HTTPS | ~3 msg/s | Mains + UPS |
| **Staff alert devices** | DECT handsets / pagers (primary), smartphones or rugged handhelds (secondary) | DECT base stations on the estate LAN; push over the local broker | | Independent of Wi-Fi coverage |

## Why two link types

- **Wi-Fi/Ethernet** where there is power and coverage (gates, cameras, server room).
- **LoRaWAN** for low-bandwidth sensors and counters spread across a large estate: kilometre-range, years of battery, does not care about Wi-Fi coverage. Three LoRaWAN gateways (main building plus two estate edges — count is an assumption until the site survey in [`TODOS.md`](../../TODOS.md)) feed a **LoRaWAN network server** container on the estate, which decodes payloads and republishes them into the MQTT broker.
- **Cellular** for the backhaul to the cloud (primary); a second SIM from another operator as failover. If cellular is unavailable (assumption A2 wrong), the same bridge runs over fixed line or satellite.

**Transport rule.** A device goes on LoRaWAN only if it sends ≤ 1 message per minute, its payload fits in ≤ 20 bytes, and the survey places it at spreading factor SF7–SF10. Anything faster, larger or further goes PoE or Wi-Fi. This keeps every device under the 1% duty-cycle limit and keeps the [airtime budget](#lorawan-airtime) honest.

## Broker

The estate broker is a **cluster-capable MQTT broker with replicated persistent sessions and queues** (EMQX / HiveMQ / VerneMQ class), not a single-writer broker behind a floating IP. Three nodes: one on each of the two edge servers, a third small witness node on the LoRaWAN network server host, all on UPS. Clients connect through one DNS name; a node failure is a reconnect, not a data loss. Details and the alternatives rejected are in [ADR-0002](../../adrs/ADR-0002-mqtt-and-cellular-backhaul.md).

## Traffic classes

Everything on the bridge belongs to one of three classes. The class decides the queue it sits in, the bridge connection it uses, the disk quota it may fill, the order in which the buffer drains after an outage, and what is dropped if the buffer ever fills.

| Class | Contents | Bridge connection | Disk quota per node (of 32 GB) | Overflow rule |
| --- | --- | --- | --- | --- |
| **Critical** | Gate entries/exits, tier-0 safety alerts, tier-1 advisories, alert acknowledgements, device health heartbeats. Downlink: allow/revocation lists, tier-0 rule parameters | Own connection, highest priority | 2 GB (≈ 3 months at current rate) | Never dropped; drained first |
| **Telemetry** | Sensor readings, counters, S1 1-minute feature windows, S2 daily estimates. Downlink: policy parameters, desired model versions | Own connection, rate-limited to leave headroom for critical | 20 GB (≈ 3 weeks) | Dropped only after clips, oldest first |
| **Clips** | S1 event clips with ±5 min of raw features, S2 sample frames | Own connection, lowest priority, paused while telemetry is behind by > 1 h | 4 GB (≈ 4 weeks) | Dropped first; regenerated from local recordings on request |

## Store-and-forward (uplink)

```mermaid
sequenceDiagram
    participant D as Device
    participant B as Local MQTT broker (cluster)
    participant C as Cloud ingestion
    D->>B: publish (QoS 1, persistent, traffic class in topic)
    Note over B: Message replicated to a second node, one queue per class
    alt Uplink up
        B->>C: bridge forwards (QoS 1), one connection per class, critical → telemetry → clips
        C-->>B: ack → message released
    else Uplink down
        Note over B: Retain ≥ 24 h (sized for 72 h)
        B->>B: keep queuing; local consumers still served
    end
    Note over C: Idempotent ingest: dedupe on (device_id, boot_id, seq)
```

- **Idempotency key is `(device_id, boot_id, seq)`.** `seq` is a per-device counter that restarts at zero on every power-up; `boot_id` is a random 64-bit value (or a monotonic boot counter in flash) generated at power-up, so a battery swap or a reboot never makes fresh readings look like duplicates of old ones. The cloud derives one **event id** (UUIDv5 over the key) that every consumer uses for its own idempotency; deduplication window 7 days. A `seq` gap is recorded, not rejected.
- **Dedupe drop rate** per device is a metric: > 1% of a device's messages dropped as duplicates means a replay loop or a misconfigured device, and alerts.
- Ordering is per device, not global — consumers are written for that.
- Local consumers (gate service, tier-0 rules, dashboards' local cache) subscribe to the same broker, so the estate keeps working while the bridge queues.
- Storage is **replicated across broker nodes**: a message is acknowledged to the device only once a second node has it, so the loss of one node's disk loses nothing (NFR-DR-3). Sized per the [capacity table](#capacity-check-at-15000-visitorsday-by-traffic-class) below — ≈ 3 GB per 72 h at 15,000 visitors/day, 32 GB provisioned per node.

## Sensor health: dead, stuck and drifting

Across 450 sensors and counters, the most likely daily fault is not an outage but one device quietly lying: a feed scale wedged at 4.20 kg, a pH probe fouled and flat, a counter that stopped incrementing while still publishing. A heartbeat catches a dead sensor, not a stuck one — and to S1 a flat feed scale looks exactly like an animal that has stopped eating.

Three states, three detectors, one event:

| State | Detector | Window | Effect |
| --- | --- | --- | --- |
| **Dead** | No message and no heartbeat | 3 × the device's reporting interval (min 5 min); LoRaWAN devices 3 × interval + one duty-cycle period | `DeviceHealthChanged(dead)` |
| **Stuck** | Zero variance in the reading while messages keep arriving — identical payload value for N consecutive reports, N per device class (feed scales 60, water quality 30, climate 120, counters: no increment during open hours with footfall present in the zone) | Per class, as above | `DeviceHealthChanged(stuck)` |
| **Drifting** | Reading diverges from the enclosure's redundant signal or from its own seasonal baseline beyond a per-class band; for counters, the hourly in/out reconciliation against gate totals already in [ADR-0009](../../adrs/ADR-0009-visitor-privacy-anonymous-counting.md) §2 | Rolling 24 h | `DeviceHealthChanged(drifting)` — advisory, not exclusion |

Detection runs on the broker, inside the tier-0 rule engine's runtime: no cloud, no model, no history beyond a per-device ring buffer. It has to keep working during an uplink outage, which is when a stuck sensor is hardest to notice. `DeviceHealthChanged` is critical class, so it reaches the cloud ahead of telemetry.

What consumes it:

- **Feature store** excludes a dead or stuck device's readings from features and baselines and marks the affected window instead of interpolating over it.
- **S1** suppresses anomalies whose only evidence is an unhealthy device and says so in the review queue ("feed scale FS-19 stuck since 06:10 — no intake signal available"), the model-path version of R15's rule that a single sensor never triggers a tier-0 alert alone.
- **Tier-0 rules** keep firing. A stuck water probe removes a signal, so the missing alert is itself alerted on ("no valid water reading for enclosure 7") — a rule that cannot evaluate is a fault, not a pass. Door contacts and PIR/beam detectors carry a supervision pulse, since a dry-zone detector that never fires is indistinguishable from a quiet dry zone.
- **Ops** gets a ticket with device, zone and state. Time-to-repair per device class is tracked; a device stuck twice in a quarter is replaced, not reset.

**Metrics:** devices by health state (target: dead + stuck = 0 during opening hours), mean time to detect per class, mean time to repair, and anomalies suppressed by device health — a rise there means either a hardware batch problem or a detector tuned too loosely. Game day GD-16 injects all three states.

## Downlink: cloud → estate

The bridge carries state *down* as well, and it shares one cellular link with a buffer that may be draining after an outage. Three things need to reach the estate:

| Downlink class | Content | Size / rate | Mechanism |
| --- | --- | --- | --- |
| **Critical** | Ticket allow/revocation list deltas (sold, refunded, used at another gate); tier-0 rule parameters (bands, badge lists) | KB; on change, full snapshot hourly | Retained MQTT messages on `downlink/critical/…`: sequence-numbered deltas plus a periodic full snapshot; delivered before the uplink drain starts |
| **Policy** | Confidence bands, gate-POS price schedule, opening hours, *desired* edge model version | KB; on change | Retained MQTT messages on `downlink/policy/…` |
| **Model artifacts** | Edge model bundles | 100 MB – 2 GB; weekly at most | **Never through MQTT.** The edge node pulls the signed artifact from object storage over HTTPS: resumable, rate-limited to ≤ 30% of backhaul, scheduled off-hours, paused while the uplink buffer is draining; verified, swapped atomically, version reported back |

```mermaid
flowchart LR
    subgraph Cloud["☁️ Cloud"]
        Down["Downlink publisher"]
        Ingest["IoT ingestion gateway"]
        Store[("Object storage<br/>signed model artifacts")]
        Down --> Ingest
    end
    subgraph Estate["🏰 Estate"]
        Broker["MQTT broker cluster<br/>retained downlink topics"]
        Gate["Gate validation"]
        Rules["Tier-0 rules"]
        Edge["Edge inference node"]
        Broker -. "allow/revocation snapshot + deltas" .-> Gate
        Broker -. "bands, policies" .-> Rules
        Broker -. "desired model version" .-> Edge
    end
    Broker == "uplink: critical → telemetry → clips" ==> Ingest
    Ingest -. "downlink: retained snapshots, critical first" .-> Broker
    Store -. "HTTPS pull: resumable, rate-limited, off-hours" .-> Edge
    Edge -. "model version + health" .-> Broker
```

Rules:

1. **Retained and sequenced.** Every downlink topic holds the latest full snapshot as a retained message; deltas carry a sequence number and the snapshot id they apply to. A consumer that reconnects gets the snapshot immediately, detects any gap, and re-applies. No polling and no request/response over the bridge.
2. **Critical first on reconnect.** The bridge runs one connection per class and direction. After an outage the downlink critical snapshot reaches the gates within a minute while the uplink starts draining critical events, then telemetry, then clips. Model pulls stay paused until the uplink buffer is below 10%.
3. **Gates never wait.** Until the revocation snapshot lands, a gate admits on signature plus local ledger — the bounded window [ADR-0011](../../adrs/ADR-0011-offline-ticket-validation.md) accepts; any admission of a since-revoked ticket shows up in the reconciliation report.
4. **Artifacts are pulled, verified, staged.** Rollout goes to one edge node, then the rest; the previous artifact stays on disk so a rollback is a re-publish of the old desired version ([ADR-0006](../../adrs/ADR-0006-edge-vs-cloud-inference.md)).
5. Game days GD-5 (revocation after outage) and GD-12 (model pull under a saturated uplink) verify this → [resilience validation](resilience-validation.md).

## Safety alerts: from sensor to a human

NFR-AVL-3 is measured to a **human acknowledgement**, not to a device: an alert on a phone nobody is looking at has not arrived.

| Step | Channel | Budget |
| --- | --- | --- |
| Rule fires on the broker | tier-0 rules, local | ≤ 1 s from sensor message |
| Delivery, primary | **DECT handsets / pagers** on every keeper and the duty manager — DECT base stations cover the estate independently of Wi-Fi and of the cloud | ≤ 5 s (NFR-AVL-3 delivery) |
| Delivery, secondary | Push to staff smartphones over the local broker; sounder and light at the enclosure for breach and dry-zone alerts | in parallel, best effort |
| **Acknowledgement** | Any recipient acknowledges on the handset (one key) or in the app; the ack is a critical-class event | ≤ 60 s |
| Escalation 1 | No ack in 60 s → head keeper and duty manager, repeated page | +60 s |
| Escalation 2 | No ack in 120 s → all staff on shift and the control room; alarm on the ops dashboard; logged as an incident | +60 s |

Metrics: delivery p99 (≤ 5 s), **time-to-ack p99** (≤ 60 s), unacknowledged alerts per day (0). Game day GD-6 exercises the whole chain with the uplink down. Tier-1 advisories use the secondary channel only and never page.

## What stays local, always

| Function | Why local | Depends on cloud? |
| --- | --- | --- |
| Gate validation | Visitors must get in | No — allow-list synced over the downlink when possible ([ADR-0011](../../adrs/ADR-0011-offline-ticket-validation.md)) |
| Tier-0 safety alerts to a human (door open without badge, water out of band, PIR/beam motion in a dry zone) | Seconds matter; poisonous animals | No — deterministic rules on the broker, DECT/pager delivery, local ack and escalation (FR-3.6) |
| Tier-1 safety advisories (aggressive behaviour, animal outside its zone) | Camera-based; an advisory to staff must not wait for the cloud | No for detection and delivery (edge node → staff devices); the review-queue copy syncs later (FR-3.7) |
| Piranha counting | 24/7 video, no bandwidth to ship it | No — edge model; results synced later |
| Feature extraction & visitor masking | Reduce video to 1-minute feature windows and event clips; privacy | No |
| LoRaWAN network server | Sensors must keep reporting during uplink loss | No — decodes and republishes locally |
| Live local dashboard for ops | Staff need to see the park while uplink is down | No (read-only cache) |

## Security: identity by transport class

One identity scheme does not fit both radios. LoRaWAN devices cannot do TLS; wired and Wi-Fi devices can.

| Transport class | Identity | Encryption / integrity | Revocation |
| --- | --- | --- | --- |
| Wired / Wi-Fi MQTT devices (gates, cameras' edge link, edge nodes, PoE counters, door contacts, PIR/beam) | Per-device **X.509** certificate; edge nodes and gate readers hold it in a TPM/secure element | Mutual TLS to the broker; topic ACLs per device class | Certificate revocation via the GitOps pipeline; short-lived certs (90 days) rotated automatically |
| LoRaWAN devices (battery sensors, counters) | Per-device **DevEUI + AppKey**, OTAA join (LoRaWAN 1.0.x); AppKey stored in the sensor's secure element where the product offers one | AES-128 session keys (NwkSKey / AppSKey) derived at join; payloads decrypted only in the estate's network/application server | Device de-registered at the join server; keys are never shared between devices |
| LoRaWAN gateways → network server | Per-gateway X.509 | TLS | As wired devices |
| LoRaWAN network server → broker | One X.509 identity per gateway region, publishing decoded payloads into per-device topics with the source gateway tagged | Mutual TLS | As wired devices |
| Bridge estate ↔ cloud | Broker cluster certificate, pinned | TLS both directions; downlink topics writable only by the cloud publisher | Rotation via GitOps |
| Model artifacts | Signed in the registry | Signature verified on the edge node before swap | Key rotation in the registry |

Also: cameras on an isolated VLAN reachable only by the edge nodes; firmware/OTA through the same GitOps pipeline as software; tamper switches on sensor housings raise a critical event (a stolen sensor's AppKey is de-registered the same hour — risk R15).

## Edge compute budget

Two GPU-class edge servers, sized **N+1**: either node alone carries the whole estate at degraded frame rates.

| Task | Streams | Frame rate | Model class | Inferences / s | Share of one mid-range inference GPU (≈ 1,000 detector inferences/s at 720p, batched) |
| --- | --- | --- | --- | --- | --- |
| Visitor masking + feature extraction (S1) | 110 | 5 fps | Person/animal detector + pose keypoints, 720p | 550 | ≈ 55% |
| Piranha detect-track-count (S2) | 3 | 15 fps | Small-object detector + tracker, multi-view fusion | 45 | ≈ 10% (small objects, higher resolution) |
| Tier-1 advisory (aggressive behaviour, out-of-zone) | flagged enclosures only, ≤ 10 concurrent | 5 fps | Behaviour classifier on pose features | 50 | ≈ 5% |
| Clip extraction and encoding | on events, ≤ 100/day | — | CPU | — | 0% GPU, 2 CPU cores |
| **Total** | | | | **≈ 650** | **≈ 70% of one GPU → 35% per node in normal operation** |

- **Normal operation:** streams split between the two nodes by enclosure; each node runs at 35% GPU with room for shadow-mode models.
- **One node lost (GD-7):** the survivor takes all 110 streams. Degradation rule, in order: keep the piranha tank at 15 fps; keep one primary camera per enclosure at 5 fps; drop secondary cameras to 1 fps; enclosures with an active tier-1 flag keep full rate. **Masking is never degraded** — if compute is short, a stream is dropped rather than stored unmasked.
- **Metric:** achieved fps per stream vs. target; alert when < 80% of target for 5 minutes. A third node is bought when the normal-operation share exceeds 50% per node (more enclosures, heavier models).

## LoRaWAN airtime

Assumptions (replaced by the site survey — see [`TODOS.md`](../../TODOS.md)): ~350 devices on LoRaWAN (150 counters + 200 sensors, the rest wired), 1 uplink/min each, 20-byte payloads, EU868 with 8 channels, spreading-factor distribution 70% SF7–SF9 (≈ 0.1 s airtime) and 30% SF10 (≈ 0.4 s).

| Quantity | Value |
| --- | --- |
| Uplinks | 350 / min ≈ 5.8 / s |
| Mean airtime per uplink | 0.7 × 0.1 s + 0.3 × 0.4 s ≈ 0.19 s |
| Airtime per second, all devices | ≈ 1.1 s / s |
| Channel load with one gateway (8 channels) | ≈ 14% — above the ≤ 10% we allow for < 5% collision loss (pure ALOHA) |
| Channel load with **three gateways** | ≈ 5% per gateway, with receive diversity at the edges |
| Worst-case device duty cycle (SF10, 1/min) | 0.4 s / 60 s ≈ 0.7% — under the 1% regulatory limit; SF11–12 would exceed it, hence the transport rule |
| Battery, SF9 at 1/min | ≥ 2 years on a 2 × AA-class cell (vendor figure; verified in the survey) |

Metric: per-gateway packet loss and SF histogram, collected by the network server; a device that drifts to SF11+ is moved to PoE or its reporting rate halved.

## Capacity check at 15,000 visitors/day, by traffic class

Assumptions: 450 sensors and counters at 1–2 msg/min (≈ 15 msg/s in total); S1 feature windows for 200 animals (per-animal mode — we size for the larger of 200 animals or 55 enclosures); 100 S1 candidate events/day; ~500 devices sending an hourly heartbeat; payload sizes from a prototype; managed IoT ingestion at ≈ $1 per million messages (typical list price, ±50%). **Volume, buffer and ingestion columns are for an average day** at 15,000 visitor-days and one person per scan; a peak day (≈ 29,400 visitor-days, [requirements/08 §1](../../requirements/08-business-case.md#1-capacity-reality-check)) at the blended 2 persons per scan produces about the same number of scans — the critical class has margin either way, and the rate cell shows the peak hour.

| Class | Source | Rate | Msg size | Volume / day | 72 h buffer | Ingestion msgs / month | Ingestion cost / month |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Critical | 30,000 gate scans, ~100 alerts and advisories with acks, 12,000 heartbeats | avg 0.5/s; peak day: up to 29,400 scans, 0.8/s in the peak hour | 0.5 KB | 21 MB | 63 MB | 1.3 M | ≈ $1 |
| Telemetry — sensors & counters | 450 devices, ≈ 15 msg/s | 15/s | 0.2 KB | 260 MB | 0.8 GB | 39 M | ≈ $40 |
| Telemetry — S1 feature windows (1-min) | 200 × 1/min | 3.3/s | 2 KB | 576 MB | 1.7 GB | 8.6 M | ≈ $9 |
| Clips | 100 events × (10 s clip ≈ 1.25 MB + ±5 min raw features ≈ 120 KB) | 100/day | 1.4 MB | 140 MB | 0.4 GB | 0.003 M | ≈ $0 (stored as objects) |
| **Total** | | **≈ 19 msg/s** | | **≈ 1.0 GB** | **≈ 3.0 GB** | **≈ 49 M** | **≈ $50** |
| *Counterfactual: raw 1 Hz features per animal, no aggregation* | *200 × 1/s* | *200/s* | *0.2 KB* | *3.5 GB* | *10 GB* | *520 M* | *≈ $520* |

The counterfactual row is an order of magnitude worse on every column, which is why edge aggregation is a design decision in S1 rather than a later optimisation.

- Gate scans: ≈ 15,000 in + 15,000 out on an average day at one person per scan; a peak day ≈ 29,400 in + out scans at the blended 2 persons per scan, with ≈ 2,940 scans in the peak hour → 0.8/s. Trivial for the broker, and the lanes hold too (requirements/08 §1).
- Video: 110 streams × 2 Mbps ≈ 220 Mbps on the camera VLAN, processed locally. Never crosses the backhaul.
- Backhaul: ≈ 1.0 GB/day ≈ 0.1 Mbps average uplink; clip bursts of a few Mbps; downlink model pulls capped at 30% of link. Fits cellular with margin.
- Buffer: ≈ 3 GB per 72 h. Provision 32 GB SSD per broker node, replicated across nodes, with per-class quotas as in the traffic-class table.

The system is not bandwidth- or throughput-bound but **connectivity-reliability-bound**, which store-and-forward solves — provided features are aggregated at the edge and LoRaWAN devices stay inside the transport rule.
