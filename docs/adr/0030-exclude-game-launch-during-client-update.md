# ADR 0030: Hold the executable open exclusively during client updates

Date: 2026-09-15; amended 2026-09-27. Status: implemented and tested on Windows.

A process snapshot alone permits eqgame.exe to start between the check and an
asset replacement. The updater must also exclude another updater for that client.

Acquire an OPEN_EXISTING handle to the selected client executable with
GENERIC_READ | GENERIC_WRITE and no sharing. Windows rejects this writable handle
while that exact image is running, including through a hard-link alias. This handle prevents concurrent
launches and updates. It is never used for writes and consumers receive only a
read/seek/stat view for exact executable preflight. Pin the client root and compare
file identity before/after opening; reject final-component reparse/nonregular files.
The guard requires write access to the executable even though it changes no bytes.

Verification uses disposable copies of the Go test executable: a second updater
is rejected, launch fails during the guard, and running the target image through
its ordinary path or a renamed hard-link alias blocks the writable handle. A
separate installation running an executable with the same name remains usable
and does not block this client update.
The real development game client was not copied over, modified or launched.

Sources: [CreateFile sharing semantics](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
and [Toolhelp process enumeration](https://learn.microsoft.com/en-us/windows/win32/toolhelp/taking-a-snapshot-and-viewing-processes).

The September 27 amendment removes the earlier global process-name snapshot.
It incorrectly blocked Nightcap when the independent EverQuest Legends client
was running. Exact-file locking remains mandatory for the entire transaction;
no process is stopped and no signature, preflight or recovery check is bypassed.
