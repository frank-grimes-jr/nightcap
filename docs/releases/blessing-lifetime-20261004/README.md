# Blessing lifetime repair — October 4, 2026

The owner retested the October 3 reconnect repair and still lost both run speed
and visible stats shortly after checking inventory. Restoring a native effect
slot was insufficient: the next client tick could expire it. The current server
image and native hashes were verified, excluding a stale deployment. Inventory
opening is an observation, not an established cause.

## Root cause and implementation

The pinned original RoF2 executable's tick routine at 0x43caff checks duration
zero, then -1. It marks -1 expired unless the spell's duration formula is 50
(DF_Permanent). Matron's normal spell definitions have finite formulas, so the
server's conversion of policy sentinel -1000 to -1 removed their native effects
on the next tick. Icons have separate storage and could remain visible.
AddBuff marks policy-permanent buffs UpdateClient; BuffProcess later sends the
duration through the same OP_Buff helper. Thus the old deferred update could
remove effects shortly after a fresh hail, independently of logout or inventory.

Client::BuffEffectDurationForClient preserves -1000 for RoF2 native player
profile and OP_Buff effect state. The client neither expires nor decrements it
in this tick path. Icon, inspect and pet-window countdowns continue using -1.
Other negative values, finite durations and older clients retain their existing
encoding. The October 3 mode-3 restoration remains necessary for missing native
slots. No recast, payment, renewal, spell-file edit or database migration occurs.

The earlier formula probe exercised effect arithmetic, not tick expiry. Its
conclusion could not exclude a duration fault. This follow-up adds the missing
native lifetime regression instead of changing spells to a long positive timer
or periodically granting blessings again.

## Verification

- The server packet regression failed on the old -1 encoding and passes with
  the actual new helper. Profile integration, ordinary updates, sparse slots,
  counters, repeat restoration and older-client controls pass.
- The exact native x86 expiry and decrement bytes are executed from original
  eqgame.exe SHA-256
  `2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e`.
  The standalone probe reads the executable; it does not modify or launch it.
  Finite-formula -1 reproduces expiry, while policy -1000 survives repeated ticks;
  natural permanent and ordinary positive expiry controls are included.
- Existing permanent-buff/death/DoT policy tests pass. The native packet probe
  covers preservation of -1000 through mode-3 copies and ordinary update/fade.
- Independent review found no blocking issue in the narrow native/icon split.
  This is not a complete client login or visible gameplay acceptance test.

Native results: [lifetime](native-lifetime.txt), [packet restoration](native-restore.txt).
Commands: `python -m unittest discover -s tools/tests -p test_buff_restore.py -v`,
`python -m unittest discover -s tools/tests -p test_gameplay_policies.py -v`,
and `python tools/tests/probe_rof2_buff_lifetime.py --repo . --client <eqgame.exe> --out <scratch>`.
Use the same arguments for `probe_rof2_buff_restore.py`. Seven rollout failure tests
pass with `python docs/releases/blessing-lifetime-20261004/ops/test_rollout.py -v`.

A fresh paired hardened world/zone build passed over the preserved October 3
production source, with exactly three changed files. Source fingerprints stayed
identical across compilation and the baseline was unchanged. Existing compiler
warnings remain. [Build provenance and binary hashes](build.json). Deployment
verification will be recorded after activation. The owner's October 3 main/server instruction
authorizes this follow-up; manual acceptance remains open.

## Exact live QA

1. In East Commonlands, hail Matron Restora (999237). Record max HP/AC, run speed
   and resting regeneration before and after. Leave inventory closed for at
   least 30 seconds, then open/close it repeatedly and wait another 30 seconds.
   Both actual effects and icons must persist without a second hail.
2. Camp to character select and return without hailing. Wait 30 seconds, inspect
   inventory/stats and run. Repeat after fully closing/reopening the game and
   after zoning out and back. Bonuses must remain stable, with no duplicates.
3. Check below level 10, 10–19, 20–29, 30–39 and 40+ when available. Stacking
   may leave four active buffs from five requested spells; that is separate.
4. Pay Magus Goldwind (999238) once for his bundle and scholar spell 21030.
   Repeat the same delay/inventory/relog/zone sequence without another payment.
   Verify XP on equivalent kills under controlled level/group/bonus conditions.
5. Click off a blessing and relog: it stays absent. Death still clears beneficial
   buffs under current policy. Ordinary finite detrimental effects still expire;
   partially consumed rune/hit-limited buffs must not refill on reconnect.
6. Repeat with the Plane of Knowledge counterparts if used. All results remain
   pending until observed; process health and native probes do not substitute.

## Deployment and rollback

Only world/zone change over the receipt-aware October 3 image. Capture current
production service/public-file identities, validate hardening and native feature
contracts, close the gateway, stop game cleanly, fingerprint saved player/rule/
receipt/corpse data locally on the server, start the new pair and verify running
hashes, healthy processes and unchanged data before reopening. Preserve current
helmet client release 2026100402, Camil, tunnel layout, quests and player progress.

Rollback uses the exact previous receipt-aware image after closing access;
never restore the database or downgrade to pre-receipt binaries. A rollback
restores the known tick-expiry bug. The rollout fault tests cover start/health/
gateway failure, channel drift and data drift; unexplained data drift holds
access closed. No raw hosted player rows enter the committed evidence.

## Preflight stopped on a pre-existing restart

The first staged archive did not activate: preflight found the old game service
had automatically restarted at 17:00:23 UTC, after one native child exited.
Its image, binaries and public release were unchanged; it was healthy with no
OOM, segfault, assertion, quest or SQL matches in the diagnostic window.
The specific exiting child is not established by this summary.
[Read-only diagnostic](preexisting-restart.json).

The refreshed baseline pins that exact startup identity and restart count.
Only preflight accepts the explicitly captured prior count; the new deployment,
rollback and report still require zero restarts. A seventh fault test rejects
an unapproved or additional restart. The original failed stage is retained and
the fresh package uses a separate r2 directory. No service was stopped by the
failed preflight. This existing runtime-exit observation is separate from the
client duration bug and is not claimed fixed by the blessing change.
