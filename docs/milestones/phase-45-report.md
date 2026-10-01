# Phase 45 — Adventure Journal and archetype Epic 0.5

Date: October 1, 2026. Candidate; manual acceptance and production activation open.

## Built

Eight native Classic adventures, preparation notes, earned archetype choices,
one recoverable all-class charm, hub-only switching, durable shared cooldown,
one-pet Binder targeting, bounded native spell durations and compatibility gate.
Added guarded content generation, disabled-by-default schema, retained-data
recovery, exact client spell additions and package-regeneration compatibility.
Recorded SQL fault/concurrency evidence and exact player/balance QA.

## Scope decisions

Used the existing Tasks window and existing named encounters. One physical
charm with stored attunement avoids inventory exchanges and five-item stacking.
No bespoke wave instances, account-wide discoveries or automated gear advice
are claimed. These can follow the first campaign's player/balance measurements.

## Verification and remaining work

Perl quest controls cover progression, hub restrictions, recovery, invalid clicks
and pet ownership. MariaDB controls cover occupied IDs, expansion gates,
mid-write rollback, uncertain acknowledgement, reconnect and concurrent clicks.
Native fixtures run the actual movement matching and duration code. Review
corrected the wrong exploration type, expansion-gated Greshvoule and the initial
duration formula. Client staging retains the entire original input prefix.

Full paired build evidence belongs in `docs/adventure-journal/native-evidence.json`
once complete. Native UI, encounter difficulty, natural spawn waits, interaction
with the legal AA/gear pool and perceived reward value require the documented
in-game QA. No production balance or rendered acceptance is asserted.

Operational guide: [Adventure Journal](../adventure-journal/README.md).
