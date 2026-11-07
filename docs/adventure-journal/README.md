# Adventure Journal — The Last Lantern

**November7: deployed for live QA.** [The Last Lantern](CAMPAIGN.md) carries one
playthrough through twelve chapters to level50: returning companions, eight
personal progression armor pieces, four legal fits, earned refits and a planar
finale. Sixteen Task definitions include five alternative oath trials. The paired
OVH runtime, signed client2026110701, wiki and private guide are published.
[Release evidence and forward recovery](release-20261107/README.md) ·
[Exact normal-player QA](release-20261107/CAMPAIGN-QA.md). Player appearance,
whole-scene/path and combined-balance acceptance remain open.

The original eight-task catalog below remains the underlying path/spell contract,
not the full release package. Use last-lantern-setup.sql and the reviewed campaign
operator for the expansion; the old setup.sql alone cannot install this runtime.

## Historical eight-task foundation

The October1 catalog below supplies the original shared objectives, five path
trials and bounded charm powers. It is retained for audit and is not the full
current release. November7 deployment and remaining player QA are recorded above.

Start at the Ancient Chronicler (NPC 999220) in the East Commonlands tunnel.
Say **journal**. Three shared chapters at levels 20, 25 and 30 lead to five
independently earnable paths at level 35. Any primary class can earn any path.
The Tasks window records progress. The Chronicler provides preparation notes,
the next eligible chapter, earned choices and the remaining shared cooldown.

After finishing a path, choose its **Attune** link, then **Claim Wayfarer's Oath**.
The campaign delivers one charm per character through a permanent receipt. Equip **Wayfarer's Oath [Epic 0.5]** in the charm slot and right-click.
Binder requires one living owned pet targeted within 100 units. Other paths act
on the wearer. Switching earned paths requires the public EC hub, no aggro and
a ready cooldown. Every path shares the same durable ten-minute timer.

| Path | Candidate effect | First two objectives | Final objective |
|---|---|---|---|
| Guardian | 15% melee absorption, 200 total cap, up to 3 ticks | Froglok shin lord; Lord Pickclaw | Xicotl |
| Striker | 6% melee damage modifier, up to 3 ticks | Butler Syncall; Maid Issis | Garton Viswin |
| Arcanist | 5% spell damage focus for DD/DoTs, up to 3 ticks | Battlewizard Unak; High Priest Zaharn | Lasna Cheroon |
| Warden | 10% max HP, capped at 400 base healing before normal bonuses | Khrix Fritchoff; Maid Issis | Garanel Rucksif |
| Binder | One pet: 8% melee modifier and 10% absorption, 150 cap, up to 3 ticks | King Thex'Ka IV; Mynthi Davissi | Xicotl |

The relic has 5 AC, 35 HP/mana and 3 classic resists. Its campaign policy is personal, no trade,
all class and level 35 required. It has no augment slots, heroics, regeneration
or random tiers. Additional paths unlock choices on the same charm.

## Evidence and scope

- [Specification](SPEC.md), [decision](../adr/0051-adventure-journal-archetype-epic.md), [canonical catalog](catalog.json).
- [Database rehearsal](database-evidence.json): isolated schema, collision and
  expansion-gate refusal, injected mid-write rollback, retained-data disable,
  237-field client/server spell match, durable cooldown and concurrent reservations.
- [Staged client evidence](client-evidence.json): six appended spells; every
  existing source byte retained. This is an asset candidate, not a signed release.
- [Native build evidence](native-evidence.json): full world/zone build, unchanged
  source fingerprints and matching feature-source hashes; not installed.
- [Exact native and balance QA](QA.md); [installation/recovery](RELEASE.md).

The campaign uses existing open-world Classic named encounters. Normal group
and pet kill credit applies; there are no random proof drops or new wave
instances. Named spawn waiting and travel are part of this candidate and must
be evaluated in QA. Task history is per character. Account-wide discoveries,
an automatic gear-upgrade adviser and bespoke waves are future work.

## Reproduce automated checks

Run from the repository checkout in PowerShell:

```powershell
python tools/epic05.py
$env:PYTHONPATH='tools'
python -m unittest discover -s tools/tests -p 'test_epic05*.py' -v
python -m unittest discover -s tools/tests -p 'test_client_gameplay_assets.py' -v
python -m unittest discover -s tools/tests -p 'test_gameplay_policies.py' -v
perl tools/tests/epic05_quests.t .
perl tools/tests/test-pok-chronicler-dialogue.pl ./server-mods/quests/ecommons/The_Ancient_Chronicler.pl
python tools/tests/rehearse_epic05.py
```

Native fixtures compile actual task matching/movement and duration functions.
Set `EQEMU_SOURCE` to the complete native checkout if it is not at
`E:/EQ_Local_Dev/akk-stack/code`. MSVC is used on Windows; `c++` elsewhere.
The MariaDB rehearsal requires the local Docker stack and creates/drops only
a randomly named `nightcap_epic05_qa_*` schema. It never updates PEQ.
