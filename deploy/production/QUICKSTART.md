# Nightcap: OVH + Cloudflare setup

Provider choice confirmed by the owner on 2026-09-20. OVH and the Cloudflare tunnel
are now active for owner testing at `play.nightcapgame.org`; see
[deployment evidence](../../docs/releases/ovh-activation-20260920.md).
This is the short owner guide; [README.md](README.md) contains the
technical deployment steps and [QA.md](QA.md) the acceptance checklist.

## 1. Order one OVH VPS — owner

At [OVHcloud US](https://us.ovhcloud.com/vps/), select the regular VPS-2:
4 vCPU, 8 GB RAM, 75 GB SSD, Vint Hill, Virginia if available, Ubuntu 24.04 LTS,
and SSH-key login. Use the regular region for this deployment, not a Local Zone.
The advertised price starts at $8.50/month; confirm commitment, renewal price,
taxes and availability at checkout. MariaDB runs on this VPS with the game.
A managed database, Windows license, control panel and load balancer are unnecessary.
Enable MFA on the account. Keep the initial credentials private.

The VPS is a subscription: shutting it down does not reduce the subscription bill.
For scheduled downtime, we can stop the game containers while keeping the small
web/tunnel services available for launcher downloads and the player guide.

## 2. Choose a domain and activate Cloudflare Free — owner

Register your chosen domain with Cloudflare Registrar or another registrar.
If registered elsewhere, [add it to Cloudflare](https://developers.cloudflare.com/fundamentals/manage-domains/add-site/)
and replace its nameservers with those Cloudflare assigns. Choose the Free website
plan, enable MFA, and wait for the domain to show Active. Reserve
`play.<your-domain>` for the launcher, guide and secure game connection.
Let the tunnel create this hostname's DNS record during deployment.

## 3. Provide setup details — owner

Once the VPS and domain are ready, provide the domain, VPS public IP, SSH username,
and the local path to the SSH key or an already configured SSH host alias.
Keep private key contents, passwords and API/tunnel tokens out of chat.
The remaining secrets are created and stored through local files or provider dashboards.
We will collect approved player IPs and account names during onboarding.

## 4. Install the prepared stack — deployment work

Use the owner hosting kit and detailed README to install Docker Compose, create
private configurations and deploy MariaDB, game, gateway, web and cloudflared.
Import a verified database backup into this new server, install the matching
runtime data, and create private login accounts. Restrict SSH to the owner's IP;
keep native game, database and admin ports closed to the Internet on IPv4 and IPv6.
The current local QA server stays available while the new host is verified.

## 5. Connect Cloudflare and backups — deployment work

In Cloudflare, open Networking > Tunnels and create `nightcap-production`.
Run its connector in the prepared Compose stack, storing its token in the private
secret file. Configure these published routes in order:

| Hostname | Path | Origin service |
|---|---|---|
| `play.<your-domain>` | `/connect` | `http://gateway:8080` |
| `play.<your-domain>` | All other paths | `http://web:8080` |

Use Block rules for denied IPs and all IPs outside the approved list; mirror the
list in the gateway. Keep interactive browser challenges off launcher routes.
[Cloudflare tunnel setup](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel/)

Enable R2 and create a private Standard bucket for encrypted database/configuration
backups. Scope its credentials to that bucket and test a restore. The prepared
kit serves signed patches from the VPS through the tunnel; R2 is for backups in
this first deployment. Cloudflare Free needs no upgrade for this design; R2 has
[separate usage-based pricing](https://developers.cloudflare.com/r2/pricing/).

## 6. Build the production launcher and test — deployment work + owner

Generate a separate production signing key, build the launcher for the real
hostname, and publish the signed patch release. Test your own Windows login,
zoning, chat and gameplay, then one friend, then up to ten. Verify denied-IP
blocking, disconnect recovery and backup restoration using QA.md before sharing.
The hosting ZIP is for the owner; it is not the player download.

## 7. Give friends the player ZIP — owner

Share the final `nightcap-friends.zip`, guide URL and each friend's private account.
Friends extract the ZIP, open the launcher, choose their own supported RoF2 folder,
select Check for updates, Install update, then Play. The launcher stays open.
No separate VPN app or manual slash commands are required by the candidate design.
This flow still needs the hosted/native acceptance in step 6.

## Routine updates — next implementation phase

The intended flow is approved main release -> GitHub Actions builds/deploys the
server and publishes signed client patches -> player launcher updates before Play.
GitHub Actions deployment, automatic patch-before-Play and launcher EXE self-update
are not implemented yet. The current patcher fetches published signed releases,
not GitHub source. Until automation is installed, use the README release procedure.
Keep manual gameplay QA and main-promotion approval in the release process.

Current owner steps: reset the existing private admin password, run the hosted
client QA in step6, and finish encrypted R2 backup configuration/restore testing
from step5. Friend distribution remains gated on acceptance.
