# Docker Desktop stale socket recovery — October 17

The local Linux engine was unavailable during the combined release build.
`com.docker.backend.exe.log` showed access failures for stale Windows AF_UNIX
runtime sockets. Docker data remained at `E:/Docker/wsl/disk/docker_data.vhdx`.

With the engine absent, stopped only Docker Desktop/backend, then renamed the
runtime `run` and `docker-secrets-engine` directories under
`C:/Users/verre/AppData/Local/Docker` to dated retained backups. Inspection showed
runtime sockets, not application credentials. Recreated both directories and
started Desktop hidden. The Linux engine and existing akk-stack containers
recovered; retained build trees and database data were intact. No factory reset,
data-disk deletion, source reset or protected client change was performed.

Inspect logs and directory contents before repeating this narrowly scoped repair;
do not treat arbitrary Docker folders as disposable. Keep the retained socket
directories until recovery is accepted. Evidence of recovery is the successful
full zone build recorded in `docs/releases/october-17-2026/`.
