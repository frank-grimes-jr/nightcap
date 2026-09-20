# OVH owner-test activation — September 20, 2026

The hosted candidate is running at `play.nightcapgame.org`. This is owner testing,
not completed native acceptance or approval to invite friends. Gameplay has not
been promoted to main and the local QA stack was not changed or stopped.

## Deployment

- OVH Ubuntu 24.04 LTS, amd64, approximately 8 GB RAM / 72 GiB root filesystem.
- Installation: `/opt/nightcap/deploy/production`; Docker Engine 29.8.1,
  Compose 5.5.1. Database, game, gateway, web and tunnel are running.
- MariaDB 10.11.19 and native game health checks pass. Twelve zone workers connect
  to world. Private Nightcap world registration authenticates successfully.
- Cloudflare tunnel `nightcap-production` has four registered QUIC connections.
  `/connect` routes to `http://gateway:8080`; the remaining hostname routes to
  `http://web:8080`, with the final 404 catch-all retained.
- SSH requires keys, root/password login is disabled, and UFW accepts SSH only
  from the current owner's IPv4. A fresh SSH connection verified access before
  cancelling the timed bootstrap rollback. No container publishes host ports.
- Cloudflare blocks unapproved IPs: owner HTTPS request 200, OVH source request
  403. The gateway independently allows only the owner address at this stage.
  Update both controls when adding friends or changing networks.
- Idle observed usage: game about 1.02 GiB, DB 352 MiB, gateway 6.5 MiB, tunnel
  16.4 MiB, web 4.8 MiB. This is not a ten-player load measurement.

The original kit ZIP remains immutable. Its Compose file required a correction:
quote comma-containing tmpfs strings; otherwise YAML split `mode=1777` into a
second invalid mount. Commit `8200cac` fixes this and tests the resolved Compose
mount/network contract. Both that check and all four production configuration,
password and backup-failure tests pass on the actual host. Independent review
found no additional definite Compose/startup blocker.

## Database and account identity

Source dump SHA256:
`27c6538122ef6403e53cc05851255d450129ee4707c17112848b4c7c739bd472`.
The complete dump includes routines/triggers and passed gzip validation. The
application DB user could not export a procedure; that failed dump was rejected
and the existing administrator credential was used inside the local container.

The empty OVH database was restored with 243 tables, 20 characters, 308928 items,
40725 spells and one stored procedure; DB version 9328. Classic expansion0,
AA minimum1 and the unlimited native per-IP setting remain present. The gateway
still limits real clients independently, since native processes see its address.

Native account lookup uses `(ls_id, lsaccount_id)`. Three restored world accounts
were in namespace `eqemu`, while their exact matching private login records use
`local`. After independent source review, stop game/gateway and back up the new DB,
then migrate only these verified world/login IDs: `2/2`, `12/3`, `13/4`.
Preconditions require exact source names/IDs, no target name/ID collision under
native collation, and transactional InnoDB tables. Forward/rollback rehearsal
changed exactly three rows each, then rolled back without identity changes.
Committed forward changes only `account.ls_id` to `local`. Account14, privileges,
password hashes, all character IDs and account ownership remain unchanged.

Pre-migration host backup SHA256:
`553c842ff9ce80a12dbe701596694358b68de542dbcc85491b7c778a6bc35677`.
The existing `admin` account owns 17 characters; reset its password interactively
with `accounts.py reset admin` before owner login. Do not create another account
to recover these characters. Other restored accounts need their own reviewed
private login onboarding. The unused LocalDev registration is disconnected.

## Client release and hosted verification

Production launcher **0.2.0**, release **2026092003**:

- Guide: `https://play.nightcapgame.org/guide.html`
- Download: `https://play.nightcapgame.org/nightcap-friends.zip`
- ZIP SHA256: `19fad8ad403237991777f1bc359f1a6ebe14c523953ab26b180c719e15acc4bc`
- Channel SHA256: `696e3fd0ad1741fb131e855b4971158541adbdb7f844ff8b0cb3d55d22d4b6ec`
- Manifest expiry: **2026-10-20 18:01:26 UTC**; publish a higher renewal before expiry.
- Production key ID: `production-4acb02e67aeb0b51`, trust expires 2028-09-20.
  The seed stays in an owner-only local directory and was never uploaded.

The signed immutable files were verified on the VPS before installing channel.json
last. Public HTTPS verification accepted the production signature and all 20 file
sizes/hashes, plus the launcher ZIP hash. Channel responses have identity encoding
and `Cache-Control: no-store`. Production-tag Go tests, Vue/TypeScript build and
Windows Wails build pass; npm audit reports zero vulnerabilities.

Real WSS connections through Cloudflare exchanged native EQ session-request/
session-response datagrams with login5998, world9000, UCS7778 and zone7000. These
prove encrypted relay routing and native transport responses, not authenticated
RoF2 login, rendering, gameplay or chat delivery.

Local public evidence/artifacts:
`E:/EQ_Local_Dev/artifacts/production-nightcapgame-20260920`.
Private source snapshot and signing seed:
`E:/EQ_Local_Dev/artifacts/ovh-private-20260920` (owner-only Windows ACL).
A proposed bootstrap configuration export to that folder was blocked by automatic
approval review because it contains database credentials and the tunnel token.
No configuration export was performed. Explicit owner approval is pending; this
would not replace the pending encrypted R2 backup service.
Runtime archive SHA256:
`a0ce0ef6bdfb72c076f81bb7c9c86f807768be07d98ca8daa758fa6be0639a63`.
Opcode symlinks were exported as actual files so the host needs no source checkout.
The native kit's original upstream commit is unavailable; preserve its recorded
binary hashes and BUILD.json rather than claiming a reconstructed source revision.

## Remaining gates and recovery

- Owner password setup, real RoF2 login/character selection, hub, zoning, chat,
  pet/gameplay QA, disconnect recovery and multi-player load remain unverified.
- R2 credentials, encrypted scheduled off-host backups and their restore test
  remain unconfigured. Restic is installed; the backup timer is not enabled.
- GitHub Actions deployment, automatic patch-before-Play, launcher self-update
  and scheduled downtime remain future implementation. Current client updates
  require Check for updates / Install update; they fetch signed hosted files.
- Use [QA.md](../../deploy/production/QA.md) before friend distribution.

To close access, stop `gateway`; to stop gameplay, stop `gateway game`, retaining
web/tunnel for downloads. Do not use `down -v`. The local QA environment is still
available. Database restoration must target an isolated environment first; the
pre-migration backup needs the same reviewed namespace conversion before local
login. To undo only that conversion, stop game/gateway and restore `ls_id='eqemu'`
only for the three verified accounts, with the same identity guards. That is a
rollback state and will not authenticate through the current local namespace.
For client data rollback, publish corrected contents under a higher release ID.
