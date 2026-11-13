# Classic raid augment production QA

The owner authorized promotion after automated tests on November 12. Main PR 435 preserves the already-tested raid feature, the disabled earned-title candidate, and the concurrent Inventory source. The shipping build uses the retained active server source so that adding raid augments cannot activate an unpublished source-only system.

## Deployment

The release uses a guarded install of IDs 963200–963215, a matched world, zone and shared-memory loader, and the existing signed RoF2 client. The native receipt pins all feature inputs and the executable hashes. The release operator checks player count before closing admissions, drains the gateway, stops the whole supervised runtime, writes a fresh database backup, applies the item rows and reopens after verifying the new cache, services and saved state. Its full-catalog rehearsal compares every prior cache entry byte for byte and checks the level, slot, LORE and pet fields on every new item.

If a transition is interrupted, inspect its receipts and actual image, cache, SQL rows, backup and gateway state before continuing. Keep saved player inventories and corpse rows. Once any trophy has been awarded, retain its definition and the compatible per-item LORE loader when withdrawing or changing the loot feature.

## Observed result

The full rehearsal loaded 310,016 items and preserved all 310,000 prior item records. The guarded install and replay passed. The stopped backup passed integrity and independent hash verification. All 12 zone workers ran build a0506a16 beside world 56a61f20 and loader 2bb1155d. The game had zero restarts and zero native, quest or database errors at verification. Public admissions reopened and the existing signed client channel stayed paired. [Production receipt](deployed.json) · [Rehearsal](preflight.json) · [Main PR](https://github.com/frank-grimes-jr/nightcap/pull/435).

The official wiki release 20261112-raid-augments-v1 passed all 631 origin checks and retained 598 predecessor files exactly. The guide, 16 item pages and eight zone pages are published. [Wiki publication receipt](wiki-publication.json) · [Player guide](https://wiki.nightcapgame.org/classic-raid-augments.html).

## Owner in-game checks

1. Log in at level 50 after reopening. Inspect a trophy on a qualifying type-22 chest, extract it, swap to a different trophy, zone and relog. Check duplicate ownership and the Power Source, pet and non-chest restrictions.
2. Loot a public dragon and a credited managed Raid boss. Confirm the party shares one extra corpse roll alongside normal loot. Check the Grind control and a restored corpse. In Sky distinguish the efreeti chain from the final Eye.
3. Cross below 35% HP with Cazic's rune, then check the next hit and the 12-second expiry. Test Heart on weapon, ranged and gem-cast direct hits while injured. Spend 10% of one resource on Prism and check the capped return. Swap, zone and relog inside the shared 90–91 second reuse.
4. Compare a Hunt chest and a raid chest on Cazic-Thule in his home zone. Repeat with three pets on Innoruuk and the Eye, recording effective healing, burst survival, resources and kill time. Human play, encounter scripts and real room geometry remain open for acceptance.
5. Phinigel’s Deepwater Pearl is augment 963202. Stock item 33961 has the same display name. Verify the raid item has the LORE, level-50 and type-22 fields.
6. Master Yael’s individual drop is present. His public spawn route still needs an observation. Check the exact NPC ID on a natural encounter before recording acquisition.

[Full balance dataset](../../items/classic-raid-augments/balance/README.md) · [Source and item catalog](../../../config/classic-raid-augments.json)
