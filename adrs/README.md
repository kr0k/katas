# Architecture Decision Records

One decision per file. Format: Context → Decision → Alternatives considered → Consequences (trade-offs) → Validation. Status: `proposed` / `accepted` / `superseded`.

| ID | Title | Status | Area |
| --- | --- | --- | --- |
| [ADR-0001](ADR-0001-edge-first-store-and-forward.md) | Edge-first architecture with store-and-forward | accepted | Core |
| [ADR-0002](ADR-0002-mqtt-and-cellular-backhaul.md) | MQTT on the estate, LoRaWAN for sensors, cellular backhaul | accepted | Core |
| [ADR-0003](ADR-0003-cloud-provider-selection.md) | Single cloud provider with an exit plan | accepted | Core |
| [ADR-0004](ADR-0004-event-driven-backbone.md) | Event-driven backbone between bounded contexts | accepted | Core |
| [ADR-0005](ADR-0005-model-gateway-and-provider-independence.md) | Inference gateway, model governance and provider independence | accepted | AI platform |
| [ADR-0006](ADR-0006-edge-vs-cloud-inference.md) | Edge vs. cloud inference placement policy | accepted | AI platform |
| [ADR-0007](ADR-0007-human-in-the-loop-confidence-bands.md) | Human in the loop via confidence bands | accepted | AI platform / S1 |
| [ADR-0008](ADR-0008-ai-evaluation-and-production-monitoring.md) | AI evaluation gate and production monitoring | accepted | AI platform |
| [ADR-0009](ADR-0009-visitor-privacy-anonymous-counting.md) | Anonymous footfall counting, no visitor identification | accepted | Core / S3 |
| [ADR-0010](ADR-0010-grounded-llm-with-guardrails.md) | Grounded LLM with output guardrails for the guest companion | accepted | S4 |
| [ADR-0011](ADR-0011-offline-ticket-validation.md) | Offline ticket validation with eventual reconciliation | accepted | Core |
| [ADR-0012](ADR-0012-ticketing-platform-adopt-not-build.md) | Ticketing platform: adopt, not build | accepted | Core |

Template: [`template.md`](template.md)
