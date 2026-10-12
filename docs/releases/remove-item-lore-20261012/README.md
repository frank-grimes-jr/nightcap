# Remove LORE from every item

Deployed October 12, 2026 after explicit owner approval to push to main and the
server. [PR #180](https://github.com/frank-grimes-jr/nightcap/pull/180) merged as
`e3da88a0a2777ca0f1be8eedf0c87ced9d91f1fe`. The owner selected **every item**,
including base items, tier rewards, quest items and shared lore groups.
Manual client/combine and balance acceptance remains pending.

Enable the existing `Items:DisableLore` rule in default ruleset 1. The native
item loader projects `LoreGroup=0` and `LoreFlag=false` for every definition,
and the RoF2 serializer sends the effective group. This allows collecting four
identical eligible items for the Reforging Box. Original SQL lore groups and
item descriptions remain intact. Future catalog rows inherit the rule whenever
the item cache is rebuilt. No binary or client update is needed.

This also permits duplicate equipment in otherwise legal slots and duplicate
quest items. Slot, class, level, attunement persistence, upgrade eligibility,
copy costs and instance-safety checks are retained. Duplicate earrings/rings,
weapons and augments can increase player power; numerical balance is not claimed.
The rule does not make bags nestable or evolving/customized items combinable.
Native legacy lore-group evolution initialization is an unimplemented stub;
CharmFileID scaling remains a separate path. Include special items in QA.

## Live verification

The same production image restarted at 17:29:07 UTC (1:29 PM America/New_York).
The gateway is open. All 309,410 cached item definitions now have LoreGroup=0
and LoreFlag=false, including all 160,783 formerly restricted definitions.
Every byte outside those two fields matches the prior cache. SQL item rows,
other rules, 46 player-state tables, 11 custom tables and 8,140 quest/plugin files
were preserved. Database/web/tunnel services and client artifacts were unchanged.

World, all 12 zones, loginserver and UCS retain their verified native hashes.
Follow-up checks found zero restarts and no detected native/quest/database errors.
The fresh 448,801,039-byte SQL backup passed gzip/completion checks. No restore
was performed. [Deployment evidence](deployment.json) records hashes and counts.
[Executed rollout](rollout.py) holds access closed on failed checks and never
re-enables LORE automatically. Its cache verifier passed [corruption/preservation
regressions](test_rollout.py) both locally and on the production host.

## Dated production preflight

Read-only inspection found 309,410 definitions: 160,783 with nonzero lore groups
(156,639 ordinary -1, 4,144 positive groups, including 3,933 >=1000). No item has
PendingLoreFlag set. `Items:DisableLore=false` is the sole explicit rule row,
in default ruleset 1. No RuleSet or disablelore variable overrides exist.
`Items:FreeTrade=true` stays unchanged. The active image is
`sha256:5e8a26cf1275758dc78ae4327f520389c98e01dcba3ffaed42e8f84ce7502022`, healthy,
started at 2026-10-12T16:32:04Z. Its supervisor rebuilds shared memory on startup.
The loader SHA-256 is
`91664a87eac78306e8a76ab4cb923ba1f03c2d0da180278db6b6cf9b6607c0ef`.
Recheck this baseline immediately before activation.

## Verification

- `python -m unittest discover -s tools/tests -p test_remove_item_lore.py -v`
  compiles actual native projection and ownership code, including pet armor,
  for normal/grouped/non-lore definitions with the rule enabled and disabled.
- `python tools/tests/rehearse_lore_guards.py` tests guarded forward/rollback and
  baseline drift in a disposable schema; results in `migration-check.json`.
- `python tools/tests/rehearse_remove_item_lore.py` clones only local content/rule
  tables into a disposable schema and private cache, uses the production-matching
  native loader, compares every item and all bytes outside the two lore fields,
  and verifies exact cache restoration after rollback. `cache-check.json` records
  counts/hashes. Local catalog evidence is not a production-cache verification.

## Activation procedure (already executed; do not repeat)

1. Recheck active image, rules, variable overrides and item counts. Take a fresh
   verified database backup and save exact rule rows and current cache hash.
2. Announce a brief reconnect, stop only gateway and game, and wait for saves.
   Keep database/web/tunnel running. Capture stopped player-state fingerprints.
3. Run `activate.sql` against production PEQ without `--force`. It requires the
   observed exact false rule and refuses changed/default/legacy rule selections.
   On a refusal, retain access closed and investigate; the handler rolls back.
   A failed CALL leaves its named procedure for inspection; remove only that
   procedure after diagnosis before a reviewed retry.
4. Start the existing game image. Its startup rebuilds the item cache. A rules
   reload alone is insufficient. Verify healthy world/all 12 zones, unchanged
   native hashes, no new errors, the true rule, and zero effective LoreGroup and
   LoreFlag across the entire production cache. Compare all other item bytes and
   stopped player-state fingerprints. Keep the gateway closed on any mismatch.
5. Open gateway after verification; run [exact in-game QA](QA.md). Record the
   resulting activation evidence separately from this candidate and its tests.

## Recovery

Before opening access, `rollback.sql` restores the exact false rule after a
matching guarded check; restart the same game image to rebuild its original
cache and verify it before reopening. It leaves item and character data intact.

**After players acquire duplicates, do not blindly re-enable LORE.** Native
cursor validation can destroy conflicting copies. Capture fresh owned inventory,
bank, cursor, augment and pet-armor state and agree a preservation/reconciliation
plan first. Do not restore an old database or delete earned copies as rollback.

The configuration approach uses existing deployed behavior and preserves source
item definitions. Rewriting all item rows loses that provenance and misses future
imports; bypassing individual loot/combine checks leaves client and other item
acquisition paths inconsistent. No C++ redesign is needed for this scope.
