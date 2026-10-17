# Independent basic Monk cooldowns — October 17 candidate

Status: implemented and regression-tested; not deployed. Base: origin/main
`a59974d`. The owner reported Dragon Punch and Round Kick sharing a timer and
explicitly requested separate cooldowns for all six basic Monk attacks.

## Behavior and implementation

When a RoF2 character holds Monk, Kick, Round Kick, Tiger Claw, Eagle Strike,
Dragon Punch/Tail Rake and Flying Kick each have their own persistent cooldown.
Using a different attack does not consume or refresh the first attack's timer.
Repeating the same attack remains blocked until its timer expires. Skill levels,
held-class authorization, target/range/status checks, damage, haste, AA reuse
reductions and Master Wu remain unchanged. This increases available attack
frequency; combined Monk/multiclass/AA balance still needs gameplay acceptance.
Non-Monk Kick/Bash and older clients keep their existing shared timer policy.

`common/combat_ability_timer.h` maps the six skill IDs into the reserved 500–599
persistent timer range. Both `Client::OPCombatAbility` and non-riposte
`Client::DoClassAttacks` use the same mapping. Existing PTimerList load/store
handles these IDs; no schema or character-data migration is needed.

RoF2's SkillManager and EQPlayer have two shared combat timer slots. Proxy
0.9.2-dev retains separate start/duration/readiness records for the six skills.
The guarded native special-attack entry exchanges only the relevant player slot
for the duration of submission, then restores it in `__finally`. All callers,
including native ability controls, use that entry. The stock post-submit commit
must retain the captured per-skill timestamp rather than overwrite it with the
restored shared slot. Native haste calculation, target/animation/packet behavior
and skill-button expiry callbacks remain in place. Leaving in-game state clears
the transient client records; persistent server timers still enforce reuse.

Source: `server-mods/code/zone/special_attacks.cpp`,
`server-mods/code/common/{combat_ability_timer,ptimer}.h`, and
`eq-client-dll/src/{monk_reuse,ui_hooks}.h` / `dllmain.cpp`.

## Verification

- Server reproduction: five failing scenarios before the fix, including Dragon
  Punch → Round Kick; five control scenarios passed. Current suite has 12 passing
  tests compiling the actual entry points and mapping, including 180 ordered
  cross-skill scenarios, same-skill expiry, saved timer restoration, mixed entry
  paths, eligibility/range/status checks, haste/AA adjustments and riposte.
- Exact pinned RoF2 reproduction: 10 failures among 25 checks before the fix.
  Current native fixture passes all 60 checks. It loads a read-only mapped copy
  of the pinned client, installs the real hooks, exercises the native reuse
  methods and installed submission/commit paths, and checks exception cleanup.
  Targeting/damage/time are controlled fixture boundaries, not live combat QA.
- Full x86 DLL build and all 20 runtime-test executables compile. All eight
  runtime test groups pass, including equipment, trainers, UI and patch failures.
- All 103 exact-client catalog sites verify; generated proxy/launcher catalogs
  agree. The source client and installed game were not modified.
- Independent review caught the initial hotbutton-only scope; moving it to the
  shared submitter and protecting the later native commit resolved the finding.
  The final review reports no remaining actionable findings.
- Wiki: all 21 maintained articles and 432 generated reward routes assessed;
  six articles carry explicit unreleased guidance. Fourteen Python and thirteen
  Node checks pass. Publication remains pending; broad audit ref stays unchanged.
- Full zone compilation/link is pending: local Docker's Linux-engine pipe is
  unavailable. Starting Desktop did not expose the engine. Do not label this
  release built for deployment until the zone build passes against current
  retained source.
- The full launcher Go suite passes using cached Go 1.27.2. Its loopback, Windows
  junction and credential fixtures require an unsandboxed run; initial sandbox
  permission failures were resolved by rerunning with that access.
- Legacy `test-multiclass-monk-combat.ps1` rejects both unchanged `a59974d` and
  this candidate because it pins superseded July source hashes. Its fragment
  checks pass before that guard; the new native regression is the behavioral
  proof. The historical patch guard has not been weakened.

## Build, pairing and activation boundary

Build the zone from the current fingerprinted retained production source,
preserving authentication hardening, item/loot receipts, dungeon journal and
intervening releases. Verify the old `special_attacks.cpp` and `ptimer.h` against
that baseline before layering this scoped patch. The header adds enum constants
only; no ItemData, rule catalog, shared-memory or world ABI changes are intended.
Link and validate the candidate zone; do not replace a current runtime from the
older default checkout. Server fixtures alone are not the full binary build.

Pair the rebuilt zone with proxy 0.9.2-dev and its signed patch catalog. Update
patch notes at publication using a fresh channel counter; preserve the existing
106 managed assets and all patch history. Candidate note text is in
`patch-note.json`; no published channel was edited. A client-only or server-only
update leaves one side of the shared-timer defect in place.

Rule/quest reload cannot install this C++ change. OVH native child exits restart
the whole runtime, so use a coordinated authorized release, not a zone kill.
Main promotion, runtime activation and signed-client/wiki publication require
release-specific approval under AGENTS.md's normal policy. No production writes,
SQL, game restart, installed-client change or publication occurred in this task.
Rollback uses the paired prior server/client with a higher signed client counter,
retaining player activity; never restore old player SQL. The new short-lived
persistent timer IDs can expire naturally and must not be repurposed.

## Exact in-game QA after paired release

1. Update through the launcher. On a level-30+ Monk or a character holding Monk
   as class 2/3, assign all six skills from Actions → Abilities to hotbuttons.
   Use a safe, durable practice target in a private test zone.
2. Use Dragon Punch, immediately Round Kick, then each remaining attack. Each
   should execute and cool down independently; other buttons remain ready.
   Repeat in reverse order and through the native ability controls.
3. Repeat one skill before expiry: it must not execute. After its cooldown,
   it must execute again. Alternate hotbutton and native controls for that skill.
4. Repeat with haste and an earned skill-reuse AA. Confirm duration changes
   remain correct, without resetting another skill's cooldown. Check Master Wu
   bonuses and resulting damage/attack frequency for balance.
5. Zone/relog during reuse: the server must still reject any remaining active
   cooldown. Client transient display reset is not a cooldown refund.
6. Check insufficient level/skill, invalid or distant target, stun and fear;
   they must not permit attacks. Check primary Monk, extra Monk and Iksar Tail
   Rake; Tail Rake and Dragon Punch are one skill, not two cooldowns.
7. Release Monk on a spare character and verify the skills cannot remain usable.
   Check a Warrior/Paladin without Monk: Kick/Bash keep their normal grouping.

Record actual gameplay and owner acceptance separately from build/publication.
