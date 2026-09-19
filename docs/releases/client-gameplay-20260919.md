# September 19 client/gameplay candidate

Status: source promoted through local dev to local test after automated
verification; not deployed to the live server, not accepted in game, and not
promoted to main. Implementation commits: 5d7f3f3 (server), d46afe5 (client),
48a087f (hub/assets), da77811 (packaging/QA). Feature, dev and test trees matched
exactly at promotion. The working candidate remains in
`E:\EQ_Local_Dev\_worktrees\client-gameplay`.

## Files and activation

Local artifacts: `E:\EQ_Local_Dev\artifacts\client-gameplay-20260919`.
The `client` subdirectory is an ordinary independent copy, never a hard link to
the original. `assets-v3` contains generated spell/UI/model assets. `hub-v3`
contains the rehearsed content migration. Earlier generations are superseded.
Final launcher: `launcher-final/nightcap-launcher-qa.exe`, signed release
2026091903. Point it at the separate `client` folder. Earlier launcher/package
1901 and 1902 artifacts failed startup and are superseded. The private signing
seed is not included in any package or source.

Manifest SHA256: `b35b0c8651edb779f3fc5ef47221a913bcc17b4a407041e92ab23bc1c30dbf9e`.
Expires: `2026-10-19T13:46:23Z` (regenerate a new signed generation after expiry).

The signed inventory includes `dinput8.dll`, `nightcap-bootstrap.exe`,
`nightcap-patches.cfg`, `nightcap-patch-sites.json`, `spells_us.txt`, the two
`uifiles/nightcap` XML files, `poknowledge_chr.txt`, and five model archives.
There are 32 verified code sites and 11 required runtime features. All required
features must initialize before the helper permits game entry.

After the matching server is deployed, use the candidate launcher with the
separate candidate client folder. In game run `/loadskin nightcap 1` once per
character. Open Inventory for the compact class label and Pet Armor tab, and
open each of the four AA tabs for the Class column. An older server will not
provide the new metadata or pet operations.

## Automated evidence

- Matching isolated world, zone and tests targets compiled successfully.
- Full native server fixture suite: 87 tests passed.
- Native spell/death policy controls and packet/cast/melee integration checks pass.
- Pet transfer controls run the actual C++ methods and inject failure at all 12
  database calls in both directions, plus stale source, occupied slot, cursor
  queue, charges and cross-session serial controls.
- Real MariaDB rehearsal uses session-local temporary tables: all 17 fields and
  six augments survive equip/remove; rollback after INSERT and DELETE restores
  the original item; changed binary custom data fails the source comparison.
- Hub-v3 independently passed 26 MariaDB controls in newly created disposable
  schemas. Forward and rollback preserve all 1,769 captured merchant rows;
  exactly 22 target states are invalidated. Corpse, other-instance, other-zone
  and unrelated NPC states survive. Row/engine/trigger drift and second apply
  reject atomically. Both scratch schemas were removed.
- Client native state/hook/runtime tests pass. Both default and signed QA Go
  suites pass; the launcher frontend builds and all eight Chrome tests pass.
  The added skin instruction was also checked in the rendered ready state.

Detailed local evidence: `pet-transfer-sql.json`, `pet-database-rehearsal.json`,
`hub-v3-review-report.json`, `hub-v3-review-after.json`, package audits and launch
status files. Release 2026091903 reached `playing`, reported runtime `ready`
with required/enabled/applied masks all 2047, and returned to `stopped` through
owned cleanup. This startup smoke test did not log in or certify gameplay.

Reproduce the hub rehearsal with
`python tools/tests/rehearse_compact_hub.py ARTIFACT_DIRECTORY hub-v3`.
Run Python controls with `PYTHONPATH=tools`. The database test additionally needs
`NIGHTCAP_DB_TESTS=1` and `NIGHTCAP_TEST_EVIDENCE` pointing to the native SQL trace.

## Deployment and recovery

1. Verify final signed generation 2026091903 and its matching server hashes in
   `server-sha256.json`; the client runtime startup gate passed.
2. Verify the target has no active players; take and verify a full PEQ backup and
   preserve the existing world/zone binaries and required quest/plugin files.
3. Stop world/zones using the existing operational runbook. Capture hub preimages
   **after** PoK shutdown has saved state. Regenerate and review forward/rollback
   SQL; do not blindly apply an earlier live capture.
4. Apply `server-mods/sql/2026-09-19-pet-armor.sql` once. It intentionally refuses
   an existing table. Deploy the candidate world and zone together, with the
   unchanged matching multiclass plugin already required by the baseline.
5. Apply the freshly generated guarded hub forward SQL without `--force`, then
   start the server. Verify required rules, schema, NPC positions and logs before
   inviting gameplay QA. Install the matching signed client generation only into
   the candidate client.
6. Rehearse content rollback while PoK is stopped. Generated rollback intentionally
   retains cache invalidation; never reinsert stale saved NPC states. If fresh
   states have appeared, recapture/reconcile instead of weakening guards.

Never drop or truncate `character_pet_armor` to roll back: it owns real player
items. Reclaim every stored item using the candidate before disabling that
feature, or retain a compatible recovery build. Database restoration after new
gameplay would lose intervening player progress and requires a separate decision.
Client rollback restores the previous signed package through the installer's
backups/recovery; the original client is untouched.

## Exact owner in-game QA

Use a normal account, one character with three selected classes, and a second
character with different classes. Preserve a before/after item inventory and
screenshots for failures. Main promotion waits for owner sign-off.

1. **Inventory and AA:** select/release second and third classes at The Ancient
   Chronicler (NPC 999220), PoK x=-285,y=-124,z=-158.875. Verify the compact
   primary/second/third label, empty slots, reconnect, zoning and character switch.
   In all four AA tabs verify Class values against the ability's original eligible
   classes, including shared and general abilities. Sort each column, select an
   ability, read its description, purchase a legal rank, and reopen the window.
   No stale previous character data, overwritten Category column or clipped text.
2. **Hub:** arrive at PoK x=-285,y=-148. Visit all sixteen class merchants
   997900–997915 in the 4×4 grid (x -321/-297/-273/-249, y -184/-160/-136/-112)
   and utilities 999225/999226/999237/999238/999239 along y=-205. Check feet on
   ground, path clearance, clickability, Find, hail, class selection, each shop's
   stock/prices and bag/epic/blessing/waypoint service. Verify Lightning Warrior,
   Pyrilen, Gelidran, Girplan and Scrykin models, including after PoK restart.
3. **Buffs:** test ordinary buffs, bard song, activated AA, discipline, Divine Aura,
   Improved Twincast, illusion and normally death-persistent beneficial effects.
   Verify no countdown over several former durations, zoning and reconnect.
   Death then resurrection removes all beneficial buffs. Test click-off, dispel,
   replacement/stacking, hit/charge exhaustion and leaving an aura's radius.
   Debuffs and hostile NPC buffs still expire. Record invulnerability/sustain
   interactions separately: this is an intentionally changed balance policy.
4. **DoTs and melee:** cast representative necromancer, shaman and bard DoTs;
   casting completes immediately while mana, target/resist checks and reuse still
   apply. Compare an ordinary direct-damage spell and hostile NPC casting.
   Autoattack a valid target while repeatedly casting a longer non-DoT spell:
   both primary and offhand rounds continue at their existing cadence. Out of
   range, stun, mez, fear and death must still stop attacks as appropriate.
5. **Pet armor:** summon primary and extra-class permanent pets. In Inventory →
   Pet Armor use Previous/Next to select each. Place a compatible ordinary item
   on an otherwise empty cursor, equip each of the eight slots, inspect, remove,
   and compare stats/appearance. Verify augments, charges, attunement, custom
   data, color and ornaments survive removal, zoning and reconnect. No ninth
   slot, cross-pet changes or duplicate lore acquisition. Try occupied/wrong
   slots, full cursor/queue, combat, casting, trade and distance >50: reject
   without moving items. Temporary No Rent, evolving/scaling, stackable, quest
   and NoPet items are currently unsupported and must reject clearly.
6. **Pet lifetime and recovery:** dismiss/kill each pet, reconnect, release a pet
   class, and confirm inactive stored armor remains inspectable/removable.
   Reacquire/resummon and check the matching loadout. Extra pets retain their
   existing summon-again requirement after zoning. Charm/swarm pets cannot use
   durable armor. Native hand-in of managed armor returns/refuses the item;
   ordinary quest loot cannot replace a managed slot. Simulated DB disconnect
   belongs in isolated QA only: reconnect must reveal exactly one committed copy.

## Remaining limits

Native ABI/layout assertions, exact executable checks, compilation and SQL tests
do not prove game rendering, packet ordering, real pet stat effects, resurrection
behavior or encounter balance. Those checks remain explicitly open until played.
No production publication or gameplay main promotion is authorized by this report.
