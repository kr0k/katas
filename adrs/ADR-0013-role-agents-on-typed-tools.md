# ADR-0013 — Role agents on typed tools, proposing into existing approvals

**Status:** accepted · **Date:** 2026-09-09
**Serves:** FR-2.8, FR-4.5, NFR-AGT-1, R21, R22, R23
**Related:** ADR-0004, ADR-0005, ADR-0007, ADR-0008, ADR-0010

## Context
The scenarios put AI where a judgement is needed, but they deliver it as an alert, a forecast or a
chat answer — one output, one screen. The decisions that actually run the estate are multi-step: the vet
wants to know *why* this animal is flagged and what it looked like last week before opening a treatment;
the ops manager wants tomorrow's roster changed for one zone and to see what that costs; the Countess
wants the follow-up question the daily report did not anticipate. Each of those is three or four lookups
and a draft, and today each is a human stitching screens together.

That is the gap between "AI in the architecture" and **AI inside the business process**, which is what
this submission now claims. The brief points the same way with its own agent example. Meanwhile the
failure modes are real and well-known: an agent that acts can be steered by content it retrieved, can
loop, can duplicate an effect on a retry, and can learn from its own output until it quietly drifts.

## Decision
1. **An agent is a model plus typed, least-privilege tools, and its output is a proposal.** Two agents
   and one read-only capability, no more: [`agent:ops-copilot`](../hld/ai-platform/agents.md#ops-copilot)
   for keepers, the vet and the ops manager; [`agent:companion`](../hld/ai-platform/agents.md#companion),
   which is S4 gaining a tool-selection turn; and
   [`ask-the-estate`](../hld/ai-platform/agents.md#ask-the-estate) for management, read-only over defined
   metrics. Tool inventories are in [agents.md](../hld/ai-platform/agents.md).
2. **Not one agent per stakeholder group.** The vet's process *is* the review queue and the Countess's
   *is* the 21:00 report; those need a better queue and a question box, not agents of their own. Four
   role agents would mean four sets of tools, evals, budgets and audit surfaces for five engineers.
3. **Agents propose into approval surfaces that already exist** — the review queue
   ([ADR-0007](ADR-0007-human-in-the-loop-confidence-bands.md)), roster approval, management price
   approval, the vendor's checkout. No new approval UI, and therefore no second place where an action can
   be authorised.
4. **A tool is a read or a command, never a write.** Reads go to the metric layer, the knowledge base and
   published read models; effects are emitted as commands to the owning context
   ([ADR-0004](ADR-0004-event-driven-backbone.md) §7–9). No agent touches another context's schema, and
   the same CI fitness function that forbids cross-module table access covers tool handlers.
5. **Retrieved content is data, never instruction**, and tools come only from a typed whitelist, so
   content cannot introduce a tool or an argument outside the schema. The worked chain is in
   [agents.md](../hld/ai-platform/agents.md#trust-boundary-with-the-chain-worked-through) and it is game
   day GD-17.
6. **Bounded, idempotent, reconstructible** (NFR-AGT-1): a step and token budget per task that degrades
   and escalates on exhaustion rather than continuing (GD-20); effectful calls idempotent on a business
   key so a retry is harmless (GD-18); every tool call a span carrying arguments, outcome, cost and
   `bundle_id`.
7. **No agent-generated memory before Phase 3.** The only things written back are human decisions, which
   we already capture as labels. When derived writes arrive they pass a **write-guard** — typed
   derivatives only, provenance, dedup, human approval for anything touching welfare, safety or money —
   with PSI on self-generated writes and rollback of a batch by provenance. Specified now because it
   shapes the schema; provenance cannot be retrofitted onto a memory that has none.
8. **Agents run inside the existing deployables.** No new service, no new datastore. The layer is
   configuration, prompts and tool handlers in the BFF and the monolith.
9. **The layer must stay proportionate to its audience.** Staff tasks are hundreds a day, not millions,
   so the whole layer is ≈ €360/yr — 1% of generative spend — and a self-test in
   [`scripts/business_case.py`](../scripts/business_case.py) fails the build if it exceeds 5%. Tool
   selection is a routing decision, not a reasoning one, and is priced on the small tier accordingly.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| **Four agents, one per stakeholder group** (the shape the sibling proposal took) | Complete coverage; a clean story per persona; more visible AI ambition | Four tool inventories, four eval suites, four budgets, four audit surfaces — and two of them would wrap processes that are already single-screen decisions (the vet's queue, the Countess's report) | Operability at five engineers (NFR-OPS-1, R9). Coverage is achieved by tools, not by multiplying agents |
| **Keep assistants only — no tools, no agency** | Nothing new to secure; today's design unchanged | The multi-step work stays manual, so the claim that AI sits inside the decision would be false. Answering "why is this animal flagged" needs three lookups, and a chat window that cannot do them is a search box | It is the claim we are making; declining it means dropping the claim |
| **Agents with direct database or SQL access** | Fastest to build; answers anything | Bypasses per-context ownership and permissions, unauditable, and text-to-SQL over raw schemas invents joins and therefore invents numbers | Correctness and ADR-0004 §7; the metric layer exists precisely so a question resolves to a defined number or is refused |
| **Fully autonomous agents that act** | No human in the loop, so no queue and no latency | Fails V&V: there is no evaluation that makes an unreviewed price change or welfare intervention acceptable, and the reputational exposure is asymmetric ([ADR-0007](ADR-0007-human-in-the-loop-confidence-bands.md)) | Safety and accountability. A human commits anything that moves money, rosters, prices or care |
| **Agent memory with free-form write-back from day one** | The loop improves itself; richer context | Opens memory poisoning and silent self-reinforcement, and without provenance there is nothing to roll back | Deferred to Phase 3 behind the write-guard (§7) — the mitigation is specified, the feature is not built |
| **Role agents on typed tools, proposing (chosen)** | AI reaches inside the decision; one tool pattern; reuses existing approvals, traces, budgets and evals | Agency is a new attack surface; nondeterministic multi-step behaviour is harder to test than a single call; a new eval axis to maintain | — |

## Consequences
**Positive:** the multi-step work in P1, P2 and P4 stops being screen-stitching; one tool pattern and one
audit surface cover every agent; the layer costs ≈ 1% of generative spend; and because tools are commands,
switching the whole layer off leaves every process working.

**Negative:** a new failure class to test (injection, loops, retries) and four game days to run for it;
tool inventories are a maintenance surface that must not quietly grow; nondeterministic chains make
regression testing statistical rather than exact; and the copilot can waste the vet's time through
`open_review`, which is why that tool is rate-limited and its items are tagged by origin.

| Risk | Mitigation |
| --- | --- |
| Indirect prompt injection through retrieved content (R21) | Quoted-context boundary, typed whitelist, human commit on every effect, tool-error visibility; GD-17 |
| Runaway task or retry storm (R23) | Step and token budget with degrade-and-escalate; idempotency on a business key; per-capability cost budget; GD-18, GD-20 |
| Memory poisoning and self-reinforcement (R22) | No agent writes before Phase 3; then the write-guard, PSI on self-writes and rollback by provenance (§7) |
| The tool inventory grows until least-privilege is meaningless | Every new tool is a pull request against this ADR naming the process it serves and who commits its effect; read tools go to the metric layer, never to a store |
| Proposals are approved without being read | `evidence` travels with every model output ([ADR-0007](ADR-0007-human-in-the-loop-confidence-bands.md) §6); override rate and shed-item audits are tracked, and a rise in approvals with falling override rate is itself the signal |

## How we will know this was right
Task success and human-override rate within their thresholds (OKR 5.4); tool-error rate falling after the
first month; duplicate effects 0 and instructions-followed-from-content 0 across GD-17 to GD-20; the
agentic layer under 5% of generative spend, asserted in the self-test; and the honest negative test — with
the layer disabled, every one of the five processes still completes, which is checked in GD-19.
