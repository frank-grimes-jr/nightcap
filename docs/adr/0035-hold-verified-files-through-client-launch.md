# ADR 0035: Hold verified files through client launch

Date: 2026-09-15. Status: implemented preparation boundary; bootstrap integration pending.

## Problem

A successful read-only inspection closes its files. An update can then replace
assets before the bootstrap loads them. The installer guard solves update
exclusion by requesting an exclusive writable executable handle, which also
prevents Windows from executing that image.

## Decision

`installer.PrepareLaunch` owns a `launchlock.Set` with a read-only executable
handle shared for reading only. It pins every directory from the drive root to
the selected client and every managed-file parent. Directory handles deny write
and delete sharing; leaf handles reject reparse points. Only ordinary local drive
paths are accepted. Windows can load the image while updater writes, replacement,
ancestor renames and writes through hard-link aliases remain blocked.

The preparation reads the active checkpoint through a retained handle, verifies
its canonical encoding, signature, release floor and expiration, and hashes every
signed inventory entry through retained handles. Entries marked optional still
belong to the complete installed generation. Required config/catalog and proxy
must be present; the exact supported executable and all recorded patch sites pass
compiled preflight. Pending recovery and retired files prevent preparation.
Cancellation and all failures release every acquired handle.

The returned single-owner `LaunchLease` must survive until the owned game exits,
or transfer equivalent locks before release. It supplies read-only executable
and proxy handles and signed generation/config identity. It creates no process
and grants no runtime approval. Preparation now derives checked PE entry/export metadata through these same
handles, using the bounded conventional PE32 profile recorded in
[phase 17](../milestones/phase-17-report.md). The next bootstrap integration must
establish private nonce/health IPC and retain process/job ownership before any
Play action is possible.

## Limits

This protects the launcher/updater protocol and the verified existing files.
Absent files cannot be locked: arbitrary same-user creation of a retired DLL or
pending journal after preparation remains outside the guarantee. Drive remapping
and a privileged local owner are also outside the trust boundary. User settings
and health/log output remain writable. UNC paths and junction-based installations
must be moved to a supported ordinary local path.

## Evidence

[Phase 16](../milestones/phase-16-report.md) records actual Windows file-sharing,
process execution, failure cleanup and signed-generation checks. API semantics:
[Microsoft CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).
