# Live release QA — 2026-09-15

The owner authorized deploying all implemented changes for live testing. This is
test acceptance, not main sign-off. Record PASS/FAIL separately for each section,
with character classes/level, exact steps, observed result and relevant logs.
Use disposable characters for purchase/refund/class-release tests; leave Done
unchanged. Existing player data is backed up; no blanket AA disablement, expansion
pool projection or balance-number change is part of this deployment.

## 1. PoK arrival hub and services

Enter Plane of Knowledge normally. The arrival point is approximately
**x=-285, y=-148, z=-159** (database x/y order). Sixteen class merchants flank
an open aisle; the Ancient Chronicler stands north at x=-285, y=-74.
The utility row is at y=-232: bags, Epic Ascension, blessings, premium blessings,
and waypoint travel. Walk the entire hub and check grounding, line of sight,
facing, arrival clearance, Find labels and NPC overlap.

Open all sixteen merchants: 1,747 listings / 1,229 unique items at cap 50,
3–275 per class merchant. Warrior/Monk/Rogue/Berserker sell tomes; Bard sells songs.
Verify all former Loremaster/II spawns are gone and exactly one Forgemaster remains.
Hail each utility NPC and check existing costs/prerequisites. Full per-class
counts and exact checks: [hub layout](../../pok/hub-layout.md),
[hub QA](../../pok/QA.md).

## 2. Class status, selection and release

On a disposable Warrior, log in, hail the Chronicler, run `#classes` and
`/say !classes`. Primary/Second/Third must agree and empty slots must be explicit.
Preview Cleric and cancel confirmation: no change. Confirm Cleric as Second,
then Wizard as Third. Duplicate/fourth choices must be refused. Camp and return;
slots and status must persist. Cancel a release, then release Second on the
zero-AA character: Wizard moves to Second and Third empties immediately.
Normal unrelated commands must continue working.

## 3. Bag prices (#22)

At Bartholomew Packwell, all 22 bags must have positive prices increasing by
capacity. The base ladder is **10 platinum for 8 slots through 7,500 for 40**;
normal charisma/faction modifiers affect displayed quotes. Review the economy
as well as functionality. Buy 8-slot item **53684**, 16-slot **52082**, and
40-slot **54726** with recorded wallets; deduction must equal the quote.
Insufficient funds must change neither items nor coin. Verify actual capacities,
specialized-container restrictions and weight reduction. Resale must be refused;
ordinary loot must still sell. Zone/relog and verify persistence.
[Full ladder and QA](../../ops/bag-vendor-pricing.md).

## 4. Skills and trainers (#36)

Use the scoped Human Cleric/Shadowknight/Monk `Monktest` fixture from epic #10,
not Done. Skills unlock at their native levels with value 1 and improve normally;
production never auto-maxes. Test Kick/Mend/dual wield at 1, Round Kick at 5,
Block/Tiger Claw at 10, Double Attack at 15, Feign Death at 17, Eagle Strike at 20,
Dragon Punch at 25, Flying Kick at 30, and Triple Attack at 50. Check empty-fist,
permitted weapon plus empty offhand, and two permitted one-handed weapons.
Try secondary/tertiary trainers, negative non-held access, unlock thresholds,
points and caps. RoF2 client UI coverage remains an open gate: record any blocked
window/action separately from server eligibility.

## 5. AA XP at level 1 (#37)

Disposable level-1 character in PoK: `#aaexp 50`, zone to East Commonlands,
kill a level-appropriate XP-awarding bat/snake and verify allocation remains 50%.
Small gains need not award a full AA point. `#aaexp off`, repeat, confirm off.
On a disposable level-50 character in Lower Guk, `#aaexp 100`, earn XP and verify
AA experience increases. Camp/relog and verify allocation persists.

## 6. Earned-AA persistence, purchases and class release

Use disposable characters and record class slots, exact AA family/rank IDs,
wallet, spent/expended totals, skills and passive bonuses before each action.
Buy legal ranks, zone, camp/relog and confirm ownership/counters/bonuses persist.
Repeat a legal charged-AA use and exhausted-charge repurchase; observe the
normal cost once. Exercise a legitimate refund/reset and verify earned cost
and grant-only retention under the documented policy.

On a disposable character with earned Wizard-only and shared AA families,
release Wizard through the Chronicler. Class slots, unique earned-AA removal,
eligible refunds and skill clamps must agree immediately and after reconnect;
shared families remain owned. Canceling release changes nothing. Repeating
release on an empty slot cannot refund again. Verify passive bonuses disappear
immediately when their unique class is removed.

Do not inject database faults into ordinary live characters. Real network
reconnect, uncertain-COMMIT recovery and fully loaded failure-session behavior
remain unverified; a rejection must request reconnect, not claim successful
release. [Native candidate evidence and boundaries](../../balance/native-aa-class-release-candidate.md).

## 7. Weapon damage, three pets and AA buff duration

Follow [the exact five-fix QA](../server-fixes-20260913/QA.md):

- Level-50 WAR/CLR/MNK in Solusek B: Balanced Tonfa of Serenity **662038** must
  deal normal weapon damage independently of Monk attacks. WAR/CLR/WIZ must
  reject it; ordinary Warrior item **662035** still works. Race-ineligible
  **5100** and required-level-65 **24587** retain restrictions. RoF2 equip
  submission can still block an off-base item; report that under #13.
- Level-50 MAG/NEC/SHM: summon water **633**, undead **443**, and spirit **166**
  pets with required reagents. All three retain ownership; test summon order,
  dismissal/death/replacement, buffs, attack/qattack at legal distance, and
  command spam without extra instant swings.
- Direct self-AA buffs keep their native expiration; ordinary persistent buffs
  keep theirs. Check shared cooldowns and HP/mana behavior. Triggered subspells
  and the separate Celestial Regeneration level restriction remain open.
- Repeat matched Nagafen/Vox encounters only with recorded gear/preparation;
  report sustain, fear, pet deaths, resources and duration. This release does
  not promise all builds win or deploy new numerical tuning.

## 8. Waypoints and established caster UI

Hail Waypoint Travel in the new hub. On a disposable character, discover an
undiscovered marker in a configured zone (for example Befallen), leave and use
the PoK service to return. Confirm discovery persists after relog, undiscovered
destinations remain unavailable, and arrival is safe. All-waypoint Explorer
completion requires its own recorded full discovery pass.

On a melee-base caster, check spellbook/gems, legal scribing/memorizing/casting,
mana gauge, regen, zoning and relog. Repeat with a stock caster and a true
zero-mana melee. Existing DLL behavior is reused; no new client patch is installed.

## Remaining work with no completed fix to deploy

AA class column (#4), missing-title remedy (#16), global spell tooltip widening
(#17), Bard movement/song landing (#19), augments (#26), complete client parity
(#13/#36), and launcher/release pipeline (#14/#15) remain open. For Bard capture
both Selo variants standing versus running, buff landing/speed/instrument modifier,
Spirit of Wolf and mount controls, and base/held-Bard classes. This is diagnosis,
not acceptance of a deployed Bard fix. #11 retains its original incomplete
best-of-stat/heroic-regeneration acceptance.
