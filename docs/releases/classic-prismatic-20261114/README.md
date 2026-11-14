# Classic Prismatic release

The release keeps the current native server image and signed RoF2 channel. Three recipes turn existing dragon scales and gems into armor augments. Thirty-six stock definitions across nine Classic families were reviewed. See [item values and player checks](../../items/classic-prismatic/README.md).

Before activation, the operator clones current production content, applies the exact migration twice, verifies its inverse, and rebuilds the candidate item cache using the shipping loader. It checks every previous record, every new scale and the expected stock stat deltas. On activation it checks occupancy, closes admission, takes a stopped backup, writes the content, boots, and verifies the actual cache, workers, saved state, market and publication before and after reopening. The checked-in operator reads the payload from the main commit.

For recovery during a closed activation, check the release receipts, running services and player admission first. Once safely stopped, run the catalog rollback only while the guarded afterimages still match. Rebuild or verify the matching original item cache and confirm the original rows, world health and saved state before reopening. After exposure, use a forward correction that preserves owned item IDs.

The Equipment guide and Recent Changes describe recipes, level, compatible slots, and the Ascended effects. These source changes await public wiki publication. Wiki refresh also reports older source drift. The deployed signed client obtains item definitions through the server.
