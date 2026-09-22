# Owner in-game QA: pet management

Run with the matching candidate server/client generation. Record character,
server, client release, primary/secondary/third classes and zone. This checklist
is not a record of a pass. Use a normal level-50 SHM/NEC/MAG character; repeat
with another primary class and with only one/two pets.

1. In the safe East Commonlands tunnel area, summon Frenzied Spirit (166),
   Invoke Death (443), and Greater Conjuration: Water (633). Pet Info must show
   all three names/classes and health percentages within one second. Its scope
   must say `Commands: All pets`. No `[NCPM1]` metadata should appear in chat.
2. Click Sit / Stand, Guard, Follow, Taunt, Stop and Back off. Verify all three
   eligible pets respond together. Repeat the matching `/pet` commands. Toggle
   mixed starting states and confirm a single shared resulting intent.
3. Click the skeleton's name: its row gets `>` and the scope names it. Sit,
   Guard, Follow and Taunt must change only that skeleton. Other rows/health
   remain visible. Click the same row again: scope returns to All pets.
4. Click the water pet in the world. Confirm its row and scope select it. Target
   a nearby decaying skeleton outside the tunnel and press Attack: only the
   water pet attacks. Back off changes only that pet. Repeat `/pet attack` and
   `/pet qattack`, ensuring the enemy target does not erase pet selection.
5. Click All pets; with a nearby hostile target, Attack and Back off control all
   three. Clear the game target after individual selection: scope becomes All
   pets. Targeting another player's pet must not select or command that pet.
6. Select one pet and Dismiss it. Exactly that pet disappears. After the next
   snapshot the remaining rows and All pets scope are correct. Resummon it;
   its prior selection must not transfer to a reused spawn ID. Click a stale
   row during death/reclaim: survivors must not receive an unintended Dismiss.
7. Verify Hold, Greater hold, Focus, Spell hold and Regroup without and then with
   legitimately owned AA permissions. Repeat on an animation/familiar build.
   Existing native restrictions must remain. Check out-of-range, feared-pet,
   mezzed-target and line-of-sight rejection; no new combat shortcut is allowed.
8. Damage a pet and verify its own row health changes. Select each pet and check
   native detail gauges/buffs show that representative. Resize the window, close
   and reopen it, reload UI, and verify all rows/buttons remain visible and usable.
   Check existing pet hotbar buttons retain their labels and saved assignments,
   and execute with the displayed scope. Dragging a new window control must not
   create an unrelated native pet hotbutton or issue a command.
9. With distinct pet armor loadouts, select a command pet and then a different
   Pet Armor pet. Command scope must stay unchanged. Existing armor, summoned
   gear and class loadouts must persist through dismiss/resummon.
10. Zone East Commonlands → West Freeport using the existing travel route, return,
    camp and log in again. All valid class pets and armor return, scope starts
    at All pets, and both window/slash controls work. Releasing one pet class
    removes only its pet and cannot retain that pet's control selection.

Use a disposable QA character for destructive lifecycle checks. Record any pet
that ignores a permitted command, the exact command/selection/target, pet type,
AA permissions and server/client build. Command correctness does not establish
three-pet encounter balance; existing balance acceptance remains separate.
