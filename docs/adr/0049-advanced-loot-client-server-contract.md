# ADR 0049: Advanced loot in the RoF2 client

Date: 2026-09-30. Status: implemented and deployed by explicit owner instruction;
native gameplay acceptance pending. [Deployment record](../releases/advanced-loot/PRODUCTION.md).

## Intent

Provide a dedicated in-game loot window that opens when eligible NPC loot drops,
supports `/advloot`, combines pending items from multiple corpses, and remembers
per-character take/never/ask preferences. Players can take or leave one drop,
take all eligible personal loot, inspect items, and edit/search saved filters.
Looting must not require opening each classic corpse window or interrupt combat.

Daybreak's [advanced loot guide](https://www.everquest.com/news/advanced-looting-system)
describes personal/shared lists, saved filters, coin splitting, master assignment,
free grab and Need/Greed/No rolls. The
[December 2024 update](https://www.everquest.com/update-notes/eq-update-notes-12-3-24)
also adds corpse finding. These are the behavioral reference; server-specific
additional personal drops are not part of Nightcap's loot economy.

## Decision

Use the existing signed Nightcap proxy to construct a native `CSidlScreenWnd`
from a new SIDL XML screen. Intercept exactly `/advloot` in the pinned command
interpreter. Extend the existing private server-message/command bridge with a
versioned advanced-loot protocol. Preserve standard client commands and chat.
The client cache is presentation only. All corpse rights, item state, transfers,
filters, rolls and awards remain authoritative on the zone server.

The earlier unbuilt prototype that opened the classic corpse window on kills
was removed from the shared source. It could interrupt combat, did not implement
the requested window or slash command, and had an accidental unrelated hook.
Its exact pre-removal files are retained under local
`artifacts/advloot-20260930/initial-prototype/` for audit.

## Requirements and proof

1. Native window, `/advloot` toggle, automatic display for new eligible drops,
   close/reopen, paging, item inspection and editable/searchable filters.
   Prove with exact-client instruction guards, ABI/lifetime tests and in-game QA.
2. Per-character persistent Ask/Always Take/Never filters; personal Loot/Leave,
   Loot All, auto-loot and auto-show settings. Never leaves the actual item on its
   corpse. A player can return to classic looting by disabling advanced loot.
   Prove persistence, filter edits and duplicate-item behavior in integration tests.
3. Shared loot retains kill credit and raid permissions. Master assignment,
   free grab and timed Need/Greed/No (plus saved choices) must never duplicate an
   item or let multiple members auto-take the same drop. Need precedes Greed;
   Never excludes personal awards without hiding other members' shared loot.
4. Recheck zone, instance, corpse generation, item identity, loot rights, range,
   locked/busy corpse, character state, lore including augments, inventory space,
   NO TRADE consent, quest veto and dynamic-zone restrictions at transfer time.
   Stale/replayed UI actions cannot target another item when an entity ID is reused.
5. Expiration, external/classic looting, zoning, death, disconnect and UI reload
   remove stale rows. Incomplete or malformed snapshots never replace a valid
   committed list. Server identity/revision accompanies every mutation request.
6. No new drops, sell/destroy automation, global loot changes, remote looting,
   era changes or unrestricted entitlement. Retain all complete item metadata,
   native task/quest behavior and transfer audit. Failed/uncertain persistence
   must not acknowledge success or offer another award of an uncertain item.
7. Build the matching server/client, preserve reproducible source provenance,
   include exact in-game QA and rollback, and use feature → dev → test → main.
   The owner explicitly authorized direct main/live deployment on September 30
   for this release and will test live. This exception does not establish manual
   acceptance or change the default branch policy for later work.

## Implementation order

1. Bounded shared protocol, client snapshot model and server decision policy,
   with malformed/stale/duplicate/replay, inventory-failure and roll tests.
2. Native screen lifecycle and command hook in `eq-client-dll`, XML generation,
   signed patch catalog and runtime health contract. Verify exact executable
   bytes and calling conventions against the pinned read-only client.
3. Tracked `server-mods/code` queue, checked preference persistence and the
   existing corpse transfer path; then death, classic loot and lifecycle hooks.
4. Isolated world/zone + proxy builds, integration/review, paired candidate
   packaging and manual QA. Never install into `Client_RoF2_Dev` as a shortcut.

Implementation status and outstanding work live in
`docs/releases/advanced-loot/README.md`; this ADR is not completion evidence.
