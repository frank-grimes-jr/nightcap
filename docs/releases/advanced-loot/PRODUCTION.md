# Advanced loot: production deployment

Deployed **September 30, 2026** to `play.nightcapgame.org`, following the owner's
explicit instruction: "Push straight to main and the live server. I'll test live."
[PR 91](https://github.com/frank-grimes-jr/nightcap/pull/91) merged directly into
main at `0f7d089610a1a3e33ff7324e187f04c19079a846`. This is the requested release
exception; native graphical/gameplay acceptance remains open.

**Restart through the usual Nightcap starter**, install game release
**2026093006**, then enter `/advloot`. The existing launcher 0.3.1 supports the
signed catalog; no separate launcher installation is required.
[Exact owner live QA](LIVE-QA.md) starts with natural skeleton kills and Bone Chips
in East Commonlands. The original RoF2 installation remains read-only.

## Shipped

Native advanced-loot window, automatic display, searchable per-character saved
filters, Always loot/Never/Ask, personal Loot/Leave/all, shared assignment,
Need/Greed/Pass, free grab, corpse finding and coin splitting. The server retains
native rights, 25-unit collection range, lore/NO TRADE restrictions and checked
inventory placement. Item/coin receipts protect saved-state replay. No drop rates,
era settings or character power changed. [Detailed behavior](README.md).

The package also retains the current classic models, pet UI and enchanter command
fix. The local isolated QA port cutover was superseded and was not performed.

## Build and deployment evidence

- Fresh paired **world/zone** build over the exact hardened production source.
  All 24 changed source paths were allowlisted; source and baseline hashes stayed
  unchanged during compilation. Independent review found no hardening regression.
  Loginserver, UCS and shared-memory binaries were retained byte for byte.
- Image: `nightcap-game:advanced-loot-20260930`.
- Image ID: `sha256:c02b2b3ceb1e64ea99226384cd22a6d51c8e9da82b264580f41b0cc901de7d5f`.
- World SHA256: `12c11b3f34f65e994c1ed06e02c45c0a9162fd05e640322acb70a67eab34b70e`.
- Zone SHA256: `8414c0f5885b944d5971ca28fc950c8c6847b64f87741b22e28df9f994ae02f6`.
- Production preflight passed image/native hashes, crypto self-test, exact
  inventory column order, transactional transfer tables and absent triggers.
- Clean game shutdown; complete private PEQ backup restored into a disposable
  database; three-table additive migration rehearsed and then applied live.
  All **47** existing player/rule/merchant/saved-state fingerprints matched.
  Runtime quest/plugin/Lua hashes matched; normal market startup rotation passed.
- Actual game database account passed rolled-back settings/filter/claim writes,
  reads and updates. No probe rows remained. Schema and permissions were checked
  again before opening access.
- All **15** native process hashes matched, including twelve zone workers.
  Healthy startup, zero unexpected restarts and the startup error scans passed.
- Signed release **2026093006**: **46 files**, 148,693,711 bytes; 63 patch sites
  and 15 required features. Public HTTPS downloads matched every file and the
  signature verified against the production public key already shipped.
  Channel SHA256: `4698296da56f328241c96ab7051f7458585da603c6c8307f623ee838a807fa99`.
  Manifest expiry: `2026-10-30T20:58:22Z`.
- The gateway remained closed through publication and verification, then opened
  successfully. All four encrypted public native handshakes passed: login 5998,
  world 9000, chat 7778 and zone 7000. Desktop/starter/guide files were unchanged.
- **13** isolated rollout fault tests passed. Final independent operational
  review found no concrete blocker. [Archived operations](ops/README.md).

Summary: [production.json](production.json). Exact package hashes:
[server](production-package-manifest.json), [client](production-client-audit.json).
The compressed production source manifest and build/configure logs are retained
beside these records. Earlier implementation fixture evidence remains in [README](README.md).

Detailed rollout evidence and the full backup remain private on the production
host. Automatic approval review declined copying that evidence locally because
it may contain internal metadata. This record uses the successful deployment
command outcomes and public/local artifact verification; it does not contain
private player rows, credentials or backup contents.

## Acceptance still required

Compilation, fixtures, signed installation/startup, process health and transport
checks do not prove rendered controls or real player looting. The owner will run
[LIVE-QA.md](LIVE-QA.md). Actual native NO TRADE/lore, quests, raid changes, UI
reload and saved-checkpoint fault/replay cases remain open until recorded. Keep
synthetic drops and injected persistence faults in the [isolated plan](QA.md).

## Recovery

Host server package: `/opt/nightcap/releases/advanced-loot-20260930`.
Private backup/evidence: `/opt/nightcap/releases/advanced-loot-evidence-20260930`.
Signed client stage: `/opt/nightcap/releases/advanced-loot-client-2026093006`.

The new receipt-aware server has started. **Do not activate an older server or
restore the pre-release PEQ dump as an ordinary rollback.** Unreconciled saved
corpses can resurrect awarded items; restoring a dump also erases later progress.
Keep the claims, preferences, saved checkpoints and current player data.

Players can turn off **Advanced loot** in the window and use classic corpse
looting. Classic NPC pickup remains on the receipt-aware transfer path.
For an operator emergency, close access and stop the game with the deployed
helper under the existing lock:

```sh
sudo flock -n /opt/nightcap/deploy/production/.deployment.lock python3 /opt/nightcap/releases/advanced-loot-20260930/rollout.py hold
```

This preserves data for investigation. Repair forward with receipt-aware code,
a fresh preservation baseline and reviewed checkpoint/receipt reconciliation.
The original `open` action is an initial-release gate, not a general reopen
after live player activity. Old enchanter/pet deployment rollback helpers are
not valid for this current image. Do not delete claims to unblock an award.
