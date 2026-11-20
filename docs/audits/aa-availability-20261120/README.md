# AA availability audit — November 20, 2026

Deployed through dev/test/main on November 20. Production and wiki verified; player acceptance remains OPEN.

Owner scope: audit availability, fix confirmed issues, validate on test, then
merge to main and deploy. Existing ranks, prices, effects, custom content and
intentional expansion exclusions are unchanged. No AA grants or player edits.

The fresh read-only production capture exactly matches all four current catalog
tables: 1,572 abilities, 6,657 ranks, 9,875 effects and 2,526 prerequisites.
The compiled allowed pool is 489 families / 1,845 ranks. Fury of Magic 215
(nine ranks) and Mystical Attuning 334 (three) are already included.

## Confirmed defect and bounded repair

Enabled Mastery of the Past 150 combines class masks from the native caster
line and disabled duplicate 251, but retains Spell Casting Expertise 26 as a
prerequisite for every class. Cleric, Paladin, Ranger, Druid, Shaman and Beastlord
cannot buy that prerequisite. The disabled duplicate has the same first three
effect values (54/56/58) and no prerequisite. Historical native diagnostics
already recorded the blocked WAR/CLR/MNK purchase path.

Waive only prerequisite 26 of family 150 for a player holding at least one of
those six classes. Apply the same filter to the client AA packet and native
purchase checks. Keep the prerequisite for SHD/BRD/NEC/WIZ/MAG/ENC-only builds.
Adding another class must not revoke the six-class path. Preserve ordinary
earned-state projection and class-release refunds; never delete an earned rank
just because a prerequisite becomes unavailable after a class release.

Implementation: `common/aa_availability.h`, `zone/aa.cpp`. No generated policy,
catalog, SQL, client binary or shared-memory change. Rebuild zone and restart
through the supported whole-runtime release procedure. Relog to refresh AA data.

## Validation and release gates

1. Reproduce blocked purchase and packet prerequisite before the fix.
2. Test all singles, pairs and trios, each existing rank, preserved caster
   prerequisite, insufficient points, earlier rank, unrelated family, and bot
   controls. Check relog/class changes and unchanged rank/policy fingerprints.
3. Independently review. Reproduce the current shipping executable, compile the
   full affected native translation unit and validate the candidate.
4. Promote through dev/test/main; retain explicit test QA and production
   stopped-backup, rollback, preservation and health evidence.
5. Review wiki impact and update installed knowledge with verified status.

## In-game QA on test (acceptance remains open)

Use existing earned AA points; do not grant player ranks to prove the fix.
In the Arena, relog and disable Recommended filtering in the AA window.
On a Paladin/Warrior or Warrior/Cleric/Monk, Mastery of the Past should show
three ranks, cost three points each, with no impossible Expertise requirement.
Purchase in order. Check reduced fizzle behavior for eligible spells; this does
not prevent melee interruption. Relog and verify points and ranks persist.
On a Wizard-only character, Expertise III must still be required. Add a Cleric
and confirm the alternative path works; remove it and confirm earned ranks
remain with normal future-purchase prerequisites. Release the last eligible
class and verify the standard exact refund and removal. Fury of Magic and
Mystical Attuning must retain their existing masks, costs and rank totals.

Native checks do not replace visible-client, persistence, or player acceptance.

## Verified release

Main 6da8492de16092d167b05467f9b3f9e6542b72e0 (PR502), following dev PR500 and test PR501. Zone 98d6214630ef36fbd34a54185630543b1fd5266d41f9191078d6ab7e2d44872b is active on all12workers. Stage aa-availability-20261120-v1 uses zero-player activation,125second admission drain, clean whole-runtime stop, fresh stopped backup and saved-state/market preservation. Gateway reopened; native/quest/database error checks pass. World, rules, content, caches and signed client2026112001 remain unchanged. No player snapshots restored.

Wiki20261120-aa-availability-v1 is published:631canonical files and private denials verified,628outputs preserved and rollback rehearsed. Twenty wiki tests and search pass.30focused/adjacent checks and11dev checks pass. Native fixtures are not real-player SQL purchase/release or UI acceptance. Current policy generator passes; historical all-class generation assertion is stale on unchanged main and is recorded separately.

Rollback selects the prior immutable fast-healing image through supported maintenance. Purchases remain earned; never restore an older player database. The old binary restores the old prerequisite behavior; existing ownership is retained. Relog refreshes the AA table. Retained operators and publisher scripts are one-shot evidence, not commands to replay.
