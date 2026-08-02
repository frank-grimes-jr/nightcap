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
AAs, buffs, spells, disciplines, equipment, or cooldown timers. One Water Flask
occupies General Slot 1 so EQEmu's inventory loader receives a valid row. This
is the functional-only pass; it does not test value-1 skill progression.

## Result

The corrected login banner reports Cleric (primary), Shadowknight (secondary),
and Monk (tertiary), and the database contains all six Monk skill rows at the
expected caps. The RoF2 Combat Abilities control was grayed out for the
Cleric-primary profile; the guarded client correction now enables it.

That window is the discipline/tome window, however, and this fixture
intentionally has zero `character_disciplines` rows. An enabled but empty Combat
Abilities window is therefore expected and does not report whether the Monk
special attacks are available. Those attacks are ordinary activated skills and
must be assigned through **Actions -> Abilities**. The original QA instructions
incorrectly conflated these two client surfaces.

The guarded combat-window correction from commit `b0ba2e9` was deployed after
the initial grayed-control result. The subsequent Actions-selector correction
from commit `1dba98c` is now deployed with DLL SHA-256
`E5B39B38B4046E46C8B9CE58C3FE08872D490B80F72663B1232AD75F34069BDD`.
That correction loaded and applied but the first retest still showed no Monk
skills. A bounded diagnostic build now records selector state for the seven
granted Monk skills. Its trace exposed a wrong raw-accessor symbol and stack
signature in the first selector build. The corrected accessor/ABI build is
deployed with SHA-256
`93353758DAEA62D6038DE2DC20582AB8BE1902F229D4620442301022F2CF96C5`.
The next retest confirmed all seven skills were visible and assignable, with
the live trace showing the expected positive raw values and combat/activated
classification. Assigned hotbuttons were then rendered **Not Usable**. The
August 2 build corrects the separate hotbutton presentation and `UseSkill`
pre-submit gates; activation, reuse, and damage QA remain pending. Deployed DLL
SHA-256:
`B8839305CFC5259365DD7268A19831115BD7922ECAAD4F66A00EFF1CD95CA845`.
That build fixed the hotbutton presentation, but manual QA showed that the six
attacks still did not activate. Feign Death did activate, isolating the issue
to RoF2's separate basic-combat submission path. The corrected activation
build is deployed for the next QA pass, with SHA-256
`8F8DF8B2B020486C32ABF8ACF6CEA37C194BFE89D29B762ED833E1C650F1B26D`.

## Steps

1. Fully log out to character select so the account list refreshes, then enter
   the world as `Monktest`.
2. Confirm the welcome/class display reports Cleric (primary), Shadowknight
   (secondary), and Monk (tertiary), at level 50 in Plane of Knowledge. A
   Cleric/Bard banner is a failure; it means a zone still has the obsolete
   quest-global login handler loaded.
3. Run `#zone arena -73.5 -979 49.9`. Target `a_training_dummy` or
   `an_undead_training_dummy`. Classic-era expansion filtering hides the static
   arena spawns; if no dummy is present, run `#npctypespawn 77002` to create a
   temporary `a_training_dummy` for this session.
4. Open the **Actions** window (Alt+M), select its second tab, whose tooltip is
   **Abilities Page**, and right-click a numbered ability square (1-6). Do not
   use the separate Combat Abilities discipline window for this step.
5. Record whether each of these is present in the right-click picker, assign it
   to a numbered square, and drag that square to a hotbar:

   | Ability | Expected skill |
   |---|---:|
   | Dragon Punch | 240 |
   | Eagle Strike | 240 |
   | Flying Kick | 250 |
   | Kick | 250 |
   | Round Kick | 240 |
   | Tiger Claw | 255 |

6. Activate each visible attack once, waiting for its reuse timer. Each should
   animate, damage the training dummy, and start the normal reuse timer.
7. Activate Kick several times. With this fixture's AAs and buffs cleared, each
   activation should produce one Kick attack—not a generic Kick plus a second
   Monk Kick.
8. Camp, re-enter `Monktest`, return to the arena, and repeat one Kick and one
   non-Kick Monk attack to verify persistence.

## Report

Please report:

- which of the six abilities were visible;
- which could be placed/activated;
- whether each produced damage and a reuse timer;
- whether Kick ever produced two attacks from one activation;
- any red rejection message, disconnect, crash, or black-screen event.

If an ability is missing from the Actions-window picker, record it as a
client-visibility result rather than a server-dispatch failure. The deployed
server path can authorize packets that reach it; the separate client slice must
expose any buttons RoF2 suppresses for a Cleric primary class.

## Fixture operations

Run from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/setup-monktest.ps1 -Mode Check
powershell -NoProfile -ExecutionPolicy Bypass -File tools/setup-monktest.ps1 -Mode Rollback
```

Pre-application backup:
`backups/peq_20260729_134657.sql.gz` (46,342,038 bytes).
