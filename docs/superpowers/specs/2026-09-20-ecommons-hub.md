# Approved East Commonlands hub implementation

The owner approved the tunnel proposal on September 20. Move the 22 existing
services to classic ecommons22, retaining identities, inventory, prices and
exotic appearance. Add ten direct Classic travel routes with returns, retain
access to PoK, and make the tunnel the start for new characters. Preserve all
existing character positions and bind rows.

Implementation order:

1. Probe native map geometry and existing client portal imports. Select grounded
   positions and verify model availability before generating mutations.
2. Generate fresh, transactionally guarded forward/rollback SQL for service
   spawns, destination doors, new-character start rows and rules, and explicit
   hub recall. Invalidate only affected non-corpse instance-0 saved spawns in
   zones202/22. Retain stock, existing routes and unrelated saved state.
3. Deploy the same service quests in ecommons and update class/hub guidance.
   Keep native Return Home/Origin bound to existing character home binds.
4. Extend the signed patcher inventory with the exact zone import assets, map
   labels and usable recall spell data. Existing silent UI behavior remains.
5. Test data guards, rollback, original content preservation, import/packaging
   checks and quest bindings. Independently review the candidate, then promote
   through dev/test and activate the QA server/client package with backups.
6. Record exact owner QA for every merchant, portal, return, new start, recall,
   model, path and pet transition. Main promotion requires manual sign-off.

An audit found the old custom recall spell99001 is outside the native uint16
cast path and uses SummonPet rather than Teleport. Retain owned AA2220/rank22200,
but assign a verified unused representable spell and include its client record.
Do not solve recall by rewriting player bind points.

Actual client rendering and walking remain owner QA. Native geometry, exact
asset linkage and successful installation are necessary evidence, not a claim
that the in-game acceptance checklist passed.
