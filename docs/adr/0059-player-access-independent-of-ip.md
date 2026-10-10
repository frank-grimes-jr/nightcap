# 0059: Player access independent of IP addresses

Date: 2026-10-10. Status: implementation candidate; not deployed.

## Intent and evidence

Frontier changes a friend's public IPv4 address and IPv6 privacy addresses. Both
Cloudflare's IP rule and the gateway's `ALLOW_CIDRS` can then reject his launcher.
Fresh production inspection confirms the gateway has no credential configuration.
The signed starter downloads the desktop before its UI opens, so requiring a new
credential on every download would also prevent first-time enrollment.

## Decision

Issue a separate, cryptographically random access code for each approved player
or device. The player enters it once in the launcher. Windows DPAPI protects the
saved code for the current Windows user; it never enters settings, activity logs,
URLs, release manifests or shared binaries. The launcher sends it only as a Bearer
authorization header to the compiled, HTTPS-validated relay endpoint. Redirects
must never carry credentials to another endpoint.

The gateway verifies a SHA-256 digest of a token containing a 256-bit random secret, indexed by a
random public credential ID. Credential records identify a player for connection
limits. Authorization does not depend on the player's IP. Retain trusted tunnel
peer validation, mandatory valid `CF-Connecting-IP`, optional explicit deny rules,
fixed game destinations, bounded packets/flows and total resource limits. Remove
the allowlist path entirely; missing or invalid credential state fails closed.

An operator-only tool issues, lists and revokes credentials under a file lock,
with atomic registry replacement. The gateway rereads the bounded registry for
new sessions and periodically for active sessions; revocation closes existing
sessions within five seconds without a gateway or game restart. Registry contents
are hashes and opaque player labels; raw codes are written only to an explicitly
selected private delivery file, never printed in operational logs.

Public signed update metadata and immutable launcher/game patch assets need no
player credential. Review the hosted inventory before removing the Cloudflare IP
rule for these exact routes. Other hosts and private services retain their current
policy. `/connect` becomes publicly reachable through Cloudflare but requires the
gateway credential before WebSocket upgrade; origin ports remain unpublished.
Do not broadly skip Cloudflare protections. Ensure this native route is not
subject to browser challenges, which a launcher cannot complete.

## Alternatives

Cloudflare Access browser identity offers centralized account/MFA lifecycle, but
adds browser session renewal and native launcher integration. Service tokens use
headers and are suited to machine access; they still require secret provisioning
and lifecycle management. A VPN introduces separate installation and support.
Broader ISP CIDRs or automatic public-IP updates retain an unreliable admission
boundary and do not meet the goal. Existing game passwords are unsuitable as the
sole Internet-facing admission secret, especially where an owner chooses a simple
password. Do not change game credentials as part of this work.

## Threat boundaries and proof

- Remote unauthenticated callers: invalid/missing/revoked codes cannot upgrade,
  including from an old allowed IP. Forged proxy headers cannot bypass admission.
- Credential theft: TLS, user-scoped DPAPI, no token logs/query parameters, strict
  parsing, fixed destination, individual revocation. A player can intentionally
  share a code; this is a bearer credential, not a hardware attestation scheme.
- Resource abuse: bounded registry/header/body sizes, constant-time hash comparison,
  per-player/global active connection limits and existing packet quotas.
- Administrative corruption: malformed/missing/duplicate registry fails closed;
  atomic updates, file locking, safe permissions and backups protect its lifecycle.
- Dynamic address regression: the same credential upgrades from multiple IPv4 and
  IPv6 source values; sessions share a per-player limit across addresses.
- Client UX: save/reopen/change/forget access code; no secret in status or logs;
  distinguish missing/rejected access, Cloudflare denial and transient network failure.
- End-to-end release: signed starter reaches the new desktop from a formerly
  unlisted network; authorized relay passes a game UDP exchange; revoked relay
  closes; in-game login/character load and reconnect after network change pass.

An IP change that breaks TCP can still interrupt a running RoF2 session. The
acceptance criterion is reconnection with the remembered credential, without
editing IP rules, not transparent migration of an existing game TCP/WebSocket.

## Implementation and rollout plan

1. Add `internal/playeraccess` token/registry verification and operator tooling;
   prove misuse cases and atomic issue/revoke behavior.
2. Replace gateway allow admission with credential verification; prove real WSS
   handshakes, address independence, quotas and live revocation.
3. Add Windows credential storage and launcher access UI; verify native round-trip,
   controller behavior and rendered UI. Preserve signed update trust contracts.
4. Update Compose, deploy guide, tests, changelog and current-status references.
   Audit dependencies and separately review correctness, security and scope.
5. Build a signed candidate, rehearse deployment/rollback with isolated endpoints,
   and provide exact manual QA. Respect the repository's test-to-main approval gate.
6. Publish approved launcher and gateway together, then replace scoped Cloudflare
   IP restrictions. Verify from unlisted networks and with the actual player.
   Do not declare success while an IP-based Cloudflare gate still blocks downloads
   or `/connect`.

Rollback must preserve the credential registry and player state. Restore previous
gateway/config and scoped Cloudflare rules only as a coordinated fallback; this
temporarily restores the original dynamic-IP limitation. Launcher rollback uses
a higher signed release counter, never an older channel. Gateway replacement
briefly disconnects relays; announce it. Do not restart the native game/database.

## Primary references

- [Cloudflare service-token headers and lifecycle](https://developers.cloudflare.com/cloudflare-one/access-controls/service-credentials/service-tokens/)
- [Cloudflare WebSocket behavior](https://developers.cloudflare.com/network/websockets/)
- [Microsoft user-scoped CryptProtectData](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata)

## Evidence status

Implementation, Windows/Go/UI/operator tests, separate-model review, isolated
Linux relay rehearsal and signed Windows candidate packaging are complete.
Publication, the scoped Cloudflare change and actual player acceptance remain
pending. [Candidate evidence](../releases/player-access-20261010.md) distinguishes
the completed checks from production acceptance; this is not deployment evidence.
