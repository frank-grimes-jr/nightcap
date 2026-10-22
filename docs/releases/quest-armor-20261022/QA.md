# In-game QA: substantial class armor

Status: **pending**. Run after authorized activation; no item grants to existing
characters, owner acceptance or balance pass is claimed by script tests.

1. On a character with the relevant held class, record the materials and coin
   before each hand-in. Complete each selected recipe with its named NPC.
   Receive exactly one corresponding **(Ascended)** piece, consume the original
   requirements, and retain the original XP/faction behavior. The eight Crafted
   recipes are listed below; the other families' exact installed requirements
   are captured in `production-reference.json` and unchanged in the candidate.
2. Repeat a successful recipe with a second complete material set: another
   Ascended piece. Repeat without the complete set: no armor. Partial/wrong items
   follow the existing return path with no upgrade; test an extra unrelated item
   alongside a successful hand-in too. Preserve repeated inputs and stacked-gem
   behavior. Do not use irreplaceable customized items for legacy resizing tests.
3. Test one Lua SummonItem reward (Crafted), one Lua QuestReward reward (Walthin),
   one Perl check_handin reward, and Leaf's coin branch. Use full inventory plus
   an occupied cursor; confirm native cursor queuing, exactly one reward and no
   material/reward loss after clearing it. Inspect/equip and relog with the armor.
4. Controls: basic Banded crafting, Lambent-gem intermediate exchange and ordinary
   unaudited hand-ins retain their original outputs. Epic, dungeon, Hunt and
   Reforging Box behavior stays separate. No normal-to-Ascended sizing exchange.
5. Compare a representative level-appropriate encounter in the old and new gear,
   holding classes/AAs/buffs/pets constant. Record incoming damage, kill time and
   sustain; confirm meaningful difficulty and worthwhile dungeon rewards remain.

## Exact Crafted hand-ins â€” South Karana

Give the items below together. IDs disambiguate similarly named materials.

| NPC | Materials | Expected item |
|---|---|---|
| Shakrn Meadowgreen | Fire Totem 13743 + Ruby 10035 | Crafted Helm (Ascended) 604173 |
| Shakrn | Aviak Charm 13737 + 2 Star Rubies 10032 | Crafted Gauntlets (Ascended) 604178 |
| Shakrn | Frost Totem 13744 + 2 Sapphires 10034 | Crafted Plate Boots (Ascended) 604180 |
| Shakrn | Griffon Eye 13739 + 2 Fire Emeralds 10033 | Crafted Vambraces (Ascended) 604176 |
| Ulan Meadowgreen | Optic Nerves 14019 + Sapphire 10034 | Crafted Bracers (Ascended) 604177 |
| Ulan | Shining Silver Circlet 13742 + 2 Star Rubies 10032 | Crafted Greaves (Ascended) 604179 |
| Ulan | Rune pieces 13698 + 13699 + 13738 + Fire Emerald 10033 | Crafted Pauldron (Ascended) 604175 |
| Ulan | Werewolf Talons 13746 + 3 Rubies 10035 | Crafted Breastplate (Ascended) 604174 |

Each complete Crafted turn-in retains 25,000 quest EXP (before existing server
and character modifiers) and its Ding call.

## Other required representative branches

| Zone/NPC | Exact inputs | Expected output |
|---|---|---|
| Solusek Ro / Cryssia Stardreamer | 10564 + 10563 + 10128 | Lambent Bracers 604156 |
| Solusek Ro / Walthin Fireweaver | 2318 + 10119 + 10561 | Lambent Boots 604159; original 1,000 EXP |
| Solusek Ro / an undead knight 80000 | 12292 + 12291 + 16507 | Darkforge Gauntlets 603144 |
| Solusek Ro / an undead knight 80001 | 12283 + 12284 + 2 x 13921 | Darkforge Helm 603140 |
| Kithicor / Gandari 20085 | 10569 + 10546 + 10033 | Ivy Etched Bracers 603189 |
| Kithicor / Leaf Falldim 20066 | 12305 + 12306 + 2,000 gold equivalent | Ivy Etched Boots 603192 |
| Lake Rathetear / Vrynn 51059 | 3064 + 10073 + 19039 + 19041 | Totemic Boots 604941 |
| Lake Rathetear / Kyralynn 51058 | 3056 + 19050 + 19036 + 19044 | Totemic Breastplate 604946 |

All other catalog branches must also be completed before claiming full-family
acceptance. A passing representative test proves only that branch and scenario.

## Shadow Knight epic dependency â€” separate later-era regression

In an authorized test environment with Overthere available, give Kurron Ni
Darkforge Helm, Breastplate and Greaves with at least900 platinum. Cover all
Normal, all Ascended and a mixed set. With the integrated tier-hand-in candidate,
also test Polished and Exalted pieces, including mixed qualities. Expect the original +7 Truespirit change
and exactly one Letter to Duriek18099 added to the NPC per spawn. Repeat on the
same spawn: no duplicate letter. A fresh spawn resets that gate. The integrated native compatibility correction explicitly refunds submitted
coins once after success; this candidate adds no900pp sink. With899pp,
a missing piece or an unrelated/epic identity, no success/letter occurs.
Unrelated items return through the original helper. This does not open Kunark
on the Classic server; use the controlled test environment for this regression.

## Palwar correction (committed offline October22; native confirmation pending)

The authorized guarded correction committed with zero clients and a login hold. On login, verify Vambraces,
Breastplate and Plate Boots show Ascended, retain their instance customization and
equip normally. The captured ordinary definitions give 24/44/24 AC respectively;
the Breastplate has 50 HP. Relog and verify persistence. Record this separately
from testing a fresh quest hand-in and from general progression/balance acceptance.
