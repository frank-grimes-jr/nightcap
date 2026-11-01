# Solo self-found mode: release notes

Status: owner authorized main and OVH on November 1 ("Push to main and OVF");
in-game QA open. Design: [ADR 0074](../../adr/0074-solo-self-found-mode.md).

## OVH rollout

`rollout.py preflight|activate|open` (and `rollback` after a held activation),
staged at `/opt/nightcap/releases/ssf-mode-20261101-v1`. The zone is built from
the deployed placeholder-loot source plus only the SSF patch; main's mirror also
carries the unreleased Power Source candidate, so main files are not copied
whole. Activation stops gateway and game, takes a fresh backup, creates the
table, installs the Chronicler, then boots the new image with access closed.
`stage.py <zone> <archive> <revision>` uploads the payload and writes the
on-host manifest.

### Deployment — November 1, 21:27 UTC

- Main PR #391 (`f87e611b`). Zone built in `akk-stack-eqemu-server-1` at
  `/tmp/nightcap-ssf-mode-20261101-v1`: the deployed placeholder-loot source
  plus `ssf.patch` (8 files). Stripped zone `2ca5fa0e…` (53,080,208 bytes),
  ELF runtime identity PASS. World and shared_memory are unchanged.
- Preflight: image `e67956fa` builds over base `9bd39442`; the Chronicler passes
  `perl -c` inside it.
- Activate: stopped backup 66,075,896 bytes; `character_ssf` created empty;
  Chronicler `777d5793…` replaced (previous copy kept in the evidence). All 12
  zones run `2ca5fa0e`. 51 schema / 671 content checks pass; 103 saved-state
  tables match the boot model; zero native, quest or DB log errors.
- Open: gateway up. No client update.

Not verified: any in-game behavior (see QA.md).

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
