# Phase 4 — Live AA audit and bag-price candidate

2026-09-15.

## Built

- #16 live title/ownership audit, native loader compatibility and 13 passing
  tests; independently reviewed and merged into dev through PR #47.
- #22 exact-ID price candidate for all 22 Bartholomew Packwell containers;
  idempotent apply, exact rollback and nine drift controls pass in an isolated
  disposable MariaDB schema. Corrected the NO TRADE comment in the setup SQL.
- Recorded a concrete price ladder, alternative economy choices, shared-item
  effects, cache/reload steps and exact in-game merchant QA.

## Deferred

- AA disablement/refunds: two characters own an unnamed Paladin rank and 17 own
  the Ancient Attunement system AA. These must be handled separately.
- Bag-price activation and owner economy/in-game acceptance. Live rows remain
  unchanged; no shared-memory rebuild, zone restart or main promotion performed.

## Shaky / remaining proof

The bag ladder is a proposal; farming rates and character-specific quotes are
not measured. Four entries on unused merchant list 9905 share item IDs, and some containers
have specialty restrictions. Audit title coverage does not itself prove what
the client displays. See the [AA evidence](../audits/aa-titles-20260915/README.md)
and [bag candidate runbook](../ops/bag-vendor-pricing.md).
