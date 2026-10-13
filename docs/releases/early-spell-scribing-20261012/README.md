# Early spell scribing — October 12, 2026

Implementation candidate; not deployed or accepted in game. Players can scribe
scrolls for any of their currently selected classes at any level. Memorizing a
spell gem and casting from that gem still require the lowest original spell
level among the held classes. This reduces repeated hub visits without granting
earlier combat power, free spells, extra spellbook capacity, or discipline access.

## Behavior and implementation

- `Client::OPMemorizeSpell` in `zone/client_process.cpp` requires canonical held
  ownership for both scribing and memorization; only scribing skips the level
  comparison. Unknown and unowned spells fail even at level 255 and with
  `Character:RestrictSpellScribing` disabled. Cursor identity/consumption and
  ordinary item restrictions remain in their existing paths.
- `Client::MemorizeSpellFromItem` in `zone/effects.cpp` is another scribing path,
  despite its name. It skips only the level comparison, preserving ownership,
  duplicate/full-book checks and scroll returns on those failures.
- RoF2 `ScribeSpellLevelHook` returns level 1 for a canonically owned spell only
  at the spellbook scribing comparison, RVA `0x35E084`. Missing/stale identity,
  unknown/unowned spells and unexpected class queries return 255. Its required
  hook and exact original bytes are included in the generated patch catalog.
- The shared spell-level accessor, inspection, merchant display, selection-menu
  labels/order, memorization, and server gem-cast recheck retain canonical levels.
  The native scribe path's following class-eligibility check at `0x35E0BE` remains
  intact. [Read-only native audit](native-scribing-audit.txt) records the pinned
  executable and call context; no installed executable was patched.

This changes no DB rows, rules, quests, original spell catalog, item definitions,
or character snapshots. Existing bulk quest/GM scribe APIs retain their explicit
caller-supplied level ranges. Releasing a class removes current access; saved
spellbook knowledge is not itself permission to memorize or cast.

## Verification

The baseline compiled regression failed at the first level-1 scribe of Summon
Waterstone (spell 4, Magician 17); the candidate passes. Actual server methods
are compiled and executed by `tools/tests/test_early_spell_scribing.py`. Coverage
includes each held-class slot, level 16/17, class release, unowned/unknown/invalid
spells, missing/mismatched scrolls, restrictions, full book, duplicate knowledge,
and an unscribed memorization request. The existing two multiclass access tests
pass, including the actual gem-cast handler and every original class-level entry.

The x86 proxy and all runtime fixture binaries build. The five runtime tests
pass, including class state, spell access/inspection/menu behavior, startup
fail-closed behavior and patch-failure injection. Exact executable verification
and generated launcher/proxy agreement pass for all 76 sites. The UI hook fixture
also executes the native scribing-level comparison with old and new accessors.

The complete zone links successfully against the fingerprinted retained
sell-all release. Both modified translation units are rebuilt; retained source,
objects, libraries and baseline zone are verified unchanged. `ldd` resolves all
dependencies. Candidate zone SHA-256:
`43d7c1edea922bb268b8cb5eac7492bbb09a8919bccf2328051b2fd7e35b0463`.
Build recipe: [build_candidate.py](build_candidate.py). The isolated local Docker
output is `/tmp/nightcap-early-scribing-build-20261012/`; input and original
sources are retained. This is a build check, not a running server/DB round trip.

Independent source review found no required changes. Native gameplay and
persistence acceptance remain pending. No production rollout has occurred.
[Compact build/test fingerprints](verification.json) record the candidate.
The full launcher Go suite was unavailable because no Go executable was found;
its changed embedded catalog passed the generated-agreement check.

## Activation and recovery boundary

Requires the new zone binary and a signed client publication containing proxy
`0.8.1-dev` and its matching catalog. A rule or quest reload cannot activate it.
The world rule catalog and shared-memory ABI are unchanged. Preserve the current
production image/source and all intervening releases when packaging the zone.
Recheck live source hashes against the retained build before using this candidate.

After owner approval, use a fresh verified backup and the established closed
gateway/graceful whole-game restart procedure; do not kill one OVH zone process.
Verify current player-state/content/rule preservation, all running zone hashes
and service health before reopening access. Publish the paired client through
the signed launcher flow, preserving all current assets/preferences. Close EQ
and use launcher Play to receive it. An old client still blocks early scribing;
a new client with an old server will have its early scribe request rejected.

Rollback selects the retained prior image after a graceful stop and publishes
prior client contents in a higher-numbered signed release. Preserve current
player data and already scribed books; do not restore pre-release player snapshots.
Original level checks continue to protect gem use after rollback.

## Exact owner in-game QA

1. Update through launcher Play, then log into East Commonlands with a level-1
   Cleric/Magician/Necromancer. Obtain an ordinary Summon Waterstone scroll
   (spell 4, Magician 17) from the class hub. Record inventory quantity.
2. Scribe it using the normal cursor-to-spellbook flow. It must enter the book
   and consume exactly one scroll despite being above level. Repeat with eligible
   spells from the primary and third selected classes, and ordinary scroll
   right-click behavior where supported. No free spell grant is expected.
3. Attempt to memorize Summon Waterstone from the book and gem selection menu,
   including a saved spell set. Below level 17 it must not occupy a gem. Menu and
   inspection must still display its real level 17. Other usable gems still work.
4. Zone and relog: the newly scribed spell remains in the book, still unusable.
   At level 16 it remains blocked. At level 17 memorize it without returning to
   the hub or buying another scroll, then cast with sufficient mana/resources.
5. On a disposable QA character, release Magician. Scribing another Magician-only
   spell and memorizing/casting the retained one must fail. A different character
   with no Magician must fail to scribe that scroll and retain it. Shared spells
   must use the lowest requirement among the classes still held.
6. Check duplicate/full-book handling, login immediately before class metadata
   arrives, and current pet, loot and merchant controls. Record actual observed
   behavior separately from automated tests and deployment authorization.
