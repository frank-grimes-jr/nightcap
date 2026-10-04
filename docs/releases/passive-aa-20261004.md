# Passive AA experience candidate — October 4, 2026

Status: implemented on `feature/passive-aa-experience`; not deployed or promoted
to main. No PEQ writes, installed binary changes, service restarts or client edits.
The managed worktree was based on fetched main `f44047f`, not the older local main.

## Player behavior

| Allocation | Level XP | AA XP |
|---|---|---|
| Off / 0% | Existing full leveling award | 1% of the full AA award, rounded down |
| On / 100% | None from an eligible award | Full AA award, without a passive bonus |

`#aaexp on` and `#aaexp off` work below RoF2's native toggle level. Numeric
1–100 requests become 100%; 0 turns focus off. Invalid command tokens are rejected;
invalid packet/profile values fail off. Saved partial allocations normalize on
login and save through the existing profile path. Below `Character:AAExpMinLevel`
or at the unused-AA bank cap, focus turns off before the next award is split.

`AA:PassiveExpPercent=1` is the compiled default; 0 disables passive awards only.
The rule clamps to 0–100. Both raw XP and percentage-of-level quests/tasks qualify,
as do solo/group/raid kills through AddEXP. Resurrection and non-progression
sources do not receive passive awards. Direct SetEXP/AA grants are not multiplied.
At the level cap, off still earns the small passive amount; focused earning remains
available. Existing earned AAs and eligibility/purchase/rank policies are retained.

AA acceleration and the per-award cap apply before the passive percentage. Bank
room is enforced before point conversion, without deleting existing over-cap
points or partial XP. XP disablement applies to both reward APIs. Percentage
rewards preserve their original level-XP calculation and use separate AA modifiers;
they do not take raw kill/zone multipliers a second time.

## Calibration

Read-only local PEQ observation: minimum AA level 1, AA XP/point 50,000, normal
XP multiplier 0.65, AA multiplier approximately 0.65, modern acceleration and
normalized AA disabled, final multiplier 1, both AA caps disabled.
This is local tuning, not a claim about current OVH rules.

With matching level/AA multipliers, no XP cap/penalty and kills only, the native
curve requires 164,708,608 level XP to reach 50: approximately 32.94 passive AAs
at 1%, before per-award rounding. 5% would be about 164.71. Quest mix, zone/character
modifiers, leadership, deaths, and rounding change the result. Tiny awards have
no guaranteed minimum: typical level-1 kills round to zero; stronger kills or
larger quest rewards begin accumulating AA. This avoids a minimum-award farm.

Validate actual progression with legal Warrior/Cleric/Wizard, melee-focused and
pet-focused multiclass builds at levels 10, 30 and 50. Record level XP, AA XP/points,
legal ranks purchased, kills/hour, time-to-kill, mana/HP recovery and deaths on the
same encounters before/after. Do not add unrestricted AAs to this acceptance run.

## Automated evidence

- Native-method harness: baseline 20 failures in 32 checks; final **71/71 pass**
  under container clang++ with C++20. It extracts production XP/allocation/packet/
  command bodies and the profile-load assignment. World/transport/SetEXP boundaries
  are faked; it does not prove real persistence, client rendering or quest events.
- **Eight full translation units compile** using configured server flags and an
  isolated source overlay: exp, client, client_packet, aa, zonedb, aa_exp,
  common/rulesys and world/main. CMake's implicit headers are included as text;
  no old precompiled header or installed object is reused. This is not a linked
  release build. See `passive-aa-20261004-build.json` for source/object hashes.
- Broader balance suite: **352 run, 347 passed, 5 failed**. All five failures are
  historical evidence document hashes; their tests and flagged documents are
  unchanged from base `f44047f`: test_aa_bulk_evidence, test_aa_class_release_evidence,
  test_aa_owned_core_evidence, test_aa_purchase_evidence, test_aa_removal_evidence.
  Do not rewrite historical expected hashes to make this feature green. Resolve
  the pre-existing evidence policy before branch promotion.
- Independent review found two related percentage-reward modifier issues; both
  were corrected and regression-tested. Final review has no actionable findings.
- Windows Strawberry g++ cannot accept C++20; native proof used the configured
  Linux clang++ instead. Initial translation-unit compilation omitted CMake's
  implicit headers; rerunning with the correct textual context passed all units.

Reproduce from this checkout in the existing build container, using an isolated
`/tmp/nightcap-passive-aa` copy (not the installed source):

```text
python3 tools/tests/test_passive_aa.py --compiler clang++
python3 compile_passive_aa.py --candidate /tmp/nightcap-passive-aa/server-mods/code
```

## Exact in-game QA (pending)

First build matching world/zone from a fresh source snapshot and activate only on
an isolated QA deployment. Preserve/recheck rule values after world startup:
minimum AA level 1, passive percent 1, XP/point 50,000, normal/AA multipliers 0.65,
final 1, normalized/modern scaling off, caps -1. Set ShowExpValues=2 for measurement;
record and later restore every QA-only rule value. Never alter the era rules.

1. Use **arena**, a disposable level-30 character, and no XP bonuses. GM-spawn
   `#spawn Passive_AA_Mob 1 30 0 10000 0 1`. Kill it through ordinary combat, not
   `#kill`. At `#aaexp off`, both normal and AA progress increase; normal XP matches
   the prior 0%-allocation baseline. Repeat with an identical spawn at `#aaexp on`:
   normal XP does not increase, and AA earns the full amount. Repeat grouped with
   two eligible characters; each receives its own share and chosen allocation.
2. At level 2 repeat with `#spawn Passive_AA_Mob 1 2 0 100 0 1`. Confirm measurable
   passive AA with allocation off. At level 1, confirm small kills can round down
   without reducing normal XP. Verify #aaexp works while the native toggle is hidden.
3. In the QA server only, copy `tools/tests/fixtures/Passive_AA_Quest.pl` to
   `quests/arena/Passive_AA_Quest.pl`, reload quests and spawn
   `#spawn Passive_AA_Quest 1 1 0 10000 0 1`. On a disposable GM (status >=200),
   say `raw`, `percent`, and `zero`, testing each at off/on. With neutral zone/level
   modifiers, raw gives approximately 6500 level XP + 65 AA XP off, versus 6500 AA
   only on. `percent` covers the same award API as percentage task rewards; zero
   changes neither total. Allow single-XP float rounding when comparing values.
4. Toggle numeric 1, 25, 99 and 100: each reports 100. Off/0 reports 0. Invalid
   `-1`, `101`, `256`, and `1.5` do not change the current command state. Test the
   native slider where visible; the next authoritative update shows only 0/100.
5. Cross an AA point threshold; check point + remainder, then zone and camp/relog.
   Both XP pools and allocation persist. Confirm real AA gain events/client updates.
   On a disposable offline profile with historical allocation 25, login shows 100.
6. On QA only, raise minimum AA level above the test character, then test both
   reward APIs: full normal XP, no new AA, previous AA preserved, allocation off.
   Restore level eligibility. Cap the disposable character's unused bank, then
   cross the cap with a large reward: no excess points, no deletion of earned
   points; next reward gives normal XP. Restore original cap before leaving QA.
7. Die/resurrect the disposable character: AA does not increase from restoration.
   Disable character XP: kills and both quest reward types change neither pool.
   Re-enable and repeat. Gray/zero-value kills do not mint normalized AA.
8. Complete the representative progression comparison above. Record actual quest/
   task IDs used for completion-path smoke tests in the acceptance log. Remove the
   QA fixture and despawn its synthetic NPCs; do not publish them to production.

## Rollout and rollback (not executed)

Keep this feature candidate pending the recorded gates; do not merge into main
without owner QA sign-off. For rollout, build every required runtime binary from
one fresh pinned source tree; at minimum world and zone must share the new rule
catalog. Preserve current production image, hashes and rule preimages, then verify
the new rule and minimum level survive startup. OVH start.py restarts the whole
runtime when a child exits: use the established coordinated deployment procedure.

No schema migration or existing-character bulk update is required. To disable
passive earning on matching binaries, set PassiveExpPercent=0 and reload rules.
Binary rollback restores the previous matched image/rule preimage; keep all earned
AA progress. Already-normalized saved allocations remain 0/100 after rollback;
do not mass-rewrite player choices. Client assets are unchanged.
