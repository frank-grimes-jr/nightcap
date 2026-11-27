# Ascended drop rate rollout

The runtime unit is the native zone paired with the existing `Zone:LootTierLegendaryChance` default rule. The new zone removes the additional armor band. The rule changes from 100 to 700 per 10,000 eligible ordinary drops. Both switch while the game is stopped. The previous image and the value 100 are the paired rollback.

1. Run the earlier Classic QA `capture.py TARGET STAGE` into `artifacts/ascended-seven-20261127/ops/TARGET`. Run `audit.py TARGET 100`. A differing image, native executable, cache, November 27 quest preimage or alternate tier override stops preparation.
2. Run `run.py TARGET package ZONE SHA256 GAMEPLAY_COMMIT`. For production run `run.py production upload`. Run `run.py TARGET prepare` to build an image derived from its own immutable parent and rehearse the exact forward and inverse rule transactions on temporary PEQ rows. A deliberately stale Epic rate must reject the Ascended write and restore the starting value.
3. Run `run.py TARGET activate` when authorized. The operator checks occupancy, closes admissions, stops the game, takes and validates a full PEQ dump, switches the single rule row and the image selector, and verifies the restarted native workers, caches, November 27 quest hashes and all three tier values. Production reopens its gateway after those checks.
4. Run `run.py TARGET verify`, `audit.py TARGET 700`, and `run.py TARGET receipt`. The receipt includes the stopped backup SHA-256, previous and current image, game health, worker counts, both cache hashes and startup error counts. New eligible NPC loot is the player test. Existing corpse or stored spawn loot can predate the rule.
5. `run.py TARGET rollback` takes another current backup and reverses the image and row together. Check the terminal receipts before retrying an interrupted operation. Rollback preserves current player progress.

The package imports the previous release's world, SHA-256, backup and Compose primitives. New packages keep their private dumps under this release name. Client and desktop channels have no part in activation.
