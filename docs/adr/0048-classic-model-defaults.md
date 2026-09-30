# 0048: Classic model defaults with a manual client opt-in

Status: implemented candidate; graphical acceptance and publication pending (2026-09-30)

The owner requests old EverQuest models for every Nightcap player, including
magician pets, skeletons and spectres. Modern visuals require a deliberate INI
edit. Existing Luclin settings carried over from another server must not silently
opt a player in.

## Decision

Apply the policy in the required, signed Nightcap client proxy before RoF2 starts.
Read `[Nightcap] UseModernModels=TRUE` from the game folder's `eqclient.ini` once
at process startup. An absent or unrecognized value selects classic models.
Keep user INIs outside the signed asset inventory and preserve their contents.

The implementation must cover three distinct native paths: player/Luclin INI
reads, model archive loading, and the race-to-actor lookup for later remakes.
Server races and combat data are not appearance settings: changing them would
also affect gameplay and would prevent a per-client visual opt-in.

Use reviewed classic assets from read-only client inputs. Original skeleton
textures collide with newer DDS textures in equipment/model archives; simply
changing the elemental option or removing one archive is insufficient evidence.
Record exact input/output hashes and the supported race/model mapping.

## Acceptance

- Fresh and existing clients default to classic visuals despite pre-existing
  `UseLuclin*=TRUE` options.
- All four magician elements, every skeleton variant used by the server,
  spectres, and other remakes of original creatures use old models by default.
- A manual INI opt-in takes effect after a full client restart and survives
  launcher repair/update. The default returns when that opt-in is removed.
- User settings, server race identity, pet behavior, stats and combat remain
  intact. Missing assets or unsupported native signatures cannot silently pass
  required startup checks.
- Verify native x86 calling conventions, signed patch catalog agreement,
  installation/update behavior and the rendered creature matrix. Owner in-game
  acceptance remains required before default-policy main promotion.

## Evidence and implementation plan

Read-only inspection of pinned RoF2 (`2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e`):
`AllLuclinPcModelsOff` is separate from `UseLuclinElementals`; global6 includes
new SKE/WOL/WOE actors; global contains old SKE/ELE and global4 contains old SPE.
`gequip5.s3d` also contains conflicting skeleton DDS textures.

`classic-models.json` pins 18 input archives. Four additional global archive
clones preserve earth (0), fire (1), water (2), and air (3) palettes when a modern
race ID encodes the element. All actor/texture prefixes use unique three-letter
aliases; mesh data, fragment indices, bone suffixes and animation data retain
their original bytes. Inverse WLD transforms verify exact restoration.

The native registry hook registers aliases for 144 race/gender pairs so reverse
lookups remain meaningful. The lookup hook maps 98 later race IDs to original
counterparts and normalizes unsupported old genders. Race data on the server is
unchanged. Later Human, Ogre and Erudite NPCs use the native original player
registry, preserving armor handling. Scaled wolf uses race 42, gender 1 (WOF).
Stock global imports remain in the generated import list.

The opt-in permits native preferences; users can retain old player models while
opting into modern NPCs. Removing it restores classic defaults. Creatures and
playable races with no original model keep their existing model. The owner
explicitly confirmed this rule on September 30: "Races without old models use
existing." The candidate already implements this fallback. The
[scope audit](../releases/classic-models-20260930/scope-audit.md) records the
native lookup scope and remaining visual acceptance.

See [release QA](../releases/classic-models-20260930/QA.md) for checks, evidence,
manual acceptance and rollback. Production publication remains pending.

Format reference: [EQEmu Client Race Inventory](https://docs.eqemu.dev/server/npc/client-race-inventory/).
