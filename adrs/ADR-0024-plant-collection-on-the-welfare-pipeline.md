# ADR-0024 — The plant collection runs on the welfare pipeline

**Status:** accepted · **Date:** 2026-09-11
**Serves:** FR-3.1, FR-3.8, OKR 1.7, A20
**Related:** ADR-0006, ADR-0007, ADR-0021, ADR-0023

## Context
The brief names the carnivorous plant collection once, and it names it as the thing the Countess would
have to **sell** if the estate does not become profitable. That makes it the only asset in the brief
whose disposal is the stated alternative to this whole project, and it appears nowhere in the
architecture.

It is also, mechanically, an enclosure. A plant house has the same problem as a reptile house — climate
and water within a band, a feeding regime, and a condition that degrades slowly and visibly — and it
has one property no animal enclosure has: a Venus flytrap closing on a fly is a scheduled, repeatable,
photogenic event that visitors will stand and wait for.

## Decision
1. **The plant house is an enclosure in the welfare model.** Same IoT classes (climate, soil moisture,
   water quality, light), same telemetry path, same anomaly capability, same confidence bands and the
   same review queue with the curator in the vet's seat
   ([ADR-0007](ADR-0007-human-in-the-loop-confidence-bands.md)). No new domain, no new context, no new
   model class.
2. **Feeding events are detected on the existing camera pipeline.** A closing trap is an activity
   excursion on features the edge node already computes; the detector is the S1 extractor pointed at a
   different subject.
3. **A detected feeding becomes a scheduled demonstration.** The event publishes into Park Operations,
   which places it on the day's programme; the companion reads the programme like any other, and the
   content pipeline may take a candidate clip from it
   ([ADR-0021](ADR-0021-content-drafting-with-a-publish-gate.md)). This is the whole monetisation
   mechanism: the estate sells attention to something it already owns.
4. **Rules first, as everywhere** ([ADR-0023](ADR-0023-rules-first-model-second.md)): Phase 1 is
   climate and moisture thresholds, which is most of the care value; the feeding detector is Phase 3,
   behind its own golden set of labelled closures.
5. **This is a COULD, and it is sized like one.** It costs one enclosure's worth of sensors and one
   camera, it adds no component, and if the demonstration does not draw an audience the detector is
   switched off and the climate rules stay.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Leave the plants out of the architecture | Smallest scope; the brief mentions them only in passing | The one asset the brief says would be sold, unmonitored and unmonetised, while the platform watches the animals | The omission is conspicuous once noticed |
| A separate plant-care domain with its own model | Botanically more accurate; room for species-specific care | A second welfare stack for one house, on a team of five, for a COULD | Operability, level of detail |
| A visitor-facing plant-care advisor in the app | A second revenue idea; educational | A generative capability about plants that can be poisoned or killed by bad advice, with no expert to ground it in — the knowledge base has no plant tier | No grounding, no owner |
| Plants as an enclosure on the existing pipeline (chosen) | Marginal cost; reuses every control already built; turns a cost centre into a programme item | Plant care is genuinely not animal care, and the shared anomaly model will be mediocre at both until the curator's labels accumulate | — |

## Consequences
**Positive:** the asset named as the fallback becomes an attraction with a place on the programme; the
reuse is exact rather than approximate — one extra subject in an existing pipeline.
**Negative:** one anomaly capability serving two biologies is a compromise, and the plant side will be
the weaker one for at least a season; the demonstration depends on a detector that fires on a plant's
schedule, not the programme's, so the programme entry is "expected today", not a time.

| Risk | Mitigation |
| --- | --- |
| The shared model degrades animal welfare detection | Separate baselines and separate golden sets per subject class; the plant house is scored as its own enclosure and never pools with animals |
| A demonstration is staged by withholding feeding | The curator owns the feeding regime and the content queue has no input to it — the same rule as [ADR-0021](ADR-0021-content-drafting-with-a-publish-gate.md) §5 |
| The demonstration draws crowds into a space not sized for them | The plant house is a zone with a counter like any other; the cap and the companion's routing already handle a busy zone |

## How we will know this was right
Climate excursions in the plant house detected and closed within their band from Phase 1; a
demonstration on the programme that visitors attend; and the detector switched off without ceremony if
they do not.
