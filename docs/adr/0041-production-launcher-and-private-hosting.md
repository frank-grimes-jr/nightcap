# 0041 — Hosted launcher and private game transport

2026-09-20. Candidate; hosted and native-client acceptance remain required.

The owner wants an independent, secured Nightcap login, container hosting for
up to ten friends in US East, IP allow/deny controls, and no separately installed
VPN. Domain and hosting accounts have not been selected or purchased.

Use a production-only compiled launcher policy, separate Ed25519 signing key,
HTTPS assets at immutable release paths, and one signed metadata envelope per
channel fetch. Publish the envelope last. QA remains an offline, separate build.
Compiled trust includes exact inventory, hosts and validity dates. Launcher
upgrades remain explicit downloads when those boundaries change.

The launcher owns a WSS datagram relay for its whole game session. Native RoF2
connects to a fixed loopback address. Login (UDP5998), world (UDP9000), chat/mail
(UDP7778), and a bounded zone range (UDP7000–7030) travel over the relay. The
gateway chooses destinations from a fixed server-owned map, never a client URL.
Native interserver TCP ports and administration endpoints are not relayed.

Cloudflare Tunnel is the only gateway ingress. An isolated Docker network makes
CF-Connecting-IP trustworthy at that origin; the gateway additionally enforces
an explicit allowlist, deny-first rules, concurrent-session and traffic limits.
Cloudflare WAF rules block denied/non-allowed IPs before WebSocket upgrade. WAF
inspection does not cover subsequent WebSocket payloads. No game UDP, DB or web
administration port is published. SSH is restricted at the provider firewall.

Private login accounts are created by the owner, with automatic account creation
and external EQEmu account lookup disabled. Native scrypt (mode14, 16MiB) support must be compiled and verified with
a correct/wrong/empty-hash self-test before serving accounts. The relay does not replace account authentication. Legacy native login
DES is not adequate Internet encryption. TLS terminates at Cloudflare; traffic
is encrypted onward through its tunnel, with plaintext only on the private host.

Reject a separate VPN because the owner rejected it. Reject exposing native
login behind only a web WAF: WAF does not protect UDP. A WSS relay carries UDP over
TCP, so packet loss can increase latency; actual login, zoning, chat, simultaneous
users and impaired-network tests are launch gates, not implied by unit tests.

Implementation order: atomic hosted metadata and release tooling; bounded relay
and launcher lifecycle; production Compose/configuration and onboarding; tests,
independent review, packaging. No production purchase, public upload or live DB
migration is performed by preparing these artifacts.
