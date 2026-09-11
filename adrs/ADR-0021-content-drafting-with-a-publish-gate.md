# ADR-0021 — Content drafting: mine the highlights, gate the publish

**Status:** accepted · **Date:** 2026-09-11
**Serves:** FR-4.5, NFR-PRV-2, OKR 1.7, R6, R26
**Related:** ADR-0006, ADR-0009, ADR-0010, ADR-0016, ADR-0017

## Context
The estate's growth case needs new households, and the platform is explicitly credited with none of
them — marketing is an external dependency with its own budget line (R18). The one thing the platform
*can* contribute is raw material: the edge nodes already compute activity features on 110 camera
streams for the welfare scenario, which means the estate is already detecting, and discarding, the
moments people would actually want to see. A piranha feeding frenzy, a cassowary display, the
carnivorous plants closing on a fly.

Today the curator has no way to find those moments except by watching, which they do not have time for,
so the estate's social presence is whatever someone happened to photograph. The temptation is to close
the loop and let a model post. That is exactly what must not happen: the subject matter is venomous
animals and children, the brand is fragile, and an apology costs more than a month of posts is worth.

## Decision
1. **Highlight mining reuses the S1 feature pipeline** — no new model class and no new camera. A
   candidate is an activity-feature excursion on a stream already being processed, scored on the edge
   node against the same 1-minute windows S1 uses. Candidates arrive as clips on the existing clip
   traffic class.
2. **Captions are drafted, never published.** The draft lands in the curator's queue with the clip, the
   species facts it used and their source records. The publish action belongs to a human and there is
   **no automated publish path at all** — not for "low-risk formats", not on a schedule.
3. **Species and safety facts are inserted verbatim** from the knowledge base's approved fields, in the
   language of the post, exactly as the companion does it
   ([ADR-0010](ADR-0010-grounded-llm-with-guardrails.md) §2). The model composes around a fact; it
   never restates one.
4. **Nothing with a visitor in it leaves the estate.** The masking capability runs before a candidate
   clip exists ([ADR-0006](ADR-0006-edge-vs-cloud-inference.md)); a candidate whose masking confidence
   is below its gate is discarded rather than queued, and the curator's queue shows the masking version
   that produced each clip.
5. **Welfare outranks content, structurally.** A clip may only be produced from an enclosure not
   currently flagged for welfare review, and the keeper can mark any enclosure or animal as not for
   content — a flag the pipeline reads, not a policy someone remembers. The estate does not publish an
   animal in distress.
6. **This is a medium-risk capability with a 5:1 error ratio**
   ([ADR-0016](ADR-0016-cost-of-error-sets-the-bands.md) §3): a discarded draft is cheap, a post that
   has to be apologised for is not.
7. **It carries the earliest kill gate in the portfolio.** If the curator's unedited-acceptance rate is
   below 40% after one season, or the queue is not being read, the capability is switched off and the
   clip mining stays as a plain highlight reel. The gate is in the roadmap, not in a retrospective.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Fully automated posting | The only version that saves the curator's whole task; matches what the market does | One bad post about a venomous animal or a visible child undoes a season of goodwill; nothing left to validate before publication | Reputation, and V&V |
| Auto-publish "low-risk" formats only, human for the rest | Most of the volume, most of the saving | The classification of low-risk is itself a model decision, and it is the one that must not be wrong; the boundary is not defensible | Moves the risk rather than removing it |
| A separate camera and model for content | Best footage; no coupling to welfare | A second inference budget on the edge nodes, a second privacy surface, and a second thing to run — for a capability carrying a kill gate | Cost and operability |
| Buy a social-content service | Nothing to build | It has no access to the estate's cameras, which is the entire asset | It cannot do the one thing that matters |
| Mining on the welfare pipeline, human publish (chosen) | Near-zero marginal cost; the estate's actual footage; the reputational decision stays human | The curator remains the throughput limit; the saving is in finding, not in publishing | — |

## Consequences
**Positive:** the estate's most interesting moments stop being lost; the marginal cost is a caption
draft, because the expensive half of the pipeline already runs for welfare.
**Negative:** the curator is now a dependency for a revenue-adjacent process, and their queue is a
real workload in the [roles table](../hld/ai-platform/README.md#humans-in-the-loop-who-does-what); an
AI-drafted voice can flatten the estate's own; the whole capability is credited with no attributable
revenue, which is why it carries the kill gate.

| Risk | Mitigation |
| --- | --- |
| A visitor is recognisable in published footage (R6) | §4 — masking gated before candidacy, unmasked frames stored = 0 is already a rollback condition ([thresholds table](../hld/ai-platform/README.md#thresholds-and-cadences-source-of-truth)) |
| A caption states something false about a venomous species (R26) | §3 — facts verbatim from approved fields; the curator sees the source record next to the draft |
| Content pressure distorts animal handling — feeding staged for the camera | §5 plus the keeper's veto; feeding schedules remain a welfare decision, and the content queue has no input to them |
| The drafts read as generated | Brand-voice examples in the bundle and the unedited-acceptance rate as the gate metric — a falling rate is the signal, and it is the same number as the kill gate |

## How we will know this was right
Unedited acceptance above 40% by the end of the first season; zero published items with a visible
visitor or a wrong species fact; and a decision at the kill gate that is actually taken, in either
direction, rather than deferred.
