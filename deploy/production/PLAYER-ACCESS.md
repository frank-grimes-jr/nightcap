# Player access without IP allowlists

Candidate dated 2026-10-10. **Not deployed.** Production still uses IP admission
until the coordinated migration below is approved and verified.
[Design and threat model](../../docs/adr/0059-player-access-independent-of-ip.md).

Players receive a personal access code, enter it once in the launcher and keep
using the same shortcut. Their Windows account protects the saved code with
DPAPI. Their private game username/password remains separate. Changing public
IPv4/IPv6 addresses does not require an administrator. A network drop can still
end a running game session; use Play to reconnect when connectivity returns.

## Operator commands

Run on the OVH host using Python 3, with an operator-owned registry parent. These
commands modify only the credential registry, not MariaDB or game accounts.

```bash
cd /opt/nightcap/deploy/production
sudo python3 player_access.py --registry private/player-access/credentials.json init
sudo python3 player_access.py --registry private/player-access/credentials.json issue joe --out /root/joe-access.txt
sudo python3 player_access.py --registry private/player-access/credentials.json list
sudo python3 player_access.py --registry private/player-access/credentials.json revoke <credential-id-from-list>
```

`init` refuses an existing registry. Issue creates a new 256-bit secret and a
random public credential ID. Deliver the private output file to the intended
player through an approved private channel; never publish it or paste it in
logs/PRs. The tool prints only ID, player label, creation time and delivery path.
The gateway stores a hash, not the secret. Delivery files cannot be inside the
mounted registry directory, and existing delivery files are never overwritten.

Use one code per player/device. Multiple codes with the same player label share
the per-player concurrent-session limit. A lost code cannot be recovered from its
hash: issue a replacement and revoke the old ID. Revocation affects existing and
new relays within five seconds, without restarting a service. Forget in the
launcher removes only the local saved copy; server revocation remains separate.

The directory is root-owned, group65532, mode0750; registry is0640. The gateway
mounts the directory read-only, not a single file, so atomic replacements are
visible. Operator backups in `.backups/` are0700/0600. The gateway fails closed
if the file is absent, corrupt or unreadable. Restore a reviewed registry backup
only after considering which revoked codes that backup would re-enable.

Issue/revoke are serialized with an OS file lock and use atomic registry rename.
After an uncertain write/fsync error, inspect the public credential ID in the
registry and retain the private delivery file; do not blindly repeat an issue
or delete the only copy of a newly valid secret.

## Cloudflare routes

The tunnel routing stays `/connect` -> `http://gateway:8080`, with web downloads
served by `http://web:8080`. No host game, gateway or database ports are published.
Gateway still validates its trusted tunnel peer and `CF-Connecting-IP`; the player
address is no longer an allow condition. Emergency `DENY_CIDRS` can still block a
known abusive source, but is not the player lifecycle mechanism.

After auditing the live public inventory and activating the credential gateway,
remove IP allowlisting on **play.nightcapgame.org only** for these necessary paths:

- `/connect`: credential required before WebSocket upgrade.
- `/launcher-channel.json`, `/launcher/`: signed desktop update and binary.
- `/channel.json`, `/release/`: signed game metadata and patch assets.
- `/nightcap-friends.zip`, `/guide.html`: starter and onboarding guide.

Only known signed desktop/game artifacts belong under those prefixes. This is an
intentional public-download policy so the starter can reach the code-entry screen.
Never expose private server files, registry/delivery files or full base game files.
Preserve SSH, unrelated hostnames (including wiki) and other existing rules. Do
not use a blanket WAF Skip rule. Browser/JavaScript challenges must not be applied
to these native-client routes. Retain applicable Cloudflare DDoS controls and
bounded upgrade rate limiting; rate limits must permit ordinary reconnects.

Cloudflare changes require a connected authenticated dashboard or a scoped API
token supplied through a private file. Do not use a tunnel connector token as an
account API token. Export the exact affected rules and capture their IDs before
editing them; re-read them after applying the scoped change.

## Coordinated rollout and rollback

1. Complete independent review, tests, dependency audits, isolated Linux relay
   rehearsal and a Windows build. The release must use the patched Go1.27.2 or
   later toolchain. Respect the repository test-to-main approval gate.
2. Read fresh live channels and image/config hashes. Back up Compose, relevant
   `.env` values, public channel bytes and the affected Cloudflare rules. Preserve
   concurrent wiki/player-site/nginx changes; do not overwrite nginx wholesale.
3. Initialize a private registry, issue owner/friend codes and privately distribute
   them before requiring credentials. Verify UID65532 can read the mounted
   registry while the container cannot write it; check no delivery files are in it.
4. Build and sign a higher launcher release using the existing trusted public-key
   policy and a new desktop version. Upload immutable desktop bytes first. Verify
   hashes/signature and publish the new launcher channel atomically. The old
   gateway permits the new client's extra header during this transition. Do not
   raise game-release counters or alter gameplay files for an access-only update.
5. Announce the brief relay disconnect. Install only the reviewed gateway image,
   registry directory mount and `PLAYER_ACCESS_FILE`, remove `ALLOW_CIDRS`, and
   recreate **gateway only** with Compose `up -d --no-deps --force-recreate
   --pull never --no-build gateway`. Keep game, database, web and tunnel unchanged.
6. Prove missing/wrong codes fail and approved codes work through the trusted
   tunnel route. Then apply the scoped Cloudflare change. Verify downloads and
   an authenticated WSS/UDP round trip from an address absent from old allowlists.
7. Complete the player QA below and check container identity/health afterwards.
   Publication alone does not establish successful in-game acceptance.

Rollback: preserve the new registry and all game/player data. Restore the prior
gateway image/environment/mount definition and the captured scoped Cloudflare
rule if necessary, then recreate only gateway. This temporarily restores the
dynamic-IP limitation. An older desktop must be re-signed under a **higher**
launcher release counter; never roll the visible signed channel backwards. Do
not delete saved DPAPI credentials, reset game accounts or restart native zones.

## Exact player QA

1. On Joe's Windows account, launch the stable shortcut from an address absent
   from both old allowlists. The new desktop must download and open without403.
2. Enter the private access code once, select the existing client folder and
   press Play. Log in with his existing game account, select/create a character
   and enter East Commonlands. Confirm chat and movement work.
3. Camp and close both game and launcher. Reopen the same shortcut; the code is
   remembered and no code entry or admin IP edit is needed.
4. After a real IPv4/IPv6 address change (or a different Internet connection),
   repeat login, character entry and zoning. Record new source address family
   without exposing the credential. A forced network drop may end the previous
   session; reconnecting must work with the saved code.
5. With disposable test credentials, revoke one player's ID while two players
   are connected. Only that credential's sessions close within five seconds;
   that player's reconnect fails and the other player keeps playing.
6. Test Change and Forget in the launcher; the field is empty after saving and
   never displays the saved code. Forgotten credentials disable Play until a
   code is entered. Updates remain available before entering a code.

## Evidence

Windows Go suite/static checks, native DPAPI tests, credential lifecycle tests,
Compose isolation tests and nine Chrome UI tests passed during implementation.
The dependency audit required source-map-js1.2.2 and Go1.27.2; the patched Go scan
reports no vulnerabilities. Separate-model review identified an HTTP body timeout
gap; finite request/response deadlines and a raw-socket regression fixed it.
The isolated Linux rehearsal also passed on OVH: real UDP exchanges through the
built gateway survived simulated source-address changes, revoked sessions closed,
another player remained connected, and registry corruption/recovery failed
closed without a process restart. Disposable containers had no external network
access; production container identities were unchanged. A separate UID65532
mount check proved the production registry permissions permit reads while the
read-only mount prevents writes.

Signed desktop candidate 0.5.0 / release2026101001 has been built and its channel
verified against the starter's compiled trust policy. It has **not** been
published. Live Cloudflare still returned403 for both update channels from an
unlisted address on October10. Publication, scoped Cloudflare migration and
actual player acceptance remain open. See the
[candidate evidence](../../docs/releases/player-access-20261010.md).
