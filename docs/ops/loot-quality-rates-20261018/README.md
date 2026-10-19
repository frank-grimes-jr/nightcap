# Ordinary loot quality tuning — October 18, 2026

Owner approved 20% Polished, 5% Exalted and 1% Ascended after reviewing the
10%/2%/0.25% baseline. Production preflight confirmed exactly those old values
in default ruleset 1, with no alternate overrides. These are independent bands
of one 1..10000 roll per eligible ordinary equipment/bag drop, not per kill.
The resulting Normal band is 74%. Missing variants retain the base item.

## Activation

Status: **activated and verified October 18 at 2:36 p.m. Eastern**. The server
runs the reforging successor zone29b80931; its retained build changes only the
inventory implementation, preserving the reviewed loot/rule/reload objects.
`result.json` verifies all three rates, unchanged other rules, all15 native
processes and all5 services. No restart, binary/cache/client or quest update.

The initial file-log assertion missed two workers with no log file descriptors.
The complete container stdout+stderr interval proves12 queued and completed
zone reloads and13 default ruleset loads including world. The scoped
`ops/finalize_reload.py` reconciled the receipt without replaying SQL or reloading
again. Complete raw logs remain private with the rule preimages. The earlier
10:49 a.m. maintenance refusal in `pending-status.json` is historical.

`ops/apply.py` changes only `Zone:LootTierRareChance` 1000→2000,
`Zone:LootTierEpicChance` 200→500 and `Zone:LootTierLegendaryChance` 25→100.
These existing DB overrides do not require compiled-default changes, a new
binary, item cache, quest script or client. Reload world and all zones using
the authenticated global Rules request. The operator preserves all rule notes,
other rules and process/service lifetimes, and refuses unexpected preimages.
Private rule preimages and guarded forward/inverse SQL are retained under
`/opt/nightcap/backups/loot-quality-rates-20261018/` when activation begins.

No changes to hunt drops/quality weights, dungeon rewards, quest rewards,
item stats, reforging costs, inventories or existing corpse loot. Already
generated NPC loot is not rerolled by rules reload; allow normal fresh spawns.

## Verification and recovery

- `tools/tests/test_loot_quality_rates.py` compiles the actual deployed loot.cpp
  block and exhausts all 10,000 rolls. Exact counts: 7,400 Normal, 2,000 Polished,
  500 Exalted, 100 Ascended. Bags, non-equippables, missing variants, already
  tiered gear, hunt IDs and dungeon IDs are checked.
- `ops/rehearse.py` runs forward/inverse and preservation checks in session-local
  temporary MariaDB tables. Changed/missing/case-drifted/already-applied inputs
  reject. `rehearsal.json` records the five passing cases.
- Activation also rehearses forward/inverse against actual rules in a rolled-back
  transaction, then commits all three guarded changes together. It verifies the
  complete rule table, global reload logs in world plus 12 workers, and unchanged
  15 native/5 service lifetimes. The receipt is authoritative, not an exit alone.
- If the operation is uncertain, inspect current values and the private receipt.
  Never blindly rerun the one-time operator. If values committed but reload
  failed, preserve values and retry only the supported reload. A deliberate
  rollback uses the retained inverse with current-value guards, then global
  rules reload. Never restore player data or a whole old rules table.

## Player QA

In an ordinary hunting zone such as Unrest or Befallen, loot newly spawned native
NPCs. Check quality names and inspect/equip the items normally. Existing corpses
and NPCs may retain pre-change loot. Record eligible equipment/bag drops by
quality rather than all kills; a short dry streak cannot disprove a 1% chance.
Confirm ordinary 3/4/4 reforging remains available. Hunt and dungeon rewards
retain their separate rules. Balance and visible gameplay acceptance are open.

## Quest reward direction

Owner also requested consideration of automatic top-tier quest armor/weapons,
explicitly excluding repeatable/easily farmed quests. The design and concrete
edge cases are in [quest-reward-policy.md](quest-reward-policy.md). This rate
activation does not implement or advertise automatic quest upgrades.

Wiki impact and publication state are recorded in `wiki-review.json`.
All 14 wiki/content/refresh tests pass. Updated notices preserve the latest combined reforging/travel/cooldown wiki;
publication20261018-loot-quality-v1 passed guarded origin verification of465
files, rollback rehearsal and service/private-download preservation.
Public HTTPS verification is recorded in wiki-public-verification.json.

Installed Nightcap items knowledge and reviewed fingerprints were updated with
the actual loot hook, verified activation and quest exclusions. `update_skill.py`
retains an exact patch and checks current preimages before installation.
