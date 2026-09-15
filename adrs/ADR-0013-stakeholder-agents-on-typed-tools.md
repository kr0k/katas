# ADR-0013 — Stakeholder agents on typed tools

**Status:** accepted · **Date:** 2026-09-11
**Serves:** FR-2.8, FR-4.7, FR-5.1, FR-5.4, NFR-AGT-1, OKR 5.4, R22, R25
**Related:** ADR-0004, ADR-0005, ADR-0007, ADR-0008, ADR-0010, ADR-0014, ADR-0015

## Context
The five original scenarios put a model where a judgement is needed, but each delivers one output onto
one screen: an alert, a forecast, a chat reply, a price. The work that actually runs the estate is not
shaped like that. The vet wants to know *why* this enclosure is flagged, what it looked like last week
and whether the scale can be trusted, before opening a treatment. The ops manager wants tomorrow's
roster changed in one zone and wants to see what the change costs. The Countess wants the follow-up
question the 21:00 report did not anticipate. Each of those is three or four lookups and a draft, and
today each is a human stitching screens together — which is exactly the work the estate has no people
for.

That gap is the difference between AI placed *in the architecture* and AI placed *inside a business
process*. Closing it means letting a model take more than one step, and that is where the known failure
modes live: an agent can be steered by the content it retrieved, can loop, can duplicate an effect on a
retry, and — if it learns from its own output — can drift without anyone noticing.

## Decision
1. **An agent is a model plus typed, least-privilege tools, and its output is a proposal.** Four
   agents, one per stakeholder group the estate actually has, described in
   [agents.md](../hld/ai-platform/agents.md): `agent:ops-copilot` (keepers and the ops manager),
   `agent:animal` (the vet), `agent:companion` (the visiting family — S4 gaining a tool-selection
   turn) and `agent:management` (the Countess and management, read-only).
2. **Agents are a layer, not a quantum.** They orchestrate capabilities and contexts that already
   exist; they own no domain data and are no new deployable. `agent:companion` runs in the BFF, the
   other three inside the business monolith ([ADR-0004](ADR-0004-event-driven-backbone.md) §7).
3. **Tools are typed and whitelisted per agent.** A tool declares its arguments as a schema, its
   read scope and whether it has an effect. There is no ad-hoc SQL, no direct access to another
   context's store, and no tool on a tier-0 safety path (FR-3.6).
4. **Effectful tools emit a command; the owning context performs the write** and publishes the event.
   Every effectful call carries an idempotency key derived from a business key, so a retried tool call
   is collapsed rather than duplicated ([core → inbox](../hld/core/README.md#consumer-side-idempotency-the-inbox)).
5. **A human commits anything that moves money, rosters, prices or an animal's care.** The agent
   proposes into the approval surface that already exists — the review queue, the roster screen, the
   vendor's checkout — rather than inventing a new one ([ADR-0007](ADR-0007-human-in-the-loop-confidence-bands.md) §5).
6. **Retrieved content and visitor text are data, never instructions.** They enter the model as quoted
   context and never as the system or tool-selection prompt; content cannot introduce a tool or an
   argument outside the schema.
7. **Budgets are structural.** Each agent task has a step limit and a token budget (NFR-AGT-1);
   exhaustion degrades and escalates to a human, and never continues.
8. **The agent is a versioned artifact of its own** — prompt, tool whitelist, step budget — promoted
   and rolled back separately from the model bundle it runs on, because the failure is at least as
   often in the wiring as in the model ([ADR-0008](ADR-0008-ai-evaluation-and-production-monitoring.md)).

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Assistants only — no tools, no steps | Cheapest; nothing to misuse | The multi-step work stays manual, which is the work the estate cannot staff; the brief's own example points the other way | Leaves the value on the table |
| One agent for everyone | One tool set, one eval suite, one budget | The union of every tool is the least-privilege of none: the companion would hold the vet's tools | Violates decision 3 |
| Fully autonomous agents that act | Fastest; no human bottleneck | Unacceptable where the effects are an animal's treatment, a roster or a price; nothing left to validate against | Safety and V&V |
| Agents with direct database access | Simple to build | Bypasses context ownership and permissions; unauditable; breaks the extraction criteria in [ADR-0004](ADR-0004-event-driven-backbone.md) §7 | Operational integrity |
| Four agents on typed tools, proposing (chosen) | Each stakeholder's process gets its own narrow tool set; effects stay in the owning context | Four tool inventories, eval suites and budgets to maintain on a team of five | — |

## Consequences
**Positive:** the multi-step part of four jobs gets help without a new team; every effect remains
reachable without the agent; one tracing and audit story covers agents and models alike.
**Negative:** four agents is four sets of tools, evals and budgets — the largest single operability
cost in this proposal, and the reason R25 exists; nondeterministic chains are harder to test than a
single call; the tool layer is code we write and own.

| Risk | Mitigation |
| --- | --- |
| Indirect prompt injection through retrieved content | Decision 6 plus a typed whitelist; the worked chain and its game day are in [agents.md](../hld/ai-platform/agents.md#trust-boundary-with-the-chains-worked-through) (GD-17) |
| An agent duplicates an effect on retry | Decision 4: idempotency key on every effectful call; verified by the same replay test every consumer runs |
| Four agents outgrow a team of five (R25) | Phased: `ops-copilot` and `companion` in Phase 2, `animal` and `management` in Phase 3, each behind a kill gate; the agent count is a tracked number in the [human roles table](../hld/ai-platform/README.md#humans-in-the-loop-who-does-what) |
| An agent becomes the only path to an action | Invariant 1 in [agents.md](../hld/ai-platform/agents.md#invariants): every tool's effect stays reachable through a form, a dashboard or the desk |

## How we will know this was right
Task success above its threshold with human-override rate falling release over release; tool-error
rate attributable to integrations rather than the model; zero effectful actions committed without a
human where policy requires one; and the agentic layer holding under 5% of generative spend
([cost](../hld/ai-platform/agents.md#cost-and-why-the-layer-is-nearly-free)). We revisit it if a
second agent has to be rolled back in a quarter, or if agent maintenance starts displacing scenario
work for the five engineers.
