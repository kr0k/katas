# ADR-0025 — Visitor feedback: themes with quotes, not a sentiment score

**Status:** accepted · **Date:** 2026-09-11
**Serves:** FR-4.4, NFR-PRV-1, OKR 1.4
**Related:** ADR-0009, ADR-0010, ADR-0015, ADR-0017

## Context
The estate knows that visitors rarely come back and does not know why. The counters say where people
went, the tills say what they bought, and neither says what annoyed them. Free-text feedback — from the
post-visit form, the companion's thumbs-down reason and the exit survey (A14) — is the only source that
does, and today it arrives as a few hundred sentences a month that nobody has time to read.

The standard answer is a sentiment score on a dashboard. It is also the wrong one: a number between
minus one and one aggregates away the only thing worth having. "Sentiment fell four points" cannot be
acted on. "Forty-one people said the queue for the piranha tank has no shade" can be acted on this
week, and it costs an awning.

## Decision
1. **The output is a ranked list of themes, each with its count, its trend and three verbatim quotes** —
   never a score. A theme without quotes is not shown, because the quote is what makes it actionable
   and what lets a human check the clustering.
2. **Themes are clustered, then named.** Clustering is classical and deterministic given its inputs;
   only the theme's label and summary are generative, and they are grounded in the cluster's own
   sentences ([ADR-0010](ADR-0010-grounded-llm-with-guardrails.md)). A theme's label changing between
   runs while its cluster does not is a bug, and the theme keeps its identity across runs so that the
   trend means something.
3. **Themes resolve to zones, rides and enclosures through the metric layer**
   ([ADR-0015](ADR-0015-metric-layer-and-estate-twin.md)), so "shade at the piranha queue" lands next
   to that queue's wait times rather than in a separate report.
4. **It joins the estate's existing reviews, not a new one.** The theme list appears in the weekly ops
   review and, when a theme crosses its threshold, in the daily report's recommendation slot — the
   surfaces that already exist.
5. **Free text is personal data until it is not.** Submissions are stripped of names, contacts and
   anything that identifies a member of staff before they reach the clustering job; a quote that cannot
   be shown without identifying its author is not shown. The submission is a subject under
   [ADR-0009](ADR-0009-visitor-privacy-anonymous-counting.md) §7 and is erased with it.
6. **Low risk class, and treated as such** ([ADR-0017](ADR-0017-ai-risk-classes-and-proportional-controls.md)):
   a wrong theme costs a human ten minutes of reading. Baseline controls only — eval gate, monitoring,
   an owner, and the fallback of reading the sentences by hand, which is today's process.
7. **No individual is scored, and no feedback is answered by a model.** A visitor who writes something
   that needs a reply gets a human; the platform routes it, and drafts nothing.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| A sentiment score per day or per zone | One number, trivially dashboarded, familiar to management | Aggregates away the cause; nobody can act on a four-point fall; invites chasing the metric | It is the version that looks like insight and is not |
| Manual reading, as today | Perfect fidelity; no model | Nobody has the hours, so it is not actually happening | Not the status quo — the status quo is that it goes unread |
| Per-visitor sentiment tied to the account | Enables targeted recovery offers | Scoring identified individuals on their mood is a surveillance surface the estate does not want and did not ask for | [ADR-0009](ADR-0009-visitor-privacy-anonymous-counting.md), R6 |
| Generative summary of all feedback, weekly | One paragraph, easy to read | A summary of complaints is a paraphrase of complaints; the specific, costed, fixable detail is exactly what a summary removes | Loses the actionable part |
| Clustered themes with verbatim quotes (chosen) | Actionable at the grain a repair is made at; the human can audit the clustering by reading the quotes | Clustering quality is uneven on small volumes; themes need a human to name well; low volume in winter | — |

## Consequences
**Positive:** the cheapest capability in the portfolio to build and the most likely to produce a fix
this month; the quotes make it self-auditing.
**Negative:** a few hundred sentences a month is thin for clustering, and early themes will be noisy;
it measures the visitors who write, who are not the average visitor, and the exit survey is the only
correction for that.

| Risk | Mitigation |
| --- | --- |
| Themes read as representative when they are not | Counts are always shown against the number of submissions and the number of visitors, never as a share of opinion |
| A quote identifies a visitor or a staff member | §5 — stripped before clustering, and a quote that cannot be anonymised is not shown |
| The theme list becomes a report nobody reads, like the sentiment score it replaced | §4 — it has no surface of its own; it appears inside reviews that already happen, or not at all |

## How we will know this was right
At least one costed change made per season that traces to a theme; themes stable across runs when the
underlying text is; and the capability switched off if a season passes without a change traceable to it.
