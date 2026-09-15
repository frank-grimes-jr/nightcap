# Five server fixes — automated gates passed, in-game QA pending

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../../status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


The candidate corrects held-class weapon damage, extra-pet ownership and attack
commands, direct-AA buff duration, and stale owned-AA profile entries. It makes
no numerical balance change and installs no expansion AA policy or ownership
ledger. See `QA.md` for the exact in-game steps and activation boundary.

## Build and verification

- All 2,787 pinned source files matched before and after a clean build.
- Fresh `zone` and `tests` targets built successfully. All 87 C++ tests passed in
  a separate test directory with its own shared-memory files.
- A separate diagnostic executable links the freshly built native objects, using
  the existing isolation adapters. Its 24 fixed-input Vox/Nagafen fights match
  all previous complete reports and raw hashes: three builds, zero and launch
  maximum AAs, both dragons, and two recorded gear sets at seed 1729.
- The three release tests validate the five source/rollback hashes, regenerated
  patch, source manifest correspondence, and all 24 complete replay reports.
- All 316 calculator and release-evidence tests pass on `dev` at revision
  `8decea37ea8a41ccfd3eb42f3ea3180cc0826715`; see `dev-python-tests.log`.
- The balance clone has zero account, character, owned-AA and inventory rows;
  its AA-table dump hash is unchanged. Only two verified reagent rows were removed.

This proves a reproducible mechanics candidate and matched simulation behavior.
It does not prove final game balance or replace the required in-game QA.

## Candidate artifact

The executable is stored outside Git at
`E:\EQ_Local_Dev\artifacts\server-fixes-20260913\zone` (78,904,056 bytes).
Its SHA256 is
`ce127436f846e2ef0d588501bc5797f13f8928cce72ea45ef9e6eb8562dbcaac`.
The copied artifact matches the successfully built ELF. The active server binary
has not been replaced.

The complete 2,787-file source archive is stored beside it as `full-source.tar.gz`,
SHA256 `ed2442a0807c7cfa61b782aeb21626765aae4731e1f77622984c4829d5611c06`.
Every archived file was checked against the source manifest after copying to E:.
`promotion-checks.json` records artifact sizes/hashes and the tested revision.

`configure-command.json`, `full-source-manifest.json`, `build.log`,
`build-checks.json`, and `cpp-tests.log` record the build. The diagnostic manifest
pins the linked objects and adapters. `replay-command.py` records the exact replay
procedure. The two fresh input/report pairs and `fresh-replay-checks.json` retain
the comparisons. Original source files are archived in `original-source.tar.gz`;
apply the source patch only after checking the recorded original hashes.

The first build was interrupted by a full C: drive and left a zero-byte zone
artifact despite a success line in its log. It was rejected. This candidate comes
from the subsequent clean build after Docker storage was moved to E:.

The first `dev` suite caught a raw source hash mismatch: the prepared `mob.cpp`
used CRLF while Git already required LF. Rebuilt that file from exact committed
bytes; its object and the complete zone binary remained byte-identical. The final
source manifests use the committed LF hash, and `line-ending-rebuild.json` retains
both source hashes and the object/binary equality proof. No assertion was relaxed.

The active binary is backed up at
`E:\EQ_Local_Dev\artifacts\server-fixes-20260913\zone.before`, SHA256
`b7b2a022e3a7f78528639aaf90dba620e561cc8d4047912d211034b7c9517540`.

## Review and remaining work

The final patch review checked native eligibility gates, unchanged primary-pet
command behavior, explicit extra-pet registration, native AA duration lookup and
profile initialization. No new database schema, global class-mask mutation,
credentials or network access is introduced. The AA duration check scans loaded
ranks only when applying an otherwise eligible self buff; it avoids a stale cache
after AA reload. This is an author review, not owner gameplay approval.

Balance remains open: the pet build's Nagafen resistance/sustain gap is not
consistently resolved by shielding or cap changes. Keep 250/250 as the measured
baseline. The proposed expansion AA pools still need a complete release offering,
earned-versus-active ownership integration and lifecycle QA before deployment.
Activated-AA subspells and the Celestial Regeneration level rejection remain
separate issues. `test` to `main` requires the owner's in-game sign-off.
