# 07 · Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- | --- |
| R1 | Uplink to cloud unavailable for hours/days | High | Medium | Edge-first design; ≥ 24 h buffering; gates and safety alerts fully local ([ADR-0001](../adrs/ADR-0001-edge-first-store-and-forward.md)) | Platform |
| R2 | Vision model misses a sick animal (false negative) | Medium | High | Conservative thresholds; sensor-based rules (feed scale, water) as independent signal; daily keeper walk remains; recall tracked on golden set ([ADR-0007](../adrs/ADR-0007-human-in-the-loop-confidence-bands.md)) | Welfare |
| R3 | Too many false alarms → vet ignores the queue | Medium | High | Confidence bands; override rate as KPI (OKR 3.5); threshold recalibration loop | Welfare |
| R4 | LLM provider raises prices or shuts down | Medium | Medium | Model gateway; per-capability budgets; named fallback provider; open-weight downgrade path ([ADR-0005](../adrs/ADR-0005-model-gateway-and-provider-independence.md)) | AI platform |
| R5 | Guest companion gives wrong/unsafe info (e.g. "you may touch the frog") | Medium | High | Grounding on estate knowledge base only; safety-critical facts served from structured data, not generated; refusal policy; eval suite with adversarial cases ([ADR-0010](../adrs/ADR-0010-grounded-llm-with-guardrails.md)) | Guest |
| R6 | Visitor tracking perceived as surveillance | Medium | High | Anonymous counting only; no face recognition; visitor areas masked in enclosure cameras; transparent signage ([ADR-0009](../adrs/ADR-0009-visitor-privacy-anonymous-counting.md)) | Platform |
| R7 | Forecasts unreliable in year 1 (no history) | High | Low | Heuristic staffing rules until data accumulates; model promoted only when MAPE target met | Ops |
| R8 | Dynamic pricing perceived as unfair | Medium | Medium | Hard floors/ceilings; transparent "quiet-day discount" framing; never raise price after a family has started checkout ([S5](../hld/scenarios/dynamic-family-passes/README.md)) | Guest |
| R9 | Small team cannot operate the platform | Medium | High | Managed cloud services; GitOps; one event backbone; no self-hosted model serving in cloud | Platform |
| R10 | Cameras stress animals or violate heritage rules | Low | Medium | Vet sign-off per enclosure; non-invasive sensors where cameras are not acceptable (A7, A10) | Welfare |
| R11 | Model drift as seasons/animals change | High | Medium | Input/output drift monitors; scheduled re-evaluation; retraining pipeline ([ADR-0008](../adrs/ADR-0008-ai-evaluation-and-production-monitoring.md)) | AI platform |
| R12 | Vendor lock-in on the chosen cloud | Medium | Medium | Open protocols (MQTT, OpenTelemetry, Parquet); containerised services; portable vision models; exit assessment in [ADR-0003](../adrs/ADR-0003-cloud-provider-selection.md) | Platform |
