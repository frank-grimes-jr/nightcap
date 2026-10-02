# Blessing reconnect repair candidate — October 2, 2026

## Intent and diagnosis

Matron Restora and Magus Goldwind buffs should retain their effects across camp,
full logout and zoning, without another hail or payment. The owner reports that
icons survive and re-hailing Matron immediately restores the lost speed/stats.
This is a candidate, not a deployed or manually accepted repair.

The native server diagnostic grants the actual bracket spells at levels 1, 10,
20, 30, 40 and 50, calls SaveBuffs, clears all buffs, calls LoadBuffs and recalculates
bonuses. All six cases retain their bonuses. At level 50, max HP/AC/run speed are
1815/121/43 after both granting and reloading, versus 1565/103/28 before granting.
The diagnostic used the pinned September 30 enchanter build, real local MariaDB,
a guarded unused character ID and rolled-back transactions; it reuses one Client
object and mocks network transport. This excludes a basic persistence/bonus
calculation failure in that fixture, not every production login failure.
[Anonymous results](server-roundtrip.json).

The pinned RoF2 native OP_Buff handler distinguishes icons from active effects.
Mode 2 updates an existing matching effect; it cannot populate an empty effect
slot. Mode 3 installs the specified slot and refreshes effects. The old encoder
mapped every non-fade mode to 2. The new regression executes the original
handler bytes with isolated slot/refresh dependencies: the old translation fails
to restore a missing native effect, while the new translation passes 240 cases
across every blessing spell ID, sparse slots, finite/permanent durations and
repeated restores. Ordinary update and removal controls pass.
[Before](client-before.txt) / [after](client-after.txt).

This proves the recovery packet behavior. It does not reproduce the entire
login/profile path or identify exactly where the client loses its initial effects.
Native formula probes found no support for blaming negative durations; permanent
buff policy and its -1000 server/-1 client sentinels remain unchanged.

## Implementation and alternatives

After CLIENT_CONNECTED and the queued login packets have been sent,
CompleteConnect restores each valid RoF2 player buff through OP_Buff mode 3.
The packet uses the authoritative current slot, caster level, instrument modifier,
remaining duration, hit count, caster ID and cast coordinates. Counter/rune
selection stays the same as existing duration updates; the RoF2 restore writes
the first slot_data counter, matching the existing profile representation.
No casting, resource consumption, quest callbacks, saved-buff edits or duration
refresh occurs. All currently valid player buffs are restored; pets and older
clients do not use this path. Existing multi-effect counter encoding limitations
are not expanded into a new serialization model here and need the rune QA below.

Alternatives considered:

- Recast blessings on login: easy to apply, but refreshes charges/durations and
  repeats spell side effects; rejected.
- Change permanent durations to a positive timer: native formula evidence does
  not support this diagnosis and it changes the owner's permanent-buff policy.
- Explicitly restore saved effect slots after client-ready: chosen because it
  repairs missing native state without granting or renewing a spell.

## Verification and limitations

- `python -m unittest discover -s tools/tests -p test_buff_restore.py -v`:
  compiles the actual server methods; tests empty/invalid/sparse slots, repeat
  sends, saved fields, runes, ordinary updates, older clients and ready ordering.
- `python -m unittest discover -s tools/tests -p test_gameplay_policies.py -v`:
  existing permanent duration, death, DoT and policy integration checks.
- `python tools/tests/probe_rof2_buff_restore.py --repo . --client <original
  eqgame.exe> --out <scratch-directory>`: MSVC x86, original executable SHA-256
  `2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e`.
  Reads bytes only; never launches or modifies the installed game.
- Fresh matching world/zone build over the preserved hardened October 2 advanced
  loot action source passed. Exactly four source files changed; source hashes were
  verified before and after compilation, and the preserved production baseline
  was unchanged. [Build and binary hashes](build.json). Existing compiler warnings
  remain. Binaries are built locally, not installed. No production diagnostics or
  changes were performed by this candidate work.

The added regression covers missing native state rather than the whole reported
login. Actual run speed, regeneration, XP gain and profile timing need owner QA.

## Exact in-game QA before main promotion

1. In East Commonlands, use Matron Restora (999237). Record unbuffed max HP, AC,
   run speed and resting HP/mana regeneration on a normal character. Hail, then
   record the increases and buff names. Test representative brackets below 10,
   10–19, 20–29, 30–39 and 40+. Spell stacking may leave four active buffs from
   five requested spells; do not require mutually exclusive lines to coexist.
2. Camp to character selection, log back into the same character, and check the
   same values before hailing anyone. Icons and actual increases must agree.
   Repeat after closing the client completely and reopening through the launcher.
3. Zone out of and back into East Commonlands, then relog twice more. Effects
   must remain stable, without duplicate icons or increasing bonuses.
4. Pay Magus Goldwind (999238) 100pp once. Record the blessing bundle and scholar
   spell 21030. Repeat camp/full logout/zoning without paying again; the bundle
   and XP modifier must remain. Verify XP with equivalent eligible kills and
   controlled group/level/bonus conditions, not only the icon or tooltip.
5. Click off one blessing and relog: it must stay absent. Die and return: the
   current beneficial-buffs-clear-on-death policy must remain in force.
6. Carry a finite detrimental effect and a partially consumed rune/hit-limited
   buff across zoning and relog. Check remaining duration, charges and absorption
   against server behavior; reconnect must not refresh them. Exercise short/song
   and discipline slots if used. Verify fresh casting and dispelling still work.
7. Repeat a grant/relog using the Matron/Magus counterparts in Plane of Knowledge
   if those services are used. No class/gear/AA changes should occur.

## Rollout and rollback

Default branch flow remains feature → dev → test → owner QA → main. This report
does not authorize main promotion or production deployment. Activation requires
current-production drift checks, the matching hardened world/zone pair, a closed
gateway during restart and running executable hash verification. Recheck recent
loot receipt and other feature contracts before rollout; never deploy the older
diagnostic build. No database migration, spell-file update or client patch is
needed. Keep the previous receipt-aware pair/image for rollback, stop access and
restart with that exact pair if login or buff regressions appear. Do not restore
the database or erase saved buffs/player progress. A rollback returns to the
reported reconnect behavior; re-hailing remains the observed workaround.

## Candidate review

Author review covered reconnect ordering, RoF2-only scope, slot translation,
duration/counter preservation, legacy call sites, buffer initialization and
absence of state mutation. Independent model review found no concrete blocker;
it verified ready ordering, slot translation, mode compatibility and the native
test's copy/refresh behavior, while retaining full-login and rune/charge QA gates.
Privacy review confirmed committed evidence has only anonymous fixture values
and hashes. No human or gameplay approval is claimed; the production gate remains
open.
