# Dungeon live-test release: exact acceptance route

Owner check, October 16: **Palwar selected Befallen's Keeper, saw Raid/Grind,
entered a Raid and killed a named boss**. The task title is present but objectives
are blank; a yellow notice followed the kill. A read-only probe confirmed retained
personal boss credit without full-clear completion. The [journal repair](journal-repair/README.md)
is deployed after the authorized restart; visible checklist/history retest is pending. Full-clear
rewards, other dungeons and broader acceptance remain open.

The owner-authorized main/OVH release is deployed and enabled; access is open.
Native binaries, production cache, SQL
and Keeper quest are paired and verified in deployment/. No new client assets
are required. For normal in-game testing, start at step 3 below. Steps 1–2 are
operator setup, already completed on OVH. Use a closed, disposable environment
for fault injection, deadline changes or forced ID recycling; never perform
those experiments on the live server.

## Installation and first Befallen run

1. Preserve the test environment's configuration, content and current player
   state. Rehearse schema/content migrations against its content clone; reject
   collisions or changed objective identities. The provided cache uses local
   public content. Regenerate it for a different target's content before use.
2. Install the paired zone/world/shared_memory and cache, then the Keeper quest.
   Apply schema followed by content while access is closed. Execute the guarded
   `20261016_dungeon_enable.sql` only after verifying package hashes. The game
   and content connections must use the same database. Leave Classic active.
3. At Befallen's entrance, hail the floating-eye Keeper, NPC **999227**. Verify
   Raid, Grind, Enter, Join, Status, Claim Rewards and Reset links. The waypoint
   shares its position and has no hail response; use `/target Instance_Keeper`
   if the waypoint obscures selection. Select Grind to create and enter the run.
   Verify a fresh run is eligible immediately, has twelve hours remaining, and
   has a Befallen–Grind task with five required boss activities.
4. Inspect/kill each name listed by Status. All five must be present initially,
   including **Gynok Moltor**. Compare maximum HP and incoming melee/spell damage
   to the same native NPC outside this instance, with matching debuffs/rules.
   Grind stats match. After the native timer plus variance, defeated mobs return.
5. Kill the last personally required boss. Verify one Normal item, one permanent
   Grind completion, and all five task activities completed. The run moves to
   Completed history. Repeated kills,
   task abandonment/reacceptance,
   Keeper claims and re-entry must not grant another reward.
6. Leave, choose Reset, then Confirm Reset within thirty seconds as creator.
   Start Raid. Verify five objectives, +35% HP, +15% outgoing damage, minibosses
   present and Gynok absent. Kill the four minibosses. Gynok appears within the
   normal spawn polling interval (approximately five seconds). Kill him and
   verify at least one exclusive corpse item plus the separate personal reward.
   Raid items are Polished or Ascended. Defeated spawn points never repopulate.

Whole-wiki review: the published guide now lists all 52 required bosses and
explains stage notices, full clears and Keeper Status when objectives are blank.
Recent changes links this guidance. Other mechanics and Live testing labels
remain unchanged; wiki publication does not establish native repair acceptance.

## Repeat in all seven dungeons and both modes

Use each entrance Keeper. Status is the authoritative exact roster; the versioned
NPC/spawn identities are in `catalog.json`. Do not substitute a similarly named
event, fabled, service or later-era actor.

| Zone / Keeper | Required bosses | Final boss | Band |
|---|---:|---|---:|
| Befallen / 999227 | 5 | Gynok Moltor | 20 |
| Unrest / 999228 | 7 | Garanel Rucksif | 30 |
| High Keep / 999229 | 4 | Carson McCabe | 40 |
| Najena / 999230 | 9 | Najena | 30 |
| Cazic-Thule / 999231 | 6 | Classic Avatar of Fear | 40 |
| Permafrost / 999232 | 8 | Lady Vox | 50 |
| Nagafen's Lair (soldungb) / 999233 | 13 | Lord Nagafen | 50 |

For each of the fourteen runs record UUID, native instance ID, creator, mode,
start/expiry, checklist, observed respawn behavior, final unlock, completion,
reward IDs and receipt IDs. Use both solo multiclass and small-group clears.
High Keep must credit Captain Bosec, Captain Boshinko and Dyrna Nlith before
Carson in Raid, retain native faction changes, and leave merchants/services usable.

For CT, compare public zone content fingerprints before/after installation and
private entry. Only managed private populations use the restoration. Walk all
rooms, traverse all doors, observe all eleven paths and 188 configured points,
check terrain/line of sight, native loot and spell casts. Avatar is level 39
with the restored Shadowknight list; do not accept public PoP-era replacements.
The excluded donor empty group is documented, not a missing objective.

## Participation, missed encounters and transitions

- Creator selects mode; another group member uses Join. The run supports six
  lifetime participants and rejects a seventh, even if someone leaves the group.
  Changing group leader cannot change the mode or reset ownership.
- Kill by melee, damaging spell, ordinary owned pet and swarm pet. Nearby loaded,
  connected party members enrolled in this instance receive credit. An ungrouped
  character, another instance, disconnected character, or member beyond the
  200-unit three-dimensional sphere does not. Test vertical distance too.
- Keep one member out of range for the first boss, then join later. They get no
  retroactive credit or completion reward. In Grind, the next respawn supplies
  that objective; in Raid, the missed objective remains missed.
- Die during an encounter while still connected and nearby. Verify group credit
  follows the same area/member rule; a dead client retains a pending claim until
  able to receive it. Owned player pets retain their normal HP and damage.
- Disconnect/reconnect, zone out/in, abandon/reopen the task and restart the
  isolated server at each stage. Original deadlines, mode, personal/shared
  progress, seed, reward identity and permanent counts remain stable.
- Test an old unmanaged instance created before enablement. Enter, Join, timers
  and legacy reset retain their old behavior until it expires or is reset.

## Claims, corpse loot and reset

- Fill all inventory destinations, including bag restrictions, and empty the
  cursor. Complete the run: the reward remains pending. Free a valid slot and
  use Claim Rewards. Verify one item and its receipt, then no second award.
  Repeat with an occupied cursor, open trade, merchant, loot and tradeskill UI.
- Submit repeated/simultaneous claim requests and disconnect at delivery. Inspect
  the inventory transaction and receipt together. Never clear a receipt or
  restore an older player inventory to repeat a test.
- Loot final-boss native and exclusive items through normal personal/group loot
  controls. Verify each exclusive design appears at most once on that corpse.
  Across recorded independent runs check the 80/18/2 item-count and 90/10 quality
  distributions statistically; do not require a particular random drop in one run.
- Trade, bank, relog and own duplicate copies of all item categories. Test links
  for highest ID 960329. Check fixed weapon delay across qualities and bag
  capacity 6/8/10, size restrictions and weight reduction through 100%.
  Merchant resale is zero. Both forging routes reject dungeon items unchanged.
- A noncreator cannot reset. Confirmation expires after thirty seconds and
  cannot reset a different/new run. Reset fails with a player inside, a pending
  zone transfer, or an unburied recoverable player corpse. Close all participants
  outside and recover corpses, then reset. Earned unclaimed items remain claimable.

## Isolated failure and restart matrix

Use a disposable DB proxy/fault injector and the test process only. Capture the
run UUID and SQL/receipt preimages. Never kill a hosted production zone: its
supervisor restarts the whole game runtime.

| Interruption | Required recovery result |
|---|---|
| Before death transaction | NPC remains eligible; no partial credit/reward |
| After death inserts, before commit | Entire death/credit/corpse/timer rolls back |
| Commit succeeds but acknowledgment is lost | Zone suspends; reboot loads one death and one corpse |
| After commit, before native death publication | Raid enemy stays dead; finalized corpse/native loot recover |
| After Grind death with an older living checkpoint | Old NPC cannot return before durable native timer |
| Two Grind deaths at the same point before corpse decay | Both independently identified corpses recover |
| After partial item/coin looting, before checkpoint | Existing receipts suppress only already delivered loot |
| Before/after personal inventory commit | At most one item; uncommitted entitlement remains claimable |
| Zone unload with state-saving rule off/on | Managed UUID checkpoint works in either setting |
| Run expiry/reset, then native ID recycled | New generation cannot load old progress/corpses/rewards |
| Schema/content/cache drift | Enablement, new creation or managed boot refuses safely |

Verify absolute corpse decay and loot-right delays continue across downtime.
Repeat death/scaling recovery through several restarts; HP/damage must not
compound and Raid enemies must not resurrect. Record each fault point and actual
outcome; source assertions alone do not close these runtime cases.

## Level-50 combat acceptance

Vox and Nagafen each require explicit level-50 owner gameplay QA. Use reproducible
melee, caster and pet multiclass builds at expected earned gear/AA levels. Record
class slots, race, gear/augments, spent AAs, buffs, pets, group size, zone/mode,
combat logs, survival rate, outgoing/incoming DPS, mana/endurance sustain,
healing consumption, clear time and reward power against contemporary drops.
Do at least three comparable attempts per build/mode, separating no-AA baselines
from earned progression and any stress test. Check native dragon banish/level,
resist, fear and area-effect behavior. Record tuning changes and repeat affected
comparisons. Neither a successful synthetic build nor granting every AA proves
the intended demanding solo/small-group balance.

## Acceptance record

- Automated verification: see dated JSON evidence; scope explicitly limited.
- Test installation/runtime fault matrix: pending.
- Fourteen-mode gameplay and CT paths/doors: pending.
- Level-50 Vox/Nagafen balance: pending.
- Owner acceptance: pending.
- Production promotion/restart: separately authorized release, not performed.
