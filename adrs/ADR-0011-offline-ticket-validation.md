# ADR-0011 — Offline ticket validation with eventual reconciliation

**Status:** accepted · **Date:** 2026-09-05
**Serves:** FR-1.3, FR-1.4, NFR-AVL-1
**Related:** ADR-0001

## Context
Tickets are sold in the cloud; gates are on an estate whose uplink fails. Visitors must never be turned away because of connectivity, and fraud (one QR used twice) must still be controlled.

## Decision
1. Tickets are **signed credentials** (QR/NFC payload with ticket id, validity window, pass type, group size, signature). Gates verify the **signature offline** with a public key — no lookup needed to admit a valid, unused ticket.
2. The **local gate validation service** keeps a **synced allow-list/revocation list** (sold, refunded, already used) and a **local "used" ledger**. It admits on signature + not-in-local-used; it records `GateEntered` to the local broker.
3. Entry/exit events flow to the cloud when the uplink is up; the cloud **reconciles** (detects duplicates used at two gates during an outage, refunds used after sale, etc.) and produces an exceptions report rather than blocking at the gate.
4. **Multi-visit passes** are validated the same way; per-day usage limits are enforced locally against the local ledger and reconciled later.
5. Gate readers themselves hold a small cache of the public key and the last synced lists, so even a broker outage degrades to "signature-only" admission.

## Alternatives considered
| Option | Pros | Cons | Why not |
| --- | --- | --- | --- |
| Online validation against the cloud | Simplest fraud control | Gates stop with the uplink | Fails NFR-AVL-1 |
| Paper tickets with manual checks during outages | Zero tech | No data, slow, fraud-prone at 15,000/day | Scale |
| Signed credentials + local ledger + reconciliation (chosen) | Always admits valid tickets; fraud detected, if slightly late | Small fraud window during outages; key management | — |

## Consequences
**Positive:** gates never depend on the cloud; visitors without connectivity are fine (QR on screen or printed); every entry is still an event for analytics.
**Negative:** a determined double-user might get two people in during an outage — an accepted, bounded loss versus turning families away.

| Risk | Mitigation |
| --- | --- |
| Signing key compromise | Key rotation; short validity windows; revocation list sync |
| Local ledger divergence between gates during outage | Gates share the local broker; if the broker is down, reconciliation flags duplicates for review |

## How we will know this was right
Gate availability 99.9% regardless of uplink; reconciliation exceptions < 0.1% of admissions; average scan time < 2 s.
