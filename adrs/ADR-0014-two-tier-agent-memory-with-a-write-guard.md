# ADR-0014 — Two-tier agent memory with a write-guard

**Status:** accepted · **Date:** 2026-09-11
**Serves:** FR-4.7, FR-5.1, NFR-AGT-1, NFR-PRV-1, R22
**Related:** ADR-0004, ADR-0009, ADR-0013, ADR-0015

## Context
The four agents of [ADR-0013](ADR-0013-stakeholder-agents-on-typed-tools.md) are only useful if they
remember something: what this animal's week looked like, what the ops manager changed last Tuesday and
why, which suggestions this household ignored. The obvious answer — "the lakehouse is the memory" —
does not survive contact with latency. The curated and feature tiers are batch and eventually
consistent, which is right for training and wrong for a conversation that has to answer in seconds.
The opposite answer — a session store and nothing else — gives an agent that forgets everything
between shifts.

There is a second problem, and it is the sharper one. As soon as an agent may *write* to a memory that
later shapes its own reads, the loop closes: a poisoned or simply wrong derivative becomes tomorrow's
context, and the degradation is silent because no business metric moves until much later.

## Decision
1. **Two tiers, with different jobs.**
   - **Long-term** — the curated and feature tiers of the data platform plus the knowledge base:
     history, per-animal baselines, decision records, golden sets, lineage. Shared by all agents,
     read through tools, never by ad-hoc query ([ADR-0015](ADR-0015-metric-layer-and-estate-twin.md)).
   - **Working** — a session and shift store: the current conversation, the current round, the last
     few events on the relevant subject. TTL'd, populated from the long-term tier, and holding no
     personal data beyond what the session itself carries.
2. **Operational truth never lives in memory.** The four contexts remain the source of record for
   their own data; memory holds derivatives and context. Where the two disagree, the context wins and
   the divergence is logged.
3. **Writes are typed derivatives, not free text.** An agent may write an outcome, a feedback flag or
   a label, each by schema. It may not write an instruction, a rule or a norm. There is no path from
   an agent's output to a prompt, a policy or a threshold.
4. **Every write passes a write-guard:** schema and range validation, **provenance** (agent id,
   session id, trace id, bundle version), and deduplication on a business key. A rejected write is
   logged and counted; the reject rate is a monitored signal, not a silent drop.
5. **Derivatives that touch welfare, safety or money are human-approved** before they enter the
   long-term tier — the same gate as an effectful action.
6. **Memory is versioned with lineage, so a batch can be rolled back by provenance** exactly as a
   model version is rolled back.
7. **Self-reinforcement is monitored explicitly:** PSI on the distribution of self-generated writes,
   and the ratio of self-generated to human-verified labels. A rise in either raises human review
   before it reaches a business metric ([thresholds table](../hld/ai-platform/README.md#thresholds-and-cadences-source-of-truth)).
8. **Erasure reaches memory.** `SubjectErased` removes the subject from both tiers on the same path as
   read models and golden sets ([ADR-0009](ADR-0009-visitor-privacy-anonymous-counting.md) §7); the
   working tier's TTL means most of it has already gone.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Lakehouse as the only memory | One store, one lineage story | Batch latency and staleness in a conversational path; every agent turn waits on an analytical query | Latency |
| Working memory only | Fast; nothing to govern | No history, no baselines, no lineage; agents forget between shifts, which removes most of the value | Loses the point |
| Agents writing to the contexts' own stores | Simplest data path | Destroys context ownership and the outbox guarantees; two writers on one schema | [ADR-0004](ADR-0004-event-driven-backbone.md) |
| Free-form writes to memory, no guard | Flexible; cheap to build | Opens memory poisoning and silent self-training, and makes rollback impossible — no provenance to roll back by | The failure this ADR exists for |
| Two tiers with a write-guard (chosen) | Latency where it is needed, lineage where it matters, a poisoned batch is revertible | Two stores to keep in step; the guard is code we own | — |

## Consequences
**Positive:** agents gain continuity without a new system of record; a poisoning attempt is a rejected
write with a name on it rather than a silent contamination; the provenance schema exists before the
first derivative does.
**Negative:** synchronisation between tiers is a freshness question we now have to answer; the guard
adds a hop to every write; before Phase 3 the long-term tier holds almost nothing an agent produced,
so part of this is built ahead of its need.

| Risk | Mitigation |
| --- | --- |
| Memory poisoning through a crafted session (R22) | Decisions 3–6; the worked chain and GD-18 are in [agents.md](../hld/ai-platform/agents.md#trust-boundary-with-the-chains-worked-through) |
| Silent self-reinforcement | Decision 7, with PSI and the self-to-human label ratio in the thresholds table |
| Personal data accumulating in the working tier | TTL plus the pseudonymous subject rule ([ADR-0009](ADR-0009-visitor-privacy-anonymous-counting.md) §7); the working tier is covered by the erasure audit query |
| Provenance retrofitted too late to be useful | Written into the schema now, before any agent writes — retrofitting provenance onto a memory that has none is not possible |

## How we will know this was right
Accepted anomalous writes = 0; derivative PSI inside its band; the share of self-generated labels flat
or falling as human-verified labels accumulate; and one rehearsed rollback of a derivative batch by
provenance, in GD-18, completing inside the game day's window.
