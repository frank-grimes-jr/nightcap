# Stock worn ATK production release

The owner authorized the production push after the persistent local test activation and main PR 440. The source is 690d67f376d367d9111a978543b623789d5e0c6f. The immutable OVH stage is stock-worn-atk-20261113-v1.

## Scope and rehearsal

The forward SQL changes the ATK field on 405 tiered items and locks 135 Normal guard rows. A fresh read of 926 complete public item definitions matched the 285-column capture used to generate the migration. The full-catalog rehearsal on OVH checked forward, replay, reverse and reapply on a disposable schema. The current production loader produced 310,016 cache records. Exactly 405 changed only in the four-byte ATK field, and the other 309,611 were byte-identical. The guarded resolver, six exceptional families, tier values and item names are in the [ATK review](../../items/stock-worn-atk/README.md) and [per-item CSV](../../items/stock-worn-atk/changes.csv).

## Release and recovery

Use the existing image, native executables, signed client and 250 base worn cap. The one-shot operator checks current image and services, compiler-derived cache layout, guarded before/after values, unrelated item and gameplay content, saved state, market rotation and admission state. It saves a complete stopped backup before applying the data and verifies the item cache fingerprint on boot. During any interruption inspect the specific stage and receipts before continuing. If withdrawal is required, stop the supervised runtime through the normal guarded maintenance path and use the exact tested inverse while its full afterimages match. Rebuild the paired item cache and verify the original bytes. Preserve current player and inventory data.

## Verified production result

All 405 production tier definitions required an ATK change. All 926 full target and control rows matched their expected values after deployment. The active item cache matched the full-catalog rehearsal. The 12 zone workers ran the existing native build with zero restarts and clean startup checks, and the gateway reopened. The stopped backup passed gzip and SHA-256 verification. Existing custom items, augments, spells and the signed client retained their verified data. [Production receipt](production-verified.json) · [Full-cache rehearsal](preflight.json) · [Focused tests and wiki impact](validation.json).

The public Equipment guide now lists all 135 families. Its Change Log and search index were updated. All 631 published files were verified, with 628 byte-identical to the predecessor. The separate current-era loot snapshot included 24 of the 405 target definitions. Every listed target matched production. [Publication receipt](wiki-publication.json) · [Loot snapshot check](loot-data.json) · [Player guide](https://wiki.nightcapgame.org/equipment.html#stock-worn-atk).

## Player checks

With clean Armguard of Shadows variants, compare the item window at Normal 50, Polished 51, Exalted 52, and Ascended 53. Record equipped ATK at levels 50 and 60 with the same skills, STR and other gear, including just below and at the 250 base cap. At level 50 the Ascended piece contributes up to 44 before the cap. Check the unchanged Heavy Yttrium Chestplate and the held cases. Local native equip, packet and mitigation checks are documented separately from owner graphical and encounter acceptance. [Local validation](../../items/stock-worn-atk/test-runtime.json).
