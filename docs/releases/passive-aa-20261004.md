# Passive AA experience release — October 4, 2026

Status: **deployed to main and OVH** under the owner's explicit October 4 request
"Deploy to main and server". [PR 125](https://github.com/frank-grimes-jr/nightcap/pull/125) merged as `a8304ccc`.
Image `nightcap-game:passive-aa-20261004` is healthy with the gateway open.
The exact in-game QA below remains open; deployment is not manual acceptance.
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
The read-only OVH preflight also confirms minimum AA level 1, XP/point 50,000,
normal/AA multipliers approximately 0.65, modern/normalized AA disabled and both
AA caps disabled. Its absent RuleSet variable selects the default ruleset (1).

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
  no old precompiled header or installed object is reused. See
  `passive-aa-20261004-build.json` for the original source/object hashes.
- A separate fresh release build links **world, zone, shared_memory, ucs and
  loginserver** from the fingerprinted current production source plus exactly
  the eight-file feature patch. Existing production hardening is retained.
  The login crypto self-test passes; the native-method harness also passes
  **71/71 against this exact production source**. Nine rollout failure tests
  cover successful activation, rollback and fail-closed preservation behavior.
  See [build summary](passive-aa-20261004/build-summary.json) and
  [native checks](passive-aa-20261004/native-tests.json).
- Broader balance suite: **352 run, 347 passed, 5 failed**. All five failures are
  historical evidence document hashes; their tests and flagged documents are
  unchanged from base `f44047f`: test_aa_bulk_evidence, test_aa_class_release_evidence,
  test_aa_owned_core_evidence, test_aa_purchase_evidence, test_aa_removal_evidence.
  Audit: all 72 pinned non-document artifacts match; nine Markdown reports gained
  the same September 15 deployment-status note in commit `9f6f48b`. Removing only
  that note in memory reproduces all nine original hashes. This is pre-existing
  narrative drift, not a feature regression or deployment blocker. Historical
  expectations remain unchanged; executable bytes from those old releases were
  not rehashed. [Audit](passive-aa-20261004/historical-evidence-audit.json).
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

Matching release binaries are built. Run rule-changing and synthetic-reward QA
on an isolated deployment; ordinary live smoke checks may use a disposable owner
character. Preserve/recheck rule values after world startup:
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

## Rollout and rollback (deployment verified)

The owner's explicit deployment request authorizes main promotion and OVH rollout
for this release. It does not mark the manual QA above complete. The reviewed
[transaction](passive-aa-20261004/ops/rollout.py) closes the gateway, stops the game
cleanly, records player/content fingerprints, inserts only the 1% passive rule,
and starts the matched image. It checks all runtime hashes, twelve zones, rule
preservation, player data, existing free-trade cache, quests and public client
artifacts before reopening access. A verified full PEQ backup precedes activation.
Failures roll back to the previous free-trade image and remove only this release's
owned rule, without restoring or rewriting player data. OVH start.py supervises
the whole runtime; individual process exits are not used for deployment.

No schema migration or existing-character bulk update is required. To disable
passive earning on matching binaries, set PassiveExpPercent=0 and reload rules.
Binary rollback restores the previous matched image/rule preimage; keep all earned
AA progress. Already-normalized saved allocations remain 0/100 after rollback;
do not mass-rewrite player choices. Client assets are unchanged.

## Hosted verification

All five native executables match the fresh build. World, UCS, loginserver and
twelve zone workers run without restarts or detected native/quest/SQL errors.
The default ruleset retains `AA:PassiveExpPercent=1`, `Character:AAExpMinLevel=1`,
XP/point 50,000 and all existing XP rules after startup. The absent RuleSet
variable continues to select default (1); no variable row was added.

The closed-gateway comparison preserved all 47 player/settings/receipt/rule/state
tables and five content-table checksums. Quest/plugin hashes match. All 308,961
cached items retain free trade, including 171,561 fixed NO DROP payouts. DB, web
and tunnel container identities/start times are unchanged. Public game 2026100407,
desktop 0.4.0, the friends download and guide are unchanged; no client update is
required. The full PEQ backup passed gzip and completion checks. No rollback or
database restoration was needed.

[Deployment identities, rules, hashes and backup receipt](passive-aa-20261004/deployment-summary.json).
The private backup and full preimages remain under
`/opt/nightcap/releases/passive-aa-20261004/` on OVH. The previous immutable
free-trade image remains available for rollback. Rollback preserves all earned
AA and other player progress; it never restores the old database snapshot.
