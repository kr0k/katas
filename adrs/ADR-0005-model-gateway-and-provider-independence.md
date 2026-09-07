# ADR-0005 — Inference gateway, model governance and provider independence

**Status:** accepted · **Date:** 2026-09-05 (revised 2026-09-07)
**Serves:** FR-5.2, NFR-EVO-1, NFR-COST-1, NFR-OBS-1, NFR-OPS-1, OKR 5.1, 5.2, R4, R9
**Related:** ADR-0003, ADR-0006, ADR-0008, ADR-0010

## Context
The judges' questions in full: *the best model today may not be the best tomorrow; what if the provider changes prices; what if the provider shuts down.* We also have a cost ceiling (AI ≤ 2% of revenue) and a small team. And we have three kinds of AI — classical ML we own, vision models we own, and generative models we rent — that must be governed the same way.

Two different problems hide under the phrase "model gateway": a **runtime proxy** in front of hosted models (routing, budgets, fallback, tracing) and the **governance** of every model we run (registry, evaluation, monitoring) — including edge vision models and batch forecasters that no HTTP proxy ever sees. Treating them as one component would either push our own models through a proxy that adds nothing, or leave them ungoverned. Routing proxies for hosted models are also a solved problem with mature open-source options; building one is not where five engineers should spend their time.

## Decision
1. **Two concerns, two components.**
   - **Model governance** — registry, evaluation gate and production monitoring ([ADR-0008](ADR-0008-ai-evaluation-and-production-monitoring.md)) — applies to **every** model: rented generative models, our own cloud models, edge models, batch models. Nothing is promoted, served or watched outside it.
   - **Inference gateway** — a runtime proxy for **hosted** models only (external LLM/vision providers and our open-weight endpoint): routing, budgets, fallback chain, tracing, PII scrubbing. We **adopt an open-source LLM gateway** (LiteLLM, Portkey, Kong AI Gateway class; Apache-2.0-licensed options exist) and configure it declaratively in Git. The one thing we build is a thin **capability resolver** that maps a capability name to the registry's current production bundle and its runtime path.
2. **No business service names a model or provider.** Services call a **capability** (`plan-visit`, `detect-feeding-anomaly`, `forecast-zone-footfall`) with a typed request. The resolver routes hosted-model capabilities through the gateway and own-model capabilities to a managed model endpoint, a batch job or an edge node — the [capability → runtime path table](../hld/ai-platform/README.md#capability--runtime-path) is the source of truth.
3. **Bundles are versioned artifacts** (model reference, prompt template, parameters, schema, eval score, owner) declared in Git and promoted through `candidate → shadow → production`. Changing a model is a pull request that must pass the capability's eval suite (ADR-0008).
4. **Routing policy per capability, as gateway configuration:**
   - *tiered* — cheap/small model first, escalate on low confidence or complexity (companion FAQ vs. planning);
   - *fixed* — one model where reproducibility matters;
   - *fallback chain* — provider A → provider B → **open-weight model on managed hosting** → **deterministic fallback** (typed "AI unavailable" the service handles: templated report, static FAQ, heuristic forecast). We do **not** self-host the open-weight rung: open weights give us the freedom to move the endpoint between hosts; managed hosting keeps R9 true ("no self-hosted model serving in cloud").
5. **Cost governance in the gateway:** cost per call attributed to capability; monthly budget per capability; alerts at 70% / 90%; at 100% the routing switches to the downgrade path automatically rather than failing or overspending.
6. **Provider-shutdown readiness:** every generative capability has a *named* secondary provider whose bundle passes the same eval suite and is exercised in shadow at least monthly; the open-weight bundle is exercised the same way, so the last rung of the ladder is tested, not assumed. All prompts, evals, traces and fine-tuning data live in our storage, not the provider's.
7. **Own models go through governance, not through the gateway.** Vision, counting, forecasting and pricing models are registered, evaluated and monitored like everything else, and served where they fit: managed endpoints in the cloud, scheduled batch jobs, or edge nodes ([ADR-0006](ADR-0006-edge-vs-cloud-inference.md)). They are exported in portable formats — no provider dependency at all.
8. **Safety-critical paths never depend on a generative model** (FR-3.6). This is not a gateway feature; it is a rule enforced in review.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Call provider SDKs directly from services | Fastest to start | Every provider change touches every service; no unified cost view; no fallback discipline | Fails NFR-EVO-1 on day one |
| Adopt one provider's "agent platform" end to end | Rich tooling, managed evals | Prompts, evals and orchestration become provider-shaped; exit is a rewrite; price/shutdown risk concentrated | Contradicts the judges' concern |
| Build our own gateway | Exactly our needs, nothing more | Routing, budgets, retries, fallbacks and tracing rebuilt by a team of five; a critical component to run and patch | OSS gateways already do this well; our differentiator is the eval suites, not the proxy |
| Self-host open-weight models only | No provider risk | Team of 5 runs GPU infrastructure (R9); quality gap for planning/dialogue; cost at low utilisation | Operability; open weights are the fallback, on managed hosting |
| One gateway for every model, including edge and batch | One concept to explain | Edge vision and batch forecasters gain nothing from an HTTP proxy and cannot use one; forces governance into a runtime component | Split runtime from governance instead |
| OSS inference gateway + thin capability resolver + model governance (chosen) | One control point for hosted calls; every model governed; portable; measurable; almost no gateway code of our own | An OSS dependency to upgrade; two concepts to explain; small added latency on hosted calls | — |

## Consequences
**Positive:** model swap ≤ 1 day; cost visible and capped; provider outage is a routing event, not an incident; consistent tracing for every hosted call; the only gateway code we maintain is the capability resolver; every model — edge, batch or rented — sits in one governance loop.
**Negative:** the gateway is a critical dependency for generative features (not for core features); prompt templates must be provider-neutral or maintained per provider; the OSS gateway's configuration model is something we now depend on; the open-weight fallback may be lower quality.

| Risk | Mitigation |
| --- | --- |
| Gateway outage | HA deployment; services treat "gateway down" as the deterministic fallback path |
| Prompt behaviour differs across providers | Eval suite per capability is the contract; secondary bundle tuned separately; monthly shadow runs |
| Budget cap degrades experience on a busy day | Tiered routing reduces cost before the cap; cap alerts give time to raise budget consciously |
| OSS gateway project stalls or changes licence | Routes, budgets and fallbacks are declarative config; the resolver isolates services; a second OSS gateway is named in the exit assessment ([ADR-0003](ADR-0003-cloud-provider-selection.md)) |
| Managed open-weight host raises prices or drops the model | Open weights are portable by definition; a second host is named; the fallback bundle passes the same evals on it |

## How we will know this was right
Model/provider swap measured in hours; AI spend within budget with no service change; secondary provider and open-weight bundle passing evals every month; zero domain services importing provider SDKs (CI check); gateway custom code limited to the capability resolver; 100% of models — including edge and batch — registered and monitored under governance.
