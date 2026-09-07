# ADR-0011 — Offline ticket validation with eventual reconciliation

**Status:** accepted · **Date:** 2026-09-05
**Serves:** FR-1.3, FR-1.4, NFR-AVL-1
**Related:** ADR-0001, ADR-0012

> **Role of this ADR since [ADR-0012](ADR-0012-ticketing-platform-adopt-not-build.md):** ticketing is adopted, not built. This document is the **requirement specification and acceptance test** for the offline validation the adopted platform must provide. It becomes a build design only if no vendor meets it (ADR-0012 §4).

## Context
Tickets are sold in the cloud; gates are on an estate whose uplink fails. Visitors must never be turned away because of connectivity, and fraud (one QR used twice) must still be controlled.

## Decision
1. Tickets are **signed credentials** (QR/NFC payload with ticket id, validity window, pass type, group size, signature). Gates verify the **signature offline** with a public key — no lookup needed to admit a valid, unused ticket.
2. The **local gate validation service** keeps a **synced allow-list/revocation list** (sold, refunded, already used) and a **local "used" ledger**. The lists arrive over the **downlink** as retained snapshots plus sequence-numbered deltas in the critical traffic class, so a reconnecting gate has the current revocations within a minute ([Edge & connectivity → Downlink](../hld/core/edge-and-connectivity.md#downlink-cloud--estate)). It admits on signature + not-in-local-used; it records `GateEntered` to the local broker.
3. Entry/exit events flow to the cloud when the uplink is up; the cloud **reconciles** (detects duplicates used at two gates during an outage, refunds used after sale, etc.) and produces an exceptions report rather than blocking at the gate.
4. **Multi-visit passes** are validated the same way; per-day usage limits are enforced locally against the local ledger and reconciled later.
5. Gate readers themselves hold a small cache of the public key and the last synced lists, so even a broker outage degrades to "signature-only" admission.

## Edge cases the product must handle

These are part of the acceptance test for the adopted platform ([ADR-0012](ADR-0012-ticketing-platform-adopt-not-build.md)) and of the build design if we end up building.

| Case | Required behaviour |
| --- | --- |
| **Clock skew** at a gate (reader unsynced, or a ticket bought at 23:59) | Validity is checked against the **operational day** (opening to closing, not midnight) with ±2 h tolerance; readers take time from the broker; a reader unsynced for > 1 h falls back to date-only checks and raises a health event |
| **Partial group entry** on a family pass | The pass carries a group size; the local ledger keeps a **per-day group counter ≤ group size**; members may enter separately, at any gate, within the day; gates share the counter through the broker — if the broker is down, each gate allows up to the group size and reconciliation flags the excess |
| **Exit and re-entry** the same day | An exit scan marks the credential "out"; re-entry within the operational day is admitted without incrementing the counter; a re-entry attempt with no exit scan is treated as a possible duplicate → staff override with a reason code, not a refusal |
| **Same credential at two gates within seconds** | Broker propagation is ~1 s; the second gate sees the "used" entry or, if it lost the race, both admissions are flagged for a staff check at the gate line |
| **Ticket for another day** presented today | Refused with a clear message and a pointer to the ticket desk; never silently admitted |
| **Refund or revocation during an uplink outage** | Admitted on signature until the revocation snapshot lands (≤ 60 s after reconnect); the admission appears in the exceptions report ([downlink](../hld/core/edge-and-connectivity.md#downlink-cloud--estate)) |
| **Reader restarts mid-queue** | Local ledger and lists persist on the reader; queued entries are re-sent from the persistent session; no double count |

**False-rejection metric:** valid tickets refused ÷ total presentations ≤ 0.05%, measured from staff override reason codes and reconciliation; it is the number the visitor feels.

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
| Ticket refunded during an outage is admitted after reconnect, before the revocation lands | Critical-class downlink delivered before the uplink drain; the window is ≤ 60 s and every admission inside it is in the exceptions report; game day GD-5 |

## How we will know this was right
Gate availability 99.9% regardless of uplink; reconciliation exceptions < 0.1% of admissions; average scan time < 2 s; revocation applied ≤ 60 s after reconnect. Verified by game days GD-4 and GD-5 in the [resilience validation catalogue](../hld/core/resilience-validation.md) — on the adopted ticketing platform's stack ([ADR-0012](ADR-0012-ticketing-platform-adopt-not-build.md)).
