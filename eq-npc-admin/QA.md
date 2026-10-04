# NPC Admin QA — 2026-10-04

## Automated and browser evidence

- Node 24.17.0; MariaDB 10.11.19 disposable container on 3317.
- Domain, API security, durable draft/CAS, and real Git/bare-remote tests.
- Database apply/rollback, stale previews, injected mid-transaction failure,
  FLOAT decimals, BIGINT snapshots, nullable defaults, merchant metadata,
  scoped saved-state preservation, all-version spawns, duplicate keys, and
  nontransactional content/state/ledger refusal.
- Independent deployment and Git/security reviews; findings became regressions.
- Live PEQ read-only schema audit: all supported fields exist and touched tables
  use InnoDB. Sortre Blackdragon #999520 can be browsed. No live rows were written.
- Browser rehearsal used real PEQ table definitions copied into
  `npc_admin_browser_qa` on 3317, with fixtures `QA_Guard_Only` #999520 and
  `QA_Shared_Guard` #999521. Spawn #42, group #7, ecommons v0; table #8/drop #9;
  merchant #10. These IDs in the **fixture database** do not describe live changes.
- Pasted `/loc` `-185.3, -1506.1, 2`; verified X=-1506.1/Y=-185.3/Z=2, staged
  without writes, applied with destination confirmation, and rolled back to 10/20/3.
- Looked up Rusty Broad Sword #5016, staged 33.3 loot chance and merchant slot 2,
  verified two-NPC loot sharing, applied and rolled back through the browser.
  Rusty Scythe #5015 remained intact. No server restart or gameplay promotion.
- Exported the two-record JSON through the browser and imported a new draft;
  the exported document contained no database credentials. Desktop and 390px
  layouts passed visual inspection; no horizontal overflow or browser console
  errors. [Workbench screenshot](preview.jpg). Disposable drafts/receipts were
  archived under ignored `.local/qa-evidence`; the disposable container was stopped.

## Owner in-game acceptance (not yet performed)

Use a backed-up **test server** and a disposable copy of an existing NPC. The
browser-only QA database has no game server attached and is not an in-game test.
Choose and record your test NPC ID, spawn ID and exact zone/version in the draft
title; never substitute these fixture IDs blindly into a live database.

1. **Placement:** use an existing test NPC in East Commonlands (`ecommons`, v0).
   Stand at the intended safe spot and copy `/loc`. In NPC Admin, select that NPC,
   Locations, and its spawn; paste the coordinates and set heading 256. Verify
   the displayed group alternatives before staging. Export the JSON for review.
2. **Apply:** take the full PEQ backup, stop the affected zone and its instances,
   preview against the test profile, review the exact saved-state IDs, confirm
   maintenance and target name, then apply. Start the zone. The NPC must appear
   at the new coordinates with the expected heading and correct ground height.
   Walk around it and check pathing, aggro and respawn timing.
3. **Loot:** choose a test NPC's existing nonproduction loot group. Add Rusty Broad
   Sword #5016 at a deliberate test chance, noting every NPC sharing the group.
   Apply, regenerate shared memory, restart affected zones, and inspect drops
   across repeated kills. Verify charges, equipping, level/era restrictions,
   group probability, global loot and quest rewards. One kill cannot verify odds.
4. **Merchant:** on a test NPC with class 41 and a non-curated merchant ID, add
   #5016 to a free slot. Apply/restart and open the shop. Verify item, price,
   availability and restrictions. The protected PoK class-hub catalog must refuse
   edits through this utility.
5. **Combat/model:** change one bounded stat/appearance field on the test NPC;
   restart its zone and verify the client model and encounter behavior. Record
   actual legal class/AA pool, gear and player level for any balance claim.
6. **Rollback:** stop affected zones first, choose the relevant applied receipt,
   preview rollback, and confirm the same target. Repeat activation. Original
   placement/stock/stats and saved-state scope must be restored. Introduce a
   harmless intervening test edit and verify rollback refuses to overwrite it.
7. **Git:** publish the reviewed draft to its generated feature branch. Verify
   only the four content files changed. Review/promote through dev and test;
   approve main only after recording the in-game results above.

Record pass/fail, exact target, IDs, timestamp, activation performed and any
unexpected effects. Pending manual acceptance is not evidence of a live defect.
