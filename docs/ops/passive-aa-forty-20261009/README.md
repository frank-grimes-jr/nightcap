# Passive AA increased to 40% — October 9, 2026

Status: **40% active on OVH**, following the owner's request to increase the
previous 20% setting. Full leveling XP remains available with AA allocation off;
the additive AA award is now 40% of the full AA award. Focus remains binary
0/100, and its full award is unchanged. The compiled fallback remains 1%; preserve
the persistent default-ruleset override `AA:PassiveExpPercent=40` on deployment.

Future kills and both raw and percentage quest/task rewards use the new rate.
Existing progress is retained. Before per-award rounding, passive AA is twice
the previous 20% rate; full focus is 2.5 times the passive award. No direct grants,
minimum stipend, new ability unlocks, cap changes, or retroactive XP adjustment
were added. Existing eligibility, multipliers and legal rank policies still apply.

## Evidence

- 129 native-method checks passed against the exact deployed source, including
  29 new 40% checks for kills/quests/tasks at levels 5/10/30/50, percentage rewards,
  live tuning with accumulated progress, point boundaries and full focus.
- The running world/zone binaries match the production source manifest. The
  extracted profile-load method retains one existing signed-comparison warning.
- All eight operation/recovery tests passed; independent review found no issues.
- A fresh full PEQ backup passed gzip validation. Forward/inverse SQL was
  rehearsed inside a rolled-back transaction before the one-row live commit.
- Only ruleset 1's `AA:PassiveExpPercent` changed, from 20 to 40. Its notes and
  the entire remaining rule table were preserved; no other ruleset overrides it.
- Fresh logs confirm the native global rule reload in world and all 12 zones.
  PIDs/start tokens are unchanged, all five services run, and game/DB are healthy.
  There was no process restart, binary/client/quest update, player-record write,
  or local development DB change.

[Live result, reload logs and backup receipt](result.json) ·
[Native test results and curve](native-tests.json) · [Binary hashes](native-runtime.json).

Backup and full rule preimages:
`/opt/nightcap/backups/passive-aa-forty-20261009/`.
Local evidence: `E:/EQ_Local_Dev/artifacts/passive-aa-forty-20261009/`.
The earlier [1% to 20% operation](../passive-aa-tuning-20261009/README.md) is historical.

## Balance and exact in-game QA (pending)

On the neutral native curve, before rounding/deaths/bonuses, 40% produces about
5.83 AA through level 10, 54.87 through 20, 195.11 through 30, and 1,317.67 through
50. These are cumulative XP estimates, not time-to-AA or combat acceptance.
The owner selected this pace; combined multiclass/gear/pet/AA balance remains open.

1. On Fists in East Commonlands, use `#aaexp off`, record level and AA progress,
   and kill XP-eligible orc pawns/centurions appropriate to the character's level.
   Normal XP should retain its prior award; passive AA should be approximately
   twice the previous 20% award for the same reward before integer rounding.
2. Use `#aaexp on` and repeat against the same mob type/level. Expect the existing
   full AA award and no level XP, then turn it off to resume ordinary leveling.
3. Cross an AA-point boundary, zone, and camp/relog. Both progress pools and the
   0/100 allocation must persist. Complete an ordinary quest and task, recording
   IDs/rewards; real completion paths and client display remain manual acceptance.
4. At levels 10/30/50 compare legal melee, pet, and Warrior/Cleric/Wizard builds
   against the same encounters with comparable gear. Record allowed ranks and
   actual points spent, kills/hour, time-to-kill, HP/mana recovery, and deaths.
   Do not substitute unrestricted AA pools or arithmetic checks for balance QA.

## Recovery

The [recorded operation](ops/apply.py) retains guarded recovery to 20% if reload
verification fails, preserving external edits and recording uncertain recovery.
Do not rerun this completed activation. For a future rollback, take fresh
preimages/backup, apply the [guarded inverse](rollback.sql), require exactly one
changed row, and run `#reload rules global`; verify world and every zone loaded
the rule. Keep all earned AA and player state. Do not restore the DB backup or
terminate a production zone to change the rate.
