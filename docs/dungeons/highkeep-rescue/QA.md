# High Keep prison-break QA

Candidate, not deployed. No owner gameplay/balance acceptance has been claimed.

## Player route

1. Start a new High Keep **Raid** after activation. At the entrance, hail the
   Gate Sergeant, choose **We're the relief detail**, then **We're here to see
   Osargen**. The replies should grow suspicious; the last choice sounds the
   alarm and guards immediately consider all participants and pets hostile.
2. Follow zone shouts/journal hints: Boshinko on the entrance approach; Bosec at
   the prison stairs; Dyrna in the prison; McCabe by the cell-block approach.
   No upstairs search is required. The four existing boss rewards remain.
3. Hail Osargen at `/loc -52,-546,-10.13` and choose **Lead the way**. Protect him
   from the first two pursuers near his cell, then two at Bosec's stairs and two
   on the entrance approach. He pauses while each wave survives. Taunt/intercept
   guards and directly heal him. Targeted heal, HoT and Complete Heal must work
   with implied targeting both on and off. Harmful player and pet effects must
   not hurt him; ordinary guard attacks must.
4. Walk him to `/loc -16,88,4`. All three waves must be defeated and nearby guard
   combat cleared. Living nearby participants with all four personal boss credits
   earn completion and the existing one-time reward. Check native Tasks history,
   full inventory pending claim, later Keeper Claim Rewards and repeated hails.

## Recovery and boundaries

- Check doors, stairs, turns and pauses through the entire actual navigation
  path, especially cellar-to-main-floor ascent. No teleports are supplied.
  The first checkpoint is intentionally in range from the cell on release.
- Separate from the guide: Osargen stops in place. Return within90seconds or
  have another enrolled player hail and take the lead. Test disconnect, death,
  charm/AI control, zoning and rapid reconnect. An abandoned attempt resets.
- Let guards kill him: the escape resets after20seconds; the four bosses remain
  defeated. A reboot returns an unfinished escort to the cell, preserving alarm
  and boss deaths. Kill remaining/reused-ID actors without crediting a new wave.
- Try to skip a wave, hail remotely, jump directly to the final dialogue choice,
  use expired conversation choices, or join after missing a boss. No completion
  or borrowed boss credit. An early guard attack/kill should also raise the alarm.
- Verify pursuers/sergeant grant no normal, raid or leadership XP, coin, ordinary,
  global or Hunt drops, and leave no permanent faction loss. Ordinary boss XP and
  loot remain. Repeated Osargen damage must not grow the zone aggro counter.
- Re-enter an old unmarked Raid, Grind and public High Keep, plus another dungeon.
  Their layout, faction, NPC dialogue, healing and completion must remain normal.
- Judge pacing and survivability at the intended level40 band and maximum legal
  multiclass/AA/gear power. Osargen6000HP and two level34 native-stat pursuers per
  wave are initial tuning, not demonstrated balance. Record gear/classes and time.

## Automated evidence and limitations

`test_highkeep_rescue.py` compiles the actual coordinator and policy with explicit
engine/storage doubles. It exercises dialogue, alarm persistence, failure before
commit, lost acknowledgement after a successful completion commit, full escort,
leader handoff, personal credit, retry, entity reuse, death, one-time completion,
legacy isolation, pet/swarm harm protection and pause guard-point behavior.
It does not simulate real pathfinding, spell effects, combat pacing or UI packets.

The real heal classifiers and pre-validation cast paths pass149checks, including
the rescue exception and implied targeting. The existing dungeon regression suite
passes26cases (the private-population harness needed the new Layout hook stub).
The actual SQL rehearsal proves disabled default, transaction rollback, personal
four-kill gating, replay refusal, uniqueness/constraints and progress preservation.
Thirty-five terrain samples have ground and at least approximately12units of
headroom. Native FindRoute connects all four escape legs in both directions,
without partial paths or teleport links. Full native compilation is recorded
separately in its manifest.

Fresh-context native review identified and corrected follow guard-point drift,
missing idle prisoner recovery, permanent faction writes, heal redirection, raid/
leadership XP leakage and noncombat aggro-count growth. The owner chose to proceed
with that review rather than an additional model. Gameplay and navigation remain
the explicit release QA boundary.
