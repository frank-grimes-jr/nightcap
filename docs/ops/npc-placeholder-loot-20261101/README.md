# Lootless respawns after zone-state boot — November 1, 2026

## Report

Palwar ran public Nagafen's Lair (soldungb, instance 0) from 14:27 to 14:48 UTC
and found every fire giant, then Lord Nagafen, dropped nothing.

## Evidence (read-only production capture, 14:51–15:10 UTC)

- soldungb booted for Palwar's login at 14:27:34 and loaded 115 saved
  `zone_state_spawns` rows, all written by the 01:53:13 UTC shutdown.
- 23 of those rows (every fire giant, King Tranix, Warlord Skarlon, Magus Rokyl)
  stored `loot_data` as the literal string `invalid`, plus the persisted entity
  variable `nightcap:advloot-invalid-state=invalid`. Kobolds/bats nearer the
  entrance had valid loot JSON — hence "suddenly stopped".
- Lord Nagafen's row (spawn2 6461) was a dead-spawn placeholder: `npc_id 0`,
  empty `loot_data`. Its timer had expired, so boot spawned him fresh. His new
  respawn timer starts 14:46 UTC (Palwar's kill).
- Server-wide: 43 non-corpse rows carry `invalid` (soldungb 23, ecommons 12,
  zones 9/36/54/59/65); 305 placeholder rows are pending respawns that would be
  wiped the same way on a future boot.

## Root cause

`Zone::LoadZoneState` (`server-mods/code/zone/zone_save_state.cpp`) applied
`LoadNPCState` to whatever NPC a saved row's spawn produced, including a fresh
respawn from a placeholder row. The placeholder's empty `loot_data` then reached
the advanced-loot validator, which (unlike upstream's empty-loot re-roll) clears
the NPC's loot and quarantines it as `invalid`. The quarantine is self-sustaining:
the next shutdown saves `invalid`, the next boot cannot parse it and quarantines
again, and `corpse.cpp` locks any corpse that inherits the flag. The NPC stays
lootless until it dies once; its respawn is then normal unless another boot
catches it as a placeholder again.

## Fix

1. Only apply saved NPC state when the row holds a live NPC (`s.npc_id > 0`).
   Placeholder respawns keep their own normal loot roll.
2. A non-corpse row whose loot is the bare `invalid` sentinel holds nothing to
   recover: lift the flag and roll the NPC's tables (upstream's fallback). This
   heals the 43 already-flagged NPCs on their next boot without SQL changes.
   Raw unparseable loot (kept verbatim for recovery) and corpses are unchanged.

Gotcha: a re-rolled NPC gets new drop IDs, so a crash between looting it and the
next save could replay that one roll. This matches upstream and closes after the
first post-fix save.

## Tests

`tools/tests/test_zone_state_home_native.py` compiles the real restore loop and
`LoadNPCState`. New cases: a placeholder respawn keeps its roll and is not marked
resumed; the `invalid` sentinel is lifted and rolled; real saved loot still goes
through the validated loader. The placeholder case failed before the fix.

## Wiki impact

No guide, command or catalog change: loot tables and rates are unchanged. The fix
restores intended drops only.

## Deployment — November 1, 15:36 UTC

Owner-authorized ("merge to main and OVH"; build-cache prune and immediate
restart approved in chat). Main PR #389 (`74f1c0d5`).

- Zone built in `akk-stack-eqemu-server-1` from the retained deployed Hate boss
  source tree plus only the fixed `zone/zone_save_state.cpp`; stripped zone
  `77c5fdff…` (53,083,688 bytes), ELF runtime identity PASS. World/shared_memory
  unchanged. Build tree: `/tmp/nightcap-npc-placeholder-loot-20261101-v1`.
- OVH disk was 532 MB free; `docker builder prune` removed 1.06 GB of unused
  build cache only (no images, evidence, backups or player data).
- `rollout.py` (staged at `/opt/nightcap/releases/npc-placeholder-loot-20261101-v1`)
  reuses the deployed release's guards. Its pre-install `public_preflight` was
  dropped: it fails by design after that release moved three boss rows.
- Preflight, activate and open passed: image `9bd39442`, all 12 zones `77c5fdff`,
  51 schema / 671 content checks, 102 saved-state tables matched the boot model,
  fresh stopped backup 65,850,590 bytes (integrity passed), zero native/quest/DB
  errors, gateway open. ~1.3 GB free afterwards. No client update.
- Rollback (only after a held activation): `rollout.py rollback` then `open`.

Not verified: in-game drops. The 43 flagged rows heal when each zone next boots.

## In-game QA

1. Kill fire giants and Lord Nagafen in public soldungb after the deploy (Nagafen
   respawns about 16:12 UTC November 4): corpses have loot and are not locked.
2. Kill a few East Commonlands NPCs: loot appears normally.
