# ADR-0015 — A metric layer over the lakehouse, and the estate twin as its projection

**Status:** accepted · **Date:** 2026-09-11
**Serves:** FR-2.2, FR-2.4, FR-2.8, FR-5.1, NFR-OBS-1
**Related:** ADR-0004, ADR-0008, ADR-0013, ADR-0014

## Context
Three consumers now want to ask the same questions of the same data, and they are not the same kind of
consumer. Dashboards want a number on a screen. Training pipelines want a feature with a definition
that will not move under them. `agent:management` wants to answer a question nobody wrote a dashboard
for — "which zone was quiet on Tuesday, and was it quiet last Tuesday too?".

The naive answer to the third is text-to-SQL over the curated tier. It fails in a specific and
expensive way: a model that has to invent a join also invents the number, and a wrong number in a
meeting with the Countess is worse than a refusal. Meanwhile the same definition — "occupancy",
"dwell", "spend per visitor-day" — already exists in three places: the dashboard query, the feature
pipeline and the daily-report read model. Three copies of a definition drift, and a drifting definition
is how two screens end up disagreeing about Tuesday.

## Decision
1. **Add a metric layer between the lakehouse and everything that asks it a question.** A metric is a
   named, versioned object: one formula, one grain, one owner, one set of allowed dimensions, and the
   events it is derived from. Dashboards, the daily report, the feature pipeline and the agents all
   resolve names against it. It is declared in Git and reconciled like everything else.
2. **The metric layer is the only surface agents may query.** `agent:management` resolves a question
   to a named metric with dimensions and a window, or it refuses and says which metric it looked for.
   There is no ad-hoc SQL path from a model to the data platform
   ([ADR-0013](ADR-0013-stakeholder-agents-on-typed-tools.md) §3).
3. **Every answer carries its definition.** A number returned to a human comes with the metric's
   formula, grain and window, so a figure quoted in a meeting can be traced to the same definition the
   dashboards use (FR-2.8).
4. **The estate twin is a set of gold projections, not a system.** "What is true about the estate right
   now" — occupancy per zone, ride and enclosure status, animals under treatment, the day's admissions
   and spend — is a family of read models over the same metric definitions, refreshed on the event
   backbone. It is the context an agent reads before it proposes anything
   ([ADR-0014](ADR-0014-two-tier-agent-memory-with-a-write-guard.md) §1). We deliberately do not build
   a simulation: nothing in the brief needs one, and a twin that predicts is a portfolio's worth of
   modelling on top of a team of five.
5. **Feature and metric stay one definition.** A feature served to training and a metric shown on a
   dashboard derive from the same declaration, so a model is not trained on one meaning of "dwell" and
   judged against another.
6. **Consent and lineage live here.** Each metric declares the subjects it touches and whether the
   data behind it may be used for training; `SubjectErased` is applied at this layer once rather than
   per consumer.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Text-to-SQL over the curated tier | No new layer; answers anything | Invents joins and therefore numbers; no owner for a definition; an erasure or consent rule has to be re-implemented per query | The failure mode is a confident wrong number |
| A BI tool's semantic model, and nothing else | Adopted rather than built; familiar | Serves dashboards only — the feature pipeline and the agents would keep their own copies of each definition | Definition drift returns |
| Definitions in each consumer, as today | Nothing to build | Three copies already; the fourth consumer makes it four | Drift is the problem being solved |
| A full digital twin with simulation | Impressive; enables what-if | Weeks of modelling for a question nobody asked; a second thing to keep true | Level of detail, NFR-OPS-1 |
| Metric layer with twin projections (chosen) | One definition per number; agents get a safe query surface; erasure applied once | A layer to build and keep in step with the events under it | — |

## Consequences
**Positive:** one owner per number; an agent that cannot invent a metric it does not have; the
daily report, the dashboards and the feature store stop being three implementations of the same idea.
**Negative:** a question whose metric does not exist is refused until someone declares it, which is a
deliberate friction and will be felt; the layer is on the path of every analytical read, so its
availability matters.

| Risk | Mitigation |
| --- | --- |
| The metric catalogue becomes a bottleneck | Adding a metric is a pull request with an owner, not a project; refusals are logged so the missing ones are visible and prioritised |
| A metric is redefined and history changes meaning | Metrics are versioned; a definition change is a new version, and answers state which version they used |
| The twin projections drift from the contexts | They are read models on the backbone, rebuilt by replay like every other (NFR-DR-2) |

## How we will know this was right
No two surfaces disagree about the same named number; `agent:management` refusals fall as the
catalogue fills rather than being answered wrongly; and an erasure request is satisfied by one change
at this layer rather than by a sweep through consumers (GD-11).
