# Appendix · LoRaWAN airtime budget

Radio planning behind the transport rule in [Edge & connectivity](../hld/core/edge-and-connectivity.md#why-two-link-types): whether 350 battery devices at one message a minute fit the duty cycle and the channel, and how many gateways that needs. Every input is an assumption until the site survey ([TODOS.md](../TODOS.md)); the architecture depends on the conclusion, not on the arithmetic.

**Conclusion:** three gateways, ≈ 5% channel load each, worst-case device duty cycle ≈ 0.7% against the 1% regulatory limit.

Assumptions (replaced by the site survey — see [`TODOS.md`](../TODOS.md)): ~350 devices on LoRaWAN (150 counters + 200 sensors, the rest wired), 1 uplink/min each, 20-byte payloads, EU868 with 8 channels, spreading-factor distribution 70% SF7–SF9 (≈ 0.1 s airtime) and 30% SF10 (≈ 0.4 s).

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

