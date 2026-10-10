# Production GM controls — October 10, 2026

Status: owner-approved production GM activation; player gateway switch pending. This
extends the [player-access release](../releases/player-access-20261010.md).

## Activation receipt — October 10, 2026

The owner explicitly approved merge and production activation. PR #143 merged at
20:29 UTC as `d261daee8f78f39905865d15aaf5c4fc2c4be1d9`. The owner-local server now
has production writes enabled. Explicit setup completed after backup
`private/gm-backups/20261010T203049.039495Z.sql.gz` (43,898,704 bytes, mode0600,
gzip contents verified). Both support tables are ready. No real account password,
character, gameplay rule or content was changed.

The reviewed `player_access.py` is installed and the empty private registry is
initialized. The credential gateway image is staged as
`sha256:2f3b9fc4d88afbb9612f7e1bb1202a31c6e975b1df4a76337cc280ac431ca36d`;
UID65532 read access and read-only mount enforcement pass. Private rollback copies
of Compose, environment, nginx and public channels are under
`private/access-rollout-20261010`. The gateway and public launcher channel remain
unchanged so players are not locked out before credentials are delivered.

Cloudflare requires owner sign-in or a privately supplied scoped API token.
Automatic approval review separately rejected issuing owner/Joe credentials without
explicit recipient authorization; that authorization was requested and no codes
were issued. These are outstanding access-rollout steps, not GM write restrictions.

Use `eq-solo-gm/Start Nightcap GM Production.cmd` to reopen the approved app with
production writes, including after a reboot. The ordinary shortcut starts a
read-only preview if no server is running. Both reuse an already-running app
without changing its mode; this was verified with its process ID unchanged.
Write mode comes from the protected local session response, so reopening does not
depend on production SSH/database health. An HTTP regression covers both modes
while the remote dependencies fail. All five production container identities and
start times, gateway/environment/nginx files and public channels were rechecked
unchanged after GM setup. The activation receipt is recorded in
[production-gm-activation-20261010.json](../releases/production-gm-activation-20261010.json).

## Owner entry point and flow

Double-click `eq-solo-gm/Start Nightcap GM.cmd`. It builds the UI, starts a hidden
loopback-only Node server and opens Accounts with OVH production selected. The
owner can switch to Local development explicitly. No server console is needed
for ordinary GM operations. Node24 and the owner's saved OVH OpenSSH identity are
required; existing SSH-agent recovery is documented in AGENTS.md.

The preview is at `http://127.0.0.1:3001/accounts?target=production` on this computer.
It cannot be reached from a friend's computer. Do not expose port3001 or5173.

Available GM flow (gateway-dependent player steps require its remaining rollout):

1. **Player access:** enter a player label, Generate code, copy the one-time code
   and send it privately. It is not emailed automatically. The player uses
   launcher → Player access → Save → Play. Revoke closes the credential's relay
   sessions. Game passwords remain separate. Names become lowercase IDs, with
   spaces converted to hyphens.
2. **Accounts:** find the exact login account, Reset password, enter its new
   password and confirm the named account/environment. The backend verifies
   mode14, writes a libsodium scrypt hash and verifies the stored result. It does
   not print or retain plaintext. External login providers are excluded.
3. **Characters:** Start maintenance, confirm that all players will disconnect,
   make level/platinum/AA/skill/teleport changes, then Resume game. Rule, MOTD,
   canonical merchant restock and account deletion also require maintenance.
   Progression tracking and password/access-code actions do not need downtime.
4. **Recovery:** failed or unanswered writes retain a nonsecret action ID across
   reload. Inspect the receipt and affected data before unlocking. Other GM tabs
   cannot overwrite this pending action. Partial runtime startup retains Resume
   and Complete shutdown actions. Never close maintenance by killing a zone.

First-time GM setup is an explicit UI action creating only `gm_operations` and
`gm_progression_kills`; opening the UI performs no DDL. Game account deletion
rejects ownership of any character, including soft-deleted characters.

## Existing feature corrections and boundaries

- Levels respect the active era cap; changing level resets that level's XP.
- Platinum and AA grants are bounded, transactional and recorded exactly once
  per request ID. Receipts are scoped to the explicit environment.
- Teleport uses `zone.zoneidnumber`, version0, and clears the saved instance.
- Max skills uses held multiclass eligibility, preserves existing higher values
  and leaves specializations/tradeskills alone because they have additional gates.
- Progression is GM tracking, not a claim to award native quest flags or loot.
  Expansion-wide batches commit together.
- Rules use the active named ruleset and typed supported names. Zone-specific
  override rulesets remain separate. Presets commit together, failing if a required
  rule is absent. Values are explicit legacy presets, not balance recommendations.
- Merchant restock executes `scripts/vendor_restock.sql`, including its catalog,
  identity, capacity, InnoDB and transaction guards. The retired no-op is gone.
- Era previews and downloadable proposals retain the repository's policy:
  commit era.json, review catalog changes, use the apply-era release workflow.
  The GM UI cannot directly activate another era or silently de-level everyone.
- Client model settings affect the owner's `C:\Nightcap\eqclient.ini` by default;
  `NIGHTCAP_CLIENT_INI` can select another owner copy. Resolved paths inside
  `Client_RoF2_Dev` are rejected, including through directory junctions.

## Security, backups and recovery

API Host/Origin/fetch-metadata checks and an in-memory per-process session protect
the loopback API. The built UI uses a restrictive CSP. Browser storage contains
only pending action ID, environment and start time, never passwords, session
tokens or access codes. Mutations use a shared Web Lock across tabs.

Production database streams go through pinned-host SSH; no public DB port or local
forwarding listener is added. Fixed SSH operations cannot take a browser-selected
host, command or path. The operator remains the trusted machine/SSH owner; this
is not a multi-user public administration service.

Before destructive SQL, the helper backs up affected tables under
`/opt/nightcap/deploy/production/private/gm-backups` (directory0700/files0600).
Setup takes a full backup. Local backups are under the owner-private
`~/.nightcap-gm/backups`. Incomplete dumps keep `.partial` and are never accepted.
Receipts name the successful backup. Backups are retained for owner review; no
automatic deletion of GM backups is introduced. Restore only after inspecting
the receipt and affected rows; never blindly restore an entire old database over
new player progress.

The stable receipt fingerprint key and local maintenance marker live under
`~/.nightcap-gm`, with Windows inheritance removed and access granted to the owner
SID. Production maintenance ownership persists in `private/gm-maintenance.json`.
Every SQL writer holds `nightcap_gm_writes` on its database connection before
acquiring the SSH lease. Resume refuses while that fence is held; lease loss
destroys the writer's connection so unfinished transactions roll back.

## Verification actually performed

- Build and Vue type checking pass. `npm audit` reports zero vulnerabilities.
- Four HTTP/SSH checks and twelve isolated MariaDB scenarios pass: browser boundary,
  read-only production enforcement, SSH lease rejection/cancellation
  and isolated MariaDB tests for target isolation, offline guard, duplicate grants,
  validation/backup failure, level/zone semantics, multiclass skills, namespace
  resets, deletion rollback, rule/progression atomicity, backend restart receipts
  and lease-loss rollback/fence release.
- Six Python helper tests pass, including partial startup recovery and refusal
  to resume across an active database fence.
- Seven Chrome tests pass, including target switching, one-time code display,
  reload recovery, partial maintenance controls, mobile layout and two-tab races.
  Desktop and390px screenshots inspected.
- Actual production read-only smoke: 6 accounts, 14 characters, 482 base zones,
  4 configured editable rules; active ruleset1 and password mode14. These are
  dated observations, not permanent counts. Status/era/access/MOTD reads pass.
- The exact helper was rehearsed with fixed QA identities in disposable Docker
  containers: shutdown, real gzip database backup, refusal to resume while a
  database fence was held, health-gated startup and marker removal passed. Worker
  containers used a harmless Python process, not the live native game. All five
  production container IDs/start timestamps/running states were unchanged.
- Independent review found no remaining coding blocker after the lease/fence,
  persistent recovery and cross-tab fixes; it independently reran the three
  browser recovery scenarios successfully.
- Disposable containers/network were removed. No live account, character, rule,
  content, access registry or runtime state was mutated by these tests.

Reproducible tests are under `eq-solo-gm/tests/`. `database.test.cjs` needs the
explicit disposable `GM_FIXTURE_HOST`; the standard unit command skips it without
that setting. `fixture-lifecycle.py` creates/removes only fixed labeled fixtures;
`rehearse_maintenance.py` accepts the helper source through its trusted test driver.
The sanitized [verification record](../releases/production-gm-verification-20261010.json)
records the observed results and the remaining acceptance boundary.

## Promotion and exact owner QA

Follow feature → dev → test. Main and production activation require owner sign-off,
which the owner supplied for this release. The GM activation above is complete.
The startup script refuses its production-write flag unless HEAD is contained in
origin/main. After approval, start the reviewed tool with production writes enabled
and run the explicit setup action. The player registry/helper and gateway rollout
must follow PLAYER-ACCESS.md, including the scoped Cloudflare native-route change.
GM code generation alone does not remove Cloudflare's old player-IP restriction.

Use a disposable game account/character for acceptance:

1. Open the tool, choose Production, verify expected names and environment labels.
   Switch Local/Production while a read is loading; old selections must disappear.
2. Reset the QA account's password while the game is running. Old password must
   fail and new password must log in. Unrelated accounts must be unchanged.
3. Issue one code, use it in the updated launcher, connect after changing networks,
   revoke it and verify disconnect/rejection. Retry a game login separately.
4. Announce maintenance to players, Start maintenance, verify the whole supervised
   game and gateway are stopped. On the QA character grant10 platinum and2 AA,
   set a legal level, raise combat skills and teleport to Plane of Knowledge
   (`poknowledge`, zone202, safe coordinates from the zone picker).
5. Resume game; verify healthy runtime before gateway opens. Log in the QA
   character: exact grants, level, skill eligibility and PoK location must persist
   through logout/login. A second click/reload must not duplicate either grant.
6. Mark/unmark one Classic progression group; verify every checkbox changes as
   one action. During another maintenance session change one XP rule/MOTD and
   restore its original value, checking receipts and the active ruleset only.
7. Restore canonical merchant stock only in the reviewed content QA window; visit
   the sixteen PoK class merchants (NPC997900–997915, merchant99300–99315), verify
   expected class/level catalog and no more than500 visible slots per merchant.
8. Try deleting an account that owns a character: it must refuse. Delete only the
   empty QA account after its character ownership is separately resolved.
9. Close/reopen the GM app during maintenance. Resume must remain available.
   A failed startup must keep the gateway closed and retain recovery controls.

Rollback of the GM app: stop its owner-local Node process and return to the prior
tool build. Leave production writes disabled. Preserve receipts, backups and any
maintenance marker; if maintenance is active, finish/recover it before removing
the new tool. Do not use the old unauthenticated API against production. Player
gateway/launcher rollback is separate and documented in PLAYER-ACCESS.md.
