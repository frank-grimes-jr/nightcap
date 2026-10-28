# Paladin grip client repair — October 27 candidate

Status: implemented and locally tested on `fix/paladin-grip-client-refresh`, based
on main `444e27dc72476e01e91b60d505634e61b5afed60`. Not signed, published or deployed.
The owner reported that SoulFire printed both conversion messages but stayed 2H
and could not equip with a shield. They had not zoned. This supersedes the earlier
open acceptance status: the October 26 live client fails this use case.

## Cause and repair

The pinned RoF2 parser interns item definitions by item ID alone. At VA 0x555745,
its call to 0x556610 replaces an incoming changed definition with the existing
cached definition. A same-slot item resend therefore retains 2HS on the client
even though server metadata and ItemType changed. This is functional equipment
behavior, not just an inspection label. Zoning has not been tested as a workaround.

Proxy 0.13.1 guards that call and the original function entry against the exact
supported executable. `KeepPaladinGripDefinition` retains the incoming shared
definition for only the ten existing weapon IDs, increments both native reference
counts, and leaves other IDs on the native cache path. It neither mutates the
shared cache nor introduces alternate item IDs. The parser owns release as usual;
separate copies may hold opposite grips. The exact ID policy is shared with the
server. The equipped server toggle also calls `ApplyWeaponsStance()` immediately
after `CalcBonuses()` so stance buffs follow the new weapon type.

Source: `eq-client-dll/src/dllmain.cpp`, generated guarded patch/runtime catalogs,
and `server-mods/code/zone/inventory.cpp`. Native proof:
`eq-client-dll/tests/paladin-grip-native.cpp` maps the protected executable into a
disposable test process, executes the actual parser/cache/type getter/release
code, and compares stock and patched outcomes. The protected game is not changed.

## Verification

- Before repair: native same-ID regression fails with the old cached grip;
  equipped-handler stance regression fails.
- After repair: all ten IDs in both directions pass through the actual parser and
  ItemType getter. Stock parser controls reproduce the old grip. Reference balance,
  independent same-ID copies, unrelated-item cache use, fail-closed guards and
  final native destruction of all ten definitions pass.
- x86 DLL build, runtime fixture build and all 11 runtime tests pass.
- Catalog generation and all 117 exact executable guards pass.
- Four production server grip test groups pass, with SQLite compare-and-set cases.
- Go preflight, manifest and package suites pass against the actual candidate DLL,
  catalog/config and signed current baseline; incompatible pairs are rejected.
- Independent final review found no blockers and reran the native probe.
- All 19 wiki content/link/anchor and source-refresh tests pass. Historical global
  source drift remains review-required; the scoped 40-article review is recorded.

The October27 Docker socket blocker was resolved. October28 native progression
relink and real MariaDB checks pass; see `../balance/progression/`. The final DLL
was rebuilt and all11 runtime groups,117 exact guards and three Go package suites
passed again. `../balance/release/` owns the final local bundle, runtime-identity
proof and fresh seven-script dispatch check. Earlier hashes in evidence.json are
historical candidates, not the final release bundle or a publication receipt.

## Release and exact player QA

`prepare_client.py` stages an unsigned three-file replacement of signed game
2026102601, preserving the other 138 descriptors, patch notes and tombstones.
`TestPaladinGripCandidate` verifies actual binary/catalog/config pairing.
`evidence.json` records candidate hashes. Reconcile the current public channel
before release; do not overwrite a newer concurrent client release.

Obtain owner authorization for the concrete paired deployment in
`../balance/release/README.md`: matching proxy/catalog/config, paired native
binaries and seven approved progression quests. No schema, SQL data,
ItemData layout or rule change is introduced. OVH requires the supported graceful
whole-runtime release, not a quest reload or individual zone kill. Client uptake
requires fully exiting EQ and launching through the signed updater after release.

1. Right-click carried SoulFire to 1HS, inspect it, equip it and a shield without
   zoning. Repeat the equipped toggle with an empty offhand. Test all qualities.
2. With a shield equipped, a 2HS toggle must refuse without changing saved state;
   remove the shield, toggle to 2HS and verify inspection and equip restrictions.
3. Hold two copies of the same ID with opposite grips; inspect and move both.
   Repeat with Fiery Avenger and Fiery Defender, including Ascended Defender.
4. Verify equipped stance buffs, attack skill and skill gains follow both grips;
   damage/delay, augments, saved charges and identity remain intact.
5. Verify relog/zone, trade, bank, corpse and Bazaar restoration preserve each
   grip. Generic item links and database search remain base 2HS by design.

These player checks are pending. Do not describe native tests as gameplay
acceptance. Preserve grip-aware server code and current player data on recovery;
rolling the client back restores the known cache defect. Wiki candidate edits are
unpublished and preserve the current published baseline and unrelated systems.
