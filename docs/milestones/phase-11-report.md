# Phase 11 - Guarded client installation and recovery

September 15, 2026. Built the Windows exclusive executable/process guard and a
signed complete-generation installer/recovery core. Retain immutable backups,
publish pending before mutation, replace from flushed local temporaries, apply
tombstones, verify files, and write the active record last. Pending removal is
the commit point. Errors and restarts restore the full prior asset generation.

Verification: 138 Go cases/subtests pass and vet passes. One symlink test skips
for missing Windows privilege; real junction tests execute. Coverage includes
actual subprocess exits at each install boundary and
mid-recovery; native Windows launch/updater exclusion; locked-file rollback;
real junction rejection; same-release repair and local high-water downgrade
rejection. Independent reviews found no remaining blockers. All automated work
uses disposable fixtures. The owner game remained running and unmodified.

No production install or in-game acceptance is claimed. The core keeps Play
false. Wails integration, configuration semantics, required DLL health, complete
patch preflight, release key/rotation/authorized rollback, Authenticode/self-update,
backup retention, and the remaining client parity matrix are still required.
Sudden power-loss and full Windows metadata preservation are not certified.
[Protocol and limits](../adr/0031-journal-client-generation-recovery.md).
