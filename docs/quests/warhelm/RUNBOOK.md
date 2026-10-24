# Ashen Compact candidate operations

This work does not authorize main promotion, deployment, client signing or wiki
publication. Production remains on its separately recorded released sources.

The entrance now belongs to Everfrost's hidden Permafrost approach, not the
former Commonlands candidate. Install exact-ID scripts 998860.pl and 998877.pl
under `quests/everfrost`; remove any superseded copies from a prior candidate
staging area. Pair the new native Keeper/Drazhul host gates with regenerated
content/contracts, the final journal zone and Kael return exits (zone 30).
The disabled installation SQL supersedes the uninstalled candidate; it is not
an upgrade script for an already-installed Ashen database. The original
reservation guards deliberately refuse that case. No new client archive or
combat retuning is needed for this relocation. See EVERFROST.md and QA.md.

## Reproduce the candidate

`warhelm_capture.py` reads only public local content. Regenerate the disabled
schema/content using `warhelm_migration.py`, then `dungeon_catalog.py` and
`dungeon_refresh_contract.py`. Run `tests/rehearse_warhelm.py` in its dedicated
no-network disposable MariaDB container. Never substitute a game DB for it.
The rehearsal checks source drift, reference collisions, atomic rollback,
repeat refusal and campaign progress preservation. Native floor/headroom probes
cover41 placements; they are not visible-client or route-pathing proof.

`build_warhelm_candidate.py` uses the verified retained complete Camil source,
overlays this checkout's server-mods/code and builds world/zone/shared_memory in
`/tmp/nightcap-warhelm-v1`. It does not install binaries or restart services.
The manifest must match the final reviewed sources, including attack.cpp's
temporary-actor XP gate and the corrected admission/capacity checks.

`warhelm_balance.py prepare` clones only the existing synthetic October23 Camil
fixture into `nightcap_warhelm_balance_20261024`; it refuses overwrite. It does
not copy PEQ player data. `diagnostics`, `build`, then `warhelm_capstone.py` use
the separate runtime and current candidate native objects. This controller has
explicit bounds documented in [BALANCE.md](BALANCE.md); arena wins do not certify full Kael.

`build_warhelm_client.py --client E:/Nightcap --eqg SOURCE --output NEW_STAGING`
pins the recovered official EQG by SHA1 and requires the installed Camil HE90
baseline. The package adds HE91 and preserves every preexisting fragment and
texture. The closed helm replaces the face surface only in its new variant.
Both global_chr.s3d and global4_chr.s3d are paired. Native8KiB PFS, typed material
closure, registration, bone bounds and24x150ms animation checks are mandatory.
The output is a staging artifact, not a signed launcher release. Never edit the
protected reference client or copy these archives manually into installed clients.

## Future authorized release

1. Rebase against the then-current integration branch and review any new High Keep changes,
   especially shared dungeon/attack hooks (dev1a8a4917 is already reconciled). Take fresh production public preimages,
   reservation/reference/engine/trigger checks and a verified full backup. The
   local capture is not production evidence; regenerate and rehearse target SQL.
2. Account for active Kael instances, saved public spawn state, corpses and all
   referenced IDs. The migration must refuse drift. Preserve unrelated content
   and player state; never restore an old player snapshot to undo this feature.
3. Stage schema, guarded content, catalogs, exact-ID Perl scripts, paired native
   binaries and regenerated item cache together. The new dungeon contract requires
   the Ashen tables and items; replacing only the zone executable is insufficient.
   Stock Kael flag and Ashen state start disabled. Preserve the global Classic50
   era; use only the scoped zone113 exception and Everfrost exits.
4. Verify all51schema/565content checks and every generated reward-cache definition.
   Publish a new signed paired client release with both archives and matching
   manifest/release history, following the existing launcher workflow. Preserve
   concurrent assets, client contract and Camil material90. Validate the client
   and run [the exact gameplay QA](QA.md) before calling the appearance accepted.
5. Enable the campaign only within the authorized maintenance procedure after
   runtime/content/client pairing succeeds. Production's supervisor restarts the
   runtime on native child exit; do not use a local kill-zone recipe in production.
   Verify all workers, quest bindings, database/cache contracts and service health.
6. The wiki overlay is based on published Hole source66c7b843. Reconcile it against
   the then-current publication, including any newly published High Keep work.
   Preserve the finder, Build Lab, private guides and existing reward routes.
   Publish only when separately authorized, with the correct release labels.

## Pause and recovery

Pause new expeditions by disabling Ashen state; retain matching schemas, content,
items, receipts and runtime so Drazhul can deliver already-earned helmets. Keep
personal chapters, dungeon runs, allocation generations and recoverable corpses.
Content removal is a separate preimage-guarded maintenance operation. There is
deliberately no automatic table-drop or player-snapshot rollback.
