# Held-Monk Combat Ability QA

Date: 2026-07-29
Epic: #10
Server commit: `6236909`
Character: `Monktest` (ID 19, account `admin`)

## Scope

This spike verifies the first partial G006 server slice: a held Monk can submit
the six stock Monk attacks from any class slot, and Kick is routed exactly once.
It does not close generic held-class Kick, Berserker Frenzy rounds, or RoF2
combat-button visibility.

`Monktest` is a level-50 Human Cleric / Shadowknight / Monk in Plane of
Knowledge. It has 60 eligible held-class skills at current caps and no inherited
AAs, buffs, spells, disciplines, inventory, or cooldown timers. This is the
functional-only pass; it does not test value-1 skill progression.

## Steps

1. Fully log out to character select so the account list refreshes, then enter
   the world as `Monktest`.
2. Confirm the welcome/class display reports Cleric (primary), Shadowknight
   (secondary), and Monk (tertiary), at level 50 in Plane of Knowledge. A
   Cleric/Bard banner is a failure; it means a zone still has the obsolete
   quest-global login handler loaded.
3. Run `#zone arena -73.5 -979 49.9`. Target `a_training_dummy` or
   `an_undead_training_dummy`.
4. Open the Skills and Combat Abilities windows. Record whether each of these is
   visible and can be placed on a hotbar:

   | Ability | Expected skill |
   |---|---:|
   | Dragon Punch | 240 |
   | Eagle Strike | 240 |
   | Flying Kick | 250 |
   | Kick | 250 |
   | Round Kick | 240 |
   | Tiger Claw | 255 |

5. Activate each visible attack once, waiting for its reuse timer. Each should
   animate, damage the training dummy, and start the normal reuse timer.
6. Activate Kick several times. With this fixture's AAs and buffs cleared, each
   activation should produce one Kick attack—not a generic Kick plus a second
   Monk Kick.
7. Camp, re-enter `Monktest`, return to the arena, and repeat one Kick and one
   non-Kick Monk attack to verify persistence.

## Report

Please report:

- which of the six abilities were visible;
- which could be placed/activated;
- whether each produced damage and a reuse timer;
- whether Kick ever produced two attacks from one activation;
- any red rejection message, disconnect, crash, or black-screen event.

If an ability is missing from the RoF2 window, record it as a client-visibility
result rather than a server-dispatch failure. The deployed server path can
authorize packets that reach it; the separate client slice must expose any
buttons RoF2 suppresses for a Cleric primary class.

## Fixture operations

Run from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/setup-monktest.ps1 -Mode Check
powershell -NoProfile -ExecutionPolicy Bypass -File tools/setup-monktest.ps1 -Mode Rollback
```

Pre-application backup:
`backups/peq_20260729_134657.sql.gz` (46,342,038 bytes).
