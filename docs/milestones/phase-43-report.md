# Phase 43: Spell inspection class audit and correction

Audited every installed spell class field and every hosted scroll item. Legacy
scroll masks explain 18,990 unusable class entries across 7,636 items. Both native
inspection builders now enumerate canonical original spell classes and display
each class's own level. The character's lowest held-class level stays in access
checks. No database or spell-data rewrite is needed.

Independent tests execute the exact two native enumeration blocks, reproduce
the old 255/false-primary-class output, and pass with the fix. The actual new
hooks also pass all 250,720 class levels. Native runtime, catalog/asset, launcher
and signed installation checks pass. The QA package verifies 67 patch sites and
all 46 managed files; current gameplay assets and bootstrap helper are preserved.

Cut: changing gameplay eligibility, removing valid future-level classes,
rewriting item/spell rows and modifying the read-only reference client.

Owner-approved PR 101 merged to main and signed production release 2026100102
is live on OVH. All 46 public files/signature verify, and the existing production
controller installs them successfully. Only the DLL and catalog changed; all
five service fingerprints and other assets are preserved. Twelve publisher
interruption/drift checks pass. No database writes or service restarts were needed.

Still open: rendered in-game owner QA. The isolated installation fixture is not
a complete playable client. [Deployment evidence and exact QA](../releases/spell-inspection-20261001.md).
