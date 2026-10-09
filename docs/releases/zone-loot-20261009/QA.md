# Required in-game acceptance after owner-authorized live deployment

Main/OVH promotion was explicitly authorized October 9, 2026 before manual acceptance. The following gameplay checks remain open; see [deployment evidence](PRODUCTION.md).

Use a normal-status test character for player behavior and a separate GM for fixture setup. Record build hashes, active rules, classes, level, equipped items, augments, allowed AA ranks and actual spent AA, buffs/pets, and the observed result. Do not run artificial item grants or spawn loops against the production player economy.

## Acquisition and existing loot

1. In East Commonlands, kill native audited wildlife/orcs outside the tunnel. `generated/sources.json` gives exact spawn and NPC IDs. Expected new families: **Tunnelward Jasper** (940160–940163) and **Ashen Trail Band** (940164–940167). Verify normal loot remains and the four quality names are Base, Polished, Exalted, Ascension.
2. Repeat with native Crushbone orcs at level 8+, expecting **Crushbone Warshard** (940416–940419) and **Orcbane Handwraps** (940420–940423). Repeat with Nagafen's Lair level-46+ audited enemies for **Emberheart Garnet** (940224–940227) and **Wyrmward Gorget** (940228–940231). Named-specific loot must remain unchanged.
3. Use seeded native automated results for probability acceptance; a short manual dry streak cannot prove or disprove 0.5%. A GM-spawned copy is deliberately ineligible. Verify tunnel residents, merchants, guards, player pets, charmed victims and script-created clones produce no custom rewards.
4. In Kithicor, an audited nighttime **risen squad leader** at level 38 can qualify for **Nightfall Soulglass**; daytime wildlife cannot. Test at least one restored corpse containing a new reward: save/unload/reload using the supported mechanism and confirm no reroll, duplicate physical drop or second receipt claim.
5. Highpass, Splitpaw, Cazic-Thule, Jaggedpine, Nedaria, Hate B, Tutorial A and Tutorial B remain acquisition-disabled pending separate access/source acceptance. Cities and PoK have no new drops. Verify version-1 Paw/Lavastorm do not roll and existing Lavastorm access gates remain intact.

## Socketing and caps

1. On Base and tiered armor, verify one visible type-22 socket in each eligible head/chest/arms/hands/legs/feet piece. Existing type-7/8 or other sockets and installed augments must remain intact. Check an unchanged item with a full socket array and a ring/ear/weapon cannot accept the new armor-only augment.
2. Insert/remove a Base augment; confirm its listed HP/mana/heroics. Confirm the augment is not consumed incorrectly by an invalid socket attempt. Test the normal solvent/removal path in the RoF2 UI.
3. At level 50 with sufficient raw Spell Damage, equip six **Abyssal Thoughtpearl (Ascension)** augments (940467, +10 heroic INT each). With the native cap at 250, expected effective Spell Damage maximum is 280. Remove one: maximum 275. Repeat in different equip order; result must match. A character below the base cap does not gain free Spell Damage.
4. Use **Ghoulheart Opal (Ascension)** (940483) for the analogous Healing Amount test. Split three INT and three WIS augments: maximum 265/265. Existing heroic gear/AA/buff values must not raise this special cap. Verify ineligible required-level items and a level-49 control do not receive level-50 headroom.
5. Check server stats and the client display, direct nukes, DoTs, direct heals and HoTs. Test Throw Stone with 250 and 280 effective Spell Damage: its ordinary base-plus-stat amount changes from 251 to 281 before other modifiers. Verify native heroic HP/mana and attribute caps, not just displayed item tooltips.

## Forge and inventory recovery

1. Carry three unmodified **Tunnelward Jasper** Base copies. Type `#zoneforge`; click the named upgrade. Exactly three become one **Polished** copy (940161), without a fee. Repeat Polished→Exalted→Ascension. Ascension offers no further upgrade.
2. Mix two Base plus one Polished, or copies from different zones: no valid three-copy choice. Equipped items, socketed wearable inputs, ornaments, dyes, custom data and evolving state must not be silently consumed.
3. Test three copies across bags, full general inventory, and one attuned input. The output occupies a consumed slot and preserves binding. Universal trading still permits normal trades. No new reward can be sold to a merchant.
4. Open a choice, move/swap a selected copy, then click the old link. It must reject. Repeat a used link: it must reject without consuming another set. After a successful forge, zone and reconnect; exactly the committed output remains.
5. Use the automated failure-injection suite for write/commit/rollback faults. If a test environment loses commit acknowledgement, expect forced reconnect and inventory reload; do not manually retry an old quote. Verify the forge receipt and actual inventory agree before resuming.

## Advanced loot and combined balance

1. Loot both families through Ask, Always, Never, direct Loot, Loot All and the classic corpse window. Check grouped permissions, existing filters, one-time physical-drop receipts, reload/reconnect, and occupied cursor behavior. Forging must be blocked while looting/trading.
2. Compare baseline and new rewards for warrior/cleric/wizard, warrior/cleric/monk and magician/necromancer/shaman at early, middle and top Classic gear stages. Use the legal Classic AA pool and record actual spent points; include pet/sustain builds and zero-AA controls.
3. Use the same preparation and native encounters before/after (a level-appropriate solo camp, a difficult dungeon pull, then Nagafen/Vox progression attempts). Record kill time, damage taken, mana/endurance use, healing throughput, deaths, pet contribution and preparation. Rewards should improve progression while preserving demanding resource and encounter decisions. No additional cap or NPC-HP changes are part of this candidate.

Sign off acquisition, client/socket behavior, inventory recovery and combined balance separately. Automated stat diagnostics do not replace these encounter checks.
