# Paladin weapon grip — October 26 candidate

Status: implemented on `feature/paladin-weapon-toggle` from main `465003f6`.
Not deployed or accepted in the game. Wiki edits are an unpublished candidate.
The user explicitly chose to replace SoulFire's Complete Heal click with the toggle.

## Behavior and scope

Right-click SoulFire, Fiery Avenger or Fiery Defender to switch between 1H
Slashing and 2H Slashing. Existing/new weapons start in their original 2HS grip.
This covers all ten existing definitions: SoulFire 5504/205504/405504/605504,
Fiery Avenger 11050/211050/411050/611050, Fiery Defender 10099/810099.
The last Defender is the separate Epic Forgemaster Ascended version.

The same instance keeps its ID/name, quality, damage/delay, other combat stats,
procs, equip/class/level restrictions, saved charges, binding, color, ornaments,
augments, GUID and recast timestamp. Its weapon type changes, so normal native
skill selection, skill gains, weapon AAs and damage-bonus rules follow that grip.
The 1HS version remains primary-only; this does not add an offhand equipment slot.
SoulFire no longer casts Complete Heal. Clicking is unlimited, including a spent
SoulFire, and never casts the spell used to make the client recognize a click.

Use a carried item or the equipped primary weapon while out of combat/casting
and other trading. Remove the offhand item before changing an equipped weapon to
2HS. A socketed augment must support the destination weapon type; incompatible
augments cause refusal without changing anything. Scaling/evolving and unrelated
custom metadata are refused. Reforging still requires unmodified inputs: switch
back to 2HS before using an otherwise eligible Reforging Box recipe. A newly
awarded/upgraded weapon starts 2HS. Quest and task identity matching is unchanged.

## Implementation and failure handling

- `common/paladin_weapon_grip.h`: exact family policy and compare-and-set SQL.
- `common/item_instance.cpp/.h`: projects the saved `nightcap_paladin_grip=1`
  key into each instance's owned ItemData. Empty metadata means canonical 2HS.
  Constructors and native custom-data loading/setters apply the projection.
- `zone/inventory.cpp`: validates session, slot, offhand and augment restrictions;
  saves one atomic UPDATE against the exact inventory preimage, then publishes.
- `zone/client_packet.cpp`: ItemVerifyRequest performs the action before ordinary
  click checks. The following CastSpell packet is consumed without another toggle,
  casting, healing or charge consumption, including the old SoulFire heal packet.
- `common/patches/rof2.cpp`: publishes unlimited click charges and no click timer
  only for these weapons. Saved values are untouched. ClickName is "Toggle Weapon
  Grip" and the existing self-target spell 288 is a routing token, never cast.

Native MaxCharges remains unchanged: it governs quantity-based deletion and
merchant/quest behavior. Unlimited max/current charges are only a RoF2 packet
projection. Both click packet paths reject out-of-range slots before int16
conversion, and combat checks include the player's hostile-mob aggro count.

An alternate item-ID family was rejected because it changes quest/forge identities
and introduces replacement inventory transactions. Native custom metadata is
already persisted for inventory, banking, trade, corpse recovery and bazaar
delivery. Only a single exact key is supported: the existing multi-key encoding
is not silently repaired. Generic item links and database-only catalog/search
filters describe the base 2HS definition; inspect the actual inventory item for
its current grip. Native client rendering and market inspection remain QA gates.

The saved UPDATE compares character/slot, item ID/GUID, charges, color, all six
augments, binding, custom data and ornaments. It changes only custom_data. It
disables retries; a query error, stale saved preimage, or publication exception
uses the existing item-transfer quarantine to prevent stale disconnect saves.
No item is deleted, summoned or copied into another inventory slot. The 2HS
transition removes the key instead of leaving a customization marker.

## Verification and release boundary

Run `python -B -m unittest discover -s tools/tests -p test_paladin_weapon_grip.py -v`.
Four focused groups compile the actual production policy, instance projection and handler with
MSVC, plus packet/persistence integration contracts. Ten definitions are toggled
both directions from three carried/equipped locations; state, metadata, offhand,
augment, invalid-slot, replay, database-error and publication-error paths are covered.
The emitted production SQL runs through 39 checks: successful transitions, replay,
each saved-field drift and legacy NULL metadata. By default this uses SQLite;
`NIGHTCAP_GRIP_DB_TEST=1` with PyMySQL uses a temporary session-local MariaDB table
created from the actual inventory schema. No player rows are read or written.

`local-content.json` records a read-only local content check, not a production
probe. `tools/build_paladin_grip_candidate.py` verifies the retained deployed
bazaar source manifest and touched-file preimages, builds isolated zone/world/
shared_memory targets, and records `native-build.json` only on success. It does
not install, restart, migrate, or publish. The complete zone/world/shared_memory
build passed; final source and binary hashes are in `native-build.json`. Focused
native/SQL tests, related regressions and independent review passed. See `QA.md`
for the still-pending native client and owner game checks.

No SQL migration, cache format/layout, rules, quest scripts or client files change.
Release uses the reviewed rebuilt native binaries with the then-current unchanged
item cache, quests and signed RoF2 client. Do not overwrite newer source or deploy
an older candidate over a later release. Quest/rule reload alone is insufficient;
use the supported whole-runtime release procedure, never kill a production zone.
Fresh backup and release preimages still belong to authorized deployment.

For rollback retain grip-aware native code and earned metadata until all 1HS
instances have been safely handled. An old binary ignores the grip key and could
load 2HS beside an equipped shield; a blind binary rollback is not supported.
Never restore an old player snapshot or clear unrelated custom data.

October26 coordination: the owner authorized the Bazaar chat to push its paired
release to server/main for QA and coordinate these weapon conversions. That chat
(01a16f3a-3aa6-7e12-877d-5718a276f184) owns the combined promotion, integrated build,
server/client and wiki release. This candidate has performed no production writes.
Preserve this isolated build manifest and binaries before adding the merged Bazaar
delta; retain both source changes. Actual native gameplay acceptance remains open.
