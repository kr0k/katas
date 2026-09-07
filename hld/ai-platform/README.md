# AI Platform

Shared infrastructure that every AI scenario uses. It exists to answer two of the judges' questions structurally rather than per-scenario: **how do we cope with a fast-changing AI landscape**, and **how do we know the AI works**.

It has two halves that are easy to confuse. **Model governance** (registry, evaluation, monitoring) covers *every* model we run — rented, own, cloud, edge or batch. The **inference gateway** is a runtime proxy for *hosted* models only, and we adopt it rather than build it. → [ADR-0005](../../adrs/ADR-0005-model-gateway-and-provider-independence.md)

## Components

```mermaid
flowchart LR
    subgraph Services["Business monolith modules & AI consumers"]
        Ops["Park Operations"]
        Welfare["Animal Welfare"]
        Guest["Guest Engagement"]
        Cons["🤖 AI consumers / batch workers"]
    end

    subgraph Gov["Model governance — every model"]
        Reg[("Model & prompt registry<br/>versions · eval scores · owners")]
        Eval["Evaluation service<br/>golden sets · CI gate · shadow runs"]
        Mon["AI monitoring<br/>drift · confidence · cost · overrides"]
    end

    subgraph Runtime["Inference runtime"]
        Res["Capability resolver (built, thin)<br/>capability → bundle → route"]
        GW["Inference gateway (adopted OSS)<br/>routing · budgets · fallback · tracing · PII scrub"]
        Own["Own model endpoints<br/>(managed hosting, cloud)"]
        Edge["Edge inference nodes 🏰"]
        Batch["GPU / batch jobs"]
    end

    subgraph Providers["Hosted models"]
        P1(["LLM provider A"])
        P2(["LLM provider B (fallback)"])
        OW(["Open-weight model<br/>(managed hosting, downgrade path)"])
    end

    HITL["Review queue service 👤<br/>confidence bands · SLAs · audit"]
    Train["Training pipelines<br/>(vision & tabular models)"]

    Ops & Welfare & Guest --> Res
    Cons --> Res
    Res --> GW
    GW --> P1 & P2 & OW
    Res --> Own
    Reg --> Res
    Reg -. "deploy" .-> Edge
    Reg -. "deploy" .-> Own
    Reg -. "deploy" .-> Batch
    GW -.-> Mon
    Own -.-> Mon
    Edge -.-> Mon
    Batch -.-> Mon
    Eval --> Reg
    Train --> Reg
    Mon -.-> Eval
    Welfare --> HITL
    HITL -.-> Train
```

## Inference runtime

### Inference gateway (adopted) and capability resolver (built)
Business services request a **capability** (`detect-feeding-anomaly`, `plan-visit`, `forecast-zone-footfall`), never a model. The **capability resolver** — the only runtime code we write here — looks the capability up in the registry and sends the request down its runtime path. For hosted models that path is the **inference gateway**, an open-source LLM gateway (LiteLLM, Portkey, Kong AI Gateway class) configured from Git. It applies:

- **Routing policy:** tiered (small/cheap model first; escalate to a larger one on low confidence or explicit need), or fixed for capabilities where determinism matters.
- **Budgets:** per-capability monthly budget; alerts at 70/90%; at 100% switch to the downgrade path rather than fail.
- **Fallback chain:** provider A → provider B → open-weight model on **managed hosting** (not self-hosted — R9) → deterministic fallback (returned as a typed "no AI available" response the service knows how to handle).
- **Tracing:** every call emits `capability`, `model_version`, `latency`, `tokens`, `cost`, `confidence` to OpenTelemetry.
- **Guardrails:** input/output schema validation, PII scrubbing on the way out to external providers, output filters for the companion.

We do not build any of that. Routes, budgets and fallback chains are declarative configuration, portable between gateways of this class.

→ [ADR-0005](../../adrs/ADR-0005-model-gateway-and-provider-independence.md)

### Capability → runtime path

| Capability (examples) | Model kind | Runtime path | Governed by |
| --- | --- | --- | --- |
| `answer-question`, `plan-visit`, `summarise-daily-welfare-report`, nudge wording | Rented generative; open-weight on managed hosting as downgrade | Capability resolver → **inference gateway** → provider or managed endpoint | Registry · eval gate · monitoring |
| `detect-feeding-anomaly`, `score-enclosure-activity` | Own tabular / time-series, cloud | AI consumer on the backbone → **own model endpoint** (managed hosting); no gateway | same |
| `extract-enclosure-features`, `mask-visitors`, `count-piranha`, `flag-aggressive-behaviour` (tier-1 advisory) | Own vision, edge | **Edge inference node**; artifact pulled from the registry over the downlink ([ADR-0006](../../adrs/ADR-0006-edge-vs-cloud-inference.md)); node reports version and confidence stats | same |
| `forecast-zone-footfall`, `estimate-price-elasticity` | Own tabular, batch | **Scheduled batch job** in the GPU/batch workers; results published as events | same |

The gateway is on the path of the first row only. The other three rows never touch a hosted provider and never depend on the gateway — but they cannot be promoted or served without passing through governance.

## Model governance

Applies to every row of the table above, wherever the model runs.

### Model & prompt registry
Versioned bundles: model reference (external model ID, or our own artifact), prompt template, parameters, eval score, owner, status (`candidate` / `shadow` / `production` / `retired`). Declared in Git and reconciled (GitOps), so a model change is a reviewed pull request. Edge nodes and batch jobs read their *desired version* from the registry; the resolver reads the production bundle for hosted capabilities.

### Evaluation service
- **Golden datasets** per capability, maintained by the domain owner (vet for welfare, ops manager for forecasting, guest team for companion).
- **CI gate:** a candidate bundle must meet the capability's thresholds (e.g. recall ≥ 0.9 on "missed meal"; MAPE ≤ 20%; companion factuality ≥ 0.95, safety-refusal 100%) or it cannot be promoted.
- **Shadow mode:** candidate runs alongside production on live traffic, outputs compared, no user impact.
- **LLM-as-judge** with human calibration sample for open-ended outputs.

→ [ADR-0008](../../adrs/ADR-0008-ai-evaluation-and-production-monitoring.md)

### AI monitoring
- Input drift (feature distributions, image statistics), output drift (confidence histograms, class balance), and **business-metric guardrails** (vet override rate, forecast error, companion thumbs-down rate, pricing floor hits).
- Automatic rollback to the previous production bundle when a guardrail trips — for hosted bundles via the gateway route, for edge and batch models via the registry's desired version.

### Review queue (human in the loop)
Confidence bands per capability decide auto-act / human review / discard-and-learn. Reviewer decisions are captured with reason codes and become training data.

→ [ADR-0007](../../adrs/ADR-0007-human-in-the-loop-confidence-bands.md)

### Training pipelines
For models we own (enclosure vision, piranha counting, forecasting, pricing): reproducible pipelines from the data platform, producing artifacts registered with lineage. Edge models are exported to a portable format, signed, and pulled by edge nodes through the downlink described in [Edge & connectivity](../core/edge-and-connectivity.md#downlink-cloud--estate).

## The three kinds of AI and how the platform treats them

| Kind | Examples | Determinism | Pre-release check | Production check |
| --- | --- | --- | --- | --- |
| Classical ML | forecasting, pricing | Deterministic given inputs | Backtests, MAPE/RMSE thresholds | Error vs. actuals, drift |
| Computer vision | welfare anomalies, piranha count | Probabilistic | Precision/recall on golden footage | Confidence bands, override rate, weekly audit |
| Generative | companion, report summaries | Non-deterministic | Factuality, safety, format evals; adversarial set | Sampled judge + human, thumbs-down, escalation rate |

## Answering the judges directly

| Question | Answer |
| --- | --- |
| Best model today isn't best tomorrow | Change the registry entry, pass the eval gate, promote. No service code changes. Target ≤ 1 day (OKR 5.2). |
| Provider changes prices | Budgets + tiered routing + downgrade path already wired in the gateway config; cost per capability visible daily. |
| Provider shuts down | Named fallback provider passing the same evals; open-weight bundle on managed hosting exercised monthly; prompts/evals/traces are ours; safety paths never depend on a generative provider. |
| The gateway itself is a dependency | It is adopted OSS with declarative config; the resolver isolates services; only hosted generative capabilities depend on it — vision, counting and forecasting never do. |
| How do we know it works? | Nothing is promoted without passing its golden set; shadow before live; guardrails with auto-rollback after. |
| How do we know it *stopped* working? | Drift monitors + business-metric guardrails + human override rate, alerting the capability owner. |
