# Cazic Thule and level-50 Classic gear

All four builds died against the original Plane of Fear boss on all three seeds. At 24,000 HP, two builds defeated Cazic on all three seeds after spending 199 AA points. WAR/CLR/MNK took 13–14½ minutes. MAG/NEC/SHM took 4–7 minutes with three prepared pets. These fights support a player QA release. The full zone assist, positioning in Cazic’s room and player tactics still need in-game testing.

| Four level-50 builds, 199 AA | Original | 32,000 HP trial | 24,000 HP candidate |
|---|---:|---:|---:|
| WAR/CLR/MNK | 0/3 | 0/3 | 3/3 |
| MAG/NEC/SHM | 0/3 | 3/3 | 3/3 |
| WAR/PAL/MNK | 0/3 | 0/3 | 0/3 |
| WAR/CLR/WIZ | 0/3 | 0/3 | 0/3 |

The two trials differ only in HP. On the original row, all 12 fights ended in 6.75–20.80 seconds. On the 32,000-HP trial, WAR/CLR/MNK died twice and reached the 900-second limit once. Each had 5,589–6,465 HP still to remove. On the candidate, the same three players finished with 1,142–3,818 HP. On the single zero-AA seed only the pet build won. On the single 500-AA seed the Monk/Cleric and pet builds won. The Paladin/Monk hybrid died with 2,138 boss HP remaining at 500 AA.

## Encounter settings

| NPC type 72003 | Original | Candidate |
|---|---:|---:|
| Level | 70 | 55 |
| HP | 451,000 | 24,000 |
| HP regeneration per tick | 194 | 13 |
| Minimum and maximum melee damage | 223–603 | 85–218 |
| Attack delay | 13 | 32 |
| Armor class | 504 | 397 |
| ATK and accuracy | 100 each | 0 each |

The prepared NPC retained zero HP regeneration per second, the original five resistances, quadruple attack, Rampage, class abilities, melee Panic proc and cast Invoke Fear. The fixture added a level-255 entry for Avatar Power (808) on Cazic’s child list 116. This shadows the inherited spell from list 27. The native trace recorded no Avatar Power events in the 20 final candidate fights. It recorded both Invoke Fear and Panic. Reducing HP to 48,000 and removing the push alone had left all four builds dead inside 20 seconds on a preliminary seed.

The damage range matches Lord Nagafen. The level, AC, ATK, accuracy and regeneration match Classic Innoruuk, NPC 76007. Fresh construction matters because the server derives NPC skills from the initial level.

## Reproduction and scope

The retained November 12 native diagnostic ran against its matching item and spell caches. The isolated MariaDB fixture used static content from the November 27 LocalDev backup and four synthetic multiclass records. The database contained zero accounts and zero character profiles. The arena exercised native attacks, abilities, resists, casting, resources and fixed decision policies on the Solusek B map. It omitted the zone quest and other Plane of Fear spawns. The Hailstone shipping zone and subsequent gear changes require player confirmation.

The server accepted a prefix of the previous native purchase sequence under each budget. The 200-point budget spent 199. The four gear sets used all 20 slots. Their base items have a positive, expansion-zero spawn and loot path in the current fixture from an NPC level 55 or lower. The catalog selection excluded Cazic, Fabled sources, Jaggedpine and both Hate zone versions. These are advanced quality-tier sets. Gear acquisition time was outside the simulation. [Equipment and source NPCs](equipment.json)

The five archived cohorts contain 44 encounters. The raw result hashes, RNG seeds, packet counts, actual AA spend and terminal HP are in [measurements.json.gz](measurements.json.gz). [inputs.json.gz](inputs.json.gz) contains the exact candidate inputs at all three budgets. With the [November 12 native encounter fixture](../../../items/classic-raid-augments/balance/README.md) prepared in its isolated database and the candidate settings above applied, run `python3 /path/to/balance/replay.py melee 200 1112` from its `/tmp/nightcap-balance-*` working directory. The replayer checks the binary, database, synthetic population and candidate settings before running.
