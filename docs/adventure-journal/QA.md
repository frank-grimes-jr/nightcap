# Epic 0.5: exact native and balance QA

All checks below remain **manual / not yet accepted** until a dated result is
recorded. Automated evidence does not establish rendered UI, encounter balance
or real client acceptance. Use the matched test runtime and a separate QA client;
normal-account acceptance must not rely on GM spell casting or forced task flags.

## Journal and shared chapters

1. At level 19, hail **The Ancient Chronicler** (999220) in the public **East
   Commonlands** (22) tunnel, then say `journal`. Expect the existing class
   dialogue to work and the first chapter to advertise level 20. No task offer.
2. At level 20, say `journal` and accept **The First Pages** (9500). Open native
   Tasks; check title, description and three objectives. Enter **Upper Guk**
   (`guktop`, 65), **Unrest** (`unrest`, 63) and **Runnyeye** (`runnyeye`, 11),
   moving several steps inside each. Each matching objective increments once;
   movement in EC or another dungeon does not. Zone/relog midway and verify
   retained progress. Finish all three; completion remains after relog.
3. Return to the Chronicler at level 25. Accept **Beneath the Surface** (9501).
   Defeat **the froglok warden** (65104) in Upper Guk and **reclusive ghoul
   magus** (63086) in Unrest. Nearby unrelated kills grant no credit. Test a
   normal owned-pet kill and a normal group-credit kill on separate characters.
4. At level 30 accept **Steel and Sorcery** (9502). Defeat **Battlelord Paluk**
   (11015) in Runnyeye and **the goblin sage** (73013) in **Permafrost** (73).
   There are no proof-drop or turn-in requirements. Before level 35, paths remain
   unavailable; at 35 all five appear regardless of primary class.
5. Cancel an incomplete task, reoffer it, and verify normal task restart behavior
   without losing completed earlier chapters. Fill the ordinary task log on a
   QA character: native refusal must leave earned history intact. Do not expect
   pre-acceptance kills or exploration to count retroactively.

## Five archetype routes

For each route, accept its task before the kills. Attempt its finale before
finishing both field objectives: no premature completion. Finish the first two
in either order; then defeat the finale again to complete. Check progression,
completion persistence, preparation text and the unlocked attunement link.

| Task / path | Field objectives | Finale |
|---|---|---|
| 9503 Guardian | froglok shin lord 65128 / Upper Guk; Lord Pickclaw 11017 / Runnyeye | Xicotl 59152 / Mistmoore 59 |
| 9504 Striker | Butler Syncall 59116 and Maid Issis 59115 / Mistmoore | Garton Viswin 59151 / Mistmoore |
| 9505 Arcanist | Battlewizard Unak 11086 / Runnyeye; High Priest Zaharn 73006 / Permafrost | Lasna Cheroon 59089 / Mistmoore |
| 9506 Warden | Khrix Fritchoff 63082 / Unrest; Maid Issis 59115 / Mistmoore | Garanel Rucksif 63062 / Unrest |
| 9507 Binder | King Thex'Ka IV 73103 / Permafrost; Mynthi Davissi 59150 / Mistmoore | Xicotl 59152 / Mistmoore |

Verify natural Classic spawns/placeholders for every named. Record travel time,
placeholder kills and waiting separately from encounter time. Greshvoule is
deliberately excluded because its captured spawn requires expansion 4.

## Reward, ownership and cooldown

1. Before earning a route, type `journal attune guardian` and `journal forge`:
   no reward or attunement. After earning a route, attune and forge at the
   Chronicler. Check item 900501's name, stats, lore/no-trade flags, level 35,
   charm slot and visible click. No random tier or augment slot is present.
2. Forge with a held cursor item, a full inventory, a banked relic and an
   equipped relic. No duplicate or lost existing item; completed tasks remain.
   Destroy only a disposable QA relic, recover it, and confirm the timer persists.
3. Click from a bag with an empty charm slot, or click another copy's bag slot
   while a charm is equipped: no effect. Equip the charm and use an earned
   attunement. Check effect, cooldown display and journal seconds remaining.
4. Attempt rapid repeated clicks, death/resurrection, zoning, reconnecting,
   class changes and recovery. No second effect before 600 seconds. After the
   timer expires, exactly one new activation works. Full HP Warden use still
   consumes the shared timer; normal resist/block/stacking behavior may consume
   a use without adding power.
5. Earn a second route. Switching during cooldown, combat, outside public EC,
   farther than 75 units from the Chronicler or while unable to act must fail.
   When ready at the guide, switching succeeds and changes the next use. All
   paths still share one cooldown. Primary class never controls path access.
6. Binder: target self, another player's pet, a corpse, unrelated NPC and an
   owned pet farther than 100 units. Each invalid attempt grants no effect and
   spends no DB cooldown. Target one living owned pet in range: exactly that pet
   receives the effect; the rest of a three-pet roster do not. Test charm loss
   and zoning after activation; no fresh activation is available.

## Native effects and balance measurements

Record server/client hashes, active rules/formulas, three held classes, legal
AA pool and ranks, actual spent points, equipment tiers, heroics, augments,
permanent buffs and pet count. Use level 35–40 earned gear, fresh level 50 and
developed level 50. Include melee-heavy, caster-heavy, hybrid sustain and one/
three-pet builds. Unrestricted AA runs must be separately labelled stress tests.

For each route and build, record three comparable fights without the click and
three with it: success/death, fight time, incoming damage, damage/healing done,
lowest HP, ending mana/endurance, pet deaths and recovery time. Reset only
disposable test fixtures between trials; never edit real player timers. Record
spawn/add variation so unlike pulls are not presented as controlled evidence.

- Guardian: melee absorption stops at 200 total or three ticks, whichever comes
  first. Spell damage is not described as protected. Check existing rune stacking.
- Striker: compare melee output under equal conditions; ordinary damage-modifier
  stacking applies. Confirm expiry after three ticks.
- Arcanist: compare an actual DD and DoT with existing focus effects. Confirm the
  candidate 5% contribution, ordinary focus selection and expiry; do not assume
  it multiplies every existing focus or retroactively retunes a running DoT.
- Warden: verify 10% max-HP base healing with a 400 base cap; record final healing
  with legal AAs/focus/crit modifiers. The final heal is not promised to cap at 400.
- Binder: measure only the targeted pet's damage/absorption, capped at 150 total
  or three ticks. Extra pets must not multiply the granted buff count.
- All timed effects: verify the native buff/song window countdown, fade, death,
  zoning/relog and no accidental permanence. Check an unrelated beneficial buff
  still follows Nightcap's permanent-buff policy.

Reject promotion for any cooldown reset, foreign/multiple-pet grant, unearned
path, lost history, stuck objective, permanent Epic buff or repeatable inventory
duplication. Tune and rerun balance if the click trivializes a representative
encounter, makes one path the universal choice, or is unnoticeable at its intended
level. Keep class epics and difficult-content rewards worthwhile.

## Failure and recovery

Use disposable QA state. Disable the release gate and verify new actions/clicks
refuse while completed tasks and cooldowns remain. Re-enable after the matching
runtime is confirmed. Disable each required task rule and check unavailable
dialogue. Missing plugins/old native contract must not allow fallback power.
Run the automated SQL error, lost-acknowledgement and concurrency rehearsal;
do not inject faults into production. Apply `disable.sql` and verify all eight
task offers disappear, owned charm/spell definitions remain, and unrelated hub
services still work. Record pass/fail evidence and unresolved findings here.
