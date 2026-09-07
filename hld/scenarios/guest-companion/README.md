# S4 · Guest Companion

> Families wander, queue, leave early, and don't come back. We want a companion that plans their day, steers them to short queues and interesting animals, and gives them a reason to return.

**Moves:** OKR 1.2 (returning share 10% → 25%), 1.3 (family passes 40%), 2.2 (queue time via load spreading)
**Requirements:** FR-4.1, FR-4.2, FR-1.6, FR-5.1, FR-5.3
**ADRs:** [ADR-0005](../../../adrs/ADR-0005-model-gateway-and-provider-independence.md), [ADR-0010](../../../adrs/ADR-0010-grounded-llm-with-guardrails.md)

## Why generative AI here (and only here)
This is a language problem: a parent typing "we have a 3-year-old who's scared of loud rides and we need lunch by 12" needs an answer, not a filter form. An LLM turns that into a plan — but **every fact it uses comes from our structured knowledge base and live queue data**, not from the model's memory. Safety facts ("can we touch it?") are never generated; they are looked up.

## Solution

```mermaid
flowchart TB
    V["👨‍👩‍👧 Visitor<br/>mobile web / kiosk"] --> BFF["API gateway"]
    BFF --> Orch["Companion orchestrator<br/>session · tools · policy"]
    Orch --> GW["Model gateway 🤖<br/>capability: plan-visit / answer-question"]
    GW --> LLM(["LLM provider<br/>(interchangeable)"])
    Orch --> KB[("Knowledge base<br/>animals · rides · rules · hours · prices")]
    Orch --> Live["Live queues & occupancy (S3)"]
    Orch --> Fc["Expected queues (S3 forecast)"]
    Orch --> Tix["Ticketing (pass status)"]
    Orch --> Guard["Output guardrails<br/>facts check · safety · tone"]
    Guard --> V
    Orch -.-> Ev["Events: ItineraryCreated,<br/>AnimalViewed, RideDone"]
    Ev -.-> Nudge["Return-visit nudges 🤖<br/>(opt-in only)"]
    Nudge --> Msg(["Email / push"])
    Esc["👤 Staff escalation"] --- Orch
```

## What it does
- **Plan the day:** builds an itinerary from constraints (children's ages, interests, time, accessibility) using forecast and live queues; re-plans when a ride closes or a queue spikes.
- **Answer questions:** grounded on the knowledge base — "Where is the axolotl?", "Is the Ferris wheel OK for a 4-year-old?", "When is the piranha feeding?" — with citations to the source fact.
- **Offline-tolerant:** the itinerary and map are cached on the device; when Wi-Fi is patchy the visitor still has their plan; live re-planning resumes on reconnect.
- **Return nudges (opt-in):** "The cassowary chick you saw is on show from Saturday", "You saw 31 of 55 enclosures — finish your collection", "Quiet-day family pass this Wednesday". Content templates are curated; the LLM personalises within them.

## Containers
| Container | Responsibility | AI? |
| --- | --- | --- |
| Companion orchestrator | Session state, tool calls (KB, live data, ticketing), policy (what may be generated vs. looked up), escalation | No (orchestration) |
| Model gateway | Resolves `plan-visit` / `answer-question` to current model bundle; tiered routing (small model for FAQ, larger for planning); budget; fallback | — |
| Knowledge base | Structured facts + curated narrative; the only citable source | No |
| Output guardrails | Verifies every factual claim is traceable to a KB record or live-data call; blocks unsafe content; enforces tone and length | Partly (classifier) |
| Return-visit nudges | Segments opted-in visitors by behaviour; personalises curated templates; respects frequency caps | Yes — LLM for wording, rules for targeting |
| Staff escalation | Hand-off to a human at an info point for anything the companion cannot answer | Human |

## Validation & verification
- **Eval suite:** 300+ question/answer pairs with expected facts; 100 planning scenarios with hard constraints (must not include closed rides, must respect age limits); 100 adversarial prompts (jailbreaks, "can I feed the piranhas", medical questions) requiring refusal/escalation. Promotion: factuality ≥ 0.95, constraint violations 0, safety refusals 100%.
- **Production:** sampled LLM-as-judge on factuality + weekly human review of 50 sessions; thumbs-down rate; escalation rate; "answer not grounded" blocks by guardrails (each one is a KB gap or a model regression).
- **Business signal:** itinerary adherence (did they go where suggested?), queue time for companion users vs. non-users, return rate of nudged vs. control cohort (A/B).

## Degradation ladder
LLM provider A down → provider B via gateway → open-weight model → **static FAQ + map + "ask at the info point"**. The park never depends on the companion.
