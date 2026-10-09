# Passive AA tuning — October 9, 2026

Historical record: superseded later October 9 by the owner's
[40% tuning](../passive-aa-forty-20261009/README.md).

Status at this activation: **20% active on OVH**, explicitly selected by the owner. Normal leveling
XP is unchanged. AA focus remains binary: off earns the additive passive award;
on earns the existing full AA award. The compiled fallback remains 1%; the
persistent default-ruleset override is now `AA:PassiveExpPercent=20`.

The owner confirmed passive progress was working but too slow, then requested
20%. The inspected level-5 character had 1,049 / 50,000 AA XP and allocation off.
The change applies to future kills and both quest/task reward paths. It does not
retroactively multiply accumulated XP or grant points directly. Tiny awards still
round down, with no minimum stipend. Existing AA eligibility, caps, multipliers,
legal ability pools and rank limits remain in force.

## Calibration and decision

The native level curve, with equal normal/AA modifiers, no deaths or other bonuses
and before per-award rounding, gives these approximate totals:

| Level | Original 1% | Considered 5% | Owner-selected 20% |
|---|---:|---:|---:|
| 10 | 0.15 AA | 0.73 AA | 2.92 AA |
| 20 | 1.37 AA | 6.86 AA | 27.44 AA |
| 30 | 4.88 AA | 24.39 AA | 97.56 AA |
| 50 | 32.94 AA | 164.71 AA | 658.83 AA |

1% preserves a very slow early pace; 5% improves it while limiting later growth;
20% is the owner's explicit choice for more substantial progression. Full focus
remains five times the passive award before rounding. At 20%, a fresh character
reaches the first AA during level 7 on this idealized curve; the observed level-5
character, retaining its prior progress, would reach it around level 8. At 1%,
the first AA is during level 18. These are XP-curve estimates, not time-to-AA or
combat-balance measurements. The combined power of multiclass, gear, pets and
earned AA still requires representative legal-build playtesting.

## Verification

- 100 native-method checks pass against the exact production source, including
  29 tuning checks for kills/raw quests/tasks at levels 5/10/30/50, percentage
  rewards, live rule changes with existing progress, normal XP and full focus.
- Running world/zone hashes match that source's production build manifest.
- Eight operational tests pass, including actual generated log-reader execution,
  fresh log boundaries, failure recovery, ambiguous commits and external edits.
- Independent review is clear. The full PEQ backup passed gzip validation; the
  forward/inverse transaction rehearsal changed one row each and rolled back.
- Activation changed exactly one rule value, preserving its notes and every other
  rule. No other ruleset overrides it; zone rulesets inherit the default value.
- The authenticated native global reload completed in world and all 12 zones,
  verified from new log output with unchanged PIDs/start tokens. All services
  remained running; game and DB health passed. No restart, binary, quest, client
  or player-record write was used. Local development DB settings are unchanged.

[Runtime result, reload logs and backup receipt](result.json) ·
[Native checks and curve](native-tests.json) · [Binary provenance](native-runtime.json).

Backup and complete rule preimages remain on OVH under
`/opt/nightcap/backups/passive-aa-tuning-20261009/`. Local operation evidence is
`E:/EQ_Local_Dev/artifacts/passive-aa-tuning-20261009/`.

## Exact in-game QA (pending)

1. On Fists in East Commonlands, use `#aaexp off`; record level and AA progress.
   Kill XP-eligible orc pawns/centurions of a suitable level through normal combat.
   Normal XP should retain its prior amount; future passive AA uses 20% of the
   full AA award, approximately twenty times the old 1% award before rounding.
2. Use `#aaexp on` and repeat against the same mob type/level: no normal XP,
   the same full AA award as before. Turn it off to resume normal leveling.
3. Cross one AA-point boundary, then zone and camp/relog. Both XP pools and the
   selected 0/100 allocation must persist. Complete an ordinary quest and a task,
   recording IDs/rewards; both reward APIs have native checks but real completion
   paths remain manual QA. Do not install synthetic reward fixtures on production.
4. At levels 10/30/50 compare legal Warrior/Cleric/Wizard, melee and pet builds on
   the same encounters. Record actual allowed ranks/spent points, kills/hour,
   time-to-kill, HP/mana recovery and deaths with comparable gear. Do not use an
   unrestricted AA pool or claim balance acceptance from the arithmetic tests.

## Recovery

The recorded [operation](ops/apply.py) rolls back only its owned 20% value if
reload verification fails, then globally reloads again. It preserves external
rule edits and records `recovery_pending` when ownership or recovery is uncertain.
Never rerun the already-completed operation blindly.

For an intentional future rollback, take fresh preimages/backup, apply the
[guarded inverse](rollback.sql), expect exactly one changed row, and run
`#reload rules global`. Verify world and every zone loaded it. Rollback changes
future earnings only and retains all earned AA and player data. Do not restore
the database snapshot or terminate a production zone to change this rule.
