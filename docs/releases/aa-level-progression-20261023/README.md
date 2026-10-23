# Level-scaled AA and level-1 allocation controls

Status: implementation candidate; not deployed or accepted in game.

## Accepted intent
The owner selected two passive AA per level of earned experience on October 23,
2026, and requires the native AA plus/minus controls to work from level 1.
Players must be able to allocate 100% to AA and hold their current level.
Normal leveling thresholds/rates and earned points, purchases and partial AA
progress are preserved. Classic 50 and the retired Goldwind boost remain.

## Behavior
At 0% allocation, full eligible normal XP also earns two AA per level-equivalent.
The existing 10% passive/full-focus ratio is retained: full focus earns twenty
AA per current-level-equivalent while normal XP stops. Intermediate percentages
divide normal XP and blend passive/focused AA, with valid 0-100 selections retained
through zone/relog. Reaching a configured AA wallet cap must not resume leveling.
The level-scaled mode uses modified normal XP as its common basis; separate
AA-only level/character/modern modifiers do not multiply this rate again.
Eligible sources are kills, quests and tasks; no resurrection or GM bonus AA.
At the level cap, AA continues against the capped level's XP span.

## Implementation plan
1. Add deterministic level-span award arithmetic and tests around actual native
   XP functions, preserving the fixed AA storage denominator and existing fraction.
2. Restore percentage allocation in XP/percentage quest rewards, saved profile
   loading, command text and server controls. Test 0%, partial and 100%, all levels,
   crossings, cap behavior, rounding, exclusions and persistence.
3. Inspect and patch the exact RoF2 allocation enable/submit gates through the
   existing signed proxy/catalog, with guarded native tests. Keep protected client
   files read-only; no broad level spoofing.
4. Review independently, compile matching world/zone and client artifacts over
   verified current inputs, and record precise client/server QA and rollback.
5. Update CHANGES/status, player guidance/wiki impact and installed knowledge.
   Publication/deployment receipts are separate from implementation and QA.

A new compiled rule requires matching world and zone builds. Internal AA point
units remain fixed to avoid reinterpreting saved fractional progress on level
changes. Awards crossing levels are segmented using actual native thresholds.
No retroactive points or player-data reset is planned.

## Verification and release scope

Native award369, legacy129, actual SetEXP8 and pinned client167 checks pass.
The client runtime suite passes10groups and112exact executable guards. Signed
client2026102301 changes only the proxy/catalog and preserves138assets. Fresh complete world/zone/shared_memory compilation passed; no gameplay/client/wiki activation is claimed.

Operator15failure cases pass. Actual MariaDB temporary-table forward/replay/
collision rehearsal leaves live rules unchanged. The compiled catalog1013rules
matches all1076existing rows/notes; only the new rule will be added. Wiki67Linux
cases and existing Node suites pass, with467publishedbaselinefiles reproduced
exactly. Private-guide responsive/reflow/keyboard checks pass. Independent source,
operator, publisher and guidance reviews found no remaining blockers.

See [matrix](matrix.md), [owner QA](QA.md), [recovery](RECOVERY.md),
[review](review.json), and the individual signed/build/deployment receipts.
The latest wiki source is feature/aa-level-wiki in the aa-level-wiki managed
worktree, preserving the published loot finder, Build Lab and handbook.
