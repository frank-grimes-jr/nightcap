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
