# ADR-0003 — Single cloud provider with an exit plan

**Status:** accepted · **Date:** 2026-09-05
**Serves:** NFR-OPS-1, NFR-COST-1, NFR-EVO-1, R12
**Related:** ADR-0004, ADR-0005

## Context
A team of ≤ 5 engineers must run ticketing, analytics, AI and a data platform. Managed services are the only realistic path. But the judges — rightly — ask what happens when a provider changes terms, and we do not want the estate's future tied to one vendor's roadmap.

## Decision
1. Use **one major cloud provider** for the cloud tier (compute, managed streaming, managed databases, object storage, managed IoT ingestion, managed model hosting for our own models). One provider keeps operations simple and IAM/observability uniform. *Our reference choice is AWS, based on team familiarity; the architecture does not depend on it.*
2. **Portability by design at the boundaries, not by avoiding managed services:**
   - open protocols in and out (MQTT, HTTPS/gRPC, OpenTelemetry);
   - data in **open table formats** (Parquet/Iceberg) in object storage;
   - business services as **containers** with no provider SDK in domain code (thin adapters only);
   - infrastructure declared as code with a control plane that abstracts providers (Crossplane-style compositions) so environments are reproducible elsewhere;
   - **LLM/vision providers are separate from the cloud decision** and abstracted by the model gateway (ADR-0005).
3. An **exit assessment** is maintained: for each managed service, the equivalent elsewhere and the estimated migration effort. Reviewed yearly.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Multi-cloud active/active | Maximum independence | Doubles operational surface for a team of 5; lowest-common-denominator services; higher cost | Operability |
| Cloud-agnostic self-hosting (Kubernetes + OSS everything) | Portable | The team runs Kafka, Postgres, vector DB, model serving… at 2 a.m. | Operability, R9 |
| Single cloud, deep native integration everywhere | Fastest to build | Domain code welded to SDKs; exit cost grows every sprint | Evolvability |
| Single cloud with portable boundaries (chosen) | Simple ops, credible exit | Some discipline cost; occasionally forgo a convenient proprietary feature | — |

## Consequences
**Positive:** one place to look; managed reliability; a migration that is expensive but *bounded and known*.
**Negative:** a real (if bounded) switching cost; discipline needed to keep SDKs out of domain code.

| Risk | Mitigation |
| --- | --- |
| Price increase on a key managed service | Exit assessment names the alternative; cost dashboards per service; architecture fitness function fails builds that import provider SDKs into domain modules |
| Provider region/service deprecation | Same |
| Team drifts into proprietary features | Quarterly review of the exit assessment; ADR required for any new proprietary dependency |

## How we will know this was right
Exit assessment estimates a migration ≤ 3 engineer-months for the cloud tier; zero provider SDK imports in domain code (enforced in CI); cloud cost per visitor trending down as attendance grows.
