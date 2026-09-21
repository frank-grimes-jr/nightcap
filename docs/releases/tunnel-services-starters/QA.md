# Owner in-game QA: tunnel services and starters

Manual QA not yet executed. The release is live on OVH as of September 21, 2026;
[activation evidence](ACTIVATION.md) records the runtime. Use a normal account
and current launcher; record character,
primary/held classes, client release, server binary manifest and result for every
row. Use a separate test character when spending currency or consuming stock.
Coordinates below are **X, Y**; EQ `/loc` presents **Y, X, Z**. All locations are
in East Commonlands (`ecommons`, zone 22), original instance 0, tunnel main room.

## Spell display and filter follow-up

Close the old launcher and open the desktop **Nightcap** shortcut, which now uses
`E:/Nightcap/nightcap-launcher.exe`. This installation was updated through the
signed production updater to game release **2026092006**, including proxy
**0.5.0**; all 22 managed files verify. The earlier installation had 2026092003 /
0.4.2-dev and its shortcut bypassed the launcher. No additional client release is
required by the tunnel deployment.

On the affected character, keep **show spells I cannot use** disabled and open a
spell merchant. Spells usable by the character's held classes should appear.
Inspect an affected scroll: its real class level should replace 255, and the
spell inventory level column should show the expected level instead of `--`.
Confirm unowned-class and above-level spells remain restricted. Record the spell
name, primary/held classes and character level for any failure. Installation and
hook inspection passed; this runtime behavior has not been visually verified.

## Arrival, appearance and movement

1. Recall/travel into EC at the existing arrival near X=-190, Y=-1725. Confirm
   clear ground, access to bank/bags/soulbinder and all travel doors, with no
   overlapping NPCs or blocked exits. Original binds and travel still work.
2. Walk through the four class groups below. NPC pairs should face conversational
   centers with varied gaps/headings, not uniform rows. Confirm feet on ground,
   reasonable appearances, readable titles and no floating/stacked NPCs.
3. Observe Alwen, Borin, Cassia, Darik, Esme, Galen, Hessa and Iven for five
   minutes. Each should walk, pause and reverse along its patrol. Hail each while
   moving; confirm response and resumed movement. No wall walking, falling,
   snapping, door obstruction or combat/aggro. Leave/re-enter and test once after
   a controlled restart to verify saved-state handling.

## Basics and spell components

Hail/open **Tessa**, NPC999600 at **(-153,-1710)**. There should be 50 distinct
listings. Buy food, water, bandages, bone chips, bat wings, malachite, tiny daggers,
and a Bard instrument from each family. Wallet deduction and stack quantities
must match the visible quote; close/reopen/relog preserves purchases.

On primary Magician, Necromancer, Enchanter, Shadow Knight, Shaman and Beastlord
characters, use an allowed pet spell needing its listed reagent. Buy that reagent,
cast, verify the right pet and normal component consumption. Check one reusable
focus spell and a Bard song/instrument. Compare any missing-component error with
`layout.json`'s full reagent list; none from the legal pool should lack a vendor.
Buy Plains Pebble and verify a positive quote, one item, correct deduction and
no buy/sell profit route under current merchant rules.

## Tradeskills and stations

Open every listed supply NPC; later pages must be separate NPCs, not silently
truncated lists. Check the required portable container, ordinary ingredients and
one actual low-trivial legal combine for each crafting discipline. Recipe success
may depend on skill; acceptance is the correct container/recipe attempt and
normal consumption/result. For fishing, equip pole/bait and fish at valid water.
No crafting class/era/skill prerequisite is removed by these merchants.

| Discipline | NPC names | First merchant X, Y | Listings | Required access |
|---|---|---|---:|---|
| Smithing | Berrin, Torvik, Haldra | -360, -1802 | 318 | Forge |
| Pottery | Pella | -310, -1840 | 119 | Pottery wheel AND kiln |
| Baking | Odel, Mara | -100, -1835 | 175 | Oven and mixing bowl |
| Brewing | Fenna | -54, -1795 | 48 | Brewing barrel |
| Tailoring | Aven | -357, -1560 | 142 | Loom and large sewing kit |
| Jewelcrafting | Della | -340, -1590 | 104 | Jeweller kit |
| Fletching | Corin | -195, -1825 | 65 | Fletching kit |
| Tinkering | Nelli | -29, -1710 | 91 | Toolbox; eligible Gnome |
| Alchemy | Yara, Fenrik, Mosslin, Usha | -45, -1657 | 465 | Medicine bag; eligible Shaman |
| Poison | Rusk, Vessa | -392, -1714 | 217 | Mortar/pestle; eligible Rogue |
| Research | Ilyen, Meris, Davin | -133, -1587 | 388 | Lexicon and class tomes/containers |
| Fishing | Finn | -69, -1744 | 17 | Pole, bait and tacklebox |

Open/close each fixed station and complete a suitable combine. Confirm its model,
name and container type are right and that another player can use it after it
closes. Required stations (X,Y):

- Loom: (-379, -1575), object 999600.
- Oven: (-116, -1817), object 999601.
- Forge: (-372, -1822), object 999602.
- Brewing Barrel: (-32, -1812), object 999603.
- Pottery Wheel: (-326, -1857), object 999604.
- Kiln: (-288, -1854), object 999605.

## Trainers and starter packages

Create one normal character per class below (allowed race/deity). On **first
login**, verify exactly 100 platinum, the named primary-class weapon equipped,
and a robe equipped with exactly 10 AC and +5 to the stat shown. Inspect item
links, usable classes/races, no-trade flag, visuals and the actual stat increase.
Use a weapon swing/cast and confirm normal skill behavior. Then zone, camp/relog
and reconnect: money/items must persist without a second grant.

At that character's trainer, hail/right-click and open the actual training
window. Exercise one eligible skill with available points and verify the expected
cost/persistence. Confirm an unrelated class trainer rejects a character who does
not hold that class, while an eligible secondary/tertiary class still follows the
existing multiclass training policy. Current server/client trainer issues remain
gates if the window or skill list is wrong.

| Primary class | Trainer | X, Y | Robe stat | Weapon damage / delay |
|---|---|---|---|---|
| Warrior | Garran | -352, -1703 | +5 STR | 6 / 28 |
| Cleric | Elowen | -257, -1584 | +5 WIS | 6 / 30 |
| Paladin | Aldric | -243, -1553 | +5 STR | 6 / 28 |
| Ranger | Maren | -258, -1802 | +5 STR | 6 / 28 |
| Shadow Knight | Veyra | -206, -1568 | +5 INT | 6 / 28 |
| Druid | Thalen | -230, -1767 | +5 WIS | 6 / 30 |
| Monk | Joren | -332, -1665 | +5 STR | 6 / 30 |
| Bard | Liora | -206, -1775 | +5 DEX | 6 / 28 |
| Rogue | Silas | -301, -1678 | +5 DEX | 5 / 24 |
| Shaman | Korra | -227, -1597 | +5 WIS | 6 / 30 |
| Necromancer | Velis | -81, -1619 | +5 INT | 5 / 24 |
| Wizard | Orwen | -68, -1577 | +5 INT | 5 / 24 |
| Magician | Mirel | -35, -1594 | +5 INT | 5 / 24 |
| Enchanter | Sarina | -54, -1629 | +5 INT | 5 / 24 |
| Beastlord | Torren | -221, -1817 | +5 WIS | 6 / 30 |
| Berserker | Brakka | -316, -1716 | +5 STR | 11 / 45 |

On an **existing** character, record wallet and equipped items before the update,
then log in/relog: no 100pp top-up or item replacement. Selecting/releasing a
secondary class must not issue a new starter package. Confirm the latest inventory
class refresh still appears immediately. Backend packet replay/failure tests are
automated; report any creation failure instead of repeating grants manually.

## OOC and auction

1. Enable OOC/auction filters on two clients in EC. Observe for 10 minutes. Both
   should hear the same resident/seller at the same time. Names in channels must
   have no surname/title/underscores; normal character chat remains unaffected.
2. OOC should arrive roughly every 45-80 seconds from multiple old/new residents,
   with varied lines and no immediate repeated speaker or per-voice line. Trift
   has six Butcherblock/goblin/corpse variations. Hails should also vary.
3. Auctions should arrive roughly every 30-55 seconds from the 16 traders below,
   showing real item links/prices. Over several announcements observe `//`, `--`
   and commas, changed phrasing and item order. Links must open intact.
4. Hail a seller with two items, purchase one through its link, confirm exact
   wallet cost and item. Rehail: the other item remains, bought item is sold out.
   A second client clicking an old quote must not receive a duplicate or lose
   money. Repeated clicks, full bags, insufficient funds and lore conflicts must
   fail safely. Camp/relog verifies wallet/item persistence.
5. Test a buyer with two items: sell one supported unmodified item through the
   normal link flow. Exactly one item disappears and the quote amount arrives;
   the other wanted item remains. Ordinary item/cash hand-in returns unchanged.
6. Check an existing city merchant find still works. A controlled world restart
   rotates to 20 sales, 12 buys and ten finds; merely zoning or reopening does not
   restock. Trades remain in the audit. Empty zones send no chatter.

| Role | NPCs |
|---|---|
| Sellers | Rellan, Mirielle, Caelith, Bromli, Tamsin, Varkyn, Doran, Mella, Kavin, Brinna |
| Buyers | Harlon, Nimri, Grukk, Selindra, Osric, Tyra |

## Acceptance record

- [ ] Arrival, door/service routes and natural layout accepted.
- [ ] All eight walkers and post-restart placement accepted.
- [ ] Basics, all tested pet reagents/instruments and positive pricing accepted.
- [ ] All twelve disciplines, six stations and portable containers accepted.
- [ ] All sixteen trainers and starter packages accepted; existing players unchanged.
- [ ] Varied first-name OOC and real multi-item auction/trades accepted.
- [ ] Owner names/date/build and any remaining failures recorded before main promotion.
