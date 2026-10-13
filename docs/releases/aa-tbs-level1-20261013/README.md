# Buried Sea AAs at character creation — October 13, 2026

The owner rejected the earlier level-gated AA implementation during live QA.
Nightcap opens customization at level 1: **every allowed AA and rank in the
release is available at character creation**, subject to class eligibility,
points and AA prerequisites. Character level never determines access.

This correction is built and awaiting the guarded OVH activation recorded below.
It does not constitute owner gameplay acceptance or permission to promote main.

## Correction

The existing legal pool is unchanged: 390 families and 941 ranks across all
classes. The TBS expansion cutoff, six bounded later exceptions, release rank
ceilings and high-risk deferrals remain. Most ordinary families still have a
three-rank release ceiling; every retained rank is now available at level 1.
The policy schema records maximum rank counts instead of character unlock levels.
Native table packets, purchase, use, earned-rank projection and default grants
ignore original database level requirements for clients. An explicit GM
GrantAllAAPoints unlock_level argument remains a content-selection filter;
the default has no level filter. Non-client purchase behavior is unchanged.

No catalog rows, purchased ranks, saved charges, point wallets or spent accounting
are removed or refunded. Previously purchased legal ranks become usable on
reconnect without buying them again. Ranks outside this release remain stored
and dormant. Reprojection on level changes preserves the same legal prefix.

All six exceptions are available at level 1: Eyes Wide Open (eight ranks),
Diminutive Companion (one), Enchanter Pet Discipline (one, requiring Animation
Empathy three), Companion's Durability/Agility (three each), and Sturdy Companion
(one, raw AC). Native class and race restrictions remain.

[Coverage](coverage.json) is invariant across levels 1/10/20/30/40/50. At creation,
WAR/CLR/WIZ has 152 visible families, 389 prerequisite-closed ranks and maximum
legal spend 1,692; MAG/NEC/SHM has 143/348/1,506; PAL/WAR/MNK has 140 visible
families, 139 prerequisite-closed families, 353 ranks and 1,491 points.
These are catalog counts, not measured combat strength. A class-dependent
prerequisite can leave a visible family unavailable for that particular union.

## Verification and rollout

The changed creation-access test failed against the previous policy. Six policy
tests pass, including a catalog with every database level_req changed to 255.
The native regression fails against the deployed old source, then passes against
the corrected actual eligibility, purchase, ownership, save and projection
methods: 5,646 rank/level checks plus class masks, identity rejection, DB-level
override, costs, prerequisites, saved charges and duplicate-purchase protection.
Three catalog/ownership preflight and ten activation/recovery tests pass.

Only aa.cpp and the generated AA header change in the retained native source.
The build verifies the previous source manifest and all recorded link inputs,
recompiles aa.cpp without stale PCH, links the other deployed objects unchanged,
and verifies runtime dependencies. No world or client binary change is needed.
The October 13 trainer, skill progression and offhand correction is preserved.

The guarded operator uses a fresh verified backup, deployment/GM locks, current
binary hashes and catalog comparison. It closes access, gracefully stops the
whole runtime, fingerprints current player/custom tables, swaps only the zone
image, checks all twelve zones and data preservation, then reopens access.
Recovery selects the preceding immutable image without restoring old SQL.
Use current data for any later recovery; reconcile intervening native releases.

The missing player summary is published through higher signed game metadata,
preserving existing client file hashes, URLs, patch history, desktop and starter.
No client asset download or extra game restart is needed for the notes.

## Exact owner QA

1. Reconnect on the existing low-level character. Open all AA tabs and confirm
   the expanded TBS choices appear with requirement level 1. Check the unchanged
   unspent/spent totals and restored previously purchased legal ranks. Camp,
   reconnect, and zone from East Commonlands to North Ro; verify they persist.
2. Create a disposable character. At level 1, earn or GM-grant test points and
   buy a chosen allowed family through its release ceiling. Test Natural
   Durability ranks 1/2/3 without leveling; confirm normal point deductions,
   prior-rank prerequisites and the unavailable fourth rank. Choose a different
   allowed family to confirm there is no forced order between unrelated AAs.
3. On a level-1 Enchanter union, buy Animation Empathy 1/2/3, then Pet Discipline.
   A single-class Warrior must not receive Enchanter-only choices. On a pet union,
   buy shrink and allowed defense ranks at 1; resummon pets for HP changes.
4. On disposable controls, level 1 -> 10 -> 30 -> 50 -> 1 without changing classes.
   The legal AA list and active owned ranks must stay the same. Existing excluded
   burn/veteran hotkeys remain dormant; no earned record should disappear.
5. Reopen the normal launcher shortcut and check Latest update for the level-1
   AA restoration and TBS summary. Previous patches must retain the skill fixes.

Combined balance/enjoyment QA remains open. Test earned builds and gear against
appropriate Classic camps; record actual spent points, survival, kill time,
resource use and recovery. Do not substitute level locks for the owner's
level-1 customization invariant in later tuning.
