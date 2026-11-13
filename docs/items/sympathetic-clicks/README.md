# Classic sympathetic item clicks

## Two earned Classic clicks

Ascended Runed Lava Pendant (610338) grants Sympathetic Strike I. Its stock source is a lava elemental in Solusek's Eye. Ascended Moonstone Ring (610150) grants Sympathetic Healing I. Its stock source is a frenzied ghoul in Lower Guk. Both are all-class jewelry with existing quality upgrades. This puts the rewards on distinct mid- and late-Classic named camps, lets a player keep their usual weapon, and makes both buffs available to any multiclass character with a qualifying spell. A player can obtain the Ascended version through the ordinary drop or upgrade route. Normal, Polished and Exalted copies remain useful toward the existing upgrade recipe. The Ring retains Extended Range II.

[Named NPCs, spawn and loot weights, full content rehearsal and client pairing](content/README.md).

The THJ item guide supplied the idea of a class-usable click on top-tier gear. Nightcap chose different sources because a starter weapon or common morning star sets a much lower acquisition bar. Nightcap's rank requirements, amounts and future releases are independent balance decisions. [THJ item guide](https://thj.gileadgames.net/equipment-guide/symp-items/).

## Rules for the test candidate

Equip and click either Ascended item to cast its self buff, then swap back to your preferred gear. Both buffs can be active. The reusable equipped click takes two seconds. Each qualifying original cast can produce one sympathetic effect on the original recipient.

- Strike requires a landed, single-target direct-damage spell cast from a player's spell gem with a base mana cost of at least 10. Bonus damage from an eligible lifetap does not feed the caster's heal.
- Healing requires a positive-base-mana, single-target direct heal cast from a player's spell gem. The same recipient receives the burst. If an existing worn sympathetic healing focus produces the heal on that cast, it takes precedence.
- A cast with 10 base mana qualifies for Strike even when mana preservation reduces the amount actually spent. A cheaper spell still falls below the threshold. The added amount has its own fixed base. The new effect has no second outgoing gear, focus or critical multiplier. Normal target protections and missing HP can affect the observed amount.
- Proc chains, triggered repeats, area spells, periodic ticks and pet-originated casts do not generate another sympathetic result. The buffs themselves do not change worn ATK, Spell Damage or Healing Amount.

## Release by expansion

The source of truth is [config/sympathetic-eras.json](../../../config/sympathetic-eras.json). Each expansion has an explicit ID matching the server expansion enum, in order from Classic (0) through Torment of Velious (26). A row with no new rank carries previously approved ranks on both lines. Strike and Healing may advance in different expansions. Only rank I has content in this candidate. A copied item, retained buff or character level by itself cannot authorize an unreleased rank. The native all-expansions setting (-1) includes only catalogued, approved ranks. Unknown IDs grant no result.

| Era review | Sources or interactions worth checking before adding any power |
|---|---|
| Kunark | Compare the stock Cone of the Mystics and Gnarled Staff against actual local acquisition, class masks and existing effects. Measure the existing Classic rank on level-60 spells, cheap lifetaps and right-sized heals. |
| Velious | Inspect Staff of the Morning Dew, Bowl of Watery Protection and Cloak of Crystalline Waters. The spreadsheet and THJ guide disagree on the era of some healing items. The Cloak already has a focus in the Nightcap sample. |
| Luclin and Planes of Power | Review Greatstaff of Power and the THJ-listed Plane of Power sources against Nightcap's raid routes. Include healing-focus VI/VII successes and player-earned AAs in the tests. |
| Legacy of Ykesha, Lost Dungeons and Gates of Discord | Verify side-expansion and instanced acquisition separately. Flawless Steel Mask has conflicting source-era labels. A later listed rank or item name supplies a research lead. |
| Omens of War through Torment of Velious | Each of the 19 expansion entries has its own release decision. In each release, retain the carried ranks by default. To add a rank, first identify a stock obtainable item, check existing effects, and test the new expansion's gear, spells, legal AAs, encounter, mana and worn focuses. There is no automatic increase per expansion. |

When preparing a new release, record its chosen item/ID, rank, acquisition route and full before/after item and spell definitions. Check the proposed spell IDs against existing references on later-era gear and other content, including references to IDs with no current spell-table row. Reserve the IDs only once the client and server audits agree. Compare the previous rank against the proposed rank with the same gear. Include normal and cheapest-eligible rotations, both sustained throughput and net mana, and actual healing after overheal. Review pre-unlock, newly unlocked and rollback eras with the buff already present. When a rollback activates an earlier era, the next cast checks the earlier ceiling, even for a saved buff from a later release. Changing caps requires the matching zone binary; adding item or spell definitions also requires a scoped migration, regenerated caches and matching client spell data. Run `python -B tools/sympathetic_eras.py --check --era 0` for Classic or pass the intended expansion ID. The normal era apply and drift-check entry points verify the catalog. New native expansion IDs require a catalog row before shipping a compatible build.

## Wiki impact

The test-branch wiki lists the candidate under **In development**. The public Equipment guide and loot finder continue to describe production. When the owner releases the feature, publish the two item sources, scope and rank values in Equipment, link the guide from Features, add one Change Log entry, and verify the current-era loot pages against the production item rows. This change adds no new commands, NPCs or zones.

## Player QA on test

1. Obtain or inspect the four qualities of each named item on the paired test client. Confirm the click appears on the Ascended copy and Extended Range II still appears on the Moonstone Ring. Check the natural drop route from a lava elemental in Solusek's Eye and a frenzied ghoul in Lower Guk. A single kill can legitimately drop neither item.
2. Equip each Ascended item, click it, remove it and put your usual gear back on. Confirm both buff icons remain. Re-click the pendant to refresh its own buff, then zone and relog. Record the visible item, buff and target combat messages.
3. With a living NPC target, compare the same qualifying single-target nuke before and after activating Strike. Try a sub-10-base-mana cast, a complete resist, a lifetap and a DoT. Check the recipient, number of extra hits and the lifetap return.
4. Try an ordinary gem heal on yourself and an injured ally or owned pet. Repeat at full health, with Healing removed and with an eligible existing worn sympathetic heal. Record effective healing versus overheal and verify the worn heal retains precedence.
5. Compare ordinary and cheapest spell rotations against Lady Vox in Permafrost and Lord Nagafen in Nagafen's Lair using progression gear and fully stacked level-50 gear. Keep the gear and legal AA allocation identical between the buff-on and buff-off parses. Capture mana, kill time and effective healing. Record graphical and encounter acceptance separately.
