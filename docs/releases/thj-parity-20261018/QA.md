# Owner testing: combined scaling candidate

Run against the isolated test candidate with its matching world/zone/cache loader,
generated item/spell caches and NCPA2/proxy0.11.0 client delta. Record the exact
bundle hashes, class order, level, earned AA points, gear/augments, buffs, target,
seed where available, time to kill, damage, mana spent and healing. A pass on one
build is not acceptance of every class order or later-era encounter.

## 1. Item values and earned progression

1. In Plane of Knowledge on a disposable GM test character, use
   `#summonitem 607869`, `#summonitem 626549`, `#summonitem 608364`,
   `#summonitem 628926`, `#summonitem 640035`, `#summonitem 626766` and
   `#summonitem 805532`. Inspect the seven exact anchor values in README, including
   Talisman's seven +8 heroics and Blood Cord's STA rather than STR. Reopen links
   after zoning/relogging; display and effective stats must agree.
2. Compare Bronze Breastplate4204/204204/404204/604204: AC6/7/8/9. Compare all four
   Bronze Long Sword qualities: damage4/5/6/7, delay32. Cloth/leather/rusty remain
   useful early steps. Check cultural armor retains its previous values.
3. At levels20/30/40/50, obtain the matching dungeon completion rewards through
   the keeper's existing task/turn-in route. Befallen is the entry test; Cazic-Thule
   covers level40; Permafrost is the level50 test. Completion chest IDs960003/960005 and960219/960221
   should show Normal/Ascended AC12/16 and24/32 respectively. A comparable Normal
   dungeon reward must beat Ascended starter armor/weapon ratio. Existing task,
   forge costs, receipts, augment colors and item ownership must remain valid.
4. Check Diaku651912 retains its WPM worn effect and sockets while HP becomes30.
   Inspect the combined changed named pet/WPM pieces with both innate effects
   and inserted augments. Zoning, trade, recovery and reforge must not lose them.
   Later-era items are GM-only test fixtures until their era is explicitly staged.

## 2. Spell, heroic and sustain controls

1. With no paid AAs, remove active focuses/proc gear and record effective SD/HA
   and heroic INT/WIS. Compare Frost Bolt54, Light Healing17 and Heat Blood360 at
   levels10/20/30/40/50; inspect noncritical hits/ticks separately from crits.
   Direct damage should add effective SD once. Ordinary DoT ticks should gain
   floor(SD/2), not a duration-divided share. Different spell durations must not
   dilute that flat tick contribution.
2. The exact arithmetic reference is SD191: base20 direct →211, base8 DoT →103,
   base5 DoT →100 before other modifiers. The automated fixture supplies these
   exact bases; actual spell rank/level must be measured before comparing logs.
   Repeat Throw Stone5225: its existing additive bonus applies once.
3. Add heroic INT/WIS while keeping SD/HA constant.100 heroics adds10% to direct
   damage/healing, with integer truncation. Ordinary ticks/HoTs do not gain this
   multiplier. Healing Amount remains percentage based. Verify item-mod opt-out
   spells and reflected direct damage with controlled GM fixtures.
4. Bard rune songs retain instrument benefit and gain no HA rune bonus. Test
   ordinary runes separately. Bard area-DoT songs keep the pre-existing native
   route; they are not represented by the ordinary DoT parity claim.
5. Compare the separate new-rule controls on the same gear via the guarded
   disable/enable scripts and global rules reload. Verify every active zone sees
   the intended rule values. Re-enabling must restore the original candidate
   result without item or AA changes.
6. Compare low-cost early spell ranks, current-level nukes and multiple ordinary
   DoTs at the same effective SD and AA budget. Measure damage per cast, damage
   per mana, sustained rotation DPS and recovery time on level-appropriate dungeon
   enemies. The fixed level-65 native caster controller loses about67% DPS while
   low-base spells gain; neither result alone establishes caster balance. Early
   Frost Bolt probes against Nagafen fully resist and are not a leveling test.

## 3. WPM and pets together

1. Exercise WAR/PAL/MNK in all six class orders, first with only normal zero-cost
   AA ranks, then the legal earned maximum (record actual spent points). Compare
   shield/dual-wield/two-hand and live shield swaps. Holy Shield, Marr sustain,
   Diaku and Healing Light/Blessing/Rage must clear/restore once; no recursive
   healing/proc chain. Check independent six-Monk timers, Master Wu and cooldown
   persistence across camp and zoning.
2. Test MAG/NEC/ENC with bare and equipped permanent pets, then each supported
   class order. Pet own SD/HA plus min(half effective owner stat,375) must match
   logged state. Owner heroic INT/WIS must not be copied. Check pet healing,
   ordinary DoTs, runes, innate/augment procs and earned caster-AA transfer.
3. Transfer full items with multiple augments into every supported pet location.
   Remove them, then test death, zoning, camping, suspension and resummoning.
   No duplicate/lost items, charges, augments or identity. Rabid benefit and bear
   illusion can be removed independently; equipment changes must not reset them.
4. In private test copies of Solusek B and Permafrost, compare Lord Nagafen32040
   and Lady Vox73057 with the same class/AA/gear/buff setup before/after. Include
   a four-mob pack and resource-limited repeat fights. The automated Nagafen
   single-target controller is a diagnostic, not proof of pack/raid balance.
   Prioritize maximum-earned-AA WPM burst: the later-era shield fixture kills
   captured Nagafen in7.1seconds versus11 with the new spell rules disabled.
   The level50 maximum-AA controller takes12.2seconds. Stop main promotion if
   comparable earned Classic equipment and legal AAs trivialize the encounter.
5. Repeat later-era fixtures at65 only with the separate complete PoP profile.
   Verify bosses, earned new drops, merchant/spell access and AA rank gates.
   No free levels, spells, AAs or epics are granted by this candidate.

Stop promotion for item/AA state loss, source/client mismatch, unexpected rule
deletion, progression inversion, runaway sustain or trivialized representative
encounters. Owner sign-off should name passed scenarios and any accepted balance
tradeoffs. Test→main and production remain separate authorized actions.
