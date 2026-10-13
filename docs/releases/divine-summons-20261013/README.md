# Paladin and Cleric Ascended summons

Owner authorized implementation, main promotion and production deployment on
October 13, 2026. Candidate verification is in progress; gameplay acceptance
remains pending.

Paladin/Cleric item-summoning hammers directly produce their existing Ascended
variant. This was already implemented in both `SpellEffect::SummonItem` and
`SummonItemIntoBag`; the production catalog audit found all eleven families and
all four quality tiers. The change closes their FreeTrade resale loophole:
the item loader projects both Price and FixedSellPrice to zero after FreeTrade.
Raw SQL, combat stats, procs, bane damage, equip restrictions, spell access and
temporary lifetime remain unchanged. Unswerving/Celestial Hammer pets are separate.

| Spell | Ascended item | Damage/delay | Undead bane |
|---|---|---|---|
| Hammer of Wrath (223) | 606307 | 8/32 | 3 |
| Hammer of Striking (37) | 606309 | 8/29 | 4 |
| Hammer of Requital (675) | 606313 | 9/29 | 5 |

These three have +20 Spell Damage and +20 Healing Amount. Their primary-only
slot and existing class masks stay intact. Later hammer definitions are covered
by the same resale policy without unlocking their spells or removing item level
requirements. They include Judgment, Divinity, Souls, Damnation, Reproach and
Reverence I/II/III. All 44 existing base/quality definitions are covered so old
inventory copies cannot retain the money faucet.

Ascended outputs have no Reforging Box or zone-forge successor. The production
audit found no tradeskill recipe references to any of the 44 definitions. The
Epic Forgemaster accepts its explicit epic catalog, not these hammers.

## Verification and deployment

`tools/tests/test_divine_summoned_weapons.py` compiles both actual summon-selection
branches, including missing variant, missing base, non-equipment and already-tiered
controls. It compiles the real FreeTrade/resale policies with all 44 IDs, tests
unchanged combat/trade fields and unrelated-item payout controls, and checks
Ascended upgrade rejection. The native loader/cache comparison must additionally
verify every existing item byte outside the two approved price fields.

`build_candidate.py` rebuilds only shared_memory using the exact retained
production loader source and link inputs, replacing one archive member. The
ItemData structure is unchanged. Deployment layers this loader onto a freshly
verified active image, preserving current world/zone/login/UCS binaries. The
supported full game restart regenerates the cache; rule/quest reload is insufficient.
No SQL content migration or client download is needed.

Before activation, verify backup, maintenance fences, exact active image and native
hashes, complete cache preimage and current player/custom tables. Close gateway,
stop game gracefully, select candidate image, start and verify all twelve zones,
cache deltas and preserved state before reopening. Rollback selects the retained
image and regenerates its cache; it never restores player inventory or SQL.

## Exact in-game QA

1. With a Paladin/Cleric build that can legally cast the spell, cast Hammer of
   Wrath and Hammer of Striking in East Commonlands. Confirm the cursor items
   are Ascended 606307/606309 with the table's ratios and bonuses.
2. With eligible Cleric access, cast Hammer of Requital and confirm 606313.
   Repeat casts and relog; preserve ordinary temporary-item lifetime behavior.
3. Equip each in the primary slot. Confirm offhand restrictions, normal swings,
   and undead bane against undead in Befallen. Compare the same build and AAs
   against a recorded earned weapon, including Slay Undead when owned.
4. At Artisan Veyra's workshop, put four identical summoned Ascended hammers in
   the Reforging Box. Combine must reject without consuming them. The Epic
   Forgemaster must return an unintended hammer hand-in.
5. Try an ordinary merchant sale and `#sellall`. Hammers must yield no coin;
   `#sellall` must retain them. Sell an unrelated formerly NO DROP item as a
   control and confirm its ordinary one-platinum payout remains.
6. For later unlocked hammer lines, verify the original proc and item-level gates
   with a legal character. Their present definitions do not authorize early use.

Automated coverage establishes implementation and preservation, not encounter
balance or owner acceptance. Retain named-drop/epic comparisons and combined
melee/AA/proc QA before claiming these weapons' long-term balance is accepted.
