# Appendix · AI incident runbook

Rollback is wired ([ADR-0008](../adrs/ADR-0008-ai-evaluation-and-production-monitoring.md)); this is the
procedure around it, written down because at 07:00 on a Saturday nobody reconstructs a procedure from an
architecture document. One page, runnable by whoever is on site.

**What counts as an AI incident:** a guardrail trip, a capability producing something harmful or
plainly wrong, an injection attempt that reached a tool, a cost anomaly, or a member of staff saying "the
system told me something untrue". The last one is a real trigger, not a courtesy.

## The four steps

| Step | What happens | Who | Target |
| --- | --- | --- | --- |
| **1 · Fall back** | Set the capability to its deterministic fallback — the rule, the template, the fixed price, the documented human procedure. This is the [kill switch](../hld/ai-platform/README.md#model-governance) and it needs no diagnosis first: falling back is always safe, because the fallback is what the process ran on before the model existed | Whoever noticed | ≤ 5 min from noticing |
| **2 · Tell the owner** | Every capability has a named owner in the [thresholds table](../hld/ai-platform/README.md#thresholds-and-cadences-source-of-truth) — vet, ops manager, guest team, management, AI platform. The owner decides whether the fallback stays, not the engineer who flipped it | The person who fell back | Same hour, in hours |
| **3 · Preserve the evidence** | Nothing is deleted or re-run before it is captured: the trace with its spans, the `bundle_id`, the inputs, the confidence and evidence fields, and for an agent the tool calls and their arguments. A capability whose incident cannot be reconstructed afterwards is a defect in its own right (NFR-AGT-1) | AI platform | Before any fix |
| **4 · Post-mortem, then re-entry** | What failed, what the evidence shows, and what check would have caught it. Returning to production means passing the eval gate again — including any case added because of this incident, which is how the golden set grows | Owner + AI platform | Within a week |

**A model failure is never a page.** Step 1 is available to anyone and the fallback holds indefinitely, so
the owner is reached in working hours. Only the deterministic safety tier wakes people at night
(NFR-AVL-3) — and it is deterministic precisely so that no model failure can.

## Two cases worth pre-deciding

**A wrong safety statement to a visitor.** Treat as an incident regardless of confidence or frequency: the
companion goes to its static-answer fallback for the affected topic, the safety field is checked against
the approved per-language source, and the case joins the adversarial eval set. Frequency is not the
measure — a single instance is the incident ([ADR-0010](../adrs/ADR-0010-grounded-llm-with-guardrails.md) §2).

**An injection attempt that reached a tool.** The attempt is a tool-error span by design
([ADR-0013](../adrs/ADR-0013-role-agents-on-typed-tools.md) §5), so the question is not whether the
guardrail held but how the content got in: the knowledge base is curated, so an edit is attributable in
the page history. Fall back, preserve the trace, and treat the *source* as the incident rather than the
model.

## What is not here

Severity tiers, an on-call rota for models, and a paging tree. A team of five running a park has one
rota, and it exists for the estate rather than for the AI. If a capability ever seems to need its own
rota, that is a signal it has been allowed onto a critical path it should not be on
([ADR-0013](../adrs/ADR-0013-role-agents-on-typed-tools.md) §1, NFR-RES-2).
