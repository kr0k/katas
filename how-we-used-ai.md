# How we used AI to build this

The kata's theme is AI-assisted software architecture, so how AI was used to produce the proposal is
part of the answer rather than a disclaimer at the bottom of a page. The team directed the work and
owns every decision in it; what follows is where the tools helped, where they were wrong, and what we
changed in our own process once we noticed.

## Where it helped

| Activity | What the tools did | What stayed with the team |
| --- | --- | --- |
| Research and synthesis | Surveyed patterns, radio and privacy constraints, and zoo-membership benchmarks against the brief | Which of them the estate actually has, and which to ignore |
| Drafting | First passes at ADR context, alternatives and consequences; first passes at prose | Every decision, every trade-off, every number that gates something |
| Diagrams | Mermaid source from a description — layout and shapes | Semantics: what is synchronous, what is a deployment boundary, what phase a component belongs to |
| Adversarial review | Independent review passes with different briefs — engineering, business, and a judge's lens — each producing a findings list | Which findings were real, which were depth for its own sake, and what to decline |

Roughly a third of the review findings were declined, and the declines are recorded with reasons in
the same place as the accepted ones. A review that is accepted wholesale has not been read.

## Where it was wrong, and how we caught it

These are the ones worth reporting, because each changed the process and not just a file.

**The numbers were right and a sentence about them was wrong.** A review pass recomputed the
generative-cost figures by hand. The arithmetic held, but a claim standing next to it did not: the
OPEX line was said to absorb the cost model's ±50% band, when what it absorbs is a 46% overrun
(€34,261 × 1.5 = €51,391 against a €50k line). Nothing tested the sentence, so it had gone unchallenged.
**The change:** load-bearing claims became invariants in `scripts/business_case.py` with assertions in
its self-test, so a price change now fails the build instead of leaving prose quietly false.

**A paragraph shipped twice.** Two documents carried the same passage, which is what happens when
long prose is generated and then moved around. **The change:** a lint check fails on any sentence of
twelve or more words that appears twice anywhere in the repository, added together with a negative
test proving it catches the case that got through.

**A diagram that rendered for us and not for a reader.** A semicolon inside a mermaid block is a
statement separator, so one sequence diagram was silently broken on GitHub while looking fine
locally. **The change:** `scripts/check_mermaid.py` renders every block in the repository with
mermaid's own parser in CI, so a diagram cannot be broken by a character again.

**A straw man dressed as an alternative.** [ADR-0006](adrs/ADR-0006-edge-vs-cloud-inference.md) had
rejected cloud inference on the grounds that video could not physically cross the backhaul. That is
false — sampled frames fit comfortably. The honest reasons are privacy, because masking would happen
after the frame leaves the estate, and continuity, because advisories would stop during an outage.
**The change:** an alternative is now written in its strongest form before it is rejected, and the
rejection has to survive that version.

**Two of the strongest artefacts here were nearly skipped.** The drafting assistant argued that a
formal architecture evaluation and a token-level cost model were unnecessary detail. The team
overruled both. They became [the ATAM-style evaluation](hld/architecture-evaluation.md) and the
generative-cost model, and they are now among the load-bearing documents. A tool optimising for a
finished-looking draft will under-invest in the parts that make a draft falsifiable.

## The lesson we generalised

**A claim that nothing tests will eventually become false.** It is not a risk specific to AI-assisted
writing, but generation makes it cheap to produce confident sentences faster than anyone can check
them. So the repository is arranged the other way round: derived numbers live in one generator and
every document quotes it, and `uv run scripts/lint_docs.py` checks links and anchors, ADR-index
symmetry, scenario-to-ADR symmetry, that every identifier referenced is defined somewhere, duplicated
prose, mermaid traps, and every generated figure against its source. GitHub Actions runs it on each
push. What cannot be checked mechanically — whether a trade-off was worth making — is what the ADRs
are for, and that is human work.

## Guardrails we held ourselves to

- **A human signs every decision.** Tools draft; the team decides and is accountable.
- **Facts and assumptions are separated.** The brief's own statements are listed as given, and
  everything else is an assumption with an owner and a stated consequence if it is wrong
  ([requirements/05](requirements/05-assumptions-and-constraints.md)).
- **No fabricated certainty.** Costs, OKR baselines and adoption rates are labelled estimates, and the
  ones the conclusions rest on are named as sensitivity points rather than buried.
- **The exclusions are written down too.** What was considered and rejected sits in each ADR's
  alternatives table, so a reader can check the reasoning instead of guessing whether we thought of it.
