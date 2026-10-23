# Level-scaled AA and level-1 allocation controls

Status: deployed to production and published October23,2026; owner native gameplay acceptance remains pending.

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
client2026102301 changes only the proxy/catalog and preserves138assets. Fresh complete world/zone/shared_memory compilation passed and the paired runtime is deployed.

Operator27failure/boundary cases pass on Windows and Linux;14client publisher Linux tests and6website concurrency/syntax tests pass. Actual MariaDB temporary-table forward/replay/
collision rehearsal leaves live rules unchanged. The compiled catalog1013rules
matches all1076existing rows/notes; only the new rule will be added. Wiki67Linux
cases and existing Node suites pass, with467publishedbaselinefiles reproduced
exactly. Private-guide responsive/reflow/keyboard checks pass. Independent source,
operator, publisher and guidance reviews found no remaining blockers.

See [matrix](matrix.md), [owner QA](QA.md), [recovery](RECOVERY.md),
[review](review.json), and the individual signed/build/deployment receipts.
The latest wiki source is feature/aa-level-wiki in the aa-level-wiki managed
worktree, preserving the published loot finder, Build Lab and handbook.

## Verified delivery

Featureâ†’dev PR303, devâ†’test PR304 and owner-authorized testâ†’main PR305 landed
at00f90e9. Active stage /opt/nightcap/releases/aa-level-progression-20261023-v3
uses image5e501da8 with fresh world/zone/shared_memory. Fresh stopped backup,
91saved-state tables,1077exact rule rows,12zones and39schema/499content checks
passed; access reopened. Existing earned points, purchases and fractions remain.
Native cache expiry handling and one market rotation were checked against exact expected state.
Signed game2026102301 verifies all140hosted files (279410356bytes); two assets
change and138remain. A private-umask directory permission issue was corrected
on the exact new public directory, with3POSIX regressions added.
Wiki20261023-aa-level-v1 verifies467HTTPS files and5private denials; private
player-guide20261023-aa-level-guide-v1 verifies5files. Loot finder, Build Lab,
reader/timer,384Hunt values and unrelated article contents remain.

The first preflight stopped on a gameplay/purge-expiry mismatch; v2 built a
valid image but stopped on disk reserve. v3 reused that exact image after
removing only task-created cache. The11obsolete upload deletions had explicit
owner approval and verified identical local recovery copies. No player snapshot,
installed image or unrelated backup was deleted. See preflight-recovery.json,
instance-expiry-audit.json and client/permission-repair.json. Do not replay
activation; use RECOVERY.md for any new incident.
