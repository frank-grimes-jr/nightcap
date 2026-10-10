# Phase 61: Player access independent of changing IPs

Date: 2026-10-10. Status: candidate, not deployed.

Built: individual revocable credentials, Windows user-scoped encrypted storage,
launcher access UI, identity-based gateway limits, fail-closed live registry
reload, private operator tooling and scoped migration/rollback instructions.
Full Go/static checks, native DPAPI tests, nine browser tests, operator/Compose
tests, dependency audits and isolated Linux relay rehearsal passed. Independent
review's HTTP slow-body finding was fixed and rechecked. Desktop0.5.0 / signed
release2026101001 is built and verified against the existing starter trust policy.
Isolated old/new/old gateway recovery and an unpublished higher signed corrective
desktop release passed against the exact live baseline; production was untouched.

Cut: broad ISP allow ranges, automatic address registration, a separate VPN,
browser/email sign-in, changed game passwords and changes to native gameplay.

Shaky/open: owner main/production sign-off, Cloudflare access and scoped policy
change and its recovery export, coordinated activation, real public-edge verification
and Windows in-game acceptance after an actual network/address change. The live
Cloudflare download routes still return403 from an unlisted source. No production
access policy or game services were changed; this is not a resolution claim.

[Candidate evidence](../releases/player-access-20261010.md) and
[exact rollout/rollback/player QA](../../deploy/production/PLAYER-ACCESS.md).
