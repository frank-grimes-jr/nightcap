# PoK arrival hub: activation and in-game QA

Candidate only, 2026-09-13. No live deployment or in-game QA has occurred.
Keep the current AA ownership branch and its binaries out of this release.

## Operator activation

1. Schedule the PoK restart with the owner; the owner previously asked not to
   restart zones while playing. Do not substitute `#repop` for the restart.
2. Take and verify a fresh PEQ backup, including routines/triggers. Preserve the
   three deployed quest/plugin files listed below with hashes for rollback.
3. Verify the five hashes in `hub-database-tests.json`. Read `hub-layout.md` and
   inspect `hub-before.json`/`hub-after.json`. Apply `hub-forward.sql` to PEQ in
   a fresh mysql connection **without `--force`**. It refuses changed preimages
   or occupied IDs and rolls back all content writes on an SQL error. Do not
   bypass a rejection; recapture/review/regenerate/retest if the source changed.
4. Deploy these candidate files from `server-mods/` to their corresponding paths
   under `E:\EQ_Local_Dev\akk-stack\server\`:
   - `quests/global/global_player.lua` → `quests/global/global_player.lua`
   - `quests/poknowledge/The_Ancient_Chronicler.pl` → `quests/poknowledge/The_Ancient_Chronicler.pl`
   - `plugins/multiclass.pl` → `plugins/multiclass.pl`
5. Promote the matching `vendor_restock.sql`, `tools/apply-era.ps1`,
   `tools/pok-hub-era.ps1`, and `docs/pok/catalog-policy.json` together through
   the agreed dev/test flow. Keep the GM refresh endpoint retired; it cannot
   overwrite merchant stock. Do not run apply-era merely to activate this hub.
6. Restart only PoK at the agreed time. Dynamic zone processes are bare `bin/zone`:
   identify PoK's PID through its current zone log, not command-line matching.
   Reload the global quest/plugin changes in other active zones as needed so
   status commands agree. No C++ build, shared-memory rebuild, or client-file
   modification belongs to this content deployment.
7. Verify 16 new class merchants (NPC IDs 997900–997915), six guide/utility
   spawns, no old Loremaster spawns, and one Forgemaster. Inspect zone logs for
   quest exceptions. Then run the player checks below.

## Player checks — normal account, current RoF2 client

Use disposable characters for class changes. Do not spend or refund a main
character's AAs to test this UI; native AA persistence remains a separate change.

1. **Arrival and walking:** enter PoK normally. Arrival is approximately
   x=-285, y=-148, z=-159. Walk between both merchant rows, through the center,
   around the guide, and to all five utility NPCs. Confirm nobody floats,
   sinks, overlaps a wall, blocks an arrival/door/path, or requires standing
   inside another NPC. Check target line of sight and facing from both sides.
   Positions are provisional until this passes; capture exact corrections.
2. **Find window and labels:** locate the Ancient Chronicler, all 16 class
   merchants, bags, both blessing services, Epic Ascension, and Waypoint Travel
   through Find. Confirm spell/song/tome labels match `hub-layout.md`. The old
   Loremaster and II/cont. shops should no longer spawn at the former location.
3. **Class status:** on a character with no secondary classes, log in, hail the
   Chronicler, type `#classes`, then `/say !classes`. Each shows Primary plus
   explicit empty Second and Third slots. Repeat with one and two selected
   secondary classes; status should agree with the saved character after relog.
   Check unrelated player commands still work.
4. **Selection:** on a disposable Warrior, preview Cleric. Preview changes
   nothing. Open confirmation and choose No; slots remain unchanged. Repeat
   and choose Yes; Second now says Cleric immediately. `#classes` agrees.
   Select Wizard as Third and confirm. Duplicate choices and attempts to add
   a fourth class must not change the selected classes. Camp to character
   selection and return; all three classes persist.
5. **Release UI:** only on the disposable zero-AA character, cancel a release
   and verify no change. Confirm releasing Second; Wizard promotes to Second
   and Third becomes empty. Hail/status/relog must agree. Native AA refunds,
   failed class-write behavior, and paid-AA release are not certified here.
6. **Shopping:** open every class shop. Counts at level cap 50 are in
   `hub-layout.md` (3–275 items each, 1,747 total listings, 1,229 unique items).
   Warrior/Monk/Rogue/Berserker stock contains tomes; Bard contains songs.
   Cleric and Wizard spells appear at their respective shops. Shared spells
   may appear on several appropriate class shops. No generic II shop is needed.
7. **Prices and learning:** compare displayed prices on the same character
   against pre-activation samples; charisma/client pricing may affect the
   displayed amount. Buy representative eligible spell/song/tome items using
   disposable characters with the matching selected class. Verify scribing,
   memorizing/training, and use subject to their level and current client UI.
   A melee-primary caster test requires the already established client patch;
   this change does not introduce a new client capability patch.
8. **Utilities:** verify bags, blessings, premium blessings, epic quest hails,
   and waypoint dialogue still open with the same costs and prerequisites.
   Five identical Forgemaster spawns were consolidated into one; confirm one
   quest response, no missing service, and no repeated NPC overlap.

## Rollback and limitations

Restore the three backed-up quest/plugin files, apply `hub-rollback.sql` in a
fresh connection without `--force`, and restart PoK at an agreed time. Rollback
restores the exact captured content, including the original duplicate spawns.
It deliberately refuses unexpected later NPC, stock, item-price, or era edits;
review those differences rather than overwriting them. The new restock script
automatically follows its legacy branch after the hub NPCs are removed.

The current inventory policy preserves the already stocked pool at expansion 0,
with original class levels up to 50. It does not certify each spell's original
expansion availability. Later releases require a reviewed expanded catalog;
both era preflight and restock refuse to silently invent that pool. Caps below
50 filter by original class level; caps above 50 require review.

The class plugin still performs the existing global spell-access widening and
requires a camp for all client state to refresh. Client spell-data synchronization
remains an operator procedure with the client closed; it is no longer printed as
a script command in player dialogue. This change improves status and navigation;
it does not certify class-change transactions or resolve the AA lifecycle work.
