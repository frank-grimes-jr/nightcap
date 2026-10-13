# Early spell scribing — October 12, 2026

Owner-approved PR #185 is on main and deployed to OVH on October 12
(October 13 UTC), paired with signed client release **2026101203**. Native
in-game acceptance remains pending. Players can scribe
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

Independent source, deployment and publisher reviews have no remaining required
findings. The full launcher Go suite passes; package/manifest/launcher tests
were rerun after integration with the newly shipped patch-history feature.
Nine native recovery tests and twelve publisher recovery tests pass.
[Compact verification](verification.json) separates automated/live deployment
evidence from pending owner gameplay and persistence acceptance.

## Production activation and recovery

The owner explicitly approved main and server publication. Native activation
uses `/opt/nightcap/releases/early-scribing-20261012-v2`; v1 was preflight-only.
The new immutable image is
`sha256:058330bce1e2539612d705b95b726d5143daa7ca5e6897debe0f598ba470558f`.
It layers only zone onto the retained live image
`sha256:4c0f464d64b6eb5dc787aaff380f4fbee41f2de8365e2622cb5fcc11cb940541`;
world, loginserver, UCS and shared-memory binaries remain byte-identical.

A fresh verified gzip SQL backup preceded a closed-gateway graceful whole-game
restart. All 12 running zone hashes match, 47 player tables and 11 custom tables
passed stopped-state preservation checks, and rules/content/runtime files and
supporting DB/web/tunnel services were preserved. Access reopened with zero
restarts and no detected native/quest/database errors. No SQL was restored.
[Server receipt](server-receipt.json) records the backup and runtime evidence.

During preparation, another authorized release published launcher 0.6.0 and
game metadata 2026101202. The prepublication baseline check detected this.
This release advanced to **2026101203**, retaining its six history entries,
minimum launcher 0.6.0, desktop channel, starter ZIP and guide. A new concise
early-scribing summary is included in `eq-launcher/patch-notes.json`.
Only `dinput8.dll` (proxy 0.8.1-dev) and `nightcap-patch-sites.json` change among
the 105 game files. Publication at `/opt/nightcap/releases/early-scribing-2026101203`
validates a fresh post-restart service baseline, writes immutable assets first,
and atomically replaces the signed channel last. All five services remain
unchanged by client publication. [Publication receipt](client-receipt.json) and
[public HTTPS verification](hosted-verification.json) confirm the shipped-key
signature and every file's size/hash. The game channel expires November 12 UTC.

Close EQ and use the normal launcher Play flow to receive the paired client.
Rule/quest reloads cannot activate this native change. Old clients still block
early scribing; new clients paired with old servers have early requests rejected.

The exact reviewed native and publication operators and tests are retained under
`deployment/`. They are release-specific, baseline-guarded scripts, not reusable
instructions to rerun activation. Native checks finish before client publication
because they compare the preflight public channel. For a future recovery, obtain
fresh evidence and authorization, close the gateway, stop the whole game
gracefully and select the retained image. Preserve all subsequent player activity
and already scribed books; never restore an old SQL snapshot. If player/custom
drift detected before any access remains after image rollback, keep the gateway
closed and investigate. Once access may have opened, do not compare against an
old player snapshot. Client rollback must re-sign prior contents with a higher
release counter, preserving patch history and the notes-aware 0.6.0+ desktop.
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
