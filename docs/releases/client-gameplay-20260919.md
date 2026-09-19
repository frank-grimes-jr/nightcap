# September 19 client/gameplay release

The server/database changes are live, verified September 19 at 16:14 UTC.
[Activation evidence and recovery](client-gameplay-live-20260919.md). The owner
explicitly requested live activation followed by main promotion on September 19. Manual gameplay acceptance remains open. Implementation commits:
5d7f3f3 (server), d46afe5 (client), 48a087f (hub/assets), da77811 (packaging/QA),
and 8756303 (automatic UI loading). The release worktree is
`E:\EQ_Local_Dev\_worktrees\client-gameplay`.

## Files and activation

Local artifacts: `E:\EQ_Local_Dev\artifacts\client-gameplay-20260919`.
The `client` subdirectory is an ordinary independent copy, never a hard link to
the original. `assets-v4` contains generated spell/UI/model assets (identical payloads to v3;
its source audit was refreshed after the owner installed the earlier package).
`live-activation/hub-v4` contains freshly captured stopped-server migration and
rollback SQL. Final launcher: `launcher-auto-ui/nightcap-launcher-qa.exe`, signed
release 2026091904. Earlier launcher/package generations are superseded; 1903
worked but required a per-character skin command. The private signing
seed is not included in any package or source.

Manifest SHA256: `78dc5c5939059deca50903d7c168418e12b367415197b0efa37837bf9430d92e`.
Expires: `2026-10-19T15:48:53Z` (regenerate a new signed generation after expiry).

The signed inventory includes `dinput8.dll`, `nightcap-bootstrap.exe`,
`nightcap-patches.cfg`, `nightcap-patch-sites.json`, `spells_us.txt`, the two
`uifiles/nightcap` XML files, `poknowledge_chr.txt`, and five model archives.
There are 34 verified code sites and 12 required runtime features. All required
features must initialize before the helper permits game entry.

Close EverQuest before Update/Repair, then use Play in the current launcher.
The native UI loader automatically selects Nightcap for every character; no
slash command is needed. Saved window positions and hotbars keep their native
handling. Open Inventory for the class label and Pet Armor tab, and each of the
four AA tabs for the Class column. The matching server provides their metadata
and pet operations. The initial character-selection screen retains its stock UI.

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
- Hub-v3 and fresh stopped-server hub-v4 each passed 26 MariaDB controls in newly created disposable
  schemas. Forward and rollback preserve all 1,769 captured merchant rows;
  exactly 22 target states are invalidated. Corpse, other-instance, other-zone
  and unrelated NPC states survive. Row/engine/trigger drift and second apply
  reject atomically. Both scratch schemas were removed.
- Client native state/hook/runtime tests pass. Both default and signed QA Go
  suites pass; the launcher frontend builds and all eight Chrome tests pass.
  Automatic-load copy and removal of the slash-command instruction were checked
  in the rendered ready state. Native tests cover the skin hook calling convention
  and saved/default/custom/missing preference values. Independent disassembly
  review confirms both full-load and reload call paths; both sites are ASLR-stable.

Detailed local evidence: `pet-transfer-sql.json`, `pet-database-rehearsal.json`,
`hub-v3-review-report.json`, `hub-v3-review-after.json`, package audits and launch
status files. Release 2026091903 reached `playing`, reported runtime `ready`
with required/enabled/applied masks all 2047, and returned to `stopped` through
owned cleanup. This startup smoke test did not log in or certify gameplay.
Release 1904 passed compilation, native hook tests, exact 34-site verification,
both Go suites and eight browser tests. Its final real-client startup/install is
pending closure of the owner's running game and the protected-folder choice;
the previous 1903 smoke must not be represented as 1904 runtime evidence.

Reproduce the hub rehearsal with
`python tools/tests/rehearse_compact_hub.py ARTIFACT_DIRECTORY hub-v3`.
Run Python controls with `PYTHONPATH=tools`. The database test additionally needs
`NIGHTCAP_DB_TESTS=1` and `NIGHTCAP_TEST_EVIDENCE` pointing to the native SQL trace.

## Deployment and recovery

1. Verify final signed generation 2026091904 and its matching server hashes in
   `server-sha256.json`; the client runtime startup gate passed.
2. Preserve the existing world/zone binaries, configuration, source/CMake and
   required quest/plugin files. Announce maintenance and prefer players camped.
3. Pause the verified Spire supervisor, SIGTERM zones, and verify character and
   zone saves. Treat exited zombie workers as stopped while their parent is
   paused; never force-kill zones still saving. Run the official Spire stop CLI,
   verify its auto-start flags are false and no server workers remain. Take and
   verify the full PEQ dump before writes. Capture hub preimages
   **after** PoK shutdown has saved state. Regenerate and review forward/rollback
   SQL; do not blindly apply an earlier live capture.
4. Apply `server-mods/sql/2026-09-19-pet-armor.sql` once. It intentionally refuses
   an existing table. Deploy the candidate world and zone together, with the
   unchanged matching multiclass plugin already required by the baseline.
5. Apply the freshly generated guarded hub forward SQL without `--force`, then
   start the server. Verify required rules, schema, NPC positions and logs before
   inviting gameplay QA. Install the matching signed client generation into the
   selected authorized client folder, with EverQuest closed.
6. Rehearse content rollback while PoK is stopped. Generated rollback intentionally
   retains cache invalidation; never reinsert stale saved NPC states. If fresh
   states have appeared, recapture/reconcile instead of weakening guards.

Never drop or truncate `character_pet_armor` to roll back: it owns real player
items. Reclaim every stored item using the candidate before disabling that
feature, or retain a compatible recovery build. Database restoration after new
gameplay would lose intervening player progress and requires a separate decision.
Client rollback uses the installer's backups/recovery for the selected folder.
The original client directory remains protected unless the owner explicitly
authorizes an exception; the owner manually installed the earlier 1903 package.

## Exact owner in-game QA

Use a normal account, one character with three selected classes, and a second
character with different classes. Preserve a before/after item inventory and
screenshots for failures. The owner authorized this release's main promotion
before these checks; promotion does not certify their results.

1. **Inventory and AA:** log in with an existing character whose saved skin was
   Default/custom, then create or use a character without a saved UI preference.
   Both must load Nightcap automatically without a command; verify hotbars and
   window layouts remain usable. Select/release second and third classes at The Ancient
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
The owner's September 19 instruction authorizes live deployment and main
promotion. It does not constitute manual gameplay acceptance or publication of
a hosted production updater; this package remains the signed offline QA channel.
