# Last Lantern implementation and authorized release

November 7, 2026: owner approved the campaign by requesting main/server release
and client notes. This authorizes this feature's main promotion and deployment;
it is not gameplay acceptance or future release permission.

Accepted design: docs/adventure-journal/CAMPAIGN.md. Existing implementation is
the unreleased eight-task Epic 0.5 candidate. Do not publish a design as gameplay.

## Ordered slices

1. Audit current target and prove reward policy: reserve IDs; compare effective
   native trade/cache rules, item bands, complete source and current release.
   Add pure native reward eligibility/identity policy and negative tests.
2. Implement one durable armor claim and atomic refit: stable per-character/slot
   entitlement, inventory CAS and receipt, preserved augments/dye/custom metadata,
   quarantine on uncertain commit. Test failure, retries and custody first.
3. Deliver first act: native Tasks, companions, first three rewards and five
   existing oath trials. Preserve task authority and the charm contract.
4. Deliver isolated continuation scenes: distinct campaign instance UUID/start
   identity and membership, no Keeper completion or loot side effects, no saved
   transient actor resurrection. Test first rescue before expanding scenes.
5. Complete later chapters, refits, planar finale and campfire; audit native map
   placement and all armor fits, derive budgets from current released items.
6. Verify complete package: actual native build retaining current source, real
   disposable MariaDB rehearsal, encounter/balance and inventory regressions.
7. Review, main promotion and owner-authorized deployment: fresh current guards,
   paired binaries/content/cache/client, stopped backup, supported runtime
   restart, exact readbacks and service/ownership preservation. Recover forward.
8. Publish truthful signed client notes and scoped wiki instructions, verify
   served hashes; maintain CHANGES/status/lore/installed skill. Record exact
   remaining player QA separately from automated and deployment evidence.

## Architecture and proof requirements

- Native completed Tasks own eligibility. No parallel persistent story mask.
- First armor delivery may use ReceiveItem with a stable slot entitlement UUID.
  Existing ForgeItems cannot refit augmented/dyed armor; add a dedicated adapter
  using clone, complete saved-row CAS and native operation receipts.
- Effective campaign item policy must run after FreeTrade projection. NO DROP,
  NoTransfer, zero resale and NoPet must survive actual cache construction.
- Campaign instances use their own notes prefix, run allocation and membership;
  never piggyback on Keeper reward enrollment. Transient attempts reset after
  restart; earned task progress and item receipts remain.
- Pin fresh live images/binaries/cache/quests/client and retained complete source;
  the selective Git mirror and historical builder are not full live authority.

Review: fresh-context architecture review identified all four issues above.
Their resolution is required before a playable release. No external model CLI
review is implied or run.
