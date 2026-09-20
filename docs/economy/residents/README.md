# Named tunnel residents

September 20, 2026 candidate. Six additional residents; the ten market traders,
their prices and finite stock are unchanged. Not activated or accepted in game.

| NPC | Appearance | World X,Y,Z |
|---|---|---|
| Sortre Blackdragon (999520) | Dark Elf warrior, Crafted, two Short Swords of the Ykesha | -340,-1645,3.75 |
| Camil Swiftwolf (999521) | High Elf paladin, Armor of Ro, Ghoulbane, Kite Shield | -275,-1695,3.75 |
| Rekk Diver (999522) | Halfling rogue, black chain, two daggers | -185,-1645,3.75 |
| Nalin Shadowbane (999523) | High Elf paladin, Valorium, SoulFire two-handed sword | -115,-1695,3.75 |
| Trift (999524) | Human warrior, level 12, Bronze | -335,-1760,3.75 |
| Khalure Ser`Tiras (999525) | Wood Elf druid, leather, Golden Efreeti Boots | -55,-1750,3.75 |

Dark Elf was confirmed by the owner. Valorium is the Classic paladin planar set
from the Plane of Fear ([P1999 reference](https://wiki.project1999.com/Valorium_Armor)).
SoulFire and ordinary daggers fill unspecified weapon choices; no equipment is
awarded, sold or added to loot. Persistent native materials, item colors and
weapon models display costumes to both arriving and reconnecting clients.
The server's current Ghoulbane/dagger model IDs are retained; exact client
appearance still needs QA. Black chain uses RGB 12,12,12 because zero means
untinted in the native NPC loader.

Trift tells one of four Butcherblock/corpse/goblin stories in actual OOC every
three to five minutes while clients are present. Each resident has hail dialogue.
Khalure offers explicit destination links on hail and moves only the requesting
player, without a fee or bind change. Range, base instance, current era, level,
combat, casting, crowd control and repeat-click checks apply. Native MovePC
retains zone restrictions; invalid/unknown era values fail closed.

## Ring catalog

The current Classic menu contains North Karana, West Commonlands, Toxxulia,
Butcherblock, Lavastorm, South Ro, Feerrott, Steamfont and Misty Thicket. Explicit
future entries add Dreadlands at Kunark; Iceclad, Great Divide, Wakening Lands,
Cobalt Scar and Surefall at Velious; four Luclin destinations at Luclin.
This is a reviewed catalog through Luclin, not automatic support for later eras.
Revisit it during expansion promotion. Surefall's spell is late Velious even
though the zone itself is Classic. Era is rechecked on each clicked link.

Coordinates are world X,Y,Z, converted from the wiki's Y,X,Z convention. The
curated Classic zones avoid PEQ spells that now point at replacement zones.
Sources: [Druid spell lines](https://wiki.project1999.com/Druid/Spell_Lines),
[Circle of the Combines](https://wiki.project1999.com/Circle_of_the_Combines),
[travel guide](https://wiki.project1999.com/Travel_Guide), and live PEQ zone/item
metadata captured in `rings.json` and `source.json`. No web requests run in quests.

## Activation prerequisite

**Do not activate Khalure until the Lavastorm map prerequisite is resolved.**
The live zone row names `lavastorm_v0.map`, which is absent. The installed
`lavastorm.map` is newer terrain and fails the Classic landing. The existing
`lavastorm_orig.map` passes ground/headroom checks at the Classic ring.
Its SHA256 is `1d4f49fa9e5bd0bf6e8511b1d8f5a42536d6e633db9ecf04430258f02dc03d94`.

During approved stopped-server activation, verify that source hash and create
the missing `maps/base/lavastorm_v0.map` as a byte-identical copy. Refuse to
overwrite an existing differing target. Do not change the zone row, replace
`lavastorm.map`, or modify the original client. Then rerun the geometry verifier
without `--verify-lavastorm-source`, using newly staged probe inputs. The normal
verifier refuses missing configured maps. Its optional source-verification mode
records a prerequisite, not a completed installation.

After a verified full backup with world/zones stopped, apply `forward.sql` and
install both `tunnel_residents.pl` and `tunnel_resident_data.pl` plugins plus
quests `ecommons/999520.pl` through `999525.pl`. Combine with the market's paired
binary activation procedure in [QA](../QA.md). This follow-up adds no C++ change.
Setup rejects identity/name/tint-reference collisions, altered item visuals,
unexpected triggers, nontransactional tables and coordinate-format drift.

## Exact In-Game QA

1. Use the approved QA client and a normal account in base East Commonlands.
   Visit each position above. Confirm names, races, classes, armor coverage and
   colors, weapons and shield; Nalin has a two-handed sword and no offhand.
   Khalure's boots must differ from his leather. Trift must con level 12.
2. Inspect from two clients, zone out/in and reconnect. Costumes must persist
   without floating, clipping into walls, missing equipment or overlapping the
   existing hub/traders. Test both Classic/Luclin model settings used by players.
3. Hail all six. Wait ten minutes with OOC enabled, then disable OOC. Trift's
   bounded story uses OOC filtering, names Butcherblock and the goblin, and
   mentions his missing corpse. Existing auction cadence stays independent.
4. Hail Khalure. Confirm exactly nine Classic destinations, with no Dreadlands,
   Surefall, Velious or Luclin links. Visit every offered ring, including
   Lavastorm with the approved client; confirm the actual stones, safe footing,
   correct zone, unchanged bind and no fee. Use existing return routes/recall.
5. Try old/forged future links, more than 100 units away, in combat and while
   casting. No travel should occur. Rapid repeated clicks must not double-zone.
   In an isolated QA copy, verify Kunark/Velious unlocks and stale-link rejection
   after era downgrade using the declarative era tooling, never ad hoc live rules.
6. Give wrong items and mixed currency to each resident. Everything must return.
   Residents must not drop their costumes or expose merchant inventories.
7. Repeat the existing market buying/selling and two-client checks. Six new
   residents must not change the ten traders' stock or saved state.

## Rollback and reproduction

With a fresh backup and stopped server, `rollback.sql` validates exact owned
rows and outside references before deleting only these six sets. It invalidates
only their base-EC non-corpse saved spawns, retaining corpses, other instances,
existing traders and all player items/money. Remove only their six quest adapters
and two plugins. Keep the corrected Classic map alias if other zone content uses
it; do not restore the known missing-map condition merely to remove residents.

Run from the candidate root:

```powershell
python -m unittest discover -s tools/tests -p test_tunnel_residents.py -v
python tools/tests/rehearse_tunnel_residents.py E:/EQ_Local_Dev/artifacts/living-economy-20260920
```

Run `tools/tests/tunnel_residents_quests.t` under server Perl with the staged
server-mods root as its argument. Run `probe_tunnel_residents.py` in the container
with the staged package and compiled native map probe. `geometry.json` records
five ground/headroom samples for each of 25 positions, with the uninstalled
Lavastorm prerequisite clearly marked. Disposable SQL tests never write live PEQ.
