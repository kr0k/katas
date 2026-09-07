# ADR-0006 — Edge vs. cloud inference placement policy

**Status:** accepted · **Date:** 2026-09-05
**Serves:** FR-3.4, FR-3.6, FR-3.7, NFR-SCL-2, NFR-PRV-2, NFR-AVL-3, NFR-COST-1
**Related:** ADR-0001, ADR-0005, ADR-0007, ADR-0008

## Context
110 camera streams cannot cross a cellular backhaul. Safety alerts must fire in seconds without the cloud. But cloud inference is cheaper to iterate, easier to monitor and elastic. We need a rule for where each model runs, not case-by-case debate.

## Decision
A model runs **on the edge** if any of these hold:
1. Its input is **video or high-rate sensor data** that cannot or should not leave the estate (bandwidth, privacy).
2. Its output is on a **safety-critical or access-critical path** with a latency budget in seconds (FR-3.6, gates).
3. It must **keep working during uplink loss** to avoid data gaps (e.g. piranha counting).

Otherwise it runs **in the cloud**. Corollaries:
- **Video → features/events at the edge; reasoning in the cloud.** Enclosure cameras are reduced to per-animal or per-enclosure features, aggregated to 1-minute windows, plus short clips at the edge; anomaly *scoring* against baselines happens in the cloud, where it can be improved weekly without touching estate hardware.
- **Two safety tiers.** **Tier-0 (FR-3.6):** deterministic rules on local sensors — door contact open without a keeper badge, water or climate out of band, PIR/beam motion in a dry zone, gate breach — run on the broker, no ML, no cloud; NFR-AVL-3 is measured on this tier. **Tier-1 (FR-3.7):** model-assisted *advisories* from the edge vision model (aggressive behaviour near visitors, animal outside its normal zone) go to staff devices as advisory and to the review queue as a clip; they are governed like any other model ([ADR-0007](ADR-0007-human-in-the-loop-confidence-bands.md) bands, [ADR-0008](ADR-0008-ai-evaluation-and-production-monitoring.md) evals). Tier-1 *adds* alerts; it never gates, delays or replaces tier-0.
- **Generative AI never runs on the edge and never sits on a safety path.**
- Edge models are deployed **from the same registry** through GitOps: the registry publishes a retained *desired version* over the downlink, the node **pulls** the signed artifact from object storage over HTTPS — resumable, rate-limited, off-hours — verifies it, swaps atomically and reports version and health back ([Edge & connectivity → Downlink](../hld/core/edge-and-connectivity.md#downlink-cloud--estate)). Rollout is staged: one node, then the rest.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Everything in the cloud | One place to run and monitor models | Video cannot be shipped; safety depends on uplink; privacy exposure | Physically impossible for video; fails NFR-AVL-3 |
| Everything on the edge | Maximum independence | GPU fleet on-site; slow iteration; hard to monitor; LLMs impractical | Operability, cost |
| Policy-based split (chosen) | Each model where it fits; safety stays deterministic and local | Two deployment targets; feature-extraction contract between edge and cloud must be versioned | — |

## Consequences
**Positive:** backhaul carries kilobytes, not video; safety is independent of AI and cloud; privacy masking happens before anything is stored.
**Negative:** edge hardware to buy and maintain (1–2 GPU-class nodes + spare); feature schema between edge and cloud becomes an interface to govern.

| Risk | Mitigation |
| --- | --- |
| Edge model drift unnoticed | Edge publishes confidence stats and sample frames; cloud monitors them (ADR-0008) |
| Edge node hardware failure | Spare node; cameras record locally; sensors and rules unaffected |
| Feature schema change breaks cloud scoring | Versioned schema; dual-publish during transitions |

## How we will know this was right
Backhaul utilisation stays low; zero safety alerts delayed by cloud/AI outages; time to iterate a cloud scoring model (days) vs. an edge model (weeks) confirms the split.
