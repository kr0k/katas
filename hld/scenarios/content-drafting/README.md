# S6 · Content drafting

> The estate's growth needs new audiences, and the platform has always disclaimed them: "new audiences come from marketing, and the platform claims none of them." That is honest about attribution and useless as help. Meanwhile 110 cameras watch the most photogenic animals in the county all day.

**Moves:** OKR 1.7 (draft approval rate; earned reach as an estimate, never as attributed attendance)
**Process:** [P6 · the weekly content slot](../../../README.md#where-ai-sits-in-the-working-day)
**Phase:** 3 — after S1's vision is in production, because the highlight candidates are its features — see [roadmap](../../../README.md#delivery-roadmap-what-we-build-when-and-what-we-buy)
**ADRs:** [ADR-0006](../../../adrs/ADR-0006-edge-vs-cloud-inference.md) (features come from the edge, video never leaves), [ADR-0007](../../../adrs/ADR-0007-human-in-the-loop-confidence-bands.md) (a human publishes), [ADR-0008](../../../adrs/ADR-0008-ai-evaluation-and-production-monitoring.md) (evals and guardrails), [ADR-0009](../../../adrs/ADR-0009-visitor-privacy-anonymous-counting.md) (no visitor reaches a published frame)

## The problem, stated narrowly

R18 is the largest external dependency in the business case: the growth ladder needs roughly ×1.8 unique
households, and marketing brings them. One curator writes the estate's posts. The scarce thing is not
ideas but **noticing** — the piranha feeding that went unusually well, the cassowary chick's first day
out, the plant that caught something at 14:40 while nobody was watching the monitor.

So this scenario is deliberately the smallest useful thing: **the platform notices and drafts; a human
publishes.** It is the only place the platform touches the third growth lever, and it still claims none
of the outcome.

## Why AI, and where it stops

**Noticing** is the AI part, and it is not generative: S1's edge pipeline already produces activity
features per enclosure, so a highlight candidate is an outlier in a series we compute anyway — unusual
activity during a scheduled feeding, a first appearance after a birth, a detected plant feeding event
(FR-3.8). No new stream, no new camera, no new model class.

**Drafting** is generative and trivial: a caption in the estate's voice from a structured candidate
(animal, enclosure, event type, time, the curated fact about that species). One capability,
`draft-caption`, and a human edits or discards every one.

**Publishing is not automated at all.** Not as a safeguard we might relax later — there is no publish
path in the architecture. The draft lands in the curator's queue and leaves the system through the
curator's own hands.

## What the guardrails actually rest on

The reputational failure modes here are specific, and two of them are already closed by decisions taken
for other reasons:

| Failure | What prevents it |
| --- | --- |
| A visitor's face in a published clip | Masking happens **at the edge before any clip exists** ([ADR-0006](../../../adrs/ADR-0006-edge-vs-cloud-inference.md), [ADR-0009](../../../adrs/ADR-0009-visitor-privacy-anonymous-counting.md) §3), and `unmasked frames stored = 0` is a rollback-grade gate, not a threshold. A candidate is drawn from that same store, so there is no unmasked path to draw from. A pre-publish check re-verifies it, because a gate you rely on twice should be checked twice (GD-23) |
| A caption that says something untrue about a venomous animal | Species facts are inserted verbatim from the knowledge base, exactly as the companion's safety fields are ([ADR-0010](../../../adrs/ADR-0010-grounded-llm-with-guardrails.md) §2). The model writes around them and may not restate them |
| Distress published as entertainment | A candidate whose enclosure has an open welfare review or a treatment in progress is **suppressed at source** — the queue never sees it. The keeper's `EnclosureStatusChanged` is what gates it, not a model's opinion, which is the [probabilistic-events rule](../../README.md#rule-probabilistic-events-do-not-cross-into-visitor-facing-contexts) doing ordinary work |
| Tone drift into generic AI voice | Approval rate without edits is the metric, and it is the kill condition below |

## Containers

| Container | Responsibility | AI? |
| --- | --- | --- |
| Highlight candidate job | Batch over S1 activity features and scheduled events; suppresses candidates from enclosures under review; emits `HighlightCandidateFound` | Statistical, not generative |
| Draft queue (Guest Engagement) | Candidate + masked clip + curated fact → the curator's queue; edit, publish or discard, each captured with a reason | No |
| `draft-caption` capability | One caption per candidate in the estate's voice | Yes, small volume |

Nothing here is a new deployable: the job runs in the existing batch workers and the queue is a read
model in Guest Engagement.

## Validation & verification

| Check | Size | Gate |
| --- | --- | --- |
| Unmasked person regions in candidates offered to the queue | Every candidate | 0 — any occurrence is an incident, not a metric |
| Species facts inserted verbatim | 100 drafts | 100%; invented facts 0 |
| Suppression of enclosures under review or treatment | Fixture stream with an open review | 100% suppressed |
| Approval without edits | Rolling 50 drafts | ≥ 60% by the end of season 3, or the capability is cut |

**Kill condition:** approval rate below 60% after a full season means the drafts are not saving the
curator time, and the honest response is deletion rather than prompt tuning forever — it is on the
[kill-gate table](../../ai-platform/README.md#every-capability-has-a-review-date-and-a-cut-condition)
with the rest.

## What this does not claim

Earned reach is reported as an **estimate**, and no attendance is attributed to it. The business case
credits the platform with incremental visitor-days on quiet days only, from the S4 nudge cohort and the
S5 discount blocks ([08 §4](../../../appendix/business-case-model.md#4-does-the-platform-pay-back)); a
post that went well is not in that arithmetic and is not going to be. R18 stays an external dependency
with the Countess as its owner. What changes is that the marketing function now has an instrument, not
that the platform has a claim.

## Degradation ladder

1. **Cloud + AI:** candidates found and captioned.
2. **Cloud without AI:** candidates still found — the job is statistical — and the curator writes the
   caption, which is exactly today's process with a better prompt to work from.
3. **Estate-only:** nothing happens, and nothing needs to. This is the least critical capability in the
   proposal, which is also why it is the first thing cut if the generative budget tightens.
