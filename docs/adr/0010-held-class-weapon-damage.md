# ADR 0010: use held-class eligibility when resolving player weapon damage

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


Date: 2026-09-12. Status: candidate passes native weapon controls and 60 matched
encounters; live deployment and manual QA remain pending. Related gates: G014 and G018.11.

## Problem and evidence

Inventory and item bonuses use `Client::CanEquipItem`, which checks every held
class. `Mob::GetWeaponDamage` still calls `ItemInstance::IsClassEquipable(GetClass())`
for the player’s base class. A legal secondary/tertiary-class weapon therefore
provides stats but returns zero base damage on every swing.

The native WAR/CLR/MNK pilot equips Balanced Tonfa of Serenity (662038), a magical
Monk/Beastlord weapon. At level 50 it meets its required level, despite recommended
level 58. All 632 normal swings in the pilot report return the native immune code
(-5). Flying Kick and Tiger Claw deal damage, so a verifier accepting any physical
damage incorrectly accepts this fight. The 900-second run times out with Nagafen
still at 19,580 HP. The original diagnostic and input/report are retained as a
reproduction, not used as a valid final melee balance baseline.

## Decision

For clients, use the existing `CanEquipItem` helper in the weapon-damage legality
gate, retaining the existing requirement that the item has worn slots. Preserve
the required-level check, native race restrictions, bot rule exceptions, NPC paths,
recommended-level scaling, magical-weapon requirements and all damage formulas.
The helper already enforces both held-class and race compatibility. Non-client
actors continue through the original base-class check.

Do not work around the bug by restricting the optimizer to base-class weapons or
changing global item class masks. Both would diverge from Nightcap's additive
multiclass equipment contract and conceal the fault in balance measurements.

## Verification and deployment boundary

Compile the reviewed `attack.cpp` only into the isolated native diagnostic using
`build_native.py --attack-source`. Preserve the source and object fingerprints.
Test actual `GetWeaponDamage` for a held-Monk weapon, ordinary Warrior weapons,
an unheld-class weapon, a race-ineligible weapon and a level-65-required weapon.
Re-run the exact pilot and matched caster controls, then the melee gear/AA matrix.
The verifier must distinguish normal weapon hits from monk special attacks.

Manual QA: on level-50 WAR/CLR/MNK, equip 662038 and confirm normal one-hand-blunt
hits against a dummy, Lord Nagafen (32040, Solusek B) and Lady Vox (73057,
Permafrost). Confirm item stats, recommended-level scaling, Flying Kick/Tiger Claw
buttons and their independent cooldowns. Verify WAR/CLR/WIZ cannot use 662038;
ordinary Warrior weapon 662035 still hits; race-ineligible 5100 and level-65-required
24587 remain unusable. Check a bot with its existing equip-any-class/race settings
to confirm the preserved non-player behavior. In-game timing, client display and
bot behavior are not proven solely by the diagnostic.

No live binary replacement or restart is part of this diagnostic step. Production
requires the usual build/restart and explicit test-branch QA; main requires the
owner's sign-off.
