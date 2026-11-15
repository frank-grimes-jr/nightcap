# Classic augment and worn-effect stacking

A level-50 human paladin wore 20 Classic equipment pieces and an arrow, with no purchased AAs, buffs, pet, charm or power-source training item. The incoming attacker and the unaugmented host items were held constant within each dodge comparison. The 23 configurations used the current production item and spell caches, the shipping zone objects and production default numeric character, spell and combat rules. The zone diagnostic used an isolated balance database and an in-memory character. [Loadout IDs, direct calculations and avoidance trials](measurements.json). The [native probe](probe.cpp) reads the [fixture](fixture.json) through the isolated zone test entry point. It checks item eligibility and reads the resulting character bonuses. Each measurement of avoidance reuses the same random state within a run.

| Equipped configuration | HP | Mana | Healing Amount | Spell Damage | Worn dodge |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full raid hosts, empty sockets | 3434 | 3477 | 124 | 127 | 10 |
| Stock augments and Frostbound Pearl | 3787 | 3794 | 407 | 402 | 10 |
| Plus eight Healing scales | 4747 | 4754 | 487 | 402 | 10 |
| Plus eight Magic scales | 4747 | 4754 | 407 | 482 | 10 |
| Plus four Healing, three Magic and one Dodging | 4747 | 4754 | 447 | 432 | 10 |

Each fully scaled set gained 960 HP and mana over stock augments. An Ascended scale and a type-22 Pearl worked together on the Golden Efreeti Chestplate. Healing and damage totals remained below the respective 750 caps. In 256 direct calculations with the mixed set, Greater Healing produced 2063 before overheal and Dismiss Undead produced 1100 before resists. The corresponding empty-socket results were 809 and 348. These are spell-effect measurements, independent of encounter criticals or resists.

One Dodging scale supplied the same +10 worn dodge as the Gauntlets of Fiery Might or Efreeti War Shield. Equipping all three, or eight scales, kept the modifier at +10. The control dodged 1079 of 20,000 frontal melee checks. Every +10 configuration dodged 1251 in the paired sequence. Eight scales supplied 40 raw damage shield, capped to 30 on this character.

The RoF2 direct augment handler had ignored the socket-compatibility boolean. The correction checks the socket type, visibility, augment restriction and whether insertion or replacement is appropriate before changing inventory. A matching occupied socket supports swapping. Item and spell cache values, effects and caps require no migration. Both shipping builds produced identical measured stats and direct spell values for all legal loadouts.

Production verified all 12 zone workers on gameplay main acb232e1. The native release uses the existing item and spell caches and signed client. [Post-open verification](production-verified.json).

## Client QA

On test, equip level-50 Classic gear in Solusek’s Eye. Insert an Ascended scale into a type-7 Golden Efreeti Chestplate socket and a Frostbound Pearl into its type-22 socket. With a Perfected Augmentation Distiller, swap the type-7 scale and verify the old augment on the cursor, both icons and the Pearl after relog. Compare one scale, the Efreeti War Shield, and both with the Gauntlets of Fiery Might. The native diagnostic covers stat calculations and socket policy. Visible RoF2 inventory and relog acceptance remain open.
