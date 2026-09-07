# ADR-0010 — Grounded LLM with output guardrails for the guest companion

**Status:** accepted · **Date:** 2026-09-05
**Serves:** FR-4.1, FR-4.2, NFR-PRF-1, R5
**Related:** ADR-0005, ADR-0008

## Context
A conversational companion is the most visible use of generative AI and the one most likely to say something wrong — "yes, you can touch the frog" is not an acceptable hallucination on an estate with poisonous animals. The model must be helpful in natural language while never inventing facts about animals, rides, prices, hours or safety.

## Decision
1. **Retrieval-grounded generation only.** The orchestrator retrieves candidate facts from the **estate knowledge base** (structured records + curated narrative) and live data (queues, ride status, pass state); the model composes an answer **from the retrieved context only** and must cite the record ids it used.
2. **Safety- and money-critical facts are looked up, not generated.** Age/height limits, "may I touch/feed", opening hours, prices, allergen info come from structured fields inserted verbatim into the response template; the model may phrase around them but cannot alter them.
3. **Output guardrails** before anything reaches the visitor: (a) every factual claim maps to a cited record or live-data call, else the answer is replaced with "let me check with staff" and the gap is logged; (b) a safety classifier blocks prohibited content and triggers escalation; (c) format/length/tone constraints.
4. **Scope policy:** the companion declines medical, legal and off-estate questions and offers the info point.
5. **Tiered models via the gateway:** small model for FAQ, larger for multi-constraint planning; secondary provider and open-weight fallback per ADR-0005; final fallback is static FAQ + map.
6. **Eval suite** (ADR-0008) includes adversarial prompts; safety refusals must be 100% at promotion and are monitored in production.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Open-ended chatbot with a system prompt | Quick, fluent | Hallucinated facts; safety depends on the model's mood | R5 |
| Fine-tune a model on estate content | Knows the estate | Facts change daily (queues, closures); retraining lag; still hallucinates | Freshness |
| Rule-based FAQ bot only | Fully predictable | Cannot plan a day from free text; poor experience | Misses FR-4.1's value |
| Grounded generation + guardrails (chosen) | Fluent and verifiable | Retrieval quality is now a dependency; guardrails add latency | — |

## Consequences
**Positive:** every answer is traceable to a source; safety facts cannot be corrupted by the model; KB gaps surface as measurable "ungrounded" blocks.
**Negative:** answers are only as good as the KB — curation is ongoing work; some latency (target p95 ≤ 3 s).

| Risk | Mitigation |
| --- | --- |
| KB out of date (ride closed) | Live status comes from events, not the KB; KB edits are owned by ops with a daily check |
| Guardrail false positives frustrate visitors | Monitor block rate; tune; "let me check" hands off gracefully |
| Prompt injection via visitor input | Input sanitisation; tools have least privilege; no write actions from the companion |

## How we will know this was right
Factuality ≥ 0.95 on sampled sessions; zero safety-critical incorrect statements in audits; thumbs-down ≤ 5%; return rate uplift in the nudged cohort.
