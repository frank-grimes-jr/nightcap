# Power Source item XP — candidate acceptance

2026-10-30: source candidate, disabled by default. No runtime installation,
production activation, public wiki publication or owner acceptance is recorded.
The requested target is 4–8 hours for one Normal/Base item to its top quality.

## Candidate curve

| Transition | Comparable-kill equivalents | At 60–120 equivalents/hour |
| --- | ---: | ---: |
| Normal/Base → Polished | 80 | 40–80 minutes |
| Polished → Exalted | 160 | 80–160 minutes |
| Exalted → Ascended/Ascension | 240 | 120–240 minutes |
| Entire path | 480 | 4–8 hours |

An equivalent is the character-level-squared native kill reward at the dated
0.65 normal XP rate. Modified combat XP is normalized at the character's current
level. Zone modifiers and group/raid shares affect progress; AA allocation and
the character level cap do not reduce it. These times are estimates, not measured
player throughput. See calibration.json for level and zone sensitivity.

## Build and activation boundary

Use the exact reviewed source overlay on an authenticated retained source tree.
Build matching world, zone, shared_memory and any other native inventory readers.
The new rule catalog must reach world as well as zone. The metadata parser must
reach every item-loading consumer before any item acquires XP plus grip metadata.
Translation-unit compilation alone is not a linked release or a deployment proof.

On an isolated test environment, retain a fresh backup and verify inventory is
InnoDB, has no triggers, and the native connection uses autocommit without an
active transaction. Confirm the ordinary and Hunt four-tier definitions exist.
Enable Items:PowerSourceItemXP only after paired installation and record its
effective value in world and zone. Record the actual command-access value for
#itemxp, current client version, source manifest and native binary hashes.
Use the supported rules reload/restart procedure for that environment; on OVH
a child exit restarts the whole runtime. This document grants no deployment.

Verified native operator commands are `#rules current`,
`#rules get Items:PowerSourceItemXP` and
`#rules setdb Items:PowerSourceItemXP true`. The last command changes the selected
ruleset in the database and the current zone only. After paired installation,
use `#rules reload` and `#rules get Items:PowerSourceItemXP` in every test zone
using that ruleset. For a temporary single-zone check, `#rules set` changes only
that zone's memory. Test the actual non-GM player with `#itemxp`; the compiled
command defaults to Player access, but existing command_settings can override it.

RoF2 receives the additional Power Source slot mask from server serialization;
no protected client files are modified. Verify real drag/drop on the current
signed client before concluding a client update is unnecessary.

## Owner in-game spike

Run in an isolated candidate server with a non-GM test character. Record exact
item IDs, character level, zone, effective XP rules, client version and results.

1. In East Commonlands, hail Artisan Veyra and obtain the reusable Reforging Box.
   Confirm 3 identical eligible Normal/Base copies make Polished, then 4 make
   Exalted and 4 make the top tier. Keep the box. Repeat with a partially trained
   otherwise eligible input: partial progress is consumed, not pooled into the
   result. Existing augment, dye and customization restrictions still apply.
2. Select an ordinary four-tier equipment family from the candidate item cache
   and Ember of the First Dawn (961000/961001/961002/961003; level50). Verify
   the ordinary family's four exact IDs against the candidate cache before
   summoning test copies. Put one eligible base copy in slot 21 and run
   #itemxp. Unsupported, stackable, evolving and below-required/recommended-level
   items must not enter training. A real Power Source retains normal behavior.
   Test inventory-to-training and reverse swaps with an occupied destination.
   A matching second/third held class must count; an item matching no held class
   must be refused. Any remaining race/deity restrictions still apply. With the
   training rule disabled, remove the item to an empty inventory slot or cursor;
   a reverse swap must not insert another ineligible item into the training slot.
3. For the level50 check, use Lower Guk (gukbottom) and native non-gray frogloks;
   record the exact NPC type/level and con for each sample. Verify increasing
   #itemxp progress, approximately ten-percent notifications, each of three
   automatic upgrades, and the top-tier stop. No cursor copy or automatic equip
   should appear. Repeat at 0%, 50% and 100% AA and at level cap; character/AA XP
   must remain equal to a control without a training item.
4. Compare displayed stats and measured melee, spell focus and worn effects with
   the item in inventory and in training. Its equipment stats, augments, focus,
   worn effects and clicks must give no benefit while training. Check raw AC,
   healing/damage focus and item spell verification. Moving it to training must
   not attune it or fire an equip quest event. Test again with the rule disabled.
5. Confirm gray kills, resurrection, quest/GM XP and owned pets/mercenaries/swarm
   victims give no item progress. Confirm normal solo, group and raid attribution
   follows each character's earned combat share; no double credit.
6. Move the item out/back, zone, relog, trade, die/recover the corpse, and list/buy
   through the Bazaar. Check exact progress, binding, charges, augments, ornament,
   explicit dye and Paladin grip after each custody change. Default color follows
   the successor's definition; explicit dye remains. A conflicting lore item or
   incompatible augment must prevent advancement without consuming the item.
7. Rehearse native failure-injection tests, then reconnect. A failed/uncertain
   inventory write must quarantine the session without stale saves or duplicate
   upgrades. Do not inject DB faults into a player server.
8. Time representative low-, middle- and level-cap builds for at least 30 minutes
   each, including normal pulling, recovery and resource use. Record kill count,
   elapsed time and starting/ending progress, AA split, zone modifiers, group size
   and gear. Project each transition from measured progress/hour. Include a
   demanding solo build and a strong multiclass build; rare drops and the box
   remain useful alternatives. Re-tune and repeat if representative eligible
   combat falls outside the accepted 4–8-hour range.

## Disable and recovery

Disable Items:PowerSourceItemXP using the supported rules procedure and verify
its effective value (`#rules setdb Items:PowerSourceItemXP false`, then reload
and verify every affected zone using that ruleset). Existing progress remains on the item; remove it from the
Power Source slot normally. Equipment effects remain suppressed in that slot
even when training is disabled. Re-enable only with matching safe readers.

Keep the corrected metadata loader on rollback: old binaries can misread
multi-key XP/grip data. Never strip metadata, restore an old player inventory,
or manually replay an uncertain UPDATE to recover a release. Retain receipts,
read the saved inventory after reconnect, and reconcile the exact instance.
Backups are forensic/recovery evidence, not permission to overwrite later play.
