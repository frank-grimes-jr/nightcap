# Independent review — October22 reward candidate

The separate dungeon_review agent reviewed the authored catalog, append-only IDs,
full-preimage migration, runtime/cache guards, native click/timer behavior, forging
exclusions, rollback tests, guide and QA. No remaining blocking source finding.

Resolved findings:
- Added the separate character_item_recast timestamp collision guard and read-only
  aggregate audit, alongside native timers and item recast-group definitions.
- Documented that Sky canlevitate=0, and the noninstant Levitate click uses one Bat
  Wing subject to native conservation. Included non-GM missing/successful reagent QA.
- Cache harness rejects NDEBUG builds, explicitly uses -UNDEBUG, and records its
  compiler command. All six click configurations have ten independent negative
  checks; every row also rejects wrong MAGIC and inspect lore.
- Froze historical330-item packaging/installation/verification entrypoints and the
  superseded expansion-only rehearsal. Current combined rehearsal creates the
  separately installed advanced-loot receipt schema and utility spell definitions.
- Cast/reuse times are documented as base values subject to native focus behavior.

No active native reward consumer retains a330-item limit. Existing forge target
lookup accepts only legacy/Hunt identities; every960330–960413 item is excluded.
Original330 values change only MAGIC; stable dungeon indices/revision and persisted
loot selection remain. Native/SQL/cache receipts provide separate verification;
this review does not establish gameplay acceptance or authorize activation.

The broader item-scaling verification failure was reproduced with HEAD's original
dungeon_catalog and unchanged generator/SQL files; see preexisting-test-drift.json.
It is not corrected as part of this reward feature.
