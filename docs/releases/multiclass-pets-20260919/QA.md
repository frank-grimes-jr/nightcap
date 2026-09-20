# Three class pets: owner QA

September 19, 2026. Candidate server build; manual acceptance is pending.
The existing signed launcher 2026091906 is sufficient. This change requires
the candidate **server**, not another client patch or a startup slash command.

## Setup

Use a disposable level-50 QA character holding Shaman, Necromancer and Magician.
In Plane of Knowledge, The Ancient Chronicler (NPC 999220) is at server
x -285, y -124, z -158.875. The nearby class merchants occupy the compact grid
x -321 to -249, y -184 to -112. Obtain the appropriate scrolls and reagents for:

- Shaman: **Frenzied Spirit**, spell 166.
- Necromancer: **Invoke Death**, spell 443.
- Magician: **Greater Conjuration: Water**, spell 633.

Use the actual spell names shown by the supported client if localization differs.
Do not change era/level rules for this test. Confirm the intended three classes
appear in Inventory. Record class order, character, zone and server build.

## Summons and the ordinary pet window

1. In a safe open area, summon all three. Expect one spirit, one skeleton and
   one water pet. Cast the Necromancer summon again: there must still be three,
   and the existing skeleton and its equipment must remain intact.
2. Repeat with a different summon order and, on a separate QA character, a
   different primary class. A non-pet primary plus two pet classes must also
   work without requiring a primary-class pet first.
3. Use the normal pet window once per action: Sit, Stand, Follow, Guard, Back
   Off, Taunt, Stop and Dismiss. All eligible pets should respond together;
   repeated toggles should leave them in the same state. Dismiss removes all
   controlled summoned pets. No new startup commands should appear in chat.
4. In East Commonlands, target an appropriate nearby hostile NPC (a decaying
   skeleton is suitable). Press Attack once: all three eligible pets should
   pursue and use normal combat AI. Back Off should stop all three. Repeat
   with Quick Attack. An out-of-range target must not bypass native range checks.
5. Hold, Greater Hold, Focus, Spell Hold and Regroup retain their native AA
   requirements. Test both unavailable and legitimately purchased commands;
   this feature must not grant missing AAs. Enchanter animations and familiars
   retain their native command restrictions.
6. Let the pet shown in the window die, or reclaim that specific pet. The
   window should switch to a surviving pet and keep working. HP, buffs and
   target display must not alternate between unrelated pets.

## Separate eight-slot armor

1. Open Pet Armor and select each of the three pets/classes. Equip clearly
   different eligible items in each loadout; inspect each item. No item may
   appear in another class's loadout. The UI has at most eight slots per pet.
2. Remove one item: the complete original item instance returns once, including
   augments/charges where supported. The other pets' gear is unchanged.
3. Summon, dismiss and resummon each class pet. Its class loadout persists.
   Underlying native/summoned gear is restored when an overriding armor item is
   removed. Items must never appear both on the cursor and in armor storage.
4. Recheck stat effects with armor that adds HP/mana. Zone and relog: resource
   values should be bounded by the armored caps, not truncated to naked caps.

## Lifecycle and persistence

1. With all three pets and distinct armor, zone **PoK → East Commonlands → PoK**,
   then camp and log back in. All three valid pets, buffs and separate gear
   should return; command the roster again after each transition.
2. If the character owns Suspend Minion, suspend the displayed pet. The other
   pets remain controllable. Zone/relog, then recall: the original class pet
   returns without replacing either survivor. Recalling while its class slot
   is already occupied must not create a duplicate.
3. On a disposable character, release a pet class through The Ancient
   Chronicler's confirmed class-release flow. Its active or suspended pet goes
   away only after successful release. Other class pets remain. Its armor
   remains recoverable; verify the existing armor recovery UI.
4. Die with three active pets. All summoned pets and beneficial buffs must go
   away. Reconnect/resurrect: no active pet should return from stale saved state.
   Stored pet armor must remain owned and recoverable.
5. Check an older character with a saved/suspended pet from before this release.
   A still-held class restores correctly. A released-class suspension must not
   block future valid suspensions. Do not inject SQL failures into the live DB;
   rollback/quarantine fault testing has already passed in the isolated clone.

Record any mismatch with the exact action, class/summon order and screenshot.
Passing native tests is not a claim that these client and gameplay checks passed.
