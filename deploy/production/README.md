# Nightcap private hosting candidate

Prepared 2026-09-20 for ten simultaneous friends in US East. The owner-test stack
is now deployed at `play.nightcapgame.org`; see
[activation evidence](../../docs/releases/ovh-activation-20260920.md).
Use [QA.md](QA.md) before friend distribution. Real client acceptance and encrypted
off-host backups remain open. Hosting does not approve gameplay promotion.

Start with the [short OVH + Cloudflare setup guide](QUICKSTART.md). The owner has
selected these providers; the guide also documents the remaining backup/QA steps.

## Lowest-cost practical starting point

Start with **one regular OVHcloud US VPS-2 in Vint Hill, Virginia**, Ubuntu Linux,
4 vCPU / 8 GB RAM / 75 GB disk, subject to checkout availability. Its advertised
price is **from $8.50/month**, and the linked offer selects `upfront12`; treat that
as a commitment price, not a verified month-to-month quote. Confirm the actual
term, taxes and total before ordering. A domain costs extra. Choose the regular regional VPS for this deployment. Earlier notes described
Docker as unsupported in Local Zones; the current page no longer establishes that
restriction, so it is not the basis for this choice.

This is a suitable low-cost candidate among the verified offers, not a claim
that no cheaper offer exists. The 4 GB entry tier saves money but leaves less
room for MariaDB, ten players spread across zones, backups and the OS. The
8 GB sizing still needs the load test below. Build binaries locally, not on the
small VPS. Upgrade if measured memory or zone tick performance requires it.

Use Cloudflare Free for DNS/TLS, five WAF custom rules and the WebSocket endpoint;
a named Cloudflare Tunnel needs no inbound server ports. Use a **private** R2
Standard bucket for encrypted restic backups: 10 GB-month is included, then
$0.015/GB-month plus applicable operation charges. Domain pricing depends on the
chosen name/TLD. Expect the VPS + domain to dominate a small friends server's
bill; confirm checkout rather than treating a budget as a quote.

Sources checked 2026-09-20:

- [OVHcloud VPS pricing, resources and Local Zone restrictions](https://us.ovhcloud.com/vps/)
- [US VPS regions include Vint Hill](https://support.us.ovhcloud.com/hc/en-us/articles/38299056076947-Upgrading-your-VPS-configuration)
- [Hetzner's June 2026 price changes](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/) — older price comparisons are stale.
- [Cloudflare custom rules](https://developers.cloudflare.com/waf/custom-rules/)
- [Cloudflare WebSockets and WAF scope](https://developers.cloudflare.com/network/websockets/)
- [R2 storage and operation pricing](https://developers.cloudflare.com/r2/pricing/)

## Network and account boundaries

```
RoF2 -> launcher loopback -> WSS/TLS443 -> Cloudflare WAF -> named Tunnel
  -> private gateway -> private native login/world/zones/UCS -> private MariaDB
```

Cloudflare terminates TLS and carries the origin leg through its encrypted tunnel.
The web WAF inspects the upgrade request, not subsequent game datagrams. The
gateway supplies fixed destinations, bounded frames/flows/traffic and deny-first
IP checks. It does not prove an executable's identity: an approved IP can reach
the login protocol, which still requires a private account. No account signup
website or public EQEmu login fallback is enabled. Never set `LSPX`, even to `0`.

Only cloudflared joins the outbound network. No Compose service publishes a
port. Trust only `10.88.1.2/32` as the proxy; never broaden this to the dev Docker
bridge. The private gateway carries UDP5998/9000/7778/7000–7030 only. Native TCP
interserver, DB, admin APIs and SSH are not relayed. Keep provider ingress denied
except SSH22 from the owner's IP; use SSH keys, disable password/root SSH login.
Use the provider console if your admin IP changes. Do not blindly replace SSH
firewall rules until a second authorized SSH session succeeds.

All native services see the gateway's IP. Retain mail-key verification, but check
`World:MaxClientsPerIP`, related exceptions and bans so ten invited accounts can
connect. Enforce each friend's real IP at Cloudflare and the gateway. The existing
native zone authentication checks a pending character name, not a distinct real
player IP; this design does not claim to rewrite that legacy behavior.

## Prepare an isolated runtime

1. Create provider and Cloudflare accounts with MFA, select a domain, and confirm
   the actual VPS order total. Do not order managed Kubernetes, a load balancer,
   managed database, premium WAF or a Windows host for this initial deployment.
2. Install Docker Engine/Compose on the VPS using the official Docker instructions.
   Put this kit under `/opt/nightcap/deploy/production`. Copy `.env.example` to
   `.env` and replace each image placeholder with a reviewed version/digest.
   The native runtime must match the build environment; the locally verified
   base is `eqemulator/eqemu-server@sha256:b6f46ebc00f8da8f103197cf2252be8173317b85fbc42716c994ad33d5da39f7`.
   The recipe pins MariaDB10.11.19. The local development image is10.5.4;
   import its logical dump into the new10.11 database and test the complete restore.
   Do not copy its raw data volume. [10.5 is no longer maintained](https://mariadb.org/about/).
3. In an isolated native source checkout with the accepted `server-mods/code`
   overlay, apply `native-hardening.patch` (`git apply --check` then `git apply`).
   Normalize the patch and candidate source files to LF if transferring from
   Windows. Enable `EQEMU_BUILD_LOGIN=ON`, build `loginserver world zone ucs
   shared_memory`, and run `loginserver --nightcap-crypto-self-test`. The native
   patch removes logged authentication keys/passwords and requires a usable
   scrypt implementation in this self-test. Never skip the test or use the
   unpatched dev login binary. Archive hashes and the exact source revision.
4. Copy those Linux binaries into a **build-only** `native-bin/` next to
   `Dockerfile.game`; build with `--build-arg EQEMU_RUNTIME_IMAGE=<digest>`.
   Build `Dockerfile.gateway` with the `eq-launcher` directory as context and a
   reviewed Go1.27 image digest as `GO_IMAGE`. Save/load both Docker images over
   SSH. No private registry subscription is required. Record final image IDs.
   The owner kit also includes verified Linux binaries: run `sha256sum -c SHA256SUMS.txt`
   before using them. Its gateway can be built without Go using
   `docker build -f Dockerfile.gateway.binary -t nightcap-gateway:<release> .`.
   The game recipe uses the included native-bin directory. Both image recipes were
   built locally; complete runtime startup and hosted acceptance still remain.
5. Create `data/server/` containing the accepted server's quests, plugins, maps,
   opcode/patch files, Lua/Perl dependencies and other runtime data. Include the
   full required server data, not just `server-mods/`. Exclude old credentials,
   logs, caches, development tools and old binaries; the image supplies binaries.
   Never substitute the EverQuest client directory for server data.
6. Run `python3 configure.py --base /secure/staging/eqemu_config.json` on Linux.
   It exclusively creates `private/` with new secrets and private-only settings.
   Set `chown -R 1000:1000 data/server`; set owner1000 on `private/eqemu_config.json`
   and `private/login.json` (each0600). Other private files remain root-owned0600.
   Keep `private/` itself traversable to UID1000 using an appropriate owning group
   and0750, or make UID1000 its owner with0700. Never make it world-readable.
7. Start only MariaDB: `docker compose up -d db`. Import a verified backup into
   this **new isolated** database using `docker compose exec -T db mariadb
   --defaults-extra-file=/run/secrets/db_backup_config peq < /secure/peq.sql`.
   This overwrites only the newly provisioned DB; take a backup before any later
   restore. Verify the accepted schema and migration state before game startup;
   automatic schema updates are disabled. Keep the dev/QA server untouched.
8. Login schema must exist. If absent, review the native login schema and create
   its tables in the isolated database; the upstream file contains DROP statements
   and must not be blindly applied to a populated database. Provision the world's
   private registration once with `docker compose run --rm --no-deps --entrypoint python3 game
   /opt/nightcap/accounts.py world`. For each friend use `... accounts.py create
   <username>`; passwords are prompted privately, never passed on the command
   line. Existing accounts use `reset`. Run one provisioning operation at a time.
   Share credentials privately yourself; they do not belong in the friend ZIP.
9. Start `game` and inspect its health and credential-free logs before starting
   `gateway`. Native crypto/config checks run on every start. Health proves
   listeners, not successful login. Complete the native acceptance matrix.

## Cloudflare and IP rules

Create a named remotely managed Tunnel. Save its token as `private/tunnel_token`
(owned by UID65532, mode0600); mount it as a Docker secret, never put it in `.env`, source or a
command line. Configure one real hostname, for example `play.<your-domain>`:

- First route: path `/connect`, service `http://gateway:8080`.
- Second route: same hostname, all other paths, service `http://web:8080`.
- No public routes for DB, admin tools or native game ports.

On that hostname, create **Block** rules for explicitly denied IPs, then for IPs
not in the approved friend list. Mirror those CIDRs in `.env` `ALLOW_CIDRS` and
`DENY_CIDRS`. Use literal IP sets or the account's supported custom list; never use
a bypass/Skip action as an allowlist. Avoid browser/JavaScript challenges on
`/connect`, `/channel.json` and `/release/*`; the launcher is not a web browser.
Add an upgrade rate limit appropriate for reconnects (start with10/minute/IP).
Do not cache `/channel.json`, and disable response compression for channel and
release paths: the launcher requests and requires identity encoding.

Update both allowlists when friends change networks. Restart/recreate `gateway`
to immediately apply revocation to existing sockets; WAF edits alone affect new
upgrades and may not terminate an established game connection. The small server
currently disconnects all relay sessions on a gateway restart; announce it first.

## Build and publish the launcher

1. Copy `profile.example.json` to a private release workspace. Set all three URLs
   to the chosen HTTPS hostname and choose the signing-key validity dates. The
   example hostname intentionally fails validation. Use version 0.2.1 or later
   for the 22-file inventory including Classic Lavastorm. Existing 0.2.0 users
   need the replacement launcher EXE; updating source does not update their EXE.
2. Create a **new production** Ed25519 seed outside source and upload directories,
   with owner-only ACLs (Windows0600 alone is not an ACL). Do not reuse the QA seed.
   Back it up offline. The key never goes on the VPS. From `eq-launcher`, run:

   ```powershell
   go run ./cmd/nightcap-package -production-profile C:/secure/profile.json `
     -client C:/source-client/eqgame.exe -assets C:/accepted-gameplay-assets `
     -key C:/secure/production.seed -new-key -release 2026092003 `
     -publish C:/releases/nightcap-2026092003
   ./build-production.ps1 -Profile C:/secure/profile.json `
     -Destination C:/releases/friends-2026092003
   ```

   Use real absolute paths, accepted native helper/proxy build inputs and a new,
   strictly increasing release number. The selected client is read-only input.
   Subsequent releases omit `-new-key`; archive the previous generated policy and
   use a fresh publish directory. Never mix QA and production build tags.
3. Upload only the generated `release/<id>/` tree, `channel.json`, the final
   friend ZIP and `guide.html` to staging under `data/public/`. Keep private seeds,
   DB dumps, account lists, configs, full client installations and build sources
   out. Review the distribution rights for any original game archives included
   in a release before sharing; friends obtain their own complete client.
4. Upload assets to their final immutable release paths first; never overwrite
   an existing release. Verify their sizes/hashes on the host. Atomically rename
   the new `channel.json` into place **last**, on the same filesystem. It carries
   the exact signed bytes and signature together, preventing a mixed-generation
   metadata fetch. Verify the public identity-encoded response from an allowed IP.
5. Share only `nightcap-friends.zip` and the guide link after QA passes. No Windows
   Authenticode certificate is included: content signing does not remove Windows
   unknown-publisher/reputation prompts. Never tell friends to disable antivirus.

Signed manifests expire after30days, including cached offline launch eligibility.
Publish a higher-numbered renewal at least weekly and alert when fewer than7days
remain. Compiled signing trust has its own fixed expiry. Changing that window,
signing keys, hosts, managed file inventory, patch catalog boundaries or launcher
code requires a new launcher download. This release does not self-update the EXE.
Do not silently move key expiry during routine manifest renewals.

## Backups, recovery and rollback

Use an independent private R2 Standard bucket and scoped credentials. Install
restic on the host, initialize its encrypted repository, and keep a second copy
of the restic password outside the VPS. Create root-owned0600
`/etc/nightcap-backup.env` with `RESTIC_REPOSITORY=s3:https://<account>.r2.cloudflarestorage.com/<bucket>`,
`RESTIC_PASSWORD_FILE`, `AWS_ACCESS_KEY_ID`, and `AWS_SECRET_ACCESS_KEY`. Never use
the public release directory/bucket for backups. Install the included service
and timer, make `backup.sh` executable, and enable `nightcap-backup.timer`.

The backup retains14daily/4weekly database snapshots plus configuration backups.
Monitor timer failures and backup age; test a full restore into another isolated
DB before invitations. Provider snapshots alone are not a verified database
restore strategy. During a restore, stop game writers, restore the verified dump,
restore matching runtime/config/quests, regenerate shared memory, then reopen
access only after health and account checks. Never restore over live players.

For a bad launcher data release, publish corrected/previous file contents under
a **higher** release number: anti-rollback intentionally rejects older metadata.
For a bad server image, stop game/gateway and select the saved previous image and
matching runtime snapshot. Schema changes need their own reviewed rollback;
switching an image alone is insufficient. Keep the tunnel closed while verifying.

Watch free disk, memory, zone CPU/tick behavior, container restarts, denied upgrade
counts, manifest expiry and backup age. Do not log packet payloads, passwords,
session keys or authorization headers. First invite the owner, then one friend,
then the remaining group after QA; record findings in [QA.md](QA.md).
