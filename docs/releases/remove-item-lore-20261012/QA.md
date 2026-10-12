# In-game QA: all items without LORE

Pending; requires approved activation. Use a normal account and disposable QA
items. Record IDs, inventory before/after, receipts and client/server versions.

1. In East Commonlands, inspect a formerly LORE base item and its Polished,
   Exalted and top-tier variants. LORE must be absent after reconnect/zone.
2. Loot or trade four Fishbone Necklaces (Polished), item 201061, to one character.
   Confirm all four coexist in bags, survive zoning/camp/login and are not lost
   from the cursor. Verify targets 401061 and 601061 exist before summoning QA
   inputs. Their names must be Fishbone Necklace (Exalted)/(Ascended).
3. Hail Artisan Veyra beside the Epic Forgemaster in the East Commonlands tunnel
   workshop, /loc Y=-1818 X=-385 Z=3.75, for Reforging Box 900620. Place it in a
   main inventory slot. Combine four 201061: exactly one 401061 remains inside
   and the box survives. Repeat with four 401061 -> one 601061. Confirm one
   receipt per combine, no fee or failure roll, and relog persistence.
4. Own another copy of the intended output before combining. The combine must
   succeed without a LORE conflict. Repeat acquisition when copies are in the
   bank, on cursor and equipped. Shared-group items with different IDs must also
   coexist; choose two current catalog rows with the same positive raw group.
5. Equip duplicates in legal paired ear/ring/wrist slots and valid dual-wield
   slots. Check resulting stats, damage and sustain for representative multiclass
   builds. Inventory permission does not bypass weapon/class/slot requirements.
6. Verify a quest item, an augment and pet armor formerly marked LORE can be
   acquired more than once. Confirm their ordinary use and persistence. Check a
   scaling/evolving item separately; it must still be rejected by the box where
   the existing upgrade policy requires that rejection.
7. Three items, mixed IDs, base/top-tier inputs and augmented/customized inputs
   still reject intact. Revisit the item-upgrade QA matrix; its historical
   output-LORE-conflict rejection case is superseded by step 4 under this rule.
8. Check ordinary loot, merchant buying/selling, player trade and advanced-loot
   claims with duplicates, plus a non-lore item as a control. No duplication,
   missing items or repeated receipts. Confirm ordinary capacity limits remain.
9. Compare solo encounters before/after legal duplicate equipment and four-copy
   upgrades. Record build, gear, AA pool, encounter, time, damage and sustain;
   progression should remain earned and challenging. Report balance separately.

Never test post-activity rollback by restoring LORE on a live character holding
duplicates. Use the disposable database/cache rehearsal for immediate rollback.
