# Merge plan — borrowing from `architecturalkatas2026` into this submission

**Working document, not part of the submission.** Excluded from `scripts/lint_docs.py`.

Two BONK solutions were built independently for the same kata. This one (`katas`) is the base; the
other (`architecturalkatas2026`, referred to below as **AD**) is merged into it. The external
review — scorecard 120 vs 119, then a deep read — found near-parity with opposite bets, and that
the two "architectural religions" differ only in the deltas listed there. This plan takes AD's
deltas that are worth having, in our voice and under our numbers.

**The motto moves.** From *"AI is a layer on top of a sound system"* to **"AI is embedded in the
estate's business processes, not a layer over them."** The discipline does not move: quantified,
falsifiable, honest about payback, and cuttable when a number says no.

---

## 0 · What the new motto means, and what it must not mean

Embedding AI in a process means: a named role, a recurring decision, AI inside that decision loop,
a human who commits, and a deterministic path that runs when AI is off. It does **not** mean AI on
the critical path.

The two sentences that carry the whole merge, and must appear in the README:

> **AI sits inside the working day** — the keeper's morning round, the ops manager's opening plan,
> the visitor's afternoon, the Countess's 21:00 review — not beside it as an analytics product.
>
> **Embedded in the process is not embedded in the critical path.** Every process runs with the AI
> switched off: every read the copilot makes is also a dashboard, every draft it writes is also a
> form, and every alert it raises is also a rule.

Our existing invariant — *probabilistic events do not cross into visitor-facing contexts* — is what
makes the embedding safe rather than reckless, and gets promoted from a note in `hld/README.md` to a
named principle. Its new complement: **no agent is the only path to any action.**

## 1 · Budget for this merge (hard, checked at every wave gate)

Our wins are *suitability*, *appropriate level of detail* and *feasibility*. AD's risk is reading as
over-engineered. Merging without a ceiling converts our advantage into their weakness, so:

| Ceiling | Value | Where it is checked |
| --- | --- | --- |
| New ADRs | **≤ 2**, and after the ADR-0014 retraction (§6, item 3.2) the plan needs only **one**: ADR-0013 | `adrs/README.md` |
| New scenario folders | **≤ 1** | `hld/scenarios/` |
| New generative capabilities | **≤ 3** (2 agents + 1 read-only NL) | capability → runtime path table |
| Generative spend at 15,000/day | **≤ €45k/yr** (today €34.3k; €67.1k without caches) | `scripts/business_case.py`, `appendix/generative-cost.md` |
| Per-visitor TCO | unchanged: **≤ €0.50** at 15,000/day (NFR-COST-2) | `appendix/cost-model.md` |
| Estate-staff hours on AI | **≤ 30 h/wk** at Phase 3 (today ≈ 25) | humans-in-the-loop table, R13 |
| New deployables | **0** — agents run in the existing BFF/monolith | ADR-0004 §7, R9 |
| Payback story | unchanged: years 4–7, physical capacity binds first | `requirements/08`, `appendix/business-case-model.md` |
| Pass-credential CAPEX (wave 5) | **≤ €150k over 3 years**, and it adds **0 ADRs** — amendments only | `appendix/cost-model.md` |

If an item cannot fit, it is cut — in this order: content drafting (S6) → copilot proactive
suggestions → agent write-back → plant collection. Stated up front so the cut is a decision, not a
retreat.

## 2 · Wave 0 — reframe (no new scope, highest value per hour)

Pure editorial. Changes what a judge reads in the first 60 seconds; adds no cost, no risk, no ADR.

| # | Task | File | Detail |
| --- | --- | --- | --- |
| 0.1 | Replace the motto sentence | `README.md` § *Our approach* | The line *"AI is a layer on top of a sound event-driven, edge-first system, not the system itself"* is the one sentence that contradicts the new direction. Replace with the two sentences from §0. Keep the four-step order but rename step 3 from *"AI third, and only where a rule or a query would not do"* to **"AI inside the decision, where the process needs a judgement a rule cannot make"** — same filter, process framing |
| 0.2 | Add the process table | `README.md`, new § *Where AI sits in the working day* | Columns: **Process · Owner · Trigger · Where AI enters · Who commits · Deterministic path when AI is off · KR moved.** Six rows: P1 morning welfare round (keeper/vet, S1) · P2 opening & staffing plan (ops manager, S3) · P3 the visitor's day (visitor, S4) · P4 the 21:00 review and the weekly commercial call (Countess/management, daily report + S5) · P5 census and stock-take (keeper, S2) · P6 collection & exhibit condition (gardener/keeper, S1-extended, wave 3). This table *is* the new motto |
| 0.3 | Give every scenario a process line | `hld/scenarios/*/README.md` headers, `hld/README.md` | Each scenario header gains **Process:** `P<n> — <name>` next to the existing **Phase:** line. Scenario ids stay S1–S5 (lint checks 3 and 5 depend on them) |
| 0.4 | Promote the invariant | `hld/README.md` § *Bounded contexts*, `README.md` | Give the probabilistic-events rule its own heading so it is citable, and add *"no agent is the only path to any action"* and *"embedded ≠ critical path"* beside it |
| 0.5 | Reframe the AI portfolio by lever | `README.md` § *AI scenarios* table | Add a column **Revenue lever** — attendance / spend per visit / repeat / cost avoided. This is AD's `Profit = Attendance × Spend × Repeat` frame, taken as a *lens on our existing five*, without adopting its optimism. Welfare stays labelled cost-avoided-and-the-product-itself, as AD has it |

**Exit:** README and `hld/README.md` tell the process story; `uv run scripts/lint_docs.py` green; not one number changed.

## 3 · Wave 2 — sharpen the AI decisions (do before wave 1; no new scope)

Cheapest depth in the merge. Every item is a strengthening of a decision we already own, and three
of them close the exact rows where the review called the comparison a tie.

| # | Task | Files | Detail |
| --- | --- | --- | --- |
| 2.1 | **Cost-of-error matrix drives the bands** | `adrs/ADR-0007`, `hld/ai-platform/README.md` (thresholds table), `hld/architecture-evaluation.md` SP-2 | Today the bands read as convention. Add one table: capability · cost of a false negative · cost of a false positive · ratio · resulting band boundary · who pays the FP. Units must be **ours** — vet hours from the humans-in-the-loop table and euros from the cost model, never invented dollars. Draft ratios to be argued, not asserted: welfare anomaly ≈ 20:1 (a lost rare animal against 20 min of vet review), aggression near visitors → advisory-only because the FN cost is uncapped and no threshold is defensible, piranha count ≈ symmetric, companion safety facts → not a threshold at all (verbatim insertion, per ADR-0010 §2), pricing asymmetric at the floor. Rewrite SP-2 so the band is **derived** and the sensitive parameter is the FN:FP ratio, not the number 0.9 |
| 2.2 | **Typed AI output contract** | `adrs/ADR-0004` (event contracts), `adrs/ADR-0007` | Every AI output crossing a module boundary is a record `{value, confidence, evidence, capability, bundle_id}` — never a bare scalar. `evidence` is what the reviewer actually reads (bbox and clip window for vision, cited KB record for the companion, factor contribution for the forecast). This is what turns human-in-the-loop from blind approval into review, and it is the mechanical reason a keeper's `EnclosureStatusChanged` can be trusted downstream of a model's `WelfareAnomalyDetected` |
| 2.3 | **Rules → model as a declared switch** | `hld/ai-platform/README.md` (capability contract), phase table in `README.md` | A capability declares `implementation: rule \| model`, a **promotion trigger** (dataset size + metric threshold + shadow duration) and the rule it keeps as its permanent fallback. Makes our phase gates an architectural mechanism instead of a project plan, and answers AD's ADR-009 without adding an ADR |
| 2.4 | **Honesty fix: a provider swap is not free** | `adrs/ADR-0005`, `requirements/04` NFR-EVO-1, `hld/architecture-evaluation.md` utility tree | We claim *"≤ 1 day, zero business-service changes"*. AD is right that models are not drop-in: the bundle carries a **per-provider prompt variant**, the eval suite is re-run per provider, and calibration is re-fitted inside the bundle (we already say this for calibration — say it for prompts too). The ≤ 1 day figure stays but must be stated as *including* those, and a capability with provider-specific tool-calling re-runs the agent eval as well |
| 2.5 | **In-production trio + separate agent rollback** | `adrs/ADR-0008`, `hld/ai-platform/README.md` (AI monitoring) | Task success (LLM-judge on a sample + human labels), tool-error rate, and **human-override rate as the leading indicator** — trust drops before the business metric does. Tie it to what we already measure: OKR 3.5 vet override rate becomes an explicit *degradation* trigger, not only a false-positive proxy. And: an **agent rollback (prompt/tool/version) is separate from a model rollback**, because the model can be fine while the tool wiring is not |
| 2.6 | Calibration response, spelled out | `hld/ai-platform/README.md` (gated metrics) | We have ECE at 10 equal-mass bins and per-band checks — stronger than AD already. Add the two things it has that we do not: **max per-bin deviation ≤ 0.1**, and the documented response *until recalibrated, bands shift conservatively toward review* rather than the capability simply failing its gate |

**Exit:** the thresholds table's boundaries all trace to the cost-of-error matrix; NFR-EVO-1 and
OKR 5.2 carry the swap caveat; `business_case.py --check` and lint green.

## 4 · Wave 1 — the agentic layer (the motto's architectural carrier)

This is what buys back *innovative use of AI* and *AI ↔ architecture characteristics*, the two rows
the review gave to AD. AD's agent-safety work is the best thing in either repository; its scope is
the thing to cut.

### 4.1 What we take, and what we shrink

| AD has | We take | We change |
| --- | --- | --- |
| 4 stakeholder agents + a physical one | **2 agents + 1 read-only capability** | The vet's process is the review queue and the Countess's is the 21:00 report — those need a better queue and a question box, not agents of their own |
| Agent = LLM + typed least-privilege tools | taken as-is | Tools are calls into existing module APIs or commands on the backbone; no tool touches another context's store (ADR-0004 §9 contract tests extended) |
| HITL on every effectful action | taken as-is | Every commit lands in an approval surface we **already run** (review queue, roster approval, management price approval, vendor checkout) — no new approval UI |
| Idempotent tools via outbox + business key | taken as-is | We already have inbox/outbox and idempotency `(device_id, boot_id, seq)`; extend the business-key rule to tool calls |
| Trace with a span per tool call | taken as-is | Same OpenTelemetry path the gateway already writes; PII redaction on ingest, because traces carry prompts |
| Step limit + token budget per task | taken as-is | New sensitivity point; on exhaustion → degrade + escalate, never continue |
| Prompt-injection trust boundary + worked kill-chain | taken as-is | Retrieved content and visitor text are data, never instructions; tools only from the whitelist |
| Two-tier agent memory with write-back | **taken as a specification, deferred as a feature** | MVP writes back only human decisions (`ReviewDecided` etc.) — which we already do. Agent-generated derivatives are Phase 3, behind the write-guard (schema + ranges + provenance + dedup), with PSI on self-writes and provenance rollback. Documented now so the safety story is complete; not built until there is something to learn from |
| Lakehouse as shared memory | **not taken as framing** | Our four-tier data platform already holds it; the Knowledge Base stays the single citation source |

### 4.2 The agents

| Agent | Process | Read tools | Draft / effectful tools | Who commits |
| --- | --- | --- | --- | --- |
| **`ops-copilot`** | P1, P2, P4 — the keeper's round, the opening plan, the review queue | `metric(name, dims, window)` (metric layer only, never raw tables) · `evidence(anomaly_id)` · `sensor_health(device_id)` | `open_review(animal_id, reason)` (creates work, not action; rate-limited) · `draft_staffing_change(...)` → `StaffingPlanDrafted` · `draft_cap_change(...)` | Vet (review), ops manager (`StaffingPlanApproved`), management (`CapacityCapChanged`) |
| **`companion`** (S4, upgraded from grounded LLM to tool-using) | P3 — the visitor's day | `kb_answer` · `queue_now` · `ride_status` · `plan_visit` | `hold_slot(slot_id)` (FR-1.7 timed entry; command to the ticketing ACL, idempotent by business key) · `escalate_to_staff(session_id)` | The visitor, in the vendor's own checkout — the agent never completes a purchase |
| **`ask-the-estate`** (capability, not an agent) | P4 — the 21:00 report and follow-up questions | `metric(...)` only | none | — read-only by construction |

### 4.3 Invariants of the agentic layer

1. No agent is the only path to any action.
2. No agent tool sits on a tier-0 safety path; tier-0 stays deterministic and local.
3. Every effectful tool emits a **command**; the write happens in the owning context.
4. Retrieved content and visitor text are **data, never instructions**; tools come only from the whitelist.
5. Every tool call is a span in one trace with `bundle_id`, latency and cost; effectful calls are idempotent by business key.
6. Step and token budget per task; on exhaustion → degrade and escalate.
7. An agent may **draft**; a human commits anything that moves money, rosters, prices or an animal's care.
8. With the agents off, every process still runs — each read is a dashboard, each draft is a form.

### 4.4 Files and ids

| Artefact | Work |
| --- | --- |
| `adrs/ADR-0013-role-agents-on-typed-tools.md` | **New.** Context (the brief's own MCP agent example; the motto), decision (2 agents + read-only capability, typed least-privilege tools, HITL on effect, memory deferred), alternatives rejected (4 stakeholder agents — team of 5; direct DB access — unauditable; fully autonomous action — fails V&V; assistants only — loses the multi-step value the motto claims), consequences, validation |
| `hld/ai-platform/agents.md` | **New.** Tool tables, the eight invariants, trust boundary, two worked kill-chains (poisoned KB document → free upgrade; poisoned memory batch → silent drift, Phase 3), in-production eval, cost and step budgets, the deferral of write-back with its write-guard spec |
| `hld/ai-platform/README.md` | Agents in the component diagram; new rows in *capability → runtime path* (`agent:ops-copilot`, `agent:companion`, `ask-the-estate`); monitoring rows for the trio; thresholds-table rows per agent; humans-in-the-loop rows (copilot review, escalation triage) |
| `adrs/ADR-0004` §9 | Contract tests extended: a tool call is a command; no cross-context store access; agent output records carry the §2.2 contract |
| `adrs/ADR-0007`, `adrs/ADR-0008` | HITL for effectful tool actions; agent-level eval and rollback separate from model rollback |
| `requirements/03` | **FR-2.8** questions answered over defined metrics (read-only) · **FR-4.5** the companion may hold a timed-entry slot on the visitor's behalf |
| `requirements/04` | **NFR-AGT-1** every tool call audited with trace, args and outcome; step and token budget enforced per task; effectful calls idempotent |
| `requirements/07` | **R21** indirect prompt injection through an agent tool · **R22** memory poisoning and self-reinforcement (Phase 3, mitigation pre-specified) · **R23** runaway agent cost or step count |
| `hld/core/resilience-validation.md` | **GD-17** poisoned KB document instructs a free upgrade → quoted as data, tool refuses, logged as a tool-error · **GD-18** effectful tool call retried after a timeout → no double booking · **GD-19** provider fails mid-chain → typed "no AI available", process continues on the deterministic path · **GD-20** step/token budget exhausted → degrade and escalate, bill bounded |
| `hld/architecture-evaluation.md` | Utility-tree rows (a poisoned document reaches a tool; an agent silently degrades) · **SP-8** step/token budget per task → cost · **SP-9** share of tool calls that are effectful → auditability and review load · **TP-8** agency vs auditability · **TP-9** AI inside the process vs the process's availability when AI is off |
| `scripts/business_case.py`, `appendix/generative-cost.md` | **Mandatory.** New request classes: copilot task (tokens in/out × tasks per day × cache hit), companion tool-calling overhead over today's plan/re-plan classes, `ask-the-estate` question. Regenerate — the €34.3k / €67.1k pair is lint-checked, never hand-edited. Must land under the €45k ceiling or the copilot's proactive suggestions are cut |
| `requirements/06` | **OKR 5.4** agent task success and human-override rate, with a rollback trigger |

**Exit:** ADR-0013 accepted; `agents.md` written; four game days in the catalogue; generative cost
regenerated and inside €45k; humans-in-the-loop total ≤ 30 h/wk; lint, mermaid and
`business_case.py --check` green.

## 5 · Wave 4 — governance frame and the metric layer

| # | Task | Files | Detail |
| --- | --- | --- | --- |
| 4.1 | **Risk class → controls matrix** | `hld/ai-platform/README.md`, new § | AD's EU AI Act framing, stated as an assumption of applicability. Our capabilities mapped: **high** — anything on a welfare decision or near visitor safety; **medium** — pricing, staffing, effectful agent tools; **low** — drafts, read-only NL analytics. Controls proportional: guardrails, human approval, model card + rollout gate, fairness audit, AI labelling, audit-trail retention, incident plan. Compact — one table, not a chapter |
| 4.2 | **Fairness for pricing, and the line we can actually claim** | `hld/scenarios/dynamic-family-passes/README.md`, `adrs/ADR-0009` | Price by **day type and load, never by identity** — and note that for us this is not a policy but a structural fact: anonymous-by-construction counting means there is no profile to price against. Add a periodic fairness audit (discount reach by day type, complaint rate) to the thresholds table. This is the one place our privacy bet pays a *revenue-side* dividend, and AD cannot make the same claim |
| 4.3 | **Metric layer** | `hld/core/README.md#data-platform`, `hld/README.md`, `hld/ai-platform/agents.md` | A named tier beside Raw → Curated → Feature → Knowledge Base: **defined business metrics**, one owner and one formula each, consumed by the daily report, the dashboards, `ask-the-estate`, and the forecasting and pricing models. It removes a real inconsistency risk (report and dashboard computing "attendance" differently) and is the grounding that keeps NL questions off raw tables. Say plainly: *this is what other proposals call a digital twin; we do not add a component — it is a projection of data we already hold* |
| 4.4 | **AI incident runbook** | `appendix/ai-incident-runbook.md` (new) | Detect → fall back to the rule → notify the capability owner → post-mortem, with welfare-decision audit retention. We have rollback wired but no incident *process*; AD does. One page, in the appendix where non-architectural work belongs |
| 4.5 | Per-capability kill-gate | `hld/ai-platform/README.md` | AD's best business-side idea: every capability carries a review date and a **cut-if** condition (S6 approval rate < 60% after a season → delete; S2 census error not improving → back to manual). This is the honest answer to the review's charge that two of our five AI features deliver nothing for years |

**Exit:** risk-class matrix present; metric layer named in the data platform and used by
`ask-the-estate`; kill-gate column in the thresholds table.

## 6 · Wave 3 — coverage of the estate's assets (cut first if the numbers refuse)

The review gave AD *coverage / stakeholders*. Three real gaps, all closable without new components.

| # | Gap | Task | Detail |
| --- | --- | --- | --- |
| 3.1 | **The carnivorous plant collection** appears once in our repository — in G1, as the thing the Countess would have to sell | Extend S1 from *animal welfare* to *welfare and collection condition* | No new context, no new component, no new scenario folder: the plant house takes the IoT class we already specify (temperature, humidity, light, soil moisture) and the same anomaly capability, generalised `score-enclosure-activity` → `score-exhibit-condition`. A "prey caught" detection on an existing edge node publishes an ordinary fact → a feeding-show slot in the ops schedule → the companion announces it. New: **FR-3.8**, **OKR 3.6** (collection loss events), one row in the process table (P6), thresholds row, and a line in the S1 README. Turns an asset-to-be-sold into an exhibit the platform serves — G1's own framing |
| 3.2 | **Remote enclosures: the geometry gap, not the delivery mode** — AD's ADR-004 asks the right question and gives two answers that do not survive our numbers | `adrs/ADR-0002` (new section), `hld/core/edge-and-connectivity.md`, §7 exclusions | **Retracted: the data mule and the radio bridge are rejected, not adopted** — arithmetic in §7.1.2. What survives is AD's *question*: how is a far enclosure served at all? Our transport rule plus LoRaWAN plus cellular answers telemetry, but **PoE reaches 100 m and the estate is "large and sprawling"**, while our table says cameras are wired PoE on an isolated VLAN reachable only by the edge nodes. Some of the 55 enclosures are certainly beyond 100 m of a switch. So: a **rule that picks per enclosure** between fibre with a media converter (inside the €60k cabling line) and a **local mini edge node** — compute to the data, so only events cross — plus a check that €60k actually covers the resulting geometry, and a row in the capacity table. No new ADR, no new appendix |
| 3.3 | **Content and marketing** — R18 says new-audience growth depends on marketing and the platform claims none of it | **New scenario S6 — content drafting** (the one new scenario folder the budget allows), Phase 3 | Highlight candidates come from edge-CV features we already compute — no new streams, and our masking gate already guarantees no visitors in frame. One generative capability drafts a caption; **a human publishes**; nothing auto-posts. This is the only item that touches the growth lever we currently disclaim, and it is the one most at risk of reading as scope creep — so it ships with a kill-gate (§4.5), a single capability, draft-only. New: **FR-4.6**, **OKR 1.7** (draft approval rate; earned reach as an estimate, never as attributed attendance), **R24** brand safety, **GD-21** (a clip containing a visitor reaches the approval queue → pre-publish check rejects it), curator hours in the humans-in-the-loop table, and a generative-cost row |

**Exit:** each item's numbers regenerated and inside the wave-1 ceilings; R18's wording updated to
say the platform now drives a *draft* of the third lever while still claiming none of its outcome.

## 7 · What we deliberately do not take

This section belongs in the submission too (`README.md` § *What this architecture does not do* and
the relevant ADRs) — the review credited our explicit exclusions. The RFID question is split: the
arithmetic that rejects the wide version is in §7.1, and the narrow version the team **did** adopt —
a durable pass credential on card-on-file — is wave 5 in §7.2.

| From AD | Why not |
| --- | --- |
| **RFID as a counting layer, or as a source of personalisation** | Counting stays LiDAR/thermal — the cost case in §7.1 is structural, not a price argument. Personalisation on stored visit history stays out: we personalise on session context and declared preferences. The invariant that separates the rejected version from the adopted one: **readers only at gates and points of sale, never at zone boundaries** (NFR-PRV-3, §7.2) |
| Personalisation on a stored visitor profile | We personalise on session context and declared preferences. There is no profile history to personalise from, by design |
| **Data mule** (delay-tolerant pickup of buffers by a vehicle) | Rejected on our own numbers — §7.1.2. It solves a bandwidth-and-coverage problem; ours is a reliability problem that store-and-forward already solves |
| **Directional radio bridges (PtP/PtMP)** | Rejected with it: they buy throughput we do not need at 0.1 Mbps aggregate, and cost a site survey, periodic re-alignment, vegetation/weather/new-structure failure modes and a zone SPOF |
| Autonomous shuttle / driverless autonomy | Rejected: certification, liability with children and venomous animals, and the hardest V&V in either repository, for five engineers. With the data mule gone there is no residual reason to put a vehicle in the architecture at all |
| Predictive maintenance of the 40 rides | Stays out (A10, certified inspection, no tier-1 equivalent). Already an explicit exclusion — keep it, and strengthen the sentence rather than soften it |
| 13 quanta, database-per-quantum, CQRS split | Our own throughput figures kill it: ≈ 19 msg/s, ≈ 0.1 Mbps, ≈ 1 GB/day buy nothing from distribution except operability cost at five engineers. **Translation rule for the whole merge: every borrowed idea is restated against our four bounded contexts — no `Q<n>` vocabulary enters this repository** |
| Four stakeholder agents, agent-per-role | Reduced to two agents plus a read-only capability (§4.1) |
| Free-form agent memory in the MVP | Specification taken, feature deferred to Phase 3 behind the write-guard |
| Feedback sentiment as its own capability | Folded into the companion's thumbs-down triage and the quarterly exit survey we already specify |
| *"IT is ≈ 0.1% of revenue, so cost is not a constraint"* | Rejected. Our payback section stays: years 4–7, year 4 only under a stated attribution, physical capacity binds before the software. The review read this as the maturity signal, and it is not for sale |

### 7.1 · Why RFID is not the counting layer — the arithmetic

The team raised replacing LiDAR/thermal counters with RFID on the grounds that it is *simpler and
cheaper*. Checked against our own cost model, because that premise is testable. All prices carry the
appendix's ±50% band; the *direction* of the finding does not depend on them. **This arithmetic
applies only to the wide version** — daily issuance to every visitor. It does not apply to the
issue-once pass credential in §7.2, which is why that one was adopted.

| | Counters (current) | RFID |
| --- | --- | --- |
| Read points | 150 × €600 = **€90k, once** | UHF portal (reader + 2–4 antennas + install) ≈ €2k × 150 ≈ **€300k, once** |
| Per visitor | **zero** | disposable tag at €0.15 → **≈ €675k/yr** at 4.5M person-visits; or reusable → ≈ €135k/yr in losses **plus** issue-and-collect labour |
| Labour | zero | issue + collect ≈ 40 s per person × 15,000/day ≈ **167 h/day** ≈ €750k/yr at €15/h loaded |

**The finding is structural, not a price argument.** Counters are a one-off with no marginal cost per
visitor; RFID introduces a per-visitor cost line where there was none. A single €0.15 tag is 30% of
the NFR-COST-2 ceiling of €0.50 per visitor, against a platform that costs €0.31 per visitor today.
Either shape — consumable or labour — lands at €400–800k/yr, which is 8–16× the whole generative
budget and comparable to the five-engineer team.

**"Simpler" also runs backwards.** `ADR-0009` currently buys *no personal data in events by
construction*, with a CI check behind it: nothing to leak and nothing to erase. A `token_id` on every
zone read voids that check and moves crypto-shredding, DSAR and erasure across the immutable log,
feature store and golden sets from an opt-in edge case onto the main path — plus a new DPIA, plus R6
(surveillance perception) live with children on site, plus §4.2's fairness claim demoted from a
structural fact to a promise.

#### 7.1.1 · Why the adopted card does not become the counting layer either

Asked again once the credential was adopted: the cards exist anyway, so why not count with them? Because
**counting on RFID works only at ~100% carry rate, and 100% carry is the daily-issuance version priced
out above.** These are not two independent choices.

Pass share of admissions is ≈ 19–20% in Y1 and ≈ 41% by Y3 (OKR 1.3), and it is a **non-random**
share: S4's nudges deliberately shift pass holders onto weekdays, and repeat visitors walk different
routes from first-timers.

**The decisive technical objection is circular.** Park-wide carry rate is known exactly from gate
events (pass admissions against all admissions). But occupancy needs a **per-zone** carry rate, which
differs by zone precisely because of that bias — and estimating it requires an independent count of
everyone in the zone, which is the counter RFID was meant to replace. **De-biasing needs the thing
being replaced.**

| What the counting layer must deliver | Can RFID |
| --- | --- |
| Occupancy for the cap and timed entry (FR-1.7), reconciled hourly against gate totals | No — a cap decision cannot run on a sample with an unknown denominator |
| OKR 2.4, staff hours in zones with no visitors | **Fails in the dangerous direction**: a zone can read zero taps with 200 people in it |
| OKR 2.2, p90 queue time on the top-10 rides | **No path at all** — a queue is not a portal; a counter on the queue line measures the line |
| OKR 2.1, 100% of zones with live popularity data | Only by building portals on all 150 boundaries |
| Little's-law dwell | A biased sample gives a biased answer |

**Physics and civil works.** Our zone boundaries are open park paths, not doorways: a directional
in/out read needs a defined portal with antennas on both sides — physical gateways on 150 boundaries
in a heritage park, which collides with the constraint we already cite about mounting infrastructure
on protected buildings. Passive UHF at 865–868 MHz is absorbed by body water and depends on card
orientation; a card carried in a pocket against the body reads materially worse. And occupancy from
in/out is a **running integral**, so every missed read accumulates all day. LiDAR has the same
structural issue, which is why ADR-0009 §2 already resets at closing, reconciles hourly against gate
totals and flags divergence above 10%. The difference that matters: **LiDAR's error is a sensor error
that can be calibrated; RFID's is an unknown denominator with nothing to calibrate against.**

**Privacy gets worse, not better.** The card is defensible because readers sit only at gates and
tills — discrete, purposeful transactions the visitor chose to make. Zone-boundary readers turn it
into continuous passive location tracking of **identified households**: a different processing purpose
needing a different legal basis and a new DPIA section, producing exactly the per-visitor paths that
ADR-0009's "We cannot" table lists as unwanted, landing on the scope-creep risk that same ADR answers
with "default answer is no", and re-arming R6 with children on site. It would also invert
**NFR-PRV-3**, the invariant that justifies the credential programme in the first place.

**And it costs more for less.** Using only cards we already issue, the marginal cost is readers:
≈ 150 portals × ≈ €2k ≈ **€300k** against the **€90k** of counters they would replace — 3.3× the price,
no queue measurement, and a biased occupancy estimate. Reading only major junctions instead loses
OKR 2.1 and still needs counters on the queues, so the estate operates **two counting systems**
instead of one, on five engineers (R9).

**What is available for free instead:** cohort analytics from the gate and till taps we collect anyway
— visit frequency and the weekday/weekend split per household (S4 nudge effectiveness, OKR 1.5),
spend by outlet where outlets sit physically in zones, re-entry patterns. Already covered by task 5.5
and OKR 1.4. And if path-level data is ever genuinely needed, the sanctioned route already exists:
ADR-0009 §5 permits the companion's itinerary-adherence metric to use *the visitor's own device
location with consent*, so a consented panel gives paths legally and without the bias, because the
panel can be randomised.

#### 7.1.2 · Why the data mule and the radio bridge are rejected

AD's author rates the data mule highly, so it went into an earlier draft of this plan as ADR-0014.
Checked against our own capacity table, it does not survive — and the reason is one sentence already
in `hld/core/edge-and-connectivity.md`: **the system is not bandwidth- or throughput-bound but
connectivity-reliability-bound, which store-and-forward solves.** A mule solves bandwidth and
coverage. Our constraint is reliability, and a 72-hour buffer already answers it.

| | Figure | Source |
| --- | --- | --- |
| What a mule would carry | clips at 100 events/day × 1.4 MB = **140 MB/day for the whole estate**; telemetry is 0.2 KB at 1–2 msg/min and goes by LoRaWAN | capacity check |
| Whole backhaul | **≈ 1.0 GB/day ≈ 0.1 Mbps**, which the same table calls "fits cellular with margin" | capacity check |
| What it would save | AD's own ≈ $1,320 per enclosure over 3 years ≈ €400/yr → **≈ €4k/yr for ten remote enclosures**, against an OPEX of €810k–1.33M: **0.3–0.5%** | AD ADR-004, `appendix/cost-model.md` |
| What it would cost | a delivery mode to operate, monitor and test · route dependency · a new failure mode (missed round) · its own game day · an idempotent bulk-upload path — on five engineers | — |

**The saving is smaller than the error bars on the number it saves from** (the cost model carries ±50%).

**And it fails the test we used to reject microservices.** The styles matrix rejects event-driven
microservices *on operability alone*, because distribution "buys nothing except operability cost for a
team of five". A data mule for €4k/yr fails that test identically — adopting it would contradict the
strongest piece of reasoning in the submission, in a document a judge reads two pages earlier.

**Why AD rates it highly: its design creates the payload.** Their storage sizing carries raw 360° video
at 1–1.5 TB/yr, which genuinely has to be moved somehow. **We designed that payload out** — edge
inference, features aggregated into 1-minute windows, raw video never stored centrally, and the
counterfactual row showing that without aggregation every column is an order of magnitude worse. The
principle behind it: **compute goes to the data, so the data never needs a ride.** A mule is the
opposite bet, and only one of the two can be taken.

**The radio bridge falls with it.** It buys throughput we do not need at 0.1 Mbps aggregate, for
€1–3k plus a site survey, periodic re-alignment, failure modes from vegetation growth, weather and new
structures in the beam, and a single bridge as a zone SPOF — against cellular at ≈ €33/month. The one
case it would win is carrying **camera streams** (the 220 Mbps class) from a remote cluster to central
compute, and our answer there is a local edge node instead. Compute to the data again.

**What the discussion did surface** is a real gap, and it is geometric rather than architectural: **PoE
reaches 100 m** while the estate is "large and sprawling", yet our table specifies cameras as wired PoE
on a VLAN reachable only by the edge nodes. Some of the 55 enclosures are beyond 100 m of a switch.
That is item 3.2 in §6.

**The counting layer and the credential layer are two questions, not one** — the cost case above is
what separates them. The credential version keeps every upside worth having (spend attribution, an
offline credential that does not depend on a phone battery, a family link for lost-child) while
issuing once to a population that is **already identified by its own opt-in**, and the growth model
puts that population at ≈ 41% of visits. That is §7.2.

### 7.2 · Wave 5 — the pass credential we did adopt (card-on-file)

**Decided 2026-09-09.** A durable NFC card, issued **once** to a pass-holding household, which
becomes the visitor's property: entry, ride entitlements, and cashless payment on the estate. The
money model is **card-on-file** — the card carries an identifier, the payment method lives with the
PSP. No balance on the card.

| # | Task | Files | Detail |
| --- | --- | --- | --- |
| 5.1 | **Credential medium and money model** | `adrs/ADR-0011` (new section) | The card is another **medium for the signed credential ADR-0011 already specifies** — it says "QR/NFC payload" today, so offline signature verification, the revocation list and the local used-ledger are unchanged. Money model recorded with its alternatives rejected: **stored value** (secure element at ≈ 4× the card price, SAM key management in every terminal, PSD2 limited-network notification once payment volume passes €1M/12 months — our ≈ €400k/month of on-site spend passes it many times over, plus unspent-balance liability on an estate the brief calls loss-making) and a **hybrid prepaid F&B wallet** (the complexity of both models for one scenario) |
| 5.2 | **Ride entitlements offline** | `adrs/ADR-0011` | Reuses the family-pass group-counter pattern **verbatim**: the local ledger decrements against the last downlink snapshot, gates share the counter through the broker, and over-spend during an outage is bounded and lands in the exceptions report. No new mechanism, no new failure mode |
| 5.3 | **Cashless offline behaviour** | `adrs/ADR-0011`, `adrs/ADR-0012` | A tap authorises against the card-on-file. Offline: a floor limit captured on reconnect; above it, degrade to "pay with your own card". The estate never holds a balance, so an outage costs a declined capture at worst, not customer money |
| 5.4 | **Vendor criteria: 13 → 16** | `adrs/ADR-0012`, `TODOS.md` | Closed-loop cashless bound to the pass credential · tap on the vendor's POS emitting `PurchaseRecorded` with the pseudonymous subject and the FR-2.6 fields · card revocation over the same critical-class downlink path as ticket revocation, ≤ 60 s. **If no vendor offers the combination, we do not build it** — the same rule as everything else in ADR-0012 — and it joins the fallback matrix in the P1 vendor-evaluation TODO |
| 5.5 | **Privacy: reword, do not reverse** | `adrs/ADR-0009` §2 and §7, `requirements/04` | §7 already states that `PurchaseRecorded` carries a subject where the family "paid with the app **or the pass**" — the card makes that the normal path instead of the exception, so this is an instantiation of a clause already written, not a reversal. Reword §2's *"no re-identification anywhere"* to **no re-identification of anonymous visitors; pass holders are identified by their own opt-in, at gates and tills only.** New **NFR-PRV-3**: readers exist only at gates and points of sale, there are no zone-boundary readers, and counting stays anonymous for every visitor — with an architecture test behind it, because ADR-0009 already names scope creep toward identification as its own risk |
| 5.6 | **Keep the fairness claim enforceable** | `hld/scenarios/dynamic-family-passes/README.md`, data-platform section | The card gives the pass segment an identity, so §4.2's *structural, not promised* is demoted to a promise unless we mechanise it: a **feature-store allowlist plus a property test that no subject-level feature enters the pricing bundle**. That turns the claim back into a CI gate, which is the only form of it worth making |
| 5.7 | **Cost** | `appendix/cost-model.md`, `scripts/business_case.py` | CAPEX line for the card programme at ≈ €0.55 per plain NFC card (±50%): **≈ €80k** per pass-holding household (≈ 145k at Y3, from the funnel's 207k repeaters × 70% pass conversion) or **≈ €280k** per person on the pass (×3.5 party size, ≈ 500k cards). ADR-0011's *members may enter separately* implies a card per person; MVP may issue one per household and leave QR for the other members. Record both numbers and make the call explicit. Re-check per-visitor TCO: headroom today is ≈ €0.19 per visitor ≈ €855k/yr at 15,000/day, so either shape fits under NFR-COST-2. **No kiosk in MVP** — issuance rides on an interaction that already exists (pass purchase at the desk or online, collected on first visit); a hopper kiosk that binds a pre-personalised card on tap is a later phase, and is much simpler than one that writes credentials |
| 5.8 | **Ride credits change the revenue model** | `requirements/05`, `scripts/business_case.py` | Our model prices admission plus on-site spend; pay-per-ride and premium experiences are not in it. Credits presuppose that change, so it lands as a **new assumption with the Countess as owner** and a new revenue line — not a silent feature. The upside is real, because spend per visit is the capital-efficient lever when attendance is capacity-bound, but it must be stated as an assumption like every other |
| 5.9 | **Verification** | `hld/core/resilience-validation.md`, `requirements/07` | **GD-22** uplink down at a food till → floor limit honoured, capture on reconnect, above-limit taps degrade cleanly · **GD-23** card reported lost → revoked ≤ 60 s over the critical-class downlink, entitlements frozen, replacement issued without losing the pass. **R25** lost or stolen card used at a till · **R26** scope creep toward zone readers |

**What this gains, stated precisely.** Purchase attribution coverage — a subject on `PurchaseRecorded`
becomes the norm rather than the exception, which is OKR 1.4's second line and a real answer to
**R20**, the row the review named as our weakest. Plus lower spend friction, offline entry without a
phone, and a family link for lost-child.

**What it does not gain, so the merge does not claim it twice:** repeat-rate measurement. OKR 1.2 is
*already* measured per credential and account from the ticketing export and `GateEntered`. Pass
holders are already counted; the card adds nothing there.

**Exit:** ADR-0011 carries the medium and the money model with alternatives; ADR-0012 is at 16
criteria with the fallback matrix updated; ADR-0009's wording is precise and NFR-PRV-3 has a test;
the pricing feature allowlist has a property test; the card line is in the cost model and per-visitor
TCO is re-checked; GD-22/23 and R25/R26 are in; the ride-credit revenue assumption has the Countess
as owner.

## 8 · Consistency ledger — the gate every borrowed item passes

An item that fails any row does not land. This is the mechanism that keeps *strictly to details*
while the motto moves.

1. **Process, owner, decision.** It names a recurring decision and the role that owns it — otherwise it is a feature, not embedding.
2. **A number it moves.** An OKR key result with current and target, or it does not ship.
3. **Deterministic fallback**, and it must be a path we already run — not one invented for the fallback column.
4. **Cost regenerated, not asserted.** Rows added to `scripts/business_case.py`; `appendix/generative-cost.md` and `appendix/cost-model.md` regenerated; generative ≤ €45k/yr, per-visitor TCO ≤ €0.50 (NFR-COST-2), AI share of revenue ≤ 2% (NFR-COST-1).
5. **Human hours.** Rows in the humans-in-the-loop table; if the total crosses 30 h/wk the phase slips instead (R13).
6. **No new deployable** unless the runtime genuinely differs (GPU, edge, ingestion) — five engineers, R9.
7. **Phase and entry gate**, and no model before the data it needs exists (A6, R7).
8. **Verification**: a row in the thresholds table **and** at least one game day.
9. **Traceability**: a README traceability row; the scenario's **ADRs:** line equals its README row (lint check 3); every new id defined where its kind is defined (lint check 5).
10. **Written in our own words.** Lint check 6 fails any 12-word sentence that appears twice in the corpus, and pasted AD prose would both trip it and read as two voices. Ideas are borrowed; sentences are not.
11. **Green**: `uv run scripts/lint_docs.py`, `uv run scripts/check_mermaid.py`, `uv run scripts/business_case.py --check`, and the GitHub Actions run.

## 9 · Ids to allocate

| Kind | Allocated | For |
| --- | --- | --- |
| ADR | **ADR-0013** only | role agents on typed tools. ADR-0014 was retracted (§6 item 3.2); remote-enclosure geometry becomes a section in ADR-0002 |
| FR | **FR-1.8**, **FR-1.9**, **FR-2.8**, **FR-3.8**, **FR-4.5**, **FR-4.6** | durable pass credential (entry + entitlement decrement); cashless tap via card-on-file; questions over defined metrics; exhibit condition; companion holds a slot; content drafts |
| NFR | **NFR-AGT-1**, **NFR-PRV-3** | agent audit trail, step and token budget, idempotent effectful calls; readers only at gates and tills, no zone-boundary readers |
| Risk | **R21**–**R26** | prompt injection via tools; memory poisoning (Phase 3); runaway agent cost; brand safety of published drafts; lost or stolen card used at a till; scope creep toward zone readers |
| Game day | **GD-17**–**GD-23** | poisoned KB · tool retry · provider fails mid-chain · budget exhausted · visitor in a clip · till offline at the floor limit · lost card revoked |
| Sensitivity | **SP-8**, **SP-9** | step/token budget → cost; effectful-tool share → auditability and review load |
| Trade-off | **TP-8**, **TP-9** | agency vs auditability; AI in the process vs the process's availability without it |
| OKR | **1.7**, **3.6**, **5.4** | draft approval rate; collection loss events; agent task success and override rate |

Existing ceilings for reference: FR up to 5.3, NFR 25 defined, A1–A15, R1–R20, GD-1–GD-16,
SP-1–SP-7, TP-1–TP-7, ADR-0001–ADR-0012.

## 10 · Order, effort, and the commit shape

| Wave | Effort | Rationale for the order |
| --- | --- | --- |
| **0 · Reframe** | ~0.5 day | Zero risk, zero cost, changes the first 60 seconds of the read. Nothing else makes sense before the motto is stated |
| **2 · Sharpen** | ~2 days | No new scope; closes the two rows the review scored as ties. Cheapest depth in the plan |
| **1 · Agents** | ~3–4 days | The largest item and the motto's carrier. Needs wave 2's output contract and cost-of-error matrix in place first |
| **4 · Governance & metric layer** | ~1.5 days | The metric layer is a dependency of `ask-the-estate`, so it cannot come last |
| **3 · Coverage** | ~2–3 days | Most cuttable, so it goes last and absorbs whatever budget remains |
| **5 · Pass credential** | ~1.5 days | Independent of the agent work — it touches ADR-0009/0011/0012, the cost model and one revenue assumption, so it can run any time after wave 0. Do it before the vendor evaluation goes out, since it adds three must-have criteria |

One commit per wave, each regenerating the derived numbers in the same commit so the lint gate never
goes red between them. The wave-1 commit is the one to review hardest: it is where an agentic layer
could quietly turn a defensible submission into an over-scoped one.


---

## 11 · Landed already (2026-09-09)

Implemented directly, outside the wave sequence, because none of it needed the agent work first. All
gates green: `lint_docs.py`, `check_mermaid.py`, `business_case.py --check`.

**Rejections written into the ADRs' own *Alternatives considered* tables**, so the reasoning lives in
the submission rather than in this plan:

| Rejected option | Where it now sits |
| --- | --- |
| Delay-tolerant pickup by a vehicle (data mule) | `ADR-0002` — with the €4k/yr against €810k–1.33M arithmetic and the operability test from the styles matrix |
| Directional radio bridges (PtP/PtMP) | `ADR-0002` — buys throughput we do not need at 0.1 Mbps |
| Vehicle-mounted mesh / autonomous shuttle as carrier | `ADR-0002` — safety and V&V, and no remaining data reason |
| RFID/NFC token portals as the counting layer | `ADR-0009` — per-visitor cost, biased 20–41% sample, circular calibration, no queue instrument |
| Drones as the sensing platform | `ADR-0006` — welfare sign-off per enclosure, flight permissions, intermittent coverage |
| Offline sales by deferring payment | `ADR-0011` — replaced by a bounded stock of **pre-signed day-ticket credentials**: the money is taken at the gate, only the issuing is deferred |

**Findings taken from AD:**

| # | Item | Where |
| --- | --- | --- |
| A | **`how-we-used-ai.md`** — the kata's own theme, answered with our evidence: five places AI was wrong (a claim nothing pinned, prose shipped twice, a mermaid semicolon, a straw-man alternative, two near-skipped artefacts) and the check added after each | new file, linked from the README's reading table |
| B | **Review-queue health as a separate signal** — override rate says the model is wrong, overdue confirmations say the people are saturated; load shedding by raising the band, with a weekly shed-item sample, and the phase gate slipping when shedding costs recall | `hld/ai-platform/README.md` + a thresholds row |
| C | **Two operational principles** — "a model failure is never a page, only the safety tier wakes anybody"; cold restore is a runbook ops staff can run without a shell, and GD-13 is run by whoever is on site | `hld/ai-platform/README.md`, `hld/core/README.md` |
| D | **"The number to challenge first"** — thirteen must-have criteria from one vendor, six of which may not exist together | new README section |
| E | **Dominant characteristic per bounded context** — why there are four contexts rather than one module or fourteen services | `hld/README.md` |
| F | **The client decision** — an installable web app, with native/hybrid/no-client rejected; nudges by e-mail as the guaranteed channel and push as the opportunistic one | `hld/scenarios/guest-companion/README.md` + a build-vs-adopt row |
| G | **Selling while the estate's uplink is down** — payment rides the terminal's own path; issuing uses a pre-signed credential stock | `ADR-0011` edge cases |

**Also landed:** ADR-0002 gains *reach is a separate question from coverage* — PoE stops at 100 m, so
an enclosure beyond it takes fibre by default or a local inference node by exception, with the count
an output of the site survey and the edge compute budget re-sized before purchase if it exceeds two.

**Not taken, on purpose:** a personas document (the wave-0 process table covers it), AD's growing-team
table (contradicts the fixed five), and AD's lower human-in-the-loop hours (ours are higher and more
honest — R13 rests on them). Still open from the same review: a glossary and SVG exports of the
diagrams, both cosmetic.


---

## 12 · Execution log (branch `ai-embedded-merge`)

All six waves implemented. Every commit left `lint_docs.py`, `check_mermaid.py` and
`business_case.py --self-test` green.

| Commit | Wave | What landed |
| --- | --- | --- |
| `68f49c6` | §11 | Rejections into each ADR's *Alternatives considered*; `how-we-used-ai.md`; review-queue health; the number to challenge first; characteristics per context; the client decision |
| `81bdf45` | 0 | Motto replaced; the five-process table with an owner, who commits and a with-AI-off column; process line on every scenario; revenue-lever column; the probabilistic-events rule promoted to a named heading |
| `c8a600a` | 2 | Cost-of-error table drives the bands; typed output record `{value, confidence, evidence, capability, bundle_id}`; the capability contract (rule-or-model, promotion trigger, must-beat, fallback); provider-swap honesty; override rate's two meanings; calibration response |
| `6c84fce` | 1 | ADR-0013 + `agents.md`; two agents and one read-only capability; eight invariants; injection and memory-poisoning chains; GD-17–GD-20; SP-8/9, TP-8/9; agent request classes in the cost model |
| `e7c115d` | 4 | Metric layer; risk classes with proportional controls; kill gate per capability; pricing fairness as an allowlist plus a property test; AI incident runbook |
| `a5dda57` | 5 | Durable pass credential, card-on-file; entitlements on the group-counter mechanism; ADR-0009 reworded precisely + NFR-PRV-3; three vendor criteria; GD-21/22; A16 |
| `64e111e` | 3 | Plant collection inside S1; reach-versus-coverage geometry; S6 content drafting with its kill gate; GD-23 |

### Where execution departed from the plan

- **ADR-0014 was never written.** The data mule and the radio bridge were retracted mid-planning (§7.1.2)
  after the user challenged the mule's value, so new ADRs went from two to **one**. Remote-enclosure
  geometry became a section in ADR-0002 plus a *Reach* section in edge & connectivity — a better outcome,
  because the rejection is now a quantified exclusion rather than an adopted channel.
- **The plant collection did not get its own scenario.** It extends S1, which keeps the scenario count at
  six with S6 rather than seven, and lets the collection inherit one governance track instead of starting
  a second.
- **Game-day numbering is sequential by implementation order,** not by wave: GD-17–20 agents, GD-21/22
  credential, GD-23 content. The catalogue is twenty-three.
- **The cost model caught a stale claim, as designed.** Adding the agent request classes moved the
  generative total and broke the pinned 46% headroom assertion — the invariant added after a reviewer once
  found a claim nothing tested. Figures were regenerated across five documents: €34,600 planned, €68,000
  without the caches, 44% absorbed.

### Budget at the end (§1)

| Ceiling | Planned | Actual |
| --- | --- | --- |
| New ADRs | ≤ 2 | **1** (ADR-0013) |
| New scenarios | ≤ 1 | **1** (S6) |
| New generative capabilities | ≤ 3 | **4** — the three agent classes plus `draft-caption`, which was wave 3 rather than wave 1 |
| Generative spend | ≤ €45k/yr | **€34,630** |
| Per-visitor TCO | ≤ €0.50 | **€0.31**, card programme conditional and excluded |
| Staff hours on AI | ≤ 30 h/wk | **≈ 27 h/wk** at Phase 3 |
| New deployables | 0 | **0** |
| Payback story | untouched | untouched — years 4–7 |

### Still open

Cosmetic only, from the tier-3 list: a glossary, and SVG exports of the diagrams for use in the
semi-final video and outside GitHub (`check_mermaid.py` already runs mermaid-cli, so the exports are
nearly free).


---

## 13 · Three capabilities added after the waves (2026-09-09)

Chosen from a longer candidate list because each passes the §8 ledger and none needs a new ADR.

| Capability | Home | Why it earned a place | Cost |
| --- | --- | --- | --- |
| **Staff protocol answers** (FR-3.9) | S1, as a copilot tool; the mechanism is [ADR-0010](adrs/ADR-0010-grounded-llm-with-guardrails.md) §7 | The copilot we had just built knew metrics, evidence and sensor health but **not the estate's own procedures** — which is what a keeper actually asks at 07:00. The protocol documents exist already for regulatory reasons | ≈ €2/yr; ≈ 1 h/month of approval by the vet and head keeper |
| **Causal ROI of investments** (FR-2.9, FR-2.10) | **New scenario S7** | FR-2.4 had promised to correlate investments with popularity and **nothing sat underneath it**. It answers the brief's own "difficult to know where to invest" with a method. The prerequisite turned out to be a *register*, not a model — Phase 0, and it costs a form | No generative cost at all; a quarterly readout |
| **Feed consumption forecast** (FR-3.10) | S1 | The feed scales were installed for FR-3.3 and produce a consumption series for free. Ordering starts from a forecast rather than last month's average | No generative cost; the keeper already approves orders |

**Departures from the discipline, stated rather than hidden.** S7 is a **seventh** scenario, one past the
budget in §1, and it is the second overrun after `draft-caption`. Both were accepted deliberately: S7
carries a kill gate, has no generative cost, and closes an FR that had been making a promise the
architecture could not keep. The scenario count is now seven against ad_kata's fifteen, and every one of
the seven still names an OKR, a fallback and a cut condition — which is the distinction that matters, not
the number.

**The most interesting property of S7:** its most common correct output is *"we cannot attribute this"* —
because a small estate makes a few large investments at once, which is exactly the condition under which
causal inference cannot work. The scenario's real contribution is therefore the advice to **stagger
investments so they can be measured**, which costs nothing to act on and needs no software.

Generative spend after all three: **€34,632/yr**, headroom 44%. The quoted figures did not move.

### Candidates considered and not taken

Refinements of existing scenarios (queue-level forecast horizon, review-queue triage by severity, feeding
schedule optimisation, return propensity, machine translation of narrative content, audio descriptions for
accessibility) and one unquantifiable (energy and climate optimisation — no data, no cost line). Explicitly
rejected: camera-based lost-child search, which is the surveillance [ADR-0009](adrs/ADR-0009-visitor-privacy-anonymous-counting.md)
exists to refuse, and species identification from visitor photographs, which brings uncontrolled frames
into a system whose masking guarantee lives at the edge.
