# September 30 court deployment operations

These are archived inputs to this specific content release. The source package
pins main commit `453e61bf150fcabc75ef34ef8ada199c2f15fd15`; its manifest preserves
the current advanced-loot native image and all existing quest/plugin files.

- `rollout.py`: checked preflight, stopped-target capture, private full backup,
  isolated restore, 19 SQL checks, exact apply/rollback and content installation.
- `test_rollout.py`: 21 isolated orchestration fault tests; no production calls.
- `package.py`, `package.json`, `package-manifest.json`: exact source and package
  provenance; these files contain no player rows, credentials or backup contents.
- `verify_open.py`: verification-only continuation after the original helper's
  `docker cp` failed against the read-only container root filesystem. It writes
  the public Perl fixture through `docker exec` into the writable tmpfs instead.
  It checks installed files, scoped content, maps/zone gates, preservation,
  market rotation, native health and 26 quest assertions before opening access.
  It does not repeat SQL or installation. An already-completed invocation fails
  harmlessly; cleanup is armed only when this invocation attempts to open access.

The original `apply` invocation installed content and started the game but kept
access closed on the verification-copy failure. The pinned helper remains intact
for provenance. The supplemental verifier's SHA256 is
`f652706530b554799e30e5f38f3fc6c46bef984fec98aab0e6aa26761d68c7fa`.
The public Perl test was made mode 0644 on the host; no private data permissions
were relaxed. Production results are recorded in [PRODUCTION](../PRODUCTION.md).

Full backup and preimages remain private on OVH. Do not restore that database
over later play. Recovery uses the original helper's guarded `rollback` under
`/opt/nightcap/deploy/production/.deployment.lock`; it keeps the receipt-aware
image, takes current preservation fingerprints and removes only unambiguous
affected NPC caches. Other-instance/corpse references or static drift stop it.
