# Production launcher candidate — September 20, 2026

Implementation and owner deployment kit are prepared. No domain, host, Cloudflare
account, production signing seed or final public Windows release has been created.
The previous EC hub live-QA deployment remains unchanged.

- [Owner setup and cost comparison](../../deploy/production/README.md)
- [Mandatory hosted/native QA](../../deploy/production/QA.md)
- [Friend instructions](../../deploy/production/FRIENDS.txt)
- [Architecture and transport tradeoffs](../adr/0041-production-launcher-and-private-hosting.md)
- Owner artifact directory: `E:/EQ_Local_Dev/artifacts/production-launcher-20260920`.
  This is an owner kit, not the friend download. It includes separately built Linux
  gateway/native candidates and their checksums; runtime data and DB remain private.

## Verification

Go tests passed for manifest canonicalization, hosted policy generation, installation,
launch/session handling, endpoint restore/conflicts, relay TLS/socket lifecycle,
source/destination validation and cross-session isolation. `go vet ./...` and
`go mod verify` passed. Desktop-tag compilation and affected final tests are recorded
with the artifact verification output. The optional Windows race-detector build
was unavailable: the installed Strawberry GCC runtime lacks WaitOnAddress /
WakeByAddress imports required by Go1.27. No race-detector pass is claimed. Frontend production build and all eight
Playwright tests passed; npm audit reported zero vulnerabilities.

Four Linux production tests passed, including a failed dump that must never produce
a restic snapshot. The real SQL fixture on pinned MariaDB10.11.19 passed create,
duplicate rejection, reset, missing-account reset, registered world and repeat-world
no-op checks (one account/admin/world row each). That fixture has no network or host
ports and no live-data mounts. Compose parsing confirmed five services, no published
ports and internal database/game/edge networks.

The isolated native build compiled loginserver, world, zone, UCS and shared_memory.
The native mode14 scrypt self-test accepted its correct password and rejected wrong
password/empty hash. The final source patch also removes client-list session keys and
authentication-capable packet dumps. Linux runtime dependencies python3, MariaDB CLI
and libsodium.so.23 were checked in the matching build environment. Both owner-kit
Docker images built successfully; the game Dockerfile ran the native crypto self-test.
Explicit COPY executable modes make extraction from a Windows-created ZIP safe.
The temporary network-isolated SQL fixture and its anonymous volume were removed.

Local image IDs:
- game: `sha256:17528ec1f4e1309a3e19adc05265b42e8cd95ba5c32e9e88a61c3d67bf5a86e9`
- gateway: `sha256:af7525d0bce521bc9415e4fe43069c4ba0d41430788b03f942e0096113db11a8`

## Remaining acceptance

The complete runtime image has not booted against a restored production-sized DB.
Hosted TLS/WAF/tunnel settings, expiry renewal, final signed download, fresh Windows
onboarding, RoF2 login/zoning/chat, ten simultaneous players, impaired-network behavior,
off-host backup restoration and rollback remain unverified. Unit/fixture success does
not substitute for these checks. Windows Authenticode signing and automatic launcher
EXE updates are not included. Build the hostname-bound friend ZIP after the owner
selects a domain, then complete the QA matrix before sharing it.
