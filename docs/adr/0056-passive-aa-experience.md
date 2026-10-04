# 0056: Passive AA experience while leveling

Date: 2026-10-04
Status: Implementation candidate; owner in-game acceptance pending.

## Intent

Kills and quest/task XP should advance AAs without enabling AA allocation or
reducing normal leveling XP. Explicit AA allocation has only two states: 0% and
100%. This extends the existing level-1 AA eligibility without widening the legal
AA pool or changing rank caps, purchase costs, or the experience cost per point.

## Design and acceptance

- Use a small, configurable passive percentage of the full AA award when
  allocation is off. `AA:PassiveExpPercent` defaults to 1 (clamped 0-100).
- Allocation on redirects the full eligible award to AA, without a passive bonus
  on top. Any valid nonzero allocation becomes 100%; zero remains off.
- Enforce the same policy for packets, commands, quest setters and saved state.
- Cover raw XP and percentage-of-level quest/task rewards. Preserve the latter's
  existing level-XP modifiers; do not apply those modifiers twice.
- No passive AA from resurrection, death, GM setters, zero XP or ineligible levels.
- Keep existing AA multipliers, acceleration, award cap and bank cap effective.
- Percentage-of-level rewards branch from the base award: level XP takes ExpMod,
  AA takes AAExpMod, and each takes FinalExpMultiplier once. As with native raw
  AA XP, an absent modifier row (ExpMod=0) leaves the award alone. These rewards
  retain their original exemption from raw kill/zone multipliers.
- Apply the passive fraction after AA acceleration and the per-award cap. Round
  down with no minimum stipend; typical level-1 kills can therefore award zero,
  while larger kills/quests begin accumulating AA. No schema/fractional bank.
- A full AA bank turns focus off before splitting the next award; retain earned
  points and partial XP, and prevent a single large award crossing the bank cap.
- No changes to the binary game client, era policy or production state.

## Implementation plan

1. Add executable regression coverage around the actual experience methods and
   allocation entry points, including a failing baseline.
2. Update `server-mods/code/zone/exp.cpp`, its declarations in `client.h`, the
   AA rule catalog, allocation setters/handler/load path and `gm_commands/aa_exp.cpp`.
3. Test normal/normalized XP, quests/tasks, 0/100 modes, eligibility, resurrection,
   modifiers, caps and low-value rounding. Compile affected server units.
4. Review independently; record calibration, exact in-game QA and rollout/rollback.
   Commit one feature candidate; broader suite failures remain promotion gates.

## Alternatives

A flat AA stipend per kill would over-reward trivial kills and require separate
quest tuning. Diverting part of normal XP would violate the requested unchanged
leveling speed. A percentage of the existing AA award preserves server tuning and
keeps focused AA earning materially faster than passive earning.

1% produces about 33 AAs by level 50 in a neutral kill-only curve with the observed
50,000 XP/point cost, before per-award rounding. 5% would produce about 165 and is
more material power growth; it remains an explicit tuning alternative after QA.
See [release and QA record](../releases/passive-aa-20261004.md).
