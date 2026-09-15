# PoK hub verification

2026-09-13; candidate code and content only, not deployed.

`hub-database-tests.json` records 14 passing controls against newly created
MariaDB schema `nightcap_pok_qa_f19ab2efd09d`, including complete content
forward/rollback equality, occupied-ID and drift rejection, a late write
failure, legacy restock equivalence, class routing despite globally widened
spell classes, lower-cap filtering, invalid cap/era rejection, merchant identity
checks, and a late restock SQL exception. Targeted rows return to the exact
captured preimage. The legacy comparison uses a controlled spell catalog;
it does not claim a full PEQ clone or in-game coverage.

The final restock failure control injects a server SQL SIGNAL immediately after
the real INSERT SELECT; it verifies the actual rollback handler and prior stock.
An earlier attempt to add a second test CHECK constraint hit MariaDB error 1025,
errno 194 while renaming the disposable table. That attempt did not pass and its
schema `nightcap_pok_qa_515a50b2a70e` is retained for inspection. The final control
avoids that test-only ALTER. No production table schema changed. Initial schema
`nightcap_pok_qa_436a02dc48a8` exposed the coordinate-format mismatch; the corrected
seven-case migration run passed in `nightcap_pok_qa_154e9f2c57e1` before restock
controls were added. Disposable schemas are not used by the game or AA harness.

Other checks:

- Four Python planner/migration tests cover all current stock, original class
  routing, source restrictions, prices, identities, and duplicate spawn checks.
- PowerShell era checks exercise valid/legacy paths, six invalid preflights,
  and missing guard/restock inputs under a Continue caller. Required files load
  before any era writes; errors stop later writes and restarts. Earlier successful
  era operations are not transactionally undone if a later operation fails.
- Existing Lua tests cover all 16 primary classes and status/login commands;
  16 Perl assertions cover the Chronicler dialogue. Seven additional Perl
  assertions exercise the actual class plugin with a database stub to verify
  updated player directions, retained camp guidance, and duplicate rejection.

Independent read-only review found and verified fixes for native six-decimal
spawn coordinate serialization, non-indexed drift predicates, malformed cap
parsing, and PowerShell missing-file failures. Read-only EXPLAIN confirms primary
key lookups for the corrected row guards. Full original merchant restriction
columns and NPC pricing/appearance fields are retained. Terrain, client Find,
merchant windows, and native class mutation remain the in-game QA boundary.

Reproduction from the worktree:

```powershell
# Run Python unit discovery from tools/.
python -B -m unittest discover -s tests -p 'test_pok_hub*.py' -v

# Run these from the worktree root.
python -B tools/tests/run_pok_hub_database.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/tests/test-pok-hub-era.ps1
```

The database runner creates a new `nightcap_pok_qa_<random>` schema through the
existing container administrator credential, never targets PEQ, and never
restarts a server. It leaves the schema for inspection. Quest tests run through
the server container's Lua and `/opt/eqemu-perl/bin/perl` in an isolated /tmp
directory. Hashes in the database report pin the tested generated SQL and data.
