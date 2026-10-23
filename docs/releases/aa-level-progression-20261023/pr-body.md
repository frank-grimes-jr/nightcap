Players now earn two passive AA per level while keeping the installed normal XP curve. Native AA +/- controls work from level1; percentages persist and100% AA pauses leveling. Fixed stored AA units preserve earned points and fractions.

Fresh paired world/zone/shared-memory builds,369award/129legacy/8actual SetEXP/167client-control checks,112exact executable guards,27Windows/Linux rollout tests and independent review pass. Production preflight verifies the pinned image, complete rule catalog and preserved runtime/content; activation remains pending. Signed client2301 changes only two assets. Current wiki preserves loot finder and Build Lab.

Owner authorized this continuing correction on main/server. Manual acceptance remains open. Exact QA: docs/releases/aa-level-progression-20261023/QA.md; matrix and recovery are adjacent.

# Owner in-game QA — paired candidate required

Status: native checks passed; visible gameplay acceptance is pending.

Use the matching launcher release after closing EverQuest. Preserve existing
character progress; a new level-1 character is the low-level control.

1. Open Alternate Advancement at level 1. Press plus from 0 to 100 and minus
   back to 0. Each click changes the selection by ten percentage points. The
   buttons stop at their bounds; the normal AA lists, Recommended filter,
   details and purchase controls continue working.
2. Set 50%, zone into East Commonlands, and relog. The selection remains 50%.
   Also set 5% with #aaexp 5: minus reaches 0%; set 95%: plus reaches 100%.
3. At 0%, fight XP-awarding fire beetles or decaying skeletons in East
   Commonlands. While staying within a level, earning one quarter of a normal
   level should add approximately half an AA point. Whole-level progression
   adds two AA points; existing points and fractional progress remain.
4. Set 100% and repeat XP-awarding fights. Normal level/XP must stay fixed,
   including at level 1, while AA increases. Return to 0% and verify leveling
   resumes. At 50%, half the normal XP is retained and AA earns 11 points per
   full level-equivalent of input XP (22 per actual level gained).
5. Test a raw quest/task XP reward and a percentage-based reward with the same
   0/50/100 settings; they follow the same allocation. Resurrection and GM
   level changes must not mint AA. No automatic or retroactive AA grants occur.
6. Cross a level boundary at 0%, then zone/relog: earned points and partial
   progress remain. Repeat near 49→50. At level 50, ordinary and focused AA
   earning continue while the Classic cap remains in force.
7. With an isolated test-only AA bank cap, reaching that cap at 100% must retain
   the selection and keep leveling paused. Production currently has no bank cap.
8. Confirm Commonlands Goldwind still provides no paid XP boost and ordinary
   Matron blessings remain available. This release does not restore retired boosts.

Native fixture coverage validates award arithmetic, actual SetEXP conversion/
level transitions, and pinned RoF2 control code. Network transport, rendered
window state, real quest rewards and player balance remain in-game checks.
