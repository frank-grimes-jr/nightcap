# Equipment client candidate QA - September 15, 2026

This is historical QA for the original permissive submission hook. Its all-class
bypass is superseded by the [October 15 held-class correction](../../docs/releases/multiclass-equipment-20261015/README.md),
which also covers cursor placement and inspection colors. Use that release's
verification and QA for the current candidate; publication remains pending.

Status: built/reviewed candidate; not deployed or manually accepted. #13 remains
open. Use an isolated RoF2 client and matching Nightcap server. The development
binary client directory is read-only; release/health gates remain in #14/#15.

## Automated evidence

- `tests/run-equipment-scope-tests.bat`: x86 assertions cover all sixteen class
  bits, identity, flags, zero/high masks, nested restore and thread isolation.
- `tests/verify-exact-client-patch-sites.ps1 -EqgamePath <eqgame.exe>`: actual
  executable size/SHA256, all four signatures and existing proxy regression sites.
  Source checks supplement these tests; they are not runtime proof.
- `build.bat`: x86 proxy build passes. Independent review found no blockers in
  calling conventions, SEH cleanup, scope or partial-install rollback.

## Owner in-game matrix (pending)

Set up in Plane of Knowledge using class selection, then use a safe combat zone.
Record character, race/deity, level, all held slots, item IDs, client/DLL hashes
and proxy log. Use original class-restricted items, not widened fixtures.

1. Base Warrior, Necromancer in slot 2: inspect a Necromancer-only robe legal for
   race/deity/level. Original class list stays truthful. Drag bag to chest: expect
   legal equip and correct stats. Repeat with Necromancer in slot 3 and each
   supported base class as part of the full class-slot matrix.
2. With neither slot holding Necromancer, attempt the robe: expect rejection,
   no item loss/duplication and no persistent stat gain.
3. Attempt items barred by race, deity or required level, and a legal item in a
   wrong slot. Expect rejection. Swap occupied equipment slots to exercise the
   displaced item's restrictions as well.
4. Verify ordinary armor/weapons, two-handed/shield rules, bags/cursor and
   augmented items. An unusable combination with zero class mask stays rejected.
5. Zone/camp/relog after legal off-base equip; verify equipment, stats and combat
   bonuses. Release the owning secondary class and check server equipment cleanup
   or validation behavior; record any mismatch.
6. Repeat with MQ enabled/disabled in the candidate setup. Capture `G013 equip
   submission APPLIED`. Isolated unsupported-executable/conflicting-site startup
   tests must disable this patch without partial widening.

#13 also includes caster/spell/combat UI requirements: equipment success alone
is insufficient for closure. Full acceptance and runtime patch health are pending.
