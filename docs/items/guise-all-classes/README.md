# Guise of the Deceiver item eligibility

All four Guise qualities become ALL/ALL. The four item IDs are 2469, 202469, 402469 and 602469. Their class mask changes from 384 to 65535. The captured race mask is already 65535. The full item preimages in before.json bind every other field, including click spell 590 and click type 1.

The guarded catalog supports before, forward, verify and rollback. Run it with Python and pipe the emitted SQL to a MariaDB client that stops on errors. The forward operation accepts an exact original or corrected row. An unexpected value causes transaction rollback.

The release reuses the verified stock-item maintenance workflow and shipping loader. Preflight rehearses forward, verification, replay and rollback on a disposable copy, then rebuilds items. The cache comparison permits only the class mask bytes on the four Guise records. Activation uses the deployment and GM locks, drains admissions, stops the game, captures a fresh backup, applies the four-row transaction and restarts the paired runtime. Verification checks the expected item cache, twelve workers, normal startup state and market rotation before reopening.

After activation, reconnect to refresh existing item definitions. Inspect each Guise quality and confirm Class ALL and Race ALL. Use a character without Bard or Rogue to equip it in the face slot and right-click its Dark Elf illusion. The automated checks verify data and cache behavior. Native item-window and click acceptance requires in-game observation.

The Lower Guk guide and Change Log describe the eligibility correction. Loot finder links the scripted source. Home, Features, commands, Hunt catalogs and other item acquisition guides have no additional impact. Public wiki publication is tracked separately.

The first activation stopped at the publication guard before maintenance or SQL because the concurrent Inventory release changed the client/wiki publication. The second immutable stage captures that published baseline; the item preimages, native image, binaries and both cache hashes are identical to the first rehearsal. The original stage remains an unsuccessful, pre-mutation attempt.
