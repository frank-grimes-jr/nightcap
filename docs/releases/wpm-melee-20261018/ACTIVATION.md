# Combined candidate activation and recovery

Status: preparation only; no production action has been executed. Repository
feature → dev → test → main and owner gameplay acceptance remain release gates.

1. Reconfirm the completed paired native matrix and independent review against
   the exact release candidate. Current results are26 scenarios/134 regressions;
   a later shared-scaling integration needs new build and regression evidence.
   Record final source, world/zone/cache-loader and client hashes. Retain the
   baseline source and all original evidence. Check disk headroom before staging.
2. Recheck current main and current production fingerprints, original AA data,
   custom-ID ranges, NPC/loot bindings and rule preimages. Dated October18
   captures are not permission to overwrite later changes. Rebuild/rehearse
   from fresh preimages if any guard fails.
3. Assemble matching world and zone, the cache loader, generated AA policy,
   pet equipment schema, shared 750 caps, Rabid/support/fragment content, WPM
   AA/items and optional heroic rule. Pair generated item/spell caches with
   those binaries. New rules require matching world and zone.
4. Activate level65/PoP only with the staged progression rules, append-only
   merchant stock, matching era/catalog/restock files and verified world/client
   access. The older general era operator rejects levels above50; do not run
   it against this staged profile or merely change one rule and claim access.
5. Stage and sign the five-file client delta against the then-current signed
   base, preserving unrelated managed assets. Update channel metadata only in
   the authorized publication step, after immutable assets verify.
6. Use the established maintenance operator, close gateway/game writers and
   make a fresh preservation backup. Apply guarded content in one controlled
   maintenance window. The WPM item/AA migrations are transactional, reject
   drift and reapply idempotently. Never patch an occupied namespace by force.
7. Restart the matched stack and verify running hashes, new rule retention,
   cache data, AA counts, native contracts and preservation of player inventory,
   stored pet instances, AA ownership/points/charges, saved cooldown deadlines,
   vendor state and receipts. Account for the normal world-start market rotation.
   OVH supervises all native children; never kill one zone to refresh it.
8. Perform the exact client/gameplay checks in README before opening this as an
   accepted release. Publish reviewed wiki changes only with authorization,
   preserving unreleased labels until the corresponding runtime is active.

## Recovery boundaries

- Disable `Combat:NightcapHeroicMeleeScaling` using the guarded disable SQL and
  a global rule reload to turn off only the new heroic multiplier.
  The separate guarded enable SQL restores it from the exact disabled row;
  the initial forward SQL deliberately rejects unexpected existing overrides.
- `items-acquisition-rollback.sql` removes only the three new acquisition links.
  It retains definitions, existing owned gear, socket metadata and proc spells.
  Pet acquisition recovery similarly retains owned fragments. No player
  inventory or AA snapshot restoration is an ordinary rollback method.
- Do not remove earned new AA definitions after players purchase them. Resolve
  eligibility/policy recovery while preserving owned ranks, points and deadlines.
- Do not shrink pet equipment schema/locations while newer stored slots exist.
  Keep complete-instance recovery available. Never clear ownership or receipts
  to make an older binary start.
- A native rollback needs a compatible world/zone/cache/quest/client bundle.
  If new player state is incompatible, keep access closed and prepare a forward
  repair. Reversing migration text alone does not establish safe rollback.
- Clients that fetched a newer signed release need a higher-numbered corrective
  release. Preserve channel and public-site preimages and verify visible state
  before changing publication pointers.
