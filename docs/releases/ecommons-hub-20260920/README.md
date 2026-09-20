# East Commonlands tunnel QA candidate

Approved September 20, 2026. Candidate only; owner in-game acceptance and main
promotion remain open. The launcher installs automatically before Play; no new
slash command is required. Use signed release **2026092002** with the matching
server migration. Older launchers lack the tunnel object imports and recall data.

## Exact owner QA

1. Close EQ and open the new QA launcher. Check/update your chosen client folder,
   then Play. Confirm inventory shows all three classes, the AA Class column and
   each pet's eight armor slots; no automatic chat command appears at login.
2. On an existing character open AA **General**, find **Ancient Attunement**, and
   make a hotkey labeled **Nightcap Recall**. Cast it from another zone: five-second
   cast, ten-minute reuse, landing at world X=-190,Y=-1725,Z=3.75 (spell base Z=4)
   in **ecommons**, beside Shady's classic tunnel. Existing bind/Origin/Return Home
   destinations must remain unchanged. Previously owned AA remains granted.
3. Walk the entrance and both merchant rows. Sixteen class merchants are 40 units
   apart, first row Y=-1610 and second Y=-1785, X=-315 through -35. Buy one legal
   level-50-or-lower spell/tome from each; stock/prices remain the same. Verify
   visible exotic models, no human fallbacks, and unobstructed walking/clicking.
4. Hail The Ancient Chronicler at X=-80,Y=-1550. Exercise class dialogue without
   releasing a class unless intended. Verify all five utilities on the same wall:
   Bags(-275), Epic Forge(-240), Restora(-205), Goldwind(-170), Waypoints(-135),
   all Y=-1550. Check their existing interactions and prices. Shady is unchanged.
5. Click **each** stone below, verify its destination and safe landing, then use
   the new nearby book to return. Existing books retain their original PoK routes.
   The ten tunnel stones follow the west wall, visible centers X=-350,
   Y=-1580,-1605,...,-1805. Confirm labels and no stone overlap or floating/burial.
   Grobb's mesh has an offset compensated in its anchor; inspect that one closely.
6. Use the tunnel book at X=-315,Y=-1550 to PoK and the new PoK book at
   X=-285,Y=-124 to return. The original PoK city stones remain unchanged.
7. Create a disposable new character with tutorial disabled. Confirm it starts
   and binds at the tunnel. Test at least a caster and melee chassis. Camp/relog
   and zone away/back; the 22 services must not reappear in old PoK positions.
8. With multiple class pets, travel both ways, camp/relog, and verify each pet and
   its armor persists under the existing three-pet policy. Check melee during
   casting, instant DoTs, and permanent beneficial buffs still work; buffs still
   disappear on death. These are regression checks, not new policy changes.

Coordinates below are server **X,Y,Z**, whereas `/loc` prints Y,X,Z.

| Route | Destination landing X,Y,Z | New return book X,Y,Z |
|---|---|---|
| qeynos2 | 487, 219, 3.75 | 504, 184, 0.0 |
| freportw | 77, -642, -29.0 | 77, -662, -34.0 |
| gfaydark | -734, -188, 0.0 | -738, -174, -3.75 |
| butcher | -523, 1726, 0.5 | -487, 1755, -3.5 |
| everfrost | -31, 2835, -60.0 | -58, 2887, -63.25 |
| misty | -1263, -546, 12.0 | -1243, -560, 4.5 |
| nektulos | -349, 705, -1.75 | -322, 743, -9.5 |
| feerrott | -163, 908, -7.0 | -141, 867, -9.5 |
| innothule | -30, -709, -25.75 | -10, -729, -28.25 |
| tox | -583, 2345, -43.25 | -563, 2325, -47.25 |

Nektulos must display its **classic** terrain. The signed installer backs up and
retires only the exact supported `nektulos.eqg`; it preserves loose `.zon` and
classic `.s3d` assets. A modified EQG blocks installation without overwriting it.
Map layer 3 must be enabled to see the added tunnel labels. This local QA bundle
contains the source client's map layer; distribute only after checking other
players' custom map-note preservation needs.

## Reproducible checks and rollback

- `python -m unittest discover -s tools/tests -p 'test_client*.py'` and
  `test_ecommons_hub.py` cover asset preservation, recall fields, string collisions,
  model imports, topology, tutorial/start policy and reserved IDs.
- `tools/tests/rehearse_ecommons_hub.py ARTIFACT_DIRECTORY hub-vN` creates a random
  disposable schema, verifies guarded apply, collision rejection, exact FLOAT
  values, preserved stock/state and immediate rollback; never writes live PEQ.
- Go tests cover signed staging/installation, pinned original retirement, concurrent
  write/delete exclusion, recovery conflicts and interrupted atomic restoration.
- Native map probes use the actual server map parser/raycaster. Native client
  disassembly confirms object imports, classic fallback, stone offsets and AA tabs.
  These checks do not constitute visual, collision, combat or portal acceptance.

Fresh capture and full PEQ backup are mandatory before activation. Stop world and
all zones gracefully; never `#repop` the old/new hub to force this migration.
Only affected non-corpse, non-zone metadata, base-instance saved NPC rows in zones
22/202 are invalidated. Merchant identities, definitions and stock are untouched.
No existing character, bind, AA ownership, inventory or pet rows are written.

The generated rollback is valid immediately after apply, before new saved state.
After player/zone activity, stop and capture again: reconcile legitimate changes,
regenerate a guarded reverse migration that invalidates only affected fresh NPC
states, and rehearse it. Do not force the stale rollback or restore a full database
on top of new player progress. Restore the archived scripts/binary and regenerate
shared memory before restart. Client installation journals retain replaced files
and the retired archive; preserve pending recovery conflicts for inspection.

Local evidence and full backups (not committed):
`E:/EQ_Local_Dev/artifacts/ecommons-hub-20260920/`.
