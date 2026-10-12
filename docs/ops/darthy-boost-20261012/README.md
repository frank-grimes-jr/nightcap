# Durable character boosts — October 12, 2026

Status: tested release candidate; main promotion, production activation and owner
in-game acceptance remain pending. Production Darthy is still level 10. No live
character writes or game restarts were performed during development.

## Incident and accepted behavior

The production GM receipt `452dca9b-51b8-46b1-b2e3-2b1adfb814ab` records Darthy's
level-50 boost on October 11 at 13:44:17 UTC. The route set `level=50,level2=50,exp=0`.
The October 12 native events record 50→8 at 15:02:06 UTC and 8→10 at 15:02:23 UTC.
Native SetEXP derives level from cumulative XP on every award; login loaded the
stored level without repairing that contradiction. Saved pets were unaffected by
the level change, and pet orders do not revalidate summon level.

Every accepted boost must persist a coherent level/XP pair in one transaction,
remain valid at the next ordinary XP award and saved-profile load, respect legal
caps, retain valid same-level progress, preserve the highest attained level, and
award training points only for newly reached lifetime levels. Boosts do not freeze
normal advancement or bypass ordinary death XP loss. Existing maintenance,
backup, fencing, exactly-once receipts and target isolation remain mandatory.

`character-level.cjs` reproduces native GetEXPForLevel with float32 rounding at
each native boundary, including enabled racial/class penalties. Award multipliers
do not affect thresholds. Level 50 starts at **164,708,608 XP** (not the rounded
164,708,600 mathematical approximation). The route uses default-rule inheritance
and active overrides; it distinguishes the administrative cap from native
MaxExpLevel. A cap permits its native full XP bar; ordinary levels do not.

Before mutation, every defined ruleset referenced by a zone must yield the same
XP interval and permit the target level. Conflicts are rejected, not silently
changed. Native uint32 XP overflows and enabled per-character quest/bucket cap
modes are rejected before writes. The UI's input ceiling of 125 does not imply the
native 32-bit XP curve supports every race/class configuration through 125.
Supporting higher overflowing levels requires a separate native/profile change.

This is the current native formula contract. Read-only inspection found no
GetEXPForLevel/SetEXP Lua override in deployed quests, plugins or mods. Introducing
such a hook or changing the native formula requires updating this adapter and
parity test before enabling offline boosts. Source parity alone is not proof of
an arbitrarily modified future running binary. Skills are seeded by the existing
native ReconcileMulticlassSkills on zone entry; the boost does not max skills or
grant spells, AAs, currency, equipment or pet power.

## Verification and review

- Real disposable MariaDB/HTTP regression first reproduced zero XP, erased
  highest level, missing training points, cap inheritance and overflow failures.
- Three further failures reproduced incompatible zone curves/caps and the
  MaxLevel versus MaxExpLevel full-bar boundary before review corrections.
- Final GM suite result is recorded in `verification.json`; no database tests
  were skipped. It includes failed backup, transaction rollback, lease loss,
  receipt retry, target isolation and the guarded Darthy repair.
- Extracted complete native GetEXPForLevel and SetEXP bodies agree with JS across
  129,024 threshold cases; 110,774 profiles retain valid levels after awards and
  decimal serialization/reload. Overflow cases reject. Both tracked server overlay
  and local native checkout passed. The exact repaired Darthy XP is also tested.
- Vue typecheck and build, six maintenance helper tests and twelve Chrome cases
  pass. Browser tests use fixtures; no player mutation was used as a UI test.
- Independent review found and resolved zone-profile and native-cap issues;
  final implementation approved. Native packet/world/quest boundaries are fakes:
  actual RoF2 reconnect, display and kill acceptance remain explicitly pending.

Run from `eq-solo-gm/`: `npm test` with the disposable `GM_FIXTURE_HOST`,
`npm run typecheck`, `npm run build`, `npm run test:browser`.
From repo root: `python tools/tests/test_boost_xp.py --compiler g++`.
Fixture lifecycle and SSH setup: `../production-gm-20261010.md`.

## Darthy's prepared repair

Original backup `private/gm-backups/20261011T134416.705900Z.sql.gz` proves ID24 was
level5, highest5, XP108257 and training points25 before the faulty boost. Current
guarded preimage is level10, highest50, XP883418 and training points25; base race12,
class11. The faulty boost discarded old XP; 883418 is earned since that reset.

`repair.cjs` restores level50/highest50, **165,592,026 XP** (native floor plus
883418 retained earned XP), and **250 training points** (25 current plus the
omitted 45×5 points). It verifies every unrelated character column unchanged.
Pets, AAs, items, skills and currency are not written. It refuses any preimage
drift instead of overwriting activity. Its fixed receipt makes retries return
the original result without repeating the 225-point credit.

## Activation and scoped recovery

1. Obtain owner sign-off for test→main and activation. Merge the reviewed commit
   into main, fetch it in the owner-local GM checkout and inspect for local edits.
   The normal startup gate and repair apply gate both require HEAD on origin/main.
2. Run `node docs/ops/darthy-boost-20261012/repair.cjs --inspect`. Confirm ID24
   and the captured state. If drifted, stop and regenerate the exact repair from
   fresh evidence; never weaken the predicate. A new correction requires a new
   operation receipt, not a retry with altered payload.
3. Start the reviewed GM with `tools/start-gm.ps1 -EnableProductionWrites`.
   Announce the brief full-game disconnect and enter Production maintenance using
   the existing GM controls. The whole supervised game and gateway must stop.
4. Run the repair with `--apply`. It takes a fresh character_data backup under
   the existing private GM backup path, obtains the shared DB fence and SSH lease,
   and commits the state and receipt atomically. Preserve the receipt/backup name.
5. Inspect the receipt and fresh character row; verify the three saved pets still
   have spell IDs495/635/690. Resume with the GM, verify game/gateway health and
   use the exact in-game QA below. Preserve the latest item-upgrade release.

Rollback of the GM tool means stop its owner-local process and return to the
previous code in production-read-only mode; never reopen the broken boost route
for writes. Do not revert Darthy to the corrupt XP pair as a code rollback.
Before any data reversal, enter maintenance and inspect current receipt/player
activity. Restore only explicitly selected progression fields from the fresh
repair backup if the current row still exactly matches the repair postimage.
Never restore a whole character_data table over unrelated player progress.
If a write response is ambiguous, query the fixed receipt first; do not retry
with a new request ID or reopen access over an uncertain in-flight transaction.

## Exact owner in-game QA for test promotion

1. Log Darthy into East Commonlands (ecommons, zone22); he may currently be saved
   in Ocean of Tears (oot, zone69). Confirm level50 and the expected partial XP
   bar before fighting. Verify Cackling Bones, Greater Conjuration: Air and
   Kintaz's Animation pets still respond normally. No new summons are required.
2. Kill two XP-awarding NPCs in Ocean of Tears: appropriate-level seafury cyclops
   are candidates; verify each actually awards XP. Confirm neither award drops
   the level and AA allocation does not break it. Record NPC names and XP text.
3. Camp fully, log back in, then zone to East Commonlands. Confirm level50,
   XP, training points, ordinary spell access and pet commands persist.
4. In an isolated test environment, use a disposable character. Boost successively
   to levels10,30,31,45,46,49,50 under the Classic cap. At each level, obtain an
   actual non-gray kill or explicit native XP award, camp/relog and verify the
   level/XP. At49 verify earned XP can advance normally to50; at50 verify the cap.
5. Repeat the same-level boost after earning partial XP: XP must remain. Check
   trainer points before/after a new highest level, repeat and lower/reboost:
   only first attainment credits points. Test a failed/cancelled action and a
   lost response/retried receipt: no double credit or partial character change.

This repair addresses invalid boosts. A general pet-discipline policy after
legitimate deleveling is a separate gameplay decision; no blanket pet removal
or new summon-level policy is introduced here.
