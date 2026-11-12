# Earned titles candidate

November12,2026 — source candidate on `feature/earned-titles`, based on
`origin/main`423f9c3b. 77 cosmetic titles and a generated wiki guide. No production
data, native runtime, client asset, public wiki or owner acceptance changed.

- Contract and alternatives: [SPEC.md](SPEC.md).
- Exact normal-player gates: [QA.md](QA.md).
- Catalog authority/generator: `tools/earned_titles.py`.
- Native policy: `server-mods/code/common/earned_title_policy.h`.
- Storage/adapter: `server-mods/code/zone/earned_titles.inc` and `setup.sql`.
- Wiki review: [wiki-impact.md](wiki-impact.md).

## Reproduce checks

From this checkout root:

```powershell
python -B tools/earned_titles.py --check
python -B -m unittest discover -s tools/tests -p test_earned_titles.py -v
python -B docs/titles/verify_native.py
python -B docs/titles/verify_storage.py
python -B wiki/check_refresh.py --repo . --ref HEAD --include-worktree
```

Native compile uses a fresh75MiB scratch copy of retained November12 build source
inside the local build container. It does not edit the active runtime overlay or
deploy a binary. Record complete translation-unit compilation separately from
unit controls, a full linked build, deployment and rendered player acceptance.

## Activation and recovery boundary

Activation has not been executed. On November12 the owner explicitly requested
"Push to main", authorizing this source promotion before manual acceptance.
The normal branch policy remains for future work; all attached player QA stays
OPEN. This instruction does not authorize server activation or public publication.
A later authorized release must reproduce the current shipping baseline and preserve all
intervening fixes before building/releasing a zone binary. No Client layout,
shared ItemData, rules catalog, item cache, quest or client change is required.
Production native child exits restart the entire runtime: use its supported
guarded whole-runtime activation and fresh backup, never kill an individual zone.

Before SQL, verify the three names are absent or match the complete reviewed
column types, primary keys, engines and trigger-free schema. Stop on drift.
Apply `setup.sql` to the game DB, preserving settings on repeated application;
new installations are disabled. Validate native/DB title-ID range collision-free,
command_settings overrides/aliases (titles access0), storage schema and all
existing native titles. Confirm the command, title packets and kill hooks against
the matching candidate. Only then activate with the guarded single-row change:

```sql
UPDATE nightcap_title_settings SET enabled=1
WHERE id=1 AND catalog_version=1 AND enabled=0;
```

Require one affected row and read back the exact row; do not replay an ambiguous
write. No quest/rule/cache reload can activate new native code. Counters begin at
activation; opening the picker/#titles lazily recovers existing recorded goals.
Keep the candidate wiki labeled Not released until actual activation evidence
permits Live testing. Publish only from a reproduction of the then-current public
wiki with retained manifests and exact scoped outputs; this older main checkout
alone does not reproduce a future public source.

Forward recovery: guard/read back `enabled=0` to suspend new counting/grants and
selection of this catalog. Retain every counter/award and the stable IDs. A worn
title may remain on its saved profile; disabling does not erase cosmetic profile
state or other titles. Do not drop the tables or restore player snapshots after
any activity. Recover forward/re-enable only against reviewed exact state.

## Verification recorded November12

- Four focused test groups pass, including compiled native policy and the actual adapter with injected storage/acknowledgment failures, persistent skill checks, historical ledgers, collision handling and permanent awards.
- All four complete changed native units compile: titles.cpp, attack.cpp, client.cpp and command.cpp. This is syntax compilation, not a full linked release. Exact source hashes/commands: native-compile.json.
- Ten real isolated MariaDB groups pass: disabled/idempotent setup, InnoDB/keys, concurrent counters/grants, saturation, per-character awards and non-destructive disable. See storage-tests.json.
- Twenty complete-site/refresh tests and Node search/equipment/experience checks pass;607HTML pages build. Browser visual QA is unavailable because no browser is connected.
- Global wiki refresh stays REVIEW REQUIRED for historical drift. No publication, native deployment or owner acceptance is claimed.
