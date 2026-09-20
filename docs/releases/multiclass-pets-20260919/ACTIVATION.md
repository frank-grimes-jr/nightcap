# Three-pet QA activation

Verified 2026-09-20T02:02:17.533201+00:00 (September 19 local time). The development server
is running the pet QA candidate. Source is promoted through dev/test; main
remains at b620beb pending owner in-game sign-off.

- Zero players were online at the maintenance guard and final verification.
- All eight previous zone workers exited after SIGTERM and saved normally.
  No forced zone termination was needed. The normal Spire CLI stopped the
  remaining services and restarted the candidate.
- A fresh full PEQ backup was decompressed and verified: **441,567,211
  bytes**, compressed to 46,395,555 bytes. SHA256:
  `72d68e29104ca53dddb40c721e108a836135f517e58f3e473ba5244d698b4347`.
- All 17 changed source/build overlays matched their committed preimages and
  the candidate build source before installation. Their final installed hashes
  match the deployment manifest.
- The running world and all eight zone executable hashes match the candidate.
  World is unchanged from the previous compatible build; zone is the new build.
- Required rules remain AAExpMinLevel=1, CurrentExpansion=0 and
  StateSavingOnShutdown=true. The pet armor table remains 18 columns.
- PoK spawn/NPC/merchant afterimages are unchanged, including 1,747 merchant
  listings and 1,229 unique items. No hub SQL, starting-zone migration or schema
  mutation was run for this release.
- 14 fresh process logs were inspected; zero Error/Fatal lines.

[Machine-readable verification](activation.json) · [Exact owner QA](QA.md).
The first verification attempt ran before zones had registered and correctly
stopped at its eight-zone guard. The completed check above used all eight zones.

## Artifacts and recovery

Local activation evidence is under
`E:\EQ_Local_Dev\artifacts\multiclass-pets-20260919\activation`:
`file-manifest.json`, `binary-manifest.json`, `stopped.json`, `backup.json`,
`peq-before.sql.gz`, `installed.json` and `live-verification.json`.
The old binary pair and changed source preimages are retained there. The
pet-specific `ops.py` has no hub or schema mutation mode; do not substitute the
older gameplay activation script, which also applied unrelated hub SQL.

Before rollback, stop/save gracefully and take a fresh backup. Compare current
pet state with the pre-activation snapshot: older binaries delete extended class
keys when saving. If players have used the candidate, retain and reconcile their
new pet states with a compatible recovery build before rolling back. Do not
overwrite newer character progress with the old full database, and never drop
or clear `character_pet_armor` while it owns items. Restore only the documented
binary/source preimages after checking current deployment hashes.

Native correctness and server activation passed. In-game rendering, zoning,
death, full item interaction and three-pet encounter balance remain owner QA.
No main promotion or tunnel relocation is implied by this activation.
