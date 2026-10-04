# NPC content change

Move swashbuckler

Revision 2. Source profile: local.

## Apply

Import change-set.json into NPC Admin, select the target, and review the current preflight. SQL files are for review only. Git publication does not apply this change to any server.

## Activation and QA

- Stop the affected zones before apply so saved state cannot overwrite placement. The app removes only reviewed non-corpse saved state for those spawns. Start those zones afterward; use #repop only when saved-state handling is not needed.
- Database application does not prove in-game activation or balance. Complete the listed zone/NPC QA before gameplay promotion.

Inspect each changed NPC in every affected zone and version. Verify placement, heading, pathing, combat, merchant stock or loot as applicable. Record results before promoting gameplay to main.
