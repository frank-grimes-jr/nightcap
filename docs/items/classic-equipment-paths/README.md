# Classic equipment coverage

149 stock families / 596 existing quality definitions. This is an addition pass across offense, defense and sustain, not a defensive-only pass. Existing healing strength and occupied effects are preserved. No custom item, augment, AA rank, spell definition, quest reward, recipe output or native combat formula changes.

## Acquisition review

Captured 19,084 enabled ungated/Classic recipes, 144,437 entries, 117,952 stock-ID item summaries, 1,030 Classic-zone quest sources plus 30 Temple sources. Recipe flags, actual component chains, merchant gates, learned requirements, containers and enchant-scroll access are evaluated. 1590 finished outputs have conservative component reachability; this is not an assertion that every definition is suitable Classic progression. Unresolved forage/quest/ground ingredient paths are held, not declared unavailable.

The Temple of Solusek Ro was incorrectly marked expansion 1 while the live era is 0. The isolated correction changes only zone row357/zone80/version0 expansion to0, with bypass still0. This restores ordinary-player access to Lambent/Darkforge quest givers and the Ro cauldron. Existing Ascended class-quest grants remain unchanged.

Enchanted jewelcraft outputs are distinct from identically named unenchanted/statless outputs. Only the enchanted IDs listed below change. Rank III platinum pieces use high-trivial recipes and tradeable purchased ingredients: an expensive tradeskill alternative, not raid-exclusive power. Named dropped equipment adds offensive alternatives without overriding current casting focuses.

## Power budgets

- New melee haste is10% on ordinary crafted/mid-drop gloves and20% on substantial quest/high-drop gloves. It competes with existing item haste; it does not add to stronger haste gear.
- New worn ATK is5 on crafted shoulders or15 on earned shoulders; one shoulder slot bounds the added contribution. Raw ATK and accuracy are unchanged.
- HP regeneration is head-only1/2, mana regeneration feet-only1/2. Existing stronger effects and item caps remain. Dodge10 and parry/block8 use the strongest corresponding worn effect.
- Damage focus I/II/III has a20% stock endpoint that existing THJ rules amplify to200%. These additions broaden access to that existing pool, rather than add another independent damage multiplier. Direct damage, periodic damage, level limits, duplicate focuses, current damage augments and legal offensive AAs require native measurements.
- Existing Prismatic, raid and Hunt augments remain byte-for-byte unchanged. Weapon procs remain unchanged: player weapon and augment procs can each fire, so broad proc additions need a separate probability/combined-power design.

## Explicit families

| ID | Item | Acquisition | Added focus | Added worn effect |
|---|---|---|---|---|
| 2319 | Black Silk Gloves | stock_drop |  | Speed |
| 2465 | Elf-hide Gloves | stock_drop |  | Speed |
| 3140 | Darkforge Helm | class_quest |  | Regeneration II |
| 3141 | Darkforge Breastplate | class_quest |  | Improved Dodge I |
| 3142 | Darkforge Vambraces | class_quest |  | Improved Dodge I |
| 3143 | Darkforge Bracer | class_quest | Mana Preservation II |  |
| 3144 | Darkforge Gauntlets | class_quest |  | Captain Nalot's Quickening |
| 3145 | Darkforge Greaves | class_quest |  | Improved Parry / Block I |
| 3146 | Darkforge Boots | class_quest |  | Flowing Thought II |
| 3150 | Helm of Ro | ro_quest |  | Regeneration II |
| 3151 | Breastplate of Ro | ro_quest | Improved Healing II |  |
| 3152 | Vambraces of Ro | ro_quest |  | Improved Dodge I |
| 3153 | Bracer of Ro | ro_quest | Mana Preservation II |  |
| 3154 | Gauntlets of Ro | ro_quest | Spell Haste II | Captain Nalot's Quickening |
| 3155 | Greaves of Ro | ro_quest |  | Improved Parry / Block I |
| 3156 | Boots of Ro | ro_quest |  | Flowing Thought II |
| 3170 | Ravenscale Gloves | stock_drop |  | Speed |
| 3181 | Ivy Etched Helm | class_quest |  | Regeneration II |
| 3184 | Ivy Etched Tunic | class_quest | Improved Healing II | Improved Dodge I |
| 3188 | Ivy Etched Sleeves | class_quest |  | Improved Dodge I |
| 3189 | Ivy Etched Bracer | class_quest | Mana Preservation II |  |
| 3190 | Ivy Etched Gauntlets | class_quest |  | Captain Nalot's Quickening |
| 3191 | Ivy Etched Leggings | class_quest |  | Improved Parry / Block I |
| 3192 | Ivy Etched Boots | class_quest |  | Flowing Thought II |
| 3808 | Kedgemail Gauntlets | stock_drop |  | Captain Nalot's Quickening |
| 4153 | Lambent Helm | class_quest |  | Regeneration II |
| 4154 | Lambent Breastplate | class_quest |  | Improved Dodge I |
| 4155 | Lambent Vambraces | class_quest |  | Improved Dodge I |
| 4157 | Lambent Gauntlets | class_quest |  | Captain Nalot's Quickening |
| 4158 | Lambent Greaves | class_quest |  | Improved Parry / Block I |
| 4173 | Crafted Helm | class_quest |  | Regeneration II |
| 4174 | Crafted Breastplate | class_quest |  | Improved Dodge I |
| 4175 | Crafted Pauldron | class_quest |  | Nature's Precision |
| 4176 | Crafted Vambraces | class_quest |  | Improved Dodge I |
| 4178 | Crafted Gauntlets | class_quest |  | Captain Nalot's Quickening |
| 4179 | Crafted Greaves | class_quest |  | Improved Parry / Block I |
| 4385 | Paineel Steel Pauldron | stock_drop |  | Nature's Precision |
| 4405 | Carnal Pauldrons | stock_drop |  | Nature's Precision |
| 4416 | Dwarven Plate Helm | crafted_armor |  | Regeneration I |
| 4418 | Dwarven Plate Collar | crafted_armor | Spell Haste II |  |
| 4419 | Dwarven Plate Breastplate | crafted_armor | Improved Healing II | Improved Dodge I |
| 4420 | Dwarven Plate Pauldron | crafted_armor |  | Endurance |
| 4427 | Dwarven Plate Boots | crafted_armor |  | Flowing Thought I |
| 4428 | Ogre War Plate Helm | crafted_armor |  | Regeneration I |
| 4431 | Ogre War Plate Breastplate | crafted_armor |  | Improved Dodge I |
| 4437 | Ogre War Plate Gauntlets | crafted_armor |  | Speed |
| 4865 | Imbrued Platemail Gauntlets | stock_drop |  | Captain Nalot's Quickening |
| 4905 | Woven Shadow Gauntlets | stock_drop |  | Captain Nalot's Quickening |
| 4915 | Indicolite Gauntlets | stock_drop |  | Captain Nalot's Quickening |
| 4941 | Totemic Boots | class_quest |  | Flowing Thought II |
| 4942 | Totemic Gauntlets | class_quest |  | Captain Nalot's Quickening |
| 4943 | Totemic Vambraces | class_quest |  | Improved Dodge I |
| 4944 | Totemic Greaves | class_quest |  | Improved Parry / Block I |
| 4945 | Totemic Bracers | class_quest | Mana Preservation II |  |
| 4946 | Totemic Breastplate | class_quest |  | Improved Dodge I |
| 4947 | Totemic Helm | class_quest |  | Regeneration II |
| 5176 | Legionnaire Scale Pauldron | stock_drop |  | Nature's Precision |
| 5179 | Legionnaire Scale Gauntlets | stock_drop |  | Captain Nalot's Quickening |
| 14640 | Silver Amber Ring | crafted_jewelry | Spell Haste I |  |
| 14641 | Electrum Amber Earring | crafted_jewelry | Spell Haste I |  |
| 14642 | Golden Amber Earring | crafted_jewelry | Spell Haste II |  |
| 14643 | Platinum Amber Ring | crafted_jewelry | Spell Haste II |  |
| 14660 | Silvered Peridot Ring | crafted_jewelry | Mana Preservation I |  |
| 14661 | Electrum Peridot Bracelet | crafted_jewelry | Mana Preservation I |  |
| 14662 | Golden Peridot Bracelet | crafted_jewelry | Mana Preservation II |  |
| 14663 | Platinum Peridot Ring | crafted_jewelry | Mana Preservation III |  |
| 14664 | Silver Emerald Ring | crafted_jewelry | Improved Healing I |  |
| 14665 | Emerald Electrum Bracelet | crafted_jewelry | Improved Healing I |  |
| 14666 | Golden Emerald Bracelet | crafted_jewelry | Improved Healing II |  |
| 14667 | Platinum Emerald Ring | crafted_jewelry | Improved Healing III |  |
| 14672 | Blackened Pearl Silver Ring | crafted_jewelry | Burning Affliction I |  |
| 14673 | Black Pearl Electrum Choker | crafted_jewelry | Burning Affliction I |  |
| 14674 | Golden Black Pearl Choker | crafted_jewelry | Burning Affliction II |  |
| 14675 | Black Pearl Platinum Ring | crafted_jewelry | Burning Affliction III |  |
| 14676 | Silver Fire Wedding Ring | crafted_jewelry |  | Improved Dodge I |
| 14677 | Electrum Fire Wedding Ring | crafted_jewelry |  | Improved Dodge I |
| 14678 | Golden Fire Wedding Ring | crafted_jewelry |  | Improved Dodge I |
| 14679 | Platinum Fire Wedding Ring | crafted_jewelry |  | Improved Dodge I |
| 14681 | Electrum Star Ruby Ring | crafted_jewelry | Improved Damage I |  |
| 14682 | Golden Star Ruby Ring | crafted_jewelry | Improved Damage II |  |
| 14683 | Platinum Star Ruby Veil | crafted_jewelry | Improved Damage III |  |
| 21001 | Fine Plate Helm | crafted_armor |  | Regeneration I |
| 21003 | Fine Plate Collar | crafted_armor | Spell Haste II |  |
| 21004 | Fine Plate Breastplate | crafted_armor | Improved Healing II | Improved Dodge I |
| 21005 | Fine Plate Pauldron | crafted_armor |  | Endurance |
| 21009 | Fine Plate Bracer | crafted_armor | Mana Preservation II |  |
| 21010 | Fine Plate Gauntlets | crafted_armor |  | Speed |
| 21012 | Fine Plate Boots | crafted_armor |  | Flowing Thought I |
| 21013 | Small Fine Plate Helm | crafted_armor |  | Regeneration I |
| 21015 | Small Fine Plate Collar | crafted_armor | Spell Haste II |  |
| 21017 | Small Fine Plate Pauldron | crafted_armor |  | Endurance |
| 21021 | Small Fine Plate Bracer | crafted_armor | Mana Preservation II |  |
| 21022 | Small Fine Plate Gauntlets | crafted_armor |  | Speed |
| 21024 | Small Fine Plate Boots | crafted_armor |  | Flowing Thought I |
| 21025 | Large Fine Plate Helm | crafted_armor |  | Regeneration I |
| 21027 | Large Fine Plate Collar | crafted_armor | Spell Haste II |  |
| 21029 | Large Fine Plate Pauldron | crafted_armor |  | Endurance |
| 21033 | Large Fine Plate Bracer | crafted_armor | Mana Preservation II |  |
| 21034 | Large Fine Plate Gauntlets | crafted_armor |  | Speed |
| 21060 | Enchanted Teir`Dal Chain Coif | crafted_armor |  | Regeneration I |
| 21062 | Enchanted Teir`Dal Chain Neckguard | crafted_armor | Spell Haste II |  |
| 21063 | Enchanted Teir`Dal Chain Tunic | crafted_armor | Improved Healing II | Improved Dodge I |
| 21064 | Enchanted Teir`Dal Chain Mantle | crafted_armor |  | Endurance |
| 21068 | Enchanted Teir`Dal Chain Bracelet | crafted_armor | Mana Preservation II |  |
| 21069 | Enchanted Teir`Dal Chain Gloves | crafted_armor |  | Speed |
| 21155 | Koada`Dal Mithril Helm | crafted_armor |  | Regeneration I |
| 21157 | Koada`Dal Mithril Collar | crafted_armor | Spell Haste II |  |
| 21158 | Koada`Dal Mithril Breastplate | crafted_armor | Improved Healing II | Improved Dodge I |
| 21159 | Koada`Dal Mithril Pauldron | crafted_armor |  | Endurance |
| 21163 | Koada`Dal Mithril Bracers | crafted_armor | Mana Preservation II |  |
| 21164 | Koada`Dal Mithril Gauntlets | crafted_armor |  | Speed |
| 21166 | Koada`Dal Mithril Boots | crafted_armor |  | Flowing Thought I |
| 21240 | Imbued Koada`Dal Mithril Helm | crafted_armor |  | Regeneration I |
| 21242 | Imbued Koada`Dal Mithril Collar | crafted_armor | Spell Haste II |  |
| 21243 | Imbued Koada`Dal Mithril Cuirass | crafted_armor | Improved Healing II | Improved Dodge I |
| 21244 | Imbued Koada`Dal Mithril Pauldron | crafted_armor |  | Endurance |
| 21248 | Imbued Koada`Dal Mithril Bracers | crafted_armor | Mana Preservation II |  |
| 21249 | Imbued Koada`Dal Mithril Gauntlets | crafted_armor |  | Speed |
| 21251 | Imbued Koada`Dal Mithril Boots | crafted_armor |  | Flowing Thought I |
| 21264 | Imbued Ogre War Helm | crafted_armor |  | Regeneration I |
| 21267 | Imbued Ogre War Breastplate | crafted_armor |  | Improved Dodge I |
| 21268 | Imbued Ogre War Pauldron | crafted_armor |  | Endurance |
| 21273 | Imbued Ogre War Gauntlets | crafted_armor |  | Speed |
| 21290 | Enchanted Dwarven Plate Helm | crafted_armor |  | Regeneration I |
| 21292 | Enchanted Dwarven Plate Collar | crafted_armor | Spell Haste II |  |
| 21293 | Enchanted Dwarven Breastplate | crafted_armor | Improved Healing II | Improved Dodge I |
| 21294 | Enchanted Dwarven Plate Pauldron | crafted_armor |  | Endurance |
| 21298 | Enchanted Dwarven Plate Bracers | crafted_armor | Mana Preservation II |  |
| 21301 | Enchanted Dwarven Plate Boots | crafted_armor |  | Flowing Thought I |
| 21362 | Dwarven Chain Coif | crafted_armor |  | Regeneration I |
| 21364 | Dwarven Chain Gorget | crafted_armor | Spell Haste II |  |
| 21365 | Dwarven Chain Mail | crafted_armor | Improved Healing II | Improved Dodge I |
| 21366 | Dwarven Chain Mantle | crafted_armor |  | Endurance |
| 21370 | Dwarven Chain Bracelet | crafted_armor | Mana Preservation II |  |
| 21371 | Dwarven Chain Gloves | crafted_armor |  | Speed |
| 21373 | Dwarven Chain Boots | crafted_armor |  | Flowing Thought I |
| 21434 | Imbued Dwarven Chain Coif | crafted_armor |  | Regeneration I |
| 21436 | Imbued Dwarven Chain Gorget | crafted_armor | Spell Haste II |  |
| 21437 | Imbued Dwarven Chain Mail | crafted_armor | Improved Healing II | Improved Dodge I |
| 21438 | Imbued Dwarven Chain Mantle | crafted_armor |  | Endurance |
| 21442 | Imbued Dwarven Chain Bracelet | crafted_armor | Mana Preservation II |  |
| 21443 | Imbued Dwarven Chain Gloves | crafted_armor |  | Speed |
| 21445 | Imbued Dwarven Chain Boots | crafted_armor |  | Flowing Thought I |
| 21485 | Enchanted Teir`Dal Chain Boots | crafted_armor |  | Flowing Thought I |
| 23468 | Imbued Dwarven Plate Helm | crafted_armor |  | Regeneration I |
| 23470 | Imbued Dwarven Plate Collar | crafted_armor | Spell Haste II |  |
| 23471 | Imbued Dwarven Breastplate | crafted_armor | Improved Healing II | Improved Dodge I |
| 23472 | Imbued Dwarven Plate Pauldron | crafted_armor |  | Endurance |
| 23479 | Imbued Dwarven Plate Boots | crafted_armor |  | Flowing Thought I |

## Deliberate exclusions

No dormant cultural output promotion is activated. No starter/epic/custom blanket matching. Empty-slot additions do not replace occupied effects, and some reviewed family members therefore remain unchanged. The retained acquisition audit lists unresolved outputs. A separate all-status recipe lookup found no output producer at any of the four qualities for50same-name armor definitions; these orphan duplicates remain unchanged. Tailored racial sets with unresolved forage components remain review items, rather than receiving unsupported availability claims.

## Validation boundary

Candidate only. Native measurements, independent review and guarded database/cache rehearsal are recorded separately. No deployment, public wiki publication or manual player acceptance is implied by this report.

## Measured results

Shipping ornament successor zonebceda35d reproduces exactly. The full suite was rerun after the ornament integration with byte-identical results to predecessor04fcbf33. All212pressure,312defense and112offense pairs pass. Incoming-pressure outcomes remain207duration/5deaths on both sides; no matched healing reduction. No-haste timed swings increase38→46 over120seconds;36% Cloak of Flames stays52→52. Existing Prismatic Magic plus60legal offensive AA points retains identical damage through20critical-roll seeds. RankIII enables full200focus on level49 Ice Comet; duplicate item focuses do not add. Native spell figures are formula samples, and outgoing melee resets HP between swings. They do not certify full encounter AI, landed spell resists or ordinary-player zone entry.

## Deployment

Main PR523 / 688932e2 deployed after the ornament release on November 21. Production verification confirms 12 workers, open access and zero errors/restarts. The successor cache changes596/324796records and preserves324200, including all ornaments. Existing client2026112101 remains valid; reconnect. Player acceptance remains open. The separately prepared wiki package is unpublished. Evidence: [production verification](../../releases/classic-equipment-paths-20261121/production-verified.json).
