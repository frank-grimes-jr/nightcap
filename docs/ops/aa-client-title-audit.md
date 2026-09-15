# AA client title audit — issue #16

## Status and intent

2026-09-15: the [live preflight](../audits/aa-titles-20260915/README.md) completed;
disablement remains unapplied because affected saved ownership exists.
The historical 193 missing-title families and 29 name-pattern matches are not
interchangeable. The RoF2 client looks up `aa_ranks.title_sid` in type-1 records
of `dbstr_us.txt`; neither the server name nor an expansion cutoff is sufficient.
This audit follows every rank in each family and reports missing/empty titles.
Counts can differ from a first-rank-only historical audit.

Saved ownership is aggregated by `character_alternate_abilities.aa_id`, which
references a **first rank**, not `aa_ability.id`. All saved rows count as a
review gate, including grants or exhausted charges; the tool does not infer
refund amounts. Disabled families are listed separately from enabled candidates.
Unknown ownership, missing first ranks, shared/cyclic rank chains and incomplete
exports abort the audit. Missing next ranks terminate the chain as in the native
loader and are recorded explicitly. Ability ID 0 is a valid native map key.
An abort requires investigation, never a name-pattern fallback.

## Run from the repository root (PowerShell)

Prerequisite: the local akk-stack MariaDB container is running. This command does
not start Docker. Use the configured local read credentials with `mysql` below;
the password is prompted interactively and is not stored in the script/report.

```powershell
New-Item -ItemType Directory -Force artifacts/aa-title-audit | Out-Null
# Use a local mysql client against MariaDB on port 3307. At its prompt:
mysql --host=127.0.0.1 --port=3307 --user=eqemu --password --database=peq --batch --raw --skip-column-names
# For unattended export, use an existing protected --defaults-extra-file and
# redirect the companion SQL via your shell. Never commit credentials.
```

For a reproducible noninteractive export using an existing protected MySQL option
file (PowerShell 7; replace its path with the local configured file):

```powershell
$snapshot = Get-Content tools/aa-client-strings-snapshot.sql -Raw |
    mysql --defaults-extra-file=C:/private/nightcap-read.cnf --host=127.0.0.1 --port=3307 --database=peq --batch --raw --skip-column-names
if ($LASTEXITCODE -ne 0) { throw 'AA snapshot failed; do not use partial output' }
$snapshot | Set-Content artifacts/aa-title-audit/snapshot.tsv -Encoding utf8
python -B tools/audit_aa_client_strings.py --snapshot artifacts/aa-title-audit/snapshot.tsv --dbstr E:/EQ_Local_Dev/Client_RoF2_Dev/everquest_rof2/dbstr_us.txt --output artifacts/aa-title-audit/report.json
if ($LASTEXITCODE -ne 0) { throw 'AA audit failed; review the error' }
```

The companion SQL contains only SELECT statements and transaction control. Its
[MariaDB read-only consistent snapshot](https://mariadb.com/docs/server/reference/sql-statements/transactions/start-transaction)
keeps reads together on transaction-safe tables. A final count summary detects
truncated exports, especially omitted ownership rows. Use this on the existing
InnoDB AA tables; verify storage engines before treating a fresh snapshot as
consistent. The report records input hashes and audit time; record the database
capture time separately if running against an older saved export. The supplied
client file is read only. Output must differ from both inputs.

## Verification in this change

`python -B -m unittest discover -s tools/tests -p test_aa_client_strings.py -v`
passes all 13 tests. Coverage includes later-rank title loss, type-1 matching,
valid titles on placeholder-named/post-RoF families, saved ownership, disabled
families, malformed inputs and rank chains, truncated exports, CLI hashes and
input preservation. Independent review found no actionable issues.

Parsing the actual local client file found 2,470 nonempty type-1 title IDs.
SQL execution against live PEQ is now verified. The report found 192 enabled
missing-title families and 19 affected saved rows, including a system AA;
these are raw coverage findings, not 192 proven visible UI defects. See the live
report for exact ownership and native-chain caveats. No gameplay data changed.

## Next implementation and in-game QA gates

1. Capture fresh PEQ data and this exact client asset; retain input/report hashes.
2. Review enabled affected families against the legal AA pool and every saved
   ownership conflict. Prefer exact title coverage over name/expansion heuristics.
   Keeping desired families requires real client strings through #14; hiding
   unsupported families requires reversible, exact-ID enable-flag changes.
3. Before any write, take the normal PEQ backup and retain each flag preimage.
   Revalidate the catalog and ownership inside the write transaction. Restore
   exact prior flags on rollback; do not enable all families indiscriminately.
4. Promote the eventual fix through feature -> dev -> test. At a controlled
   restart/reload window, ensure all serving zones load the reviewed AA catalog.
5. In PoK on Darth, open General/Archetype/Class AA tabs: no missing-title rows,
   intended valid AAs still visible, wallet/spent/earned counters unchanged.
   Zone, camp and reconnect; repeat. Compare a single-class control and a
   character holding a different second/third class. Verify no owned ability
   disappeared and no points changed without the separately approved handling.
6. Owner sign-off is required before main promotion and closure. A clean audit
   alone does not establish display, gameplay, runtime reload or refund safety.
