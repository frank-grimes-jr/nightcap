# High Keep: The Prison Break

Candidate, 2026-10-24. Source baseline origin/main ebeb6591; not deployed.
Integrated main7fe3a783's subsequent Hole release evidence; the native baseline
is unchanged. Final full zone build and scoped tests pass; gameplay QA is open.

The entrance must explain the raid before combat. Hail the Gate Sergeant, claim
to be a relief detail, then insist on seeing Osargen. Suspicion escalates through
three ordered, short-lived dialogue steps; the final response commits the alarm
and immediately makes every keep guard hostile to every participant in this run.
Attacking a guard also sounds the alarm. No permanent faction write is involved.

The route is entrance -> Boshinko on the ground-floor approach -> Bosec and Dyrna
in the prison -> McCabe at the cell-block approach -> Osargen -> entrance.
Keep existing four objective identities and boss loot. Move only the two raid
boss poses and suppress their overlapping ordinary guard spawns. Zone-wide NPC
lines and the journal explain where to go; there is no required upstairs hunt.

After the four bosses, hail Osargen and choose Lead the way. He follows that
living participant using native navigation, pauses when the player gets too far
away, and accepts a new leader on hail. Three fixed escape checkpoints each
spawn two guards who attack him. Clear all three and bring him within 25 units
of the entrance, with no nearby engaged guard, to finish. Players can heal him
and intercept/taunt the guards. Guard damage is real; player/pet harm is blocked.

Osargen's death, a missing actor, or abandonment resets only the escort attempt
after a cooldown. Disconnect permits another nearby enrolled participant to
take over. A zone reboot preserves alarm, boss deaths and earned completions,
but returns an unfinished escort to the cell. Dynamic attackers have no XP,
money, items, global loot or permanent spawn deaths. Attempts are token scoped.

Only living, connected, loaded, enrolled participants near Osargen at extraction
who personally earned all four boss credits receive completion. Existing atomic
inventory receipts remain the sole reward-delivery authority. Missed boss kills
cannot be borrowed. Repeated ticks/hails cannot replay completion or rewards.

Scope: newly created opted-in managed High Keep Raid runs only. Existing runs,
Grind, public High Keep and other dungeons retain their current behavior. Install
the new schema and matching native zone together; the flag defaults off. Native
High Keep operations fail closed if the required schema is missing or malformed.
No item-cache, spell, client, permanent-faction or public spawn mutation.

Implementation: common/highkeep_policy.h; zone/highkeep_rescue.inc; narrow hooks
in dungeon_service, client say/faction and aggro attack permission. Add guarded
schema SQL, native behavior/adapter tests, terrain evidence, QA/runbook, CHANGES,
status and a whole-wiki impact assessment. Review scope, persistence, ownership,
failure recovery and player guidance before promotion. Native build and terrain
checks do not constitute owner gameplay or balance acceptance.
