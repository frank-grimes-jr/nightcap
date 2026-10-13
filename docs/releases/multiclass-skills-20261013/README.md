# Multiclass skill progression and offhand repair — October 13, 2026

Corrective candidate for Palwar's failed purchases, skills stuck at 1, and blocked
offhand weapons. The owner confirmed that the October 12 trainer patch opens the
window, but its training/purchase claim was incomplete. This repair uses the
same-session approval to merge to main and deploy the paired server/client fix.
Native tests and deployment checks are separate from owner gameplay acceptance.

## Root causes and scope

The 09:39 UTC production probe found Palwar (29), level 6, Paladin/Warrior/Monk,
30 training points, Dual Wield 1 and Kick 1. Canonical level-6 Monk caps are 47
and 30; the database caps are correct. No points, skills, coins, classes or cap
rows are granted or rewritten.

- Retained production `Client::MaxSkill(skill)` was still an inline primary-class
  lookup, despite main already containing the held-class union. Actual
  `CheckIncreaseSkill` and `AddSkill` therefore stopped/clamped non-Paladin
  skills. Stage the reviewed union and rebuild **all 126 zone translation units**
  with a freshly compiled candidate PCH. Do not reuse objects embedding the old
  inline function. Retained source and every link input are fingerprinted.
- Native trainer purchase calls its own at-cap predicate (RVA 0x185955), whose
  current-level lookup (0x184C2B) remained primary-only. A character-scoped,
  thread-local wrapper projects held caps only during that trainer call. Native
  specialization, tradeskill restrictions, costs, points, server-cap checks and
  packet authorization remain intact. Scope restores even on exceptions.
- Secondary-slot weapon validation calls primary-only native HasSkill at
  0x183445 before the existing item-class hook. Its narrow fallback requires
  current identity/profile match, a positive server skill, and an eligible held
  class cap at the actual character level. Released-Monk/low-level-Warrior stale
  values, missing identity and zero skills do not grant access. Stock success
  and the surrounding weapon, slot and two-handed restrictions remain native.
- Retained empty-fist dual wield checked primary Monk/Beastlord. The predicate
  now checks held membership directly; this avoids importing an undeployed
  hand-to-hand helper. Other hand-to-hand damage formulas are outside this fix.

Client proxy **0.8.3-dev**, 91 guarded signatures/catalog sites. Intended signed
game release **2026101301**. Pair both sides: rule/quest reload cannot install
native changes, and an old client still blocks the corrected server.

## Verification and release

`tools/tests/test_multiclass_skill_progression.py` compiles actual selected
methods from any source root: the retained deployment fails five scenarios and
passes four controls; repository and staged candidate pass all nine. Tests
retain previous Monk/Beastlord slot, level, specialization and release coverage.
`eq-client-dll/tests/trainer-native.cpp` executes the hash-pinned RoF2 native
purchase/cap/offhand paths; both new failures reproduce before the patch and
pass after it. Cap exhaustion, native tradeskill limits, scope isolation, raw
skill absence and stale/released identity cases are covered. The protected
reference executable is unchanged. The complete 126-object zone build and dependency check pass, along with the full
launcher suite, nine rollout tests and twelve publication tests. See
`verification.json` and `build-manifest.json` for final results.

`tools/build_skill_progression_candidate.py` builds from the retained trainer
release into an isolated directory. Changed staged source is exactly client.h,
client.cpp and mob.cpp. No world/rule/ABI change is needed. The deployment recipe
creates a zone-only layer, validates both images and takes an integrity-checked
backup. Close gateway, gracefully stop the whole game, preserve saved data,
start and verify all 12 zones, then reopen access. Never kill one production
zone: its supervisor restarts the entire runtime. Retain the previous image for
rollback; never restore an old player snapshot. Publish the signed client
channel last and preserve all unrelated assets and launcher history. A client
rollback needs a new monotonically increasing release number.

## Owner gameplay QA

1. Close EQ, use launcher Play to fetch the new release, then log in Palwar.
2. In East Commonlands, hail and right-click Joren (Monk guildmaster, NPC 999656).
   Buy one Dual Wield and one Kick point below the current cap. Each should
   increase by one, charge normal points/coins once, and survive relog.
3. Practice Kick on a legal combat target. It should gain naturally above 1;
   gains are probabilistic and stop at the held-class level cap.
4. Equip legal one-handed weapons in both hands. Offhand placement must succeed;
   fight enough rounds to observe offhand attacks and Dual Wield skill gains.
   A two-handed primary or a shield must still prevent offhand attacks.
5. With empty hands and held Monk, verify unarmed offhand attacks. Also verify
   primary Paladin weapon gains, Garran (Warrior, 999650), Aldric (Paladin,
   999652), and rejection by an unheld-class trainer.
6. With a disposable QA character, release the class that uniquely owns a skill
   and verify skill/access removal. Do not release Palwar's classes for this test.

Current owner acceptance: trainer window opens on the previous release; buying,
natural skill gains and offhand gameplay on this corrective release are pending.
