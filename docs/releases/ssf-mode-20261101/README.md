# Solo self-found mode: release notes

Status: candidate. Not built, deployed or owner-accepted. Design: [ADR 0074](../../adr/0074-solo-self-found-mode.md).

## Contents

| Part | Files |
|---|---|
| Schema | `server-mods/sql/20261101_character_ssf.sql` (plain `CREATE`, fails if the table exists) |
| Zone | `client.{h,cpp}`, `client_packet.cpp`, `client_process.cpp`, `client_bazaar.cpp`, `inventory.cpp`, `exp.cpp`, `perl_client.cpp` |
| Quest | `server-mods/quests/poknowledge/The_Ancient_Chronicler.pl` (`walk alone`, popup 500) |
| Tests | `tools/tests/test_ssf.py`; `test_passive_aa.py` harness stubs `IsSSF`/`PassiveAAPercent` |

There is no `ruletypes.h` change and no client, cache or `shared_memory` update.
World is unchanged; only zone is rebuilt.

## Deploy order

1. Back up PEQ (`tools/backup-peq.ps1`). Apply the SQL.
2. Copy the zone files into `akk-stack/code/zone/` and build zone. Restart the
   whole runtime; never kill individual production zones.
3. Copy the Chronicler script into `akk-stack/server/quests/poknowledge/` and run `#reload quest`.

Deploying the zone before the table is safe: the load fails open and no
character is SSF.

## Clearing SSF (GM only)

```sql
DELETE FROM character_ssf WHERE character_id = ?;
```

The character must then zone (or camp) for the change to take effect.

## Rollback

Revert the zone binary and the Chronicler script. Keep the table; old binaries
ignore it. If the feature is abandoned for good, drop it:

```sql
DROP TABLE character_ssf;
```

## Wiki impact

Player-facing. Needs a wiki entry for the oath and its restrictions before release.
