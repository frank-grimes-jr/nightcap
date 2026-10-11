# Player access activated — October 11, 2026

Production now accepts personal launcher access codes independently of a player's
public IPv4/IPv6 address. The owner explicitly requested codes for owner and Joe,
and reconfirmed “Maintenance is finished—resume and activate.” The two credentials
were issued through the protected owner-local GM API and delivered in private
owner files. No plaintext codes, game passwords or private rule snapshots belong
in this repository.

## Live state and verification

- Signed desktop 0.5.0 / launcher release **2026101001** is published. Its SHA256
  is `d63056dbdbca42c5567a284539a596a188b5f5a0fe06842f4c2f3d1f1c75c8ba`;
  the signed channel SHA256 is
  `dccdedfe30a7c9a16e360176c8c15cb56e5ee5b0df1066c6e923821993a8a289`.
  Ed25519 signature, expiry, executable size and bytes were verified before
  publication; public downloads reproduce the reviewed bytes.
- Gateway image `nightcap-gateway:player-access-20261010`, image ID
  `sha256:2f3b9fc4d88afbb9612f7e1bb1202a31c6e975b1df4a76337cc280ac431ca36d`,
  uses `PLAYER_ACCESS_FILE=/run/nightcap-access/credentials.json` and a read-only
  directory mount. `ALLOW_CIDRS` is removed from its configuration. No host ports
  are published. The existing trusted tunnel-peer checks remain active.
- The existing Cloudflare Block rule remains active, first in order. Only GET/HEAD
  to `/connect`, the two channel files, `/launcher/`, `/release/`, `/guide.html`
  and `/nightcap-friends.zip` on play.nightcapgame.org bypass its player-IP check.
  Other hosts, methods and paths retain the previous policy. No WAF Skip rule or
  global protection disable was added. Exact before/after rule snapshots and the
  saved dashboard screenshot are retained privately in the task artifacts.
- Both actual credentials passed WebSocket upgrade and received the native EQ
  login-service UDP SessionResponse using synthetic IPv4 and IPv6 client headers
  through the trusted tunnel namespace. Missing and wrong codes returned401.
- Public TLS WebSocket/UDP checks passed for both credentials from OVH, whose
  source address is absent from the old allowlist. Actual public test transport
  was IPv4; this is not a claim of a real external IPv6 login test. Both invalid
  credential cases returned401 through Cloudflare.
- With the actual Go client User-Agent, both public signed channels, the full
  desktop download, a signed game asset, starter and guide passed. The Python
  default User-Agent encountered Cloudflare1010, so native-download verification
  explicitly matched the existing Go client. Cloudflare protection was retained.
  Unlisted-source GET `/`, GET `/private/player-access/credentials.json` and
  POST `/connect` remained403.
- GM reports game/gateway running, credential gateway active, maintenance off,
  setup ready and production writes enabled. Game and database are healthy.

The owner briefly started GM maintenance during preparation. After explicit
confirmation, the existing guarded Resume operation restarted the stopped game
and gateway and waited for game health. A fresh baseline was then captured.
The access deployment recreated **only gateway** at13:53:18UTC; game, database,
web and tunnel IDs/start times remained unchanged from that resumed baseline.
The current game channel, nginx, player-site, wiki, starter and guide were retained.
Game release2026101001 (stock icons) remains byte-identical, channel SHA256
`4432fa74642d2ae9856a22e80fd1a0d257cd19325b2a4d4ae741bcacf11ef9ed`.

## Recovery and evidence

Private OVH backup: `/opt/nightcap/deploy/production/private/access-rollout-20261011`.
It holds fresh Compose/environment/nginx/public-file baselines, frozen signed
candidate, container identities, `activated.json` and `verified.json`.
Local task artifacts: `artifacts/player-access-activation-20261011`; code delivery
and exact Cloudflare rollback expressions remain in the owner's private GM state.
Independent script review passed after fixes for frozen channel publication,
partial-write recovery, symlink inventory, edge-network selection and readiness.
The rollout shared the GM lock and rejected an active maintenance marker.

If recovery is needed, restore the captured old gateway configuration and scoped
Cloudflare rule, recreate only gateway and verify health. Preserve the registry
and player data. Never roll the signed launcher counter backward: the privately
prepared corrective release2026101002 contains the old desktop bytes. Recheck
live counters and expiry before publishing any correction. Original isolated
gateway and signed-channel recovery rehearsal remains in the
[candidate evidence](../releases/player-access-20261010.md).

## Player flow and outstanding acceptance

Close EQ and the launcher, reopen the normal Nightcap shortcut to update, then
Player access → enter personal code → Save → Play. The code is remembered for
that Windows user. Send Joe only his private code; game passwords are separate.
Future issuance/revocation is available in the owner-local GM tool's Player access
section; nothing is emailed automatically.

Joe's actual Windows/game acceptance remains open: from a changed address, update
without403, save his code, log in, enter East Commonlands, move/chat and zone;
camp/close/reopen and confirm the code is remembered; repeat from another network
without an administrator IP edit. A network outage can still interrupt an active
session. Full steps, including separately rehearsed revocation/Forget behavior,
are in [player QA](../../deploy/production/PLAYER-ACCESS.md#exact-player-qa).
