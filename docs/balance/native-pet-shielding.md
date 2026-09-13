# Focused owner shielding comparison

Date: 2026-09-13. No live changes; caps remain 250/250.

The existing pet baseline uses Talisman of Altuna 168 on the owner and all pets.
Arch Shielding 67 offers a different HP/armor/resistance combination, but does not
stack with the owner Talisman. Compare replacing only the owner's spell, with and
without Resist Magic 64 on the owner and all three pets. Pets retain their original
Talisman and haste/regen/resistance preparation. The native spell definitions and
dragon defenses are captured in pet-shield-source.json.

The comparison uses zero, launch maximum (165 spent) and later maximum (306 spent)
at seeds 1729–1731 against Nagafen and Vox: 36 fights total. Gear, purchases, eight
combat gems, commands and all non-preparation inputs remain identical. Each native
initial build matches its paired baseline. Verification requires Arch Shielding
to remain on the owner, Talisman to be absent there, and the optional Resist Magic
buffs to survive preparation; accepted casting alone is insufficient.

| Actual AA spent | Arch: Nagafen | Arch: Vox | Arch + Resist Magic: Nagafen | Arch + Resist Magic: Vox |
|---:|---:|---:|---:|---:|
| 0 | 0/3 | 0/3 | 0/3 | 0/3 |
| 165 | 0/3 | 3/3 | 2/3 | 3/3 |
| 306 | 1/3 | 3/3 | 0/3 | 3/3 |

These sample counts do not establish a reliable improvement or win probability.
Arch alone does not resolve the launch Nagafen failure. Adding Resist Magic
improves that particular launch sample set, but not the deeper-AA set. Buff choice
changes recovery time, native timing and RNG consumption. Retain the baseline and
the comparison without asserting that extra AAs or resistance inherently hurt.

The original launch Nagafen seed-1729 trace contains 131 healing requests and 35
debuff/DoT requests with none of those buffs observed landing. Captured Nagafen
MR/PR/DR are all 340. This identifies resistance and support pressure for future
controller/mechanics work; it does not justify treating every interrupted or
unsuccessful cast as a proven resist. The source query also confirms Malosi 112
is the legal Shaman-level-48 debuff and Blizzard Blast 510 is level 44.

The simulator binary and server source did not change for this experiment. The
Python verifier now derives the declared owner armor spell from the actual
preparation actions instead of requiring Talisman in every comparison. The three
new input/evidence tests cover exact permitted input differences, all 36 native
cases, unchanged initial builds and rejection of a missing chosen buff. The final
isolated account, character, owned-AA and inventory fixtures are empty after
removing only the two verified synthetic reagent rows.

This ends the focused preparation check before packaging the existing server
fixes for fresh compilation and in-game QA. No additional broad sweep or global
balance change is selected from these results.
