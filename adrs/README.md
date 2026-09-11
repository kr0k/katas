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
| [ADR-0013](ADR-0013-stakeholder-agents-on-typed-tools.md) | Stakeholder agents on typed tools | accepted | AI platform / agents |
| [ADR-0014](ADR-0014-two-tier-agent-memory-with-a-write-guard.md) | Two-tier agent memory with a write-guard | accepted | AI platform / agents |
| [ADR-0015](ADR-0015-metric-layer-and-estate-twin.md) | A metric layer over the lakehouse, and the estate twin | accepted | Core / data |
| [ADR-0016](ADR-0016-cost-of-error-sets-the-bands.md) | The cost of an error sets the confidence bands | accepted | AI platform |
| [ADR-0017](ADR-0017-ai-risk-classes-and-proportional-controls.md) | AI risk classes and proportional controls | accepted | AI platform / governance |
| [ADR-0018](ADR-0018-visitor-token-and-anonymised-paths.md) | Visitor token: personal at the tap, anonymous in the analytics | accepted | Core / S3 |
| [ADR-0019](ADR-0019-reach-for-remote-enclosures.md) | Reach for remote enclosures: radio bridge, pickup, cellular | accepted | Core |
| [ADR-0020](ADR-0020-internal-transport-and-autonomy.md) | Internal transport: a manned land train, and where autonomy stops | accepted | Core |
| [ADR-0021](ADR-0021-content-drafting-with-a-publish-gate.md) | Content drafting: mine the highlights, gate the publish | accepted | S7 |
| [ADR-0022](ADR-0022-ride-condition-monitoring.md) | Ride condition monitoring: the model flags, a human clears | accepted | S8 |
| [ADR-0023](ADR-0023-rules-first-model-second.md) | Rules first, model second: the cold-start policy | accepted | AI platform |
| [ADR-0024](ADR-0024-plant-collection-on-the-welfare-pipeline.md) | The plant collection runs on the welfare pipeline | accepted | S1 |
| [ADR-0025](ADR-0025-feedback-themes-not-scores.md) | Visitor feedback: themes with quotes, not a sentiment score | accepted | S7 |

Template: [`template.md`](template.md)

**Reading order.** ADR-0001 to ADR-0012 decide the foundation and the first five AI scenarios (S1 to S5).
ADR-0013 to ADR-0017 are the AI platform's second layer — agents, their memory, the metric surface they
read, how bands are derived and which controls a capability owes. ADR-0018 to ADR-0025 are the
capabilities and reach the merged portfolio added.
