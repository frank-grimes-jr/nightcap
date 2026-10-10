# Player access candidate — October 10, 2026

Status: built and reviewed; **not deployed**. Production still uses IP admission.
This candidate removes the need to edit gateway/Cloudflare IP rules whenever a
player's public address changes. It does not make a disconnected TCP session
survive an ISP outage: the remembered credential permits reconnection afterwards.

[Design and threat model](../adr/0059-player-access-independent-of-ip.md) ·
[Operator commands, rollout, rollback and exact player QA](../../deploy/production/PLAYER-ACCESS.md)

## Release receipt

The signed candidate is in the owner's local artifact directory
`E:\EQ_Local_Dev\artifacts\player-access-20261010`:

| Artifact | Verified value |
|---|---|
| Desktop version / signed release | 0.5.0 / 2026101001 |
| Desktop relative path | `launcher-publish/launcher/2026101001/nightcap-desktop.exe` |
| Desktop size | 12,623,360 bytes |
| Desktop SHA-256 | `d63056dbdbca42c5567a284539a596a188b5f5a0fe06842f4c2f3d1f1c75c8ba` |
| Gateway SHA-256 | `3ab5fa9f866896fdea5991d172174e1f4bcaaff24b5abb283ec3443db5e9e177` |
| Signed channel expiry | 2026-11-09T14:23:48Z |
| Compiled Go toolchain | go1.27.2, verified from executable metadata |

`launcher-publish/launcher-channel.json` passed the production release checker
against the existing compiled signing-key policy. The friends directory contains
the stable starter and distribution archive. Signing material remains private and
local. No real player access codes have been issued for this candidate. Do not
share the candidate as a functioning live update before the coordinated rollout.

## Completed verification

- Windows `go test ./...` and `go vet ./...` passed with Go1.27.2. Coverage includes
  native current-user DPAPI round-trip/replacement/tamper/forget, controller state,
  strict token parsing, concurrent-safe snapshots and fail-closed registry reload.
- Actual TLS/WebSocket tests passed for multiple IPv4/IPv6 addresses, missing and
  revoked credentials, live revocation, identity-based connection limits, trusted
  proxy checks and prevention of credentials following redirects.
- Operator/Compose suite: five tests passed. Concurrent issuance, atomic recovery,
  no overwrites, private delivery, file permissions and unpublished ports checked.
- Frontend production build/typecheck and all nine Chrome Playwright tests passed;
  access-entry/saved states were captured and visually inspected.
- `govulncheck` found no vulnerabilities after selecting Go1.27.2. npm audit found
  none after source-map-js1.2.2; 48 registry signatures and 30 attestations verified.
- Separate-model review identified missing HTTP request/response deadlines before
  WebSocket admission. Finite timeouts and a raw TCP slow-body regression fixed
  that finding; the follow-up review reported no remaining coding blockers.
- On OVH, disposable network-none/read-only containers ran the Linux Go tests,
  four operator tests and the built gateway against a loopback UDP echo endpoint.
  Real datagrams passed through the relay from changing reported IPv4/IPv6 source
  addresses. Revocation closed only the targeted credential's sessions, registry
  corruption closed access, and registry restoration recovered without restart.
  The live game, database, gateway and tunnel container identities were unchanged.
- A separate production-style mount check proved UID65532 can read a root-owned
  0750/group65532 directory and 0640 registry, while its read-only mount rejects
  writes. Test directories and containers were removed afterwards.
- Recovery rehearsal used the actual live gateway image and the new scratch image
  in a disposable namespace: old image/config, credential image/config, then old
  image/config again all passed real UDP exchanges and their expected admission
  rules. New-client credentials were compatible with the old gateway during the
  transition. No ports were published, the registry was preserved and all five
  production containers (including web) retained their identities. Disposable
  containers and the rehearsal image were removed.
- The exact live desktop0.4.0/release2026100401 was captured and its signature and
  bytes verified. A local, unpublished corrective release2026101002 wraps those
  original bytes. The actual starter verifier accepted candidate2026101001 after
  the baseline, rejected the old channel after the candidate, and accepted the
  higher corrective release after the candidate. No production channel changed.

Machine-readable rehearsal output is `rehearsal-result.json` in the local artifact
directory; `govulncheck.txt` records the patched Go scan. The sanitized
[recovery receipt](player-access-recovery-20261010.json) records both recovery
checks. The local `recovery-publish` directory contains the corrective bundle;
revalidate counters and expiry before using it, and never publish it during a
successful forward rollout. These checks do not prove
actual public-edge traversal or a real player's login/character/zoning experience.

## Remaining acceptance and release gates

1. Respect the repository `test` to `main` owner sign-off gate. The candidate is
   reviewable; game credentials, database, native game binaries and services have
   not been modified by this implementation.
2. Obtain an authenticated Cloudflare dashboard or a private path to a zone-scoped
   rules API credential; export the affected rules before making scoped changes.
   Fresh native-client requests from OVH's unlisted source still received403 from
   Cloudflare for `/launcher-channel.json` and `/channel.json` on October10.
3. Revalidate live channels/config and retain exact preimages before activation.
   Repeat the isolated gateway/signed-channel recovery checks if the live baseline
   differs from the tested receipt. Cloudflare recovery still requires a fresh
   export of the affected rules once access is available.
   Preserve concurrent player-site/wiki/nginx changes. Publish the launcher and
   replace only the gateway after private code distribution and a relay-disconnect
   announcement. Then adjust only the documented play-host routes at Cloudflare.
4. Prove signed downloads and authenticated WSS/game traffic work from a formerly
   unlisted address; prove missing/wrong/revoked codes fail. Game/database services
   must keep their existing container identities throughout the gateway change.
5. Run the exact Windows/player QA: saved code after reopening, login/character
   entry, East Commonlands movement/chat and zoning, reconnect after a real source
   address change, Change/Forget, and revocation isolation with two test players.

The public route policy is intentionally limited to the documented native-client
download/connect paths. It must not become a blanket Cloudflare WAF Skip rule.
The current 10 connections per player and 20 total remain bounded; further server
capacity tuning requires observed load evidence rather than changing these limits
as part of authentication work.
