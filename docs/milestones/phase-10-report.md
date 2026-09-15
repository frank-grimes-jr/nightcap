# Phase 10 - Signed asset inspection and complete staging

September 15, 2026. Added launcher size/SHA256 diff and full candidate staging.
Metadata is verified before filesystem access. Current files are copied and
rehashed; changed/missing files download through bounded HTTPS with per-redirect
trust checks. Preserve signed metadata and write completion marker last.

Read-only client access rejects nonregular paths and links; rooted operations
confine path resolution. Staging rejects physical client descendants including
Windows junction aliases. Download failures discard the candidate; cleanup
failures are reported and leave an unmarked orphan. Crashes may leave staging
artifacts; future installer discovery must validate all content independently.

Verification: 100 Go cases/subtests pass and vet passes; independent review
found no remaining blockers after boundary/cleanup fixes. Tests include real Windows
junctions and partial-generation failures. Symlink creation on this Windows
host lacks privilege, so that test is skipped; junction cases execute. The full
product remains unaccepted. Transactional activation/recovery, process/Play gate,
Wails shell, production signing/rotation/rollback/self-update and client parity
remain required. No installed client asset or server state changed.
