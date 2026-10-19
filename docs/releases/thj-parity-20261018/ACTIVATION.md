# Combined release activation and recovery

The owner explicitly authorized main and server promotion on October18. The
release is now installed for live testing; [deployment/README.md](deployment/README.md)
contains the guarded execution, first-boot rule-description hold and reviewed
forward resume. Use its pinned-image entrypoint for this retained recovery.
The steps below explain the preparation contract; they are not an instruction
to replay the completed activation. Owner gameplay acceptance remains open.

1. Reconcile the final candidate with current main and the then-current deployed
   runtime/client. Pin all overlay/retained inputs. Build matching world, zone and
   shared_memory; confirm ldd and source hashes. Never replace newer production
   sources with the default workspace or an older worktree.
2. The full content capture here is October18 23:53:52UTC,1710 items/285 columns,
   from the29b80931 zone release. It is reproducible test input, not a permanent
   activation preflight. Fresh target drift requires review, new captures and
   rerunning the migration rehearsal, not weakening guards.
3. Prepare pet schema and paired Rabid/support spells; WPM earned AA changes;
   shared750 caps; heroic STR rule. For existing items, use ONLY this folder's
   `content/items-forward.sql`. Companion `pet-content-forward.sql` and
   `wpm-content-forward.sql` here deliberately omit their separate gear updates.
   Do not run older full-row gear migrations before/after the combined installer.
4. Apply the non-gear pet/WPM content and combined item migration, then the new
   `rules-forward.sql`. Repeated application accepts exact afterimages only. World rewrites rule notes
   to compiled descriptions; the corrected rule generators match those notes.
   A failed CREATE/CALL/DROP sequence can leave a procedure: inspect and
   authenticate it before any retry; do not blindly replay an uncertain component.
   Data components are transactional; pet schema DDL is separate and the entire
   bundle is not one transaction. Keep writers closed until components and caches verify.
   Preserve both independent Seru loot links and all original acquisition rows.
5. Leave the declared Classic50 era intact unless the complete staged PoP65
   profile is explicitly part of the test. Rules alone are insufficient: era,
   catalog/restock, merchant additions, world and client access must agree.
6. Rebuild caches against the final content and binaries. Stage the five-file
   pet/WPM client delta against the current signed base, including unrelated
   October18 travel assets. Formula/item changes add no client spell IDs beyond
   the companion content. Do not write the protected reference client or publish
   a channel pointer while merely preparing tests.
7. For a later authorized activation, use the supported maintenance operator,
   close gateway/game writers, take a fresh backup and retain running hashes and
   player/custom-table receipts. OVH child exits restart the whole runtime; use
   a supported full paired restart, never kill an individual zone as a reload.
   Verify new rules survived world boot and all zones, caches and client agree.
8. Run QA.md, retain explicit results and then review balance. Local wiki edits
   remain Not released until separately authorized publication.

## Recovery

- `rules-disable.sql` sets both new spell rules false without deleting registered
  rule rows; global rule reload turns off only these formula changes. The paired
  `rules-enable.sql` restores them from the exact disabled state.
- `items-rollback.sql` restores the companion numeric baseline for1369 affected
  rows. It retains pet/WPM effects and sockets, including their stat floors.
  Run twice safely or reapply the combined forward afterward. This does not
  restore pre-release player state or remove the new content definitions.
- Companion acquisition-only recovery removes new drop links, retaining owned
  definitions/spells. Do not delete earned AA ranks or shrink pet storage while
  players own new state. Keep access closed and repair forward if an older native
  bundle cannot represent that state. Never restore an old inventory snapshot.
- A rollback of numeric definitions requires fresh item-cache generation and a
  compatible runtime restart. A client repair uses a higher signed release and
  preserves all unrelated assets; signed client2026101802 is published; recovery must use a higher counter.
