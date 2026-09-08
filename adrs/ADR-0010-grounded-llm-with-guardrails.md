# ADR-0010 — Grounded LLM with output guardrails for the guest companion

**Status:** accepted · **Date:** 2026-09-05
**Serves:** FR-4.1, FR-4.2, NFR-PRF-1, R5
**Related:** ADR-0005, ADR-0008

## Context
A conversational companion is the most visible use of generative AI and the one most likely to say something wrong — "yes, you can touch the frog" is not an acceptable hallucination on an estate with poisonous animals. The model must be helpful in natural language while never inventing facts about animals, rides, prices, hours or safety.

## Decision
1. **Retrieval-grounded generation only.** The orchestrator retrieves candidate facts from the **estate knowledge base** (structured records + curated narrative) and live data (queues, ride status, pass state); the model composes an answer **from the retrieved context only** and must cite the record ids it used.
2. **Safety- and money-critical facts are looked up, not generated.** Age/height limits, "may I touch/feed", opening hours, prices, allergen info come from structured fields inserted verbatim into the response template; the model may phrase around them but cannot alter them.
3. **Output guardrails** before anything reaches the visitor: (a) every factual claim maps to a cited record or live-data call, else the answer is replaced with "let me check with staff" and the gap is logged; (b) a safety classifier blocks prohibited content and triggers escalation; (c) format/length/tone constraints; (d) **indirect injection defence** — retrieved knowledge-base text, live data and anything a visitor pastes are delimited as *data*, never as instructions; the model has no write tools and only allow-listed read tools. Guardrails run **progressively on the stream**: each claim is checked as it arrives, and a failed check replaces the partial answer rather than letting it finish.
4. **Scope policy:** the companion declines medical, legal and off-estate questions and offers the info point.
5. **Tiered models via the gateway, budgeted by request class** (NFR-PRF-1): FAQ answers come from a small model, p95 ≤ 3 s, with a daily **FAQ cache** of the top questions keyed by knowledge-base version; planning uses a larger model with **streaming** — first token ≤ 2 s, first stop suggestion ≤ 5 s, full plan ≤ 15 s, re-plan ≤ 5 s — so the family sees the first stop while the rest is composed. Secondary provider and open-weight fallback per ADR-0005; final fallback is static FAQ + map.
6. **Eval suite** (ADR-0008): 300+ Q&A pairs, 100 planning scenarios with hard constraints, 100 adversarial prompts, **100 indirect-injection cases** (the injection sits in a ride description, a live-status field or pasted text), an **ungrounded-block false-positive gate ≤ 5%** on 300 answerable questions, an **offline itinerary end-to-end test** (device offline → cached plan → re-plan on reconnect) and a **load test at 500 concurrent sessions** against the latency budgets. Safety refusals and injection resistance must be 100% at promotion and are monitored in production.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Open-ended chatbot with a system prompt | Quick, fluent | Hallucinated facts; safety depends on the model's mood | R5 |
| Fine-tune a model on estate content | Knows the estate | Facts change daily (queues, closures); retraining lag; still hallucinates | Freshness |
| Rule-based FAQ bot only | Fully predictable | Cannot plan a day from free text; poor experience | Misses FR-4.1's value |
| **Multi-step agent loop** — the model plans, calls tools iteratively and re-plans until it is satisfied | Day planning with a closure and a queue spike is a multi-constraint re-planning problem, which is what an agent loop is for; fewer orchestration paths written by hand | Non-determinism moves from the *answer* into the *control flow*: the guardrail contract of §3 must then hold over an unbounded number of steps, and each step is another indirect-injection surface (§3d). The NFR-PRF-1 budgets are per answer, not per loop, and tokens per session stop being bounded — both matter at 500 concurrent sessions. Our eval suite scores answers; scoring a *trajectory* is a different instrument we do not have. | **Deferred, not rejected.** Today the orchestrator holds the loop: a fixed retrieve → compose → guardrail → re-plan-affected-stops path with a bounded step count, so latency, cost and injection surface are all bounded by construction. Revisit when trajectory-level evals exist for it — the capability boundary (ADR-0005 §2) means the swap needs no service change |
| Grounded generation + guardrails (chosen) | Fluent and verifiable | Retrieval quality is now a dependency; guardrails add latency | — |

## Consequences
**Positive:** every answer is traceable to a source; safety facts cannot be corrupted by the model; KB gaps surface as measurable "ungrounded" blocks.
**Negative:** the orchestrator, not the model, owns the planning loop, so every new planning move is our code rather than the model's initiative; answers are only as good as the KB — curation is ongoing work; latency budgets differ by request class (FAQ p95 ≤ 3 s; planning streamed, full plan ≤ 15 s) and the guardrails add to them.

| Risk | Mitigation |
| --- | --- |
| KB out of date (ride closed) | Live status comes from events, not the KB; KB edits are owned by ops with a daily check |
| Guardrail false positives frustrate visitors | False-positive gate ≤ 5% at promotion on answerable questions; block rate monitored; "let me check" hands off gracefully |
| Prompt injection — direct via visitor input, **indirect via retrieved KB text or live data** | Retrieved content delimited as data; read-only allow-listed tools; 100-case indirect-injection eval at 100% resistance; input sanitisation |
| Planning too slow on a Saturday | Streaming with progressive guardrails; FAQ cache; load test at 500 sessions gates every promotion; tiered routing keeps FAQ off the large model |

## How we will know this was right
Factuality ≥ 0.95 on sampled sessions; zero safety-critical incorrect statements in audits; thumbs-down ≤ 5%; ungrounded-block false positives ≤ 5%; latency budgets met per request class in production; return rate uplift in the nudged cohort. Thresholds live in the [thresholds & cadences table](../hld/ai-platform/README.md#thresholds-and-cadences-source-of-truth).
