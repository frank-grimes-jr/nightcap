# Power Source item XP — OVH release 2026-11-03

Owner authorized on November 3: "Push to server. I'll test", then "Enable at deploy".
Design, curve and candidate evidence: [Power Source XP QA](../../items/power-source-xp/QA.md),
[ADR 0073](../../adr/0073-power-source-item-experience.md). Owner gameplay acceptance is open.

## What ships

- Paired `world`, `zone` and `shared_memory` (ruletypes.h adds `Items:PowerSourceItemXP`;
  the old world would delete the rule as orphaned).
- `rule_values` row `(1, Items:PowerSourceItemXP, true)` inserted in a guarded transaction
  before the new world boots, so world injects nothing.
- No client update: RoF2 receives the Power Source slot mask from server serialization.

## Build

`build.py` starts from the deployed Hunt-rates source
(`/tmp/nightcap-zone-hunt-rates-20261101-v1`, stripped zone `90717ac7…`) in
`akk-stack-eqemu-server-1`. Seventeen of the 21 item-XP files are unchanged on that base
since the Oct 31 candidate (`/tmp/nightcap-item-xp-live-20261031-v1`, built from Hate boss)
and are copied from it. SSF/placeholder-loot changed `zone/client.h`,
`zone/client_packet.cpp`, `zone/exp.cpp` and `zone/inventory.cpp`; those are three-way
merged (`git merge-file`, zero conflicts; SSF guards and `PassiveAAPercent` do not touch
the item-XP hooks). CRLF files stay CRLF. World is rebuilt from the same tree; every
source change since Oct 30 is zone-only. `package.py` strips all three and runs ELF
runtime identity ([native-identity.json](native-identity.json)).

## Rollout

`stage.py` → `/opt/nightcap/releases/power-source-xp-20261103-v1`; `rollout.py
preflight|activate|open` chains Hunt-rates' guards. `rule_values` leaves the generic
content hash and is compared exactly (before/after one row), as in
aa-level-progression-20261023-v3. Activation stops gateway and game, takes the stopped
backup, commits the rule, boots the new image with access closed, verifies binaries,
saved state, market, contract and rule catalog, then `open` reopens the gateway.
The whole runtime restarts (all players disconnect for a few minutes).

## Disable and rollback

Disable: `#rules setdb Items:PowerSourceItemXP false`, then `#rules reload` in every
running zone (or restart the runtime). Progress stays on items; take the item out of the
Power Source slot normally. Keep these binaries: older ones misread multi-key XP/grip
metadata. `rollout.py rollback` is only for a held activation before access reopens.

## Production (OVH, 2026-11-03 19:42 UTC) — deployed, owner testing

Staged from `106952bd`. Preflight built image `3999a935…` over Hunt-rates `b821548e…`.
The first activate attempt never connected (SSH timeout, no evidence written); it was
rerun detached on-host (`setsid nohup … > activate.log`) so an SSH drop cannot kill it
mid-transition. Activation: stopped backup `private-backup/peq-before.sql.gz`
(66,040,500 bytes, gzip integrity passed), rule committed, game booted at 19:42:23
with access closed. All processes run world `f33c5925…`, zone `7b61b96c…`
(shared_memory `56939…` at boot); saved state matched the boot model; exact rule
catalog = before + one row; contract and market checks passed. `open` restored the
gateway; effective rule `true`; no client update. 22 GB free on `/`.

Not verified: any in-game behaviour. Wiki not published (player-facing; publish after
owner testing confirms the feature stays on).

## Owner test spike

Full matrix: [Power Source XP QA](../../items/power-source-xp/QA.md) "Owner in-game spike".
Shortest useful pass, as a non-GM character:

1. `#itemxp` with nothing in the Power Source slot → explains the slot is empty.
2. Put one ordinary Normal/Base four-tier item you can use in the Power Source slot
   (inventory slot 21). Drag/drop must work on the current client. Unusable, stackable
   or evolving items must be refused. A real Power Source keeps working normally.
3. Kill non-gray mobs (e.g. Lower Guk frogloks at 50). `#itemxp` progress rises with
   roughly 10% notifications; character/AA XP gain matches a kill without the item.
4. While training, the item's stats, focus and worn effects give no benefit.
5. Zone, relog, then remove and re-insert the item: progress is unchanged and no
   duplicate appears. At 100% it upgrades in place (Polished, then Exalted, then top
   tier) and stops at top tier.
6. Reforging Box still combines 3 Base → Polished.

Report anything wrong with the item ID, zone and `#itemxp` output.
