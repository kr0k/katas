# ADR-0005 — Model gateway and provider independence

**Status:** accepted · **Date:** 2026-09-05
**Serves:** FR-5.2, NFR-EVO-1, NFR-COST-1, NFR-OBS-1, OKR 5.1, 5.2, R4
**Related:** ADR-0003, ADR-0008, ADR-0010

## Context
The judges' questions in full: *the best model today may not be the best tomorrow; what if the provider changes prices; what if the provider shuts down.* We also have a cost ceiling (AI ≤ 2% of revenue) and a small team. And we have three kinds of AI — classical ML we own, vision models we own, and generative models we rent — that must be governed the same way.

## Decision
1. **No business service calls a model or provider directly.** Services call the **model gateway** with a *capability name* (`plan-visit`, `detect-feeding-anomaly`, `forecast-zone-footfall`) and a typed request. The gateway resolves the capability to the current **model/prompt bundle** in the registry.
2. **Bundles are versioned artifacts** (model reference, prompt template, parameters, schema, eval score, owner) declared in Git and promoted through `candidate → shadow → production`. Changing a model is a pull request that must pass the capability's eval suite (ADR-0008).
3. **Routing policy per capability:**
   - *tiered* — cheap/small model first, escalate on low confidence or complexity (companion FAQ vs. planning);
   - *fixed* — one model where reproducibility matters;
   - *fallback chain* — provider A → provider B → self-hosted open-weight → **deterministic fallback** (typed "AI unavailable" the service handles: templated report, static FAQ, heuristic forecast).
4. **Cost governance in the gateway:** cost per call attributed to capability; monthly budget per capability; alerts at 70% / 90%; at 100% the routing switches to the downgrade path automatically rather than failing or overspending.
5. **Provider-shutdown readiness:** every generative capability has a *named* secondary provider whose bundle passes the same eval suite and is exercised in shadow at least monthly; all prompts, evals, traces and fine-tuning data live in our storage, not the provider's.
6. **Own models** (vision, forecasting, pricing) go through the same registry and gateway. They are exported in portable formats and can be served in the cloud or on edge nodes (ADR-0006) — no provider dependency at all.
7. **Safety-critical paths never depend on a generative model** (FR-3.6). This is not a gateway feature; it is a rule enforced in review.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Call provider SDKs directly from services | Fastest to start | Every provider change touches every service; no unified cost view; no fallback discipline | Fails NFR-EVO-1 on day one |
| Adopt one provider's "agent platform" end to end | Rich tooling, managed evals | Prompts, evals and orchestration become provider-shaped; exit is a rewrite; price/shutdown risk concentrated | Contradicts the judges' concern |
| Self-host open-weight models only | No provider risk | Team of 5 runs GPU infrastructure; quality gap for planning/dialogue; cost at low utilisation | Operability; use as fallback instead |
| Gateway + registry (chosen) | One control point; portable; measurable | A component we own and must run; small added latency | — |

## Consequences
**Positive:** model swap ≤ 1 day; cost visible and capped; provider outage is a routing event, not an incident; consistent tracing for every AI call.
**Negative:** the gateway is a critical dependency for AI features (not for core features); prompt templates must be provider-neutral or maintained per provider; open-weight fallback may be lower quality.

| Risk | Mitigation |
| --- | --- |
| Gateway outage | HA deployment; services treat "gateway down" as the deterministic fallback path |
| Prompt behaviour differs across providers | Eval suite per capability is the contract; secondary bundle tuned separately; monthly shadow runs |
| Budget cap degrades experience on a busy day | Tiered routing reduces cost before the cap; cap alerts give time to raise budget consciously |

## How we will know this was right
Model/provider swap measured in hours; AI spend within budget with no service change; secondary provider passing evals every month; zero domain services importing provider SDKs (CI check).
