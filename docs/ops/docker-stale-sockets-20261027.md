# Local Docker recovery for the Palwar/Vox experiment

October 27, 2026. Docker Desktop's Linux engine was unavailable. Its current
backend log identified inaccessible AF_UNIX reparse-point sockets (Windows error
1920), including `Docker/run/sailor-ingest.sock`; the earlier failure involved
`docker-secrets-engine/engine.sock`.

After the graceful stop stalled, only the failed local Docker Desktop/backend
processes were stopped. Inspection confirmed normal parent directories containing
runtime sockets. The exact parents were renamed in PowerShell, then recreated:

- `C:/Users/verre/AppData/Local/Docker/run` was retained as
  `run.palwar-vox-20261027-preserved` in the same Docker directory.
- `C:/Users/verre/AppData/Local/docker-secrets-engine` was retained as
  `docker-secrets-engine.palwar-vox-20261027-preserved` in Local.

Docker Desktop was restarted hidden. `docker info` returned server version
29.7.2 and the existing akk-stack containers and retained native build trees were
available. No factory reset, image/volume cleanup, data-disk deletion, account
change or production operation occurred. The preserved socket directories remain.
This supersedes the local Docker blocker recorded earlier in the Paladin task;
it does not establish that the candidate gameplay/client release has been built
or deployed.

The isolated experiment uses `/tmp/nightcap-balance-palwar-vox-20261027` and a new
local database `nightcap_palwar_vox_20261027`. The native executable is linked
separately from retained October26 paired objects and never replaces `bin/zone`.
Only synthetic character ID1 is reset; no account or character profile rows were
copied. Private source snapshots and credentials remain outside repository/wiki
artifacts. See the [combat evidence](../items/paladin-weapon-grip/balance/vox-test/README.md).

Before any future repair, inspect fresh logs and exact directory contents again.
These paths are evidence of this recovery, not permission to remove arbitrary
Docker folders or bypass filesystem restrictions.
