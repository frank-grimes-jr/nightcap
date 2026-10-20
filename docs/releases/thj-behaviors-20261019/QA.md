# Owner testing spike — not accepted

Use the deployed server and signed game2026101902 through the normal launcher.
Reopen the launcher and press Play before testing. Classic50 remains active.
Never edit Client_RoF2_Dev. Deployment is verified; gameplay acceptance is open.
Record character, held classes, level, spent AA, item IDs, rules, logs, build/client
manifest hashes and before/after values. Purchased AA setup is a labeled test
fixture, not a player grant or unrestricted balance result.

## Progression and gear

1. In East Commonlands, compare an existing level 1 starter character and fresh
   character before/after. All starter items/grants, vendors and forge costs remain.
   Verify a level 50 character cannot naturally exceed the Classic cap.
2. Inspect Normal, Polished, Exalted and Ascended versions of an eligible researched
   ordinary family in gear-audit.json; compare every changed field to the generated
   plan. Use Dragonspine Rapier as a weapon reference and its observed Ascended
   row in config/thj-item-parity.json. Verify delay/proc/focus/socket text unchanged.
3. Inspect Enchanted Werebone 51908/651908, Diaku Armor Fragment 51912/651912 and
   Water Sprinkler of Nem Ankh 5532/805532: existing exact values/effects remain.
   Inspect a custom Hunt family and a 209-list starter family: unchanged.
4. Equip/remove the four ordinary qualities. Compare actual HP/mana/AC/SD/HA and
   attack-log damage, including a pet wearing supported gear and shield/WPM builds.
   Reforge and zone/relog with existing owned items; identity and sockets persist.

## AA catalog and refunds

1. Turn Recommended AA off. Browse all held classes. New access matches
   aa-access-delta.json. Non-target classes retain their previous lines/costs.
2. On isolated characters with canonical purchased 25,252,8300,3521,3522,758,
   record wallet, spent points and unrelated purchases. Login refunds each recorded
   cost once. Rezone/relog again: no second refund. Unrelated ranks and class slots
   remain. Verify purchase/release/refund after conversion remains usable.
3. Buy Warlord and the four-burn prerequisite chain normally in the test fixture.
   Verify full Hastened Manaburn shows 15 min for all four. No two unrelated AAs share
   a countdown; relog preserves already-running deadlines.

## Resource and interruption behavior

Use the Arena (`arena`) for grouped players and controlled nonpersistent test
opponents. In East Commonlands use an orc centurion for hostile targeting; choose
nonlethal test weapon/spell ranks and record the target's health so overkill is not
mistaken for measured damage. Do not persist new spawns or alter live NPCs.

1. Valor at maxmana 10000 spends 5000 once and gives each in-range injured group
   member 10000 base healing, subject only to incoming modifiers and missing HP.
   Repeat solo, groups 3/6, out-of-range member, pet/group edge cases. At 4999 mana
   reject without mana loss or cooldown; caster is not killed. Test recipient
   incoming percent, HealRate and flat healing bonuses/debuffs; a final nonpositive
   amount heals zero. Caster Healing Amount and critical healing do not increase it.
2. Harvest at maxmana 10000 restores 4000 up to the mana cap on activation. Kill
   unrelated mobs to confirm it did not become an unsourced passive kill proc.
3. Burns at maxmana 10000 spend 1000/2000/3000/4000 and deal 4000/8000/12000/16000
   before target mitigation. Try every rank on a burn-immune target: no mana or
   cooldown consumed. Test insufficient mana, invalid/dead/out-of-range target,
   resisted delivery, casting cancellation and relog timer behavior.
4. With Dimensional Shielding active, test casting while moving, taking hits and
   receiving hostile interrupt spells. Casting should finish. Stun, voluntary
   cancellation, death and zone change retain ordinary interruption behavior.
   Repeat after 120 s expiration. Native Dimensional Shield teleport proc is separate.
5. Warlord expires by 12 s and adds 100 percentage points in the native physical
   skill-damage modifier path. Record other modifiers when comparing totals. Gut increases incoming physical hit damage 50% by 12 s; spells are not
   physical hits. Press lowers AC and Grapple evasion. Test buff refresh and saved
   old long-duration buffs to ensure they do not regain a full duration on relog.

## Focus and proc behavior

1. Repeat the same direct and DoT spell with/without known item, spell and AA
   Improved Damage focuses. Static endpoint and 10× bonus should match logs and
   client inspection. Test supported AoE and a school/level/mana-restricted failure.
2. Heart of Flame is 100%, Fire Core 150%, never 1000/1500. Test permanent pet and
   temporary pet separately. Temporary pets retain their prior focus behavior.
3. Bard:3 s songs become 2.5 s base; receiving focus/twincast does not change songs.
   Existing instant-DoT casting still applies to damaging songs.
   A DD-focus song still varies its outgoing benefit within the 10× range when a
   grouped caster nukes. Forpar's DoT-focus songs retain their prior random range.
4. Silent Casting is available to all 12 caster classes, lasts 1 h with 60 s reuse and
   suspends in a buff-timer-suspended zone. Each retained rank's hate reduction
   remains 20/40/60/80/100%. Verify temporary timer rather than blanket permanence.
5. Pyro/Cryomancy coexist with ordinary buffs and each other; identical or lower
   ranks do not stack repeatedly. Qualifying isolated high-rank spell fixtures
   should proc 35%, initial damage plusDoT and opposite resist reduction. Ordinary
   Classic spells failing retained level 60/minmana/cast limits must not proc.
   This controlled future-rank fixture does not authorize an era/level change.

## Acceptance gate

Automated checks cannot certify group/raid packet delivery, spell reflect/resist
edge cases, client timers or encounter balance. Record these manual results before
main/server activation or accepting parity. Then run representative solo melee,
caster, healer and pet builds in Befallen/Unrest and Classic raid encounters at
normal progression gear and the actual curated AA cap; compare difficulty and
resource sustain. Balance tuning is a separate decision, not a claim of this build.
