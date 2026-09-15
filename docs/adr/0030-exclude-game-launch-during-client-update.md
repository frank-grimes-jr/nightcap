# ADR 0030: Hold the executable open exclusively during client updates

Date: 2026-09-15. Status: implemented and tested on Windows; no client deployment.

A process snapshot alone permits eqgame.exe to start between the check and an
asset replacement. The updater must also exclude another updater for that client.

Use Toolhelp process enumeration, failing closed on snapshot errors. Reject a
running eqgame.exe, then acquire an OPEN_EXISTING executable handle with
GENERIC_READ | GENERIC_WRITE and no sharing. This handle prevents concurrent
launches and updates. It is never used for writes and consumers receive only a
read/seek/stat view for exact executable preflight. Pin the client root and compare
file identity before/after opening; reject final-component reparse/nonregular files.
The guard requires write access to the executable even though it changes no bytes.

Verification uses a disposable copy of the Go test executable: second updater
rejected, process found, launch fails during the guard, and a running image blocks
the writable handle even when its process name is deliberately not matched.
The real development game client was not copied over, modified or launched.

Sources: [CreateFile sharing semantics](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
and [Toolhelp process enumeration](https://learn.microsoft.com/en-us/windows/win32/toolhelp/taking-a-snapshot-and-viewing-processes).
