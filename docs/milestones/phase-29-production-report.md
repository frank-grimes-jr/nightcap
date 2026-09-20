# Phase 29 — Production launcher and private hosting candidate

2026-09-20. Owner requested a low-cost independent server for ten friends in US East,
with container infrastructure, secured private login, IP allow/deny and no separate VPN.

Built: production-only hosted trust generation, one-object signed release metadata,
immutable artifact layout, launcher-owned WSS transport, bounded native UDP relay,
transactional temporary login endpoint, private container network design, account
provisioning, native credential-log redaction/crypto test, backup failure handling,
Windows friend packaging and owner/player instructions.

Verification: Go component and desktop tests, relay TLS/socket isolation/disconnect
checks, Linux configuration/backup/hash tests, real isolated MariaDB10.11.19 account
creation/duplicate/reset/world-registration checks, native Linux compilation/crypto
self-test, frontend build/eight browser cases, npm audit (zero reported advisories),
Go module verification and Compose no-published-port assertions. Exact evidence and
remaining gates: [production release record](../releases/production-launcher-20260920.md).

Not shipped: a hostname-bound Windows production EXE or public service. Domain/cloud
accounts, final trust key, full DB/runtime migration and actual hosted RoF2 login,
zoning, chat and ten-player load tests remain open. WSS uses TCP underneath and may
increase latency under packet loss. Cloudflare inspects the HTTP upgrade, not the
subsequent game stream. The owner must complete the listed acceptance cases before
friend distribution. The existing live QA stack and original client remain unchanged.

Operational learning: real SQL fixtures exposed same-table LOCK/PREPARE aliasing;
backup producer success must precede restic snapshot creation; the native CLI mode13
hashing path disagrees with its mode14 default, so production uses tested mode14;
secret-bearing packet logs need review beyond ordinary Info-level messages.
