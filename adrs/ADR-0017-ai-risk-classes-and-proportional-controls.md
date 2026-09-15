# ADR-0017 — AI risk classes and proportional controls

**Status:** accepted · **Date:** 2026-09-11
**Serves:** FR-5.1, FR-5.4, NFR-VER-1, NFR-OPS-1, OKR 5.3, R22, R24, R25
**Related:** ADR-0005, ADR-0007, ADR-0008, ADR-0013, ADR-0016, ADR-0022

## Context
With four agents and a portfolio of twenty-three AI applications, the controls are no longer few enough to
carry in one head. They also already exist and are scattered: calibration gates and golden sets in
[ADR-0008](ADR-0008-ai-evaluation-and-production-monitoring.md), bands and review queues in
[ADR-0007](ADR-0007-human-in-the-loop-confidence-bands.md), fallbacks and budgets in
[ADR-0005](ADR-0005-model-gateway-and-provider-independence.md), privacy in
[ADR-0009](ADR-0009-visitor-privacy-anonymous-counting.md). What is missing is the rule that says
*which* of them a given capability must have — and, just as importantly, which it may skip.

The failure this prevents is symmetrical. Apply every control to every capability and a caption
drafter costs as much to ship as a welfare model, so on a team of five the small capabilities never
ship. Apply the light set everywhere and something that can hurt an animal, a child or the estate's
licence goes out with a caption drafter's rigour.

## Decision
1. **Every AI capability and every agent carries a risk class**, declared in the registry next to its
   bundle, and the class determines the mandatory controls.

   | Class | What puts a capability here | Mandatory controls on top of the baseline |
   | --- | --- | --- |
   | **High** | A wrong output can injure a person, kill an animal, or invalidate a certification. Today: S1 welfare scoring, S8 ride condition, the tier-1 safety advisory | **No automatic band may act on the world**: a named human decides the consequential outcome — whether an animal is treated, whether a ride opens — and what a high-confidence band may do on its own is bounded to recording, ranking and routing ([ADR-0007](ADR-0007-human-in-the-loop-confidence-bands.md) §1, [ADR-0016](ADR-0016-cost-of-error-sets-the-bands.md) §3). Plus a cost-of-error row; a game day; delayed ground truth joined monthly; a documented incident path; the capability cannot be its own safety guarantee, and a deterministic rule must stand behind it. Where no band can be drawn safely at all — S8 — the capability has none at any confidence ([ADR-0022](ADR-0022-ride-condition-monitoring.md) §3) |
   | **Medium** | A wrong output moves money, a roster, a visitor's day or an animal's routine, and a human can still catch it. Today: S3 forecasting and staffing, S5 pricing, S4 companion, S7 content, and the three agents that draft or create work (`ops-copilot`, `animal`, `companion`) | Human approval on anything effectful; confidence bands; drift and business guardrails with automatic rollback; per-capability budget; the fairness check where a price or a person is involved |
   | **Low** | A wrong output wastes a human's minute. Today: report phrasing, S7 theme naming, the FAQ tier of the companion, and `agent:management`, which is read-only by construction | Baseline only: eval gate, monitoring, a named fallback, an owner |

2. **The baseline is not optional at any class**: a versioned bundle in the registry, a passing eval
   suite, a named deterministic fallback (NFR-RES-2), an owner, and full decision logging (FR-5.1).
3. **Class is assigned at design time and re-checked at promotion.** A capability that gains an
   effectful tool or a safety consequence is reclassified before it ships, not after.
4. **The high class has a hard rule the others do not:** AI never issues a clearance. It may flag, rank
   and explain; a certified human decides whether an animal is treated or a ride opens
   ([ADR-0022](ADR-0022-ride-condition-monitoring.md) §3).
5. **Autonomy above the high class is out of scope in this submission.** A driverless vehicle
   ([ADR-0020](ADR-0020-internal-transport-and-autonomy.md)) or a model that clears a ride would need a
   safety case, an operational design domain and an insurer, none of which a team of five can carry
   alongside the estate. The class exists so that the boundary is stated rather than assumed.
6. **Controls are audited, not asserted.** A quarterly check reads the registry and reports any
   production capability whose class controls are incomplete; the check is the same job that reports
   capabilities without a passing eval (OKR 5.3).
7. **AI incidents follow one path** regardless of class: contain (kill switch to the fallback,
   [ADR-0008](ADR-0008-ai-evaluation-and-production-monitoring.md) §7), notify the capability owner,
   preserve the trace and the bundle version, and record the outcome as a game-day candidate.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| No framework — each ADR carries its own controls | Already the state of things; no new artefact | Nothing says which controls a *new* capability needs; gaps are invisible until an audit or an incident | Does not scale past a handful of capabilities |
| One maximum control set for everything | Simplest rule; nothing under-protected | A caption drafter would need a cost-of-error row, a game day and delayed ground truth; on five engineers that means it never ships | Blocks the cheap capabilities |
| An external AI-management standard adopted whole | Recognised; audit-ready | Written for organisations with a compliance function; the process overhead alone exceeds this team's capacity | NFR-OPS-1 |
| Three classes with proportional controls (chosen) | The strictness follows the harm; a new capability's obligations are readable in one table | The class boundaries are judgements and will occasionally be argued | — |

## Consequences
**Positive:** a new capability's obligations are a table lookup; the low class makes small AI cheap
enough to try and to kill; the gap between "we have controls" and "this capability has its controls" is
now measurable.
**Negative:** three classes is a simplification, and some capabilities sit awkwardly between two — the
companion's safety answers behave like high while the rest of it is medium, which is resolved by
splitting the capability rather than the class; the quarterly audit is real work.

| Risk | Mitigation |
| --- | --- |
| A capability is classified low to avoid the controls | Class is part of the promotion review and visible in the registry; the audit reports class changes alongside gaps |
| The framework becomes paperwork nobody reads | Its only artefacts are a field in the registry and a quarterly report; everything else it references already exists |
| Condition monitoring is read as a safety certification (R24) | Decision 4, repeated in [ADR-0022](ADR-0022-ride-condition-monitoring.md) and on the ride screen itself |

## How we will know this was right
Every production capability has a complete control set for its class at each quarterly audit; a new
low-class capability reaches production inside a phase rather than a year; and no incident review finds
a control that was required by class and absent in fact.
