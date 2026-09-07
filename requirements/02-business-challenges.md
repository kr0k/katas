# 02 · Business Challenges & Pain Points

## Challenges (as stated by the Countess)

1. No real idea which parts of the estate are popular → hard to know where to invest and deploy staff.
2. Looking after the animals is costly, even more so when they get sick → want healthy and happy animals.
3. Want more returning visitors, but don't know how.

## Pain points (our decomposition)

We rewrote each challenge as observable pain, because that is what an architecture can actually target.

### Operations & visitor experience
- **Blind staffing.** Staff are allocated by habit; queues form at some rides while others sit empty. Nobody can say *when* a zone is busy, only that it "feels busy".
- **No feedback loop on investment.** Money spent on a ride or enclosure cannot be linked to a change in visitor behaviour.
- **Patchy Wi-Fi** breaks anything that assumes a live connection — including the visitor's phone.
- **Family logistics are hard.** Families with small children need help planning a day around nap times, food and the rides they can actually go on; today they wander and leave early.

### Animal welfare
- **Problems are noticed late.** A keeper spots reduced appetite or lethargy after it has become obvious; by then treatment is expensive.
- **Feeding is unmeasured.** How much each animal eats — and whether it ate at all — is not recorded systematically across 55 enclosures.
- **Piranha counting is manual, slow and inaccurate.** Jumping piranhas do not hold still for a census.
- **Poisonous species raise the stakes.** An escaped or aggressive animal is a safety incident, not a welfare metric.

### Growth & retention
- **One-and-done visits.** There is no reason, reminder or relationship that brings a family back.
- **No segmentation.** Every visitor gets the same offer; families, school groups and history enthusiasts are indistinguishable.
- **No pricing lever.** A fixed price cannot fill quiet weekdays or extract value from peak Sundays.

### Constraints that shape everything
- Cloud is allowed but the estate must still function when the uplink is down.
- There is budget for MQTT-capable devices — the estate is willing to instrument itself.
- The team is small; whatever we build must be operable by a handful of people.
